"""Offline API lifecycle tests; no GPU, remote server or generation fees."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

SCRIPT = Path(__file__).resolve().parents[1] / "skills/comfyui-minimax-music/scripts/music.py"
SPEC = importlib.util.spec_from_file_location("music_runner", SCRIPT)
music = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(music)


def flac_header(rate=48000, seconds=2):
    # STREAMINFO test fixture. Full decoding is tested through a mocked decoder;
    # these bytes intentionally make no claim of valid compressed frames.
    packed = (rate << 44) | (1 << 41) | (15 << 36) | int(rate * seconds)
    return b"fLaC\x80\x00\x00\x22" + b"\x00" * 10 + packed.to_bytes(8, "big") + b"\x00" * 16 + b"fixture-frames"


def schema():
    def n(required, outputs):
        return {"input": {"required": required}, "output": outputs}
    string = ["STRING", {}]
    integer = ["INT", {"min": 0, "max": 2**64-1}]
    number = ["FLOAT", {"min": 0, "max": 100}]
    inputs = {
        "clip": ["CLIP"], "style": string, "lyrics": string, "seed": integer,
        "mode": [["full", "melody"]], "temperature": number, "top_p": number,
        "top_k": integer, "repetition_penalty": number,
    }
    return {
        "UNETLoader": n({"unet_name": [["minimax_music3_dit_fp16.safetensors"]], "weight_dtype": [["default"]]}, ["MODEL"]),
        "CLIPLoader": n({"clip_name": [["minimax_music3_text_encoder_pruned_int8_convrot.safetensors"]], "type": [["minimax"]], "device": [["default"]]}, ["CLIP"]),
        "VAELoader": n({"vae_name": [["minimax_music3_dav.safetensors"]]}, ["VAE"]),
        "MiniMaxMusic3TextEncode": n({"clip": ["CLIP"], "caption": string, "lyrics": string, "seed": integer,
                                       "max_duration": ["FLOAT", {"min": .04, "max": 360}], "cfg_scale": number, "top_k": integer}, ["CONDITIONING", "FLOAT"]),
        "CheckpointLoaderSimple": n({"ckpt_name": [["yue2_3b_int8_convrot.safetensors"]]}, ["MODEL", "CLIP", "VAE"]),
        "YuE2GenerateABC": n({**inputs, "max_abc_tokens": integer, "penalty_window": integer}, ["STRING"]),
        "YuE2GenerateMusic": n({**inputs, "abc": string, "max_duration": ["FLOAT", {"min": .04, "max": 900}]}, ["CONDITIONING", "FLOAT"]),
        "ConditioningZeroOut": n({"conditioning": ["CONDITIONING"]}, ["CONDITIONING"]),
        "EmptyMiniMaxMusic3LatentAudio": n({"seconds": ["FLOAT"], "batch_size": integer}, ["LATENT"]),
        "EmptyYuE2LatentAudio": n({"seconds": ["FLOAT"], "batch_size": integer}, ["LATENT"]),
        "KSampler": n({"seed": integer, "steps": integer, "cfg": number, "sampler_name": [["euler", "dpm_2"]],
                        "scheduler": [["simple", "sgm_uniform"]], "denoise": number, "model": ["MODEL"],
                        "positive": ["CONDITIONING"], "negative": ["CONDITIONING"], "latent_image": ["LATENT"]}, ["LATENT"]),
        "VAEDecodeAudio": n({"samples": ["LATENT"], "vae": ["VAE"]}, ["AUDIO"]),
        "VAEDecodeAudioTiled": n({"samples": ["LATENT"], "vae": ["VAE"], "tile_size": integer, "overlap": integer}, ["AUDIO"]),
        "SaveAudioAdvanced": n({"audio": ["AUDIO"], "filename_prefix": string, "format": ["COMFY_DYNAMICCOMBO_V3", {"options": [
            {"key": "flac", "inputs": {}}, {"key": "mp3", "inputs": {"required": {"quality": [["V0", "128k", "320k"]]}}}
        ]}]}, ["AUDIO"]),
    }


class Server:
    """Fake HTTP transport implementing native ComfyUI endpoint responses."""
    def __init__(self):
        self.info = schema()
        self.requests = []
        self.submissions = []
        self.pending = False
        self.execution_error = False
        self.lose_ack = False
        self.bad_audio = False
        self.reject = False

    def entry(self):
        payload = self.submissions[-1]
        graph = payload["prompt"]
        output = next(k for k, n in graph.items() if n["class_type"] == "SaveAudioAdvanced")
        return {"prompt": [0, "prompt-1", graph, payload["extra_data"], [output]],
                "status": {"completed": True, "status_str": "error" if self.execution_error else "success"},
                "outputs": {output: {"audio": [{"filename": "远端&歌.flac", "subfolder": "audio/music", "type": "output"}]}}}

    def open(self, request, timeout=60):
        self.requests.append(request)
        path = urlsplit(request.full_url).path.removeprefix("/comfy")
        if path == "/system_stats":
            value = {"system": {"comfyui_version": "fixture"}}
        elif path == "/object_info":
            value = self.info
        elif path == "/prompt":
            if self.reject:
                raise HTTPError(request.full_url, 400, "validation error", {}, BytesIO(b"private-token"))
            self.submissions.append(json.loads(request.data))
            if self.lose_ack:
                self.lose_ack = False
                raise TimeoutError()
            value = {"prompt_id": "prompt-1", "node_errors": {}}
        elif path.startswith("/history"):
            value = {} if self.pending or not self.submissions else {"prompt-1": self.entry()}
        elif path == "/queue":
            rows = [self.entry()["prompt"]] if self.pending and self.submissions else []
            value = {"queue_running": rows, "queue_pending": []}
        elif path == "/view":
            query = parse_qs(urlsplit(request.full_url).query)
            assert query["filename"] == ["远端&歌.flac"]
            return BytesIO(b"<html>login</html>" if self.bad_audio else flac_header())
        else:
            raise AssertionError(path)
        return BytesIO(json.dumps(value, ensure_ascii=False).encode())


class WorkflowTests(unittest.TestCase):
    def graph(self, model, **kwargs):
        return music.build_workflow(model, "自然中文描述", "[Verse]\n用户原词\n[Chorus]\n完整副歌", 75, 12345, "audio/test", **kwargs)

    def test_both_workflows_have_valid_schema_and_lossless_output(self):
        server = Server()
        with patch.object(music, "build_opener", return_value=server):
            for model in music.MODELS:
                spec, graph = self.graph(model)
                music.preflight(music.Client("https://example.com/comfy"), graph)
                for node in spec["output_nodes"]:
                    self.assertEqual(graph[node]["inputs"]["format"], "flac")

    def test_minimax_text_seeds_and_duration(self):
        _, graph = self.graph("minimax-music3")
        self.assertEqual(graph["37:13"]["inputs"]["caption"], "自然中文描述")
        self.assertEqual(graph["37:13"]["inputs"]["seed"], graph["37:9"]["inputs"]["seed"])
        self.assertEqual(graph["37:13"]["inputs"]["max_duration"], 75)
        self.assertEqual(graph["37:15"]["inputs"]["seconds"], ["37:13", 1])

    def test_yue_syncs_both_planning_inputs_and_sampler(self):
        spec, graph = self.graph("yue2", mode="melody")
        for key in ("style", "lyrics", "seed", "mode"):
            self.assertEqual(graph["24"]["inputs"][key], graph["25"]["inputs"][key])
        self.assertEqual(graph["8"]["inputs"]["seed"], 12345)
        self.assertEqual(graph["5"]["inputs"]["seconds"], ["25", 1])
        self.assertEqual(graph["25"]["inputs"]["abc"], [spec["abc_node"], 0])

    def test_yue_disabled_planning_has_no_abc_dependency(self):
        _, graph = self.graph("yue2", abc_planning=False)
        self.assertNotIn("24", graph)
        self.assertEqual(graph["25"]["inputs"]["abc"], "")
        # No leftover planning-node link remains anywhere.
        self.assertFalse(any(v == ["24", 0] for n in graph.values() for v in n["inputs"].values()))

    def test_missing_model_node_and_out_of_range_stop_before_submit(self):
        for fault in ("node", "model", "duration"):
            server = Server()
            _, graph = self.graph("yue2")
            if fault == "node":
                del server.info["YuE2GenerateMusic"]
            elif fault == "model":
                server.info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"] = [["other.safetensors"]]
            else:
                graph["25"]["inputs"]["max_duration"] = 901
            with patch.object(music, "build_opener", return_value=server):
                with self.assertRaises(music.MusicError):
                    music.preflight(music.Client("https://example.com/comfy"), graph)
            self.assertEqual(server.submissions, [])

    def test_invalid_connection_and_mapping_are_rejected(self):
        _, graph = self.graph("yue2")
        graph["5"]["inputs"]["seconds"] = ["25", 0]  # conditioning != float
        server = Server()
        with patch.object(music, "build_opener", return_value=server):
            with self.assertRaises(music.MusicError):
                music.preflight(music.Client("https://example.com/comfy"), graph)
        with TemporaryDirectory() as temp:
            spec, graph = self.graph("yue2")
            graph["24"]["class_type"] = "UnknownNode"
            music.write_json(Path(temp)/"yue2.params.json", spec)
            music.write_json(Path(temp)/"yue2.api.json", graph)
            with self.assertRaises(music.MusicError):
                self.graph("yue2", folder=temp)

    def test_ui_workflows_have_subgraphs_and_flac_widgets(self):
        for model in music.MODELS:
            ui = music.read_json(music.SKILL / "workflows" / f"{model}.workflow.json")
            self.assertTrue(ui["definitions"]["subgraphs"])
            save = next(n for n in ui["nodes"] if n["type"] == "SaveAudioAdvanced")
            self.assertEqual(save["widgets_values"][1], "flac")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/"description.txt").write_text("中文风格，清晰人声", encoding="utf-8")
        (self.root/"lyrics.txt").write_text("[Verse]\n用户原词", encoding="utf-8")
        self.server = Server()
        self.patchers = [patch.object(music, "build_opener", return_value=self.server),
                         patch.object(music.shutil, "which", return_value=None),
                         patch.dict(music.os.environ, {"COMFYUI_TOKEN": "private-token"}, clear=True)]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.temp.cleanup()

    def call(self, args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = music.main(args)
        self.assertNotIn("private-token", out.getvalue()+err.getvalue())
        return code, out.getvalue(), err.getvalue()

    def run_song(self, model="yue2", more=()):
        return self.call(["run", "--url", "https://example.com/comfy", "--model", model,
                          "--title", "我的/歌", "--description-file", str(self.root/"description.txt"),
                          "--lyrics-file", str(self.root/"lyrics.txt"), "--duration", "2", "--max-duration", "3",
                          "--date", "2026-11-02", "--output-dir", str(self.root/"output"), *more])

    def state_file(self):
        return next(self.root.glob("output/**/run.json"))

    def resume(self, more=()):
        return self.call(["resume", "--url", "https://example.com/comfy", "--run-file", str(self.state_file()), *more])

    def test_end_to_end_both_models_preserve_original_and_pending_decode(self):
        for model in music.MODELS:
            code, out, err = self.run_song(model)
            self.assertEqual(code, 0, err)
            self.assertIn(".flac", out)
        self.assertEqual(len(self.server.submissions), 2)
        for state_file in self.root.glob("output/**/run.json"):
            state = music.read_json(state_file)
            self.assertEqual(state["status"], "downloaded_pending_decode")
            self.assertEqual(state["files"][0]["inspection"]["sample_rate"], 48000)
            self.assertEqual((state_file.parent/"lyrics.txt").read_text(encoding="utf-8"), "[Verse]\n用户原词")
            combined = "".join(f.read_text(encoding="utf-8") for f in state_file.parent.glob("*.json"))
            self.assertNotIn("private-token", combined)
            self.assertNotIn("https://example.com", combined)

    def test_timeout_then_resume_never_resubmits(self):
        self.server.pending = True
        self.assertEqual(self.run_song(more=["--timeout", ".01", "--poll-interval", ".001"])[0], 1)
        self.assertEqual(music.read_json(self.state_file())["status"], "waiting_timeout")
        self.server.pending = False
        self.assertEqual(self.resume()[0], 0)
        self.assertEqual(len(self.server.submissions), 1)

    def test_lost_submission_response_recovers_original_id(self):
        self.server.lose_ack = True
        self.assertEqual(self.run_song()[0], 1)
        self.assertEqual(music.read_json(self.state_file())["status"], "submission_unknown")
        self.assertEqual(self.resume()[0], 0)
        self.assertEqual(len(self.server.submissions), 1)
        self.assertEqual(music.read_json(self.state_file())["prompt_id"], "prompt-1")

    def test_unknown_submission_not_found_stops_without_retry(self):
        self.server.lose_ack = True
        self.run_song()
        self.server.submissions.clear()
        code, _, err = self.resume()
        self.assertEqual(code, 1)
        self.assertIn("不会自动重发", err)
        self.assertEqual(self.server.submissions, [])

    def test_download_failure_then_retry_reuses_prompt(self):
        self.server.bad_audio = True
        self.assertEqual(self.run_song()[0], 1)
        self.assertEqual(list(self.root.glob("output/**/*.part")), [])
        self.server.bad_audio = False
        self.assertEqual(self.resume()[0], 0)
        self.assertEqual(len(self.server.submissions), 1)

    def test_redownload_keeps_previous_file(self):
        self.run_song()
        self.assertEqual(self.resume(["--redownload"])[0], 0)
        self.assertEqual(len(list(self.state_file().parent.glob("*.previous-*"))), 1)
        self.assertEqual(len(self.server.submissions), 1)

    def test_download_resume_uses_saved_outputs_after_history_is_cleared(self):
        self.server.bad_audio = True
        self.run_song()
        before = len(self.server.requests)
        self.server.submissions.clear()  # Server history no longer has the original prompt.
        self.server.bad_audio = False
        self.assertEqual(self.resume()[0], 0)
        self.assertEqual(len(self.server.requests), before + 1)  # Only /view, no history or prompt.

    def test_explicit_rejection_records_failure_without_leaking_body(self):
        self.server.reject = True
        code, _, err = self.run_song()
        self.assertEqual(code, 1)
        self.assertIn("HTTP 400", err)
        self.assertEqual(music.read_json(self.state_file())["status"], "submission_rejected")
        self.assertEqual(self.server.submissions, [])

    def test_binding_a_foreign_prompt_id_is_rejected(self):
        self.server.lose_ack = True
        self.run_song()
        code, _, _ = self.resume(["--prompt-id", "another-prompt"])
        self.assertEqual(code, 1)
        self.assertEqual(len(self.server.submissions), 1)

    def test_failure_does_not_download_or_resubmit(self):
        self.server.execution_error = True
        self.assertEqual(self.run_song()[0], 1)
        self.assertEqual(music.read_json(self.state_file())["status"], "generation_failed")
        self.assertFalse(list(self.root.glob("output/**/*.flac")))
        self.assertEqual(len(self.server.submissions), 1)

    def test_readonly_check_retains_reverse_proxy_and_bearer(self):
        code, _, err = self.call(["check", "--url", "https://example.com/comfy", "--model", "yue2"])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.server.submissions, [])
        self.assertTrue(all(r.full_url.startswith("https://example.com/comfy/") for r in self.server.requests))
        self.assertTrue(all(r.get_header("Authorization") == "Bearer private-token" for r in self.server.requests))

    def test_resume_rejects_other_server_before_renaming(self):
        self.run_song()
        code, _, _ = self.call(["resume", "--url", "https://other.example", "--run-file", str(self.state_file()), "--redownload"])
        self.assertEqual(code, 1)
        self.assertFalse(list(self.state_file().parent.glob("*.previous-*")))

    def test_success_after_full_decode_and_failure_for_corruption(self):
        with patch.object(music.shutil, "which", return_value="ffmpeg"), patch.object(music.subprocess, "run") as decode:
            decode.return_value.returncode = 0
            self.assertEqual(self.run_song()[0], 0)
            self.assertEqual(music.read_json(self.state_file())["status"], "completed")
            decode.return_value.returncode = 1
            self.assertEqual(self.resume()[0], 1)


class FileTests(unittest.TestCase):
    def test_streaminfo_reports_real_values_and_rejects_lossy_or_empty(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)/"song.flac"
            path.write_bytes(flac_header())
            self.assertEqual(music.flac_info(path)["duration_sec"], 2)
            self.assertEqual(music.flac_info(path)["channels"], 2)
            for data in (b"ID3lossy.mp3", b"", b"fLaC", flac_header(seconds=0)):
                path.write_bytes(data)
                with self.assertRaises(music.MusicError):
                    music.flac_info(path)

    def test_only_designated_output_flac_is_accepted(self):
        spec = {"output_nodes": ["10"]}
        for item in ({"filename": "song.mp3", "type": "output"}, {"filename": "song.flac", "type": "temp"}):
            with self.assertRaises(music.MusicError):
                music.collect_outputs({"outputs": {"10": {"audio": [item]}}}, spec)
        with self.assertRaises(music.MusicError):
            music.collect_outputs({"outputs": {"other": {"audio": [{"filename": "song.flac", "type": "output"}]}}}, spec)

    def test_safe_titles_locks_and_url_secrets(self):
        self.assertEqual(music.safe_title("CON"), "song-CON")
        self.assertEqual(music.safe_title("../我的:歌."), "-我的-歌")
        for url in ("https://u:secret@host", "https://host?token=secret", "ftp://host"):
            with self.assertRaises(music.MusicError):
                music.Client(url)
        with TemporaryDirectory() as temp:
            with music.run_lock(temp):
                with self.assertRaises(music.MusicError):
                    with music.run_lock(temp):
                        pass
            self.assertFalse((Path(temp)/".running.lock").exists())


if __name__ == "__main__":
    unittest.main()
