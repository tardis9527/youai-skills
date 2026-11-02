"""Behavior regressions for complete songs, model routing and resource tracking."""
from __future__ import annotations

import copy
import json
import sys
import unittest
import wave
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/mv-creator/scripts"
sys.path.insert(0, str(SCRIPTS))
import mv
from mvlib import comfy, media, music, shots
from mvlib.common import DEFAULT_CONFIG, VIDEO_PROFILES, MVError, Project, read_json, video_frames, write_json
from mvlib.runs import RunMonitor


def wav(path, seconds):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as f:
        f.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        f.writeframes(b"\0\0" * round(seconds * 8000))


class OptimizationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = copy.deepcopy(DEFAULT_CONFIG)
        self.cfg.update(_root=self.tmp.name)
        self.project = Project(self.cfg, "demo")
        self.project.save({"video": dict(DEFAULT_CONFIG["video"]),
                           "music": {"duration_sec": 60, "takes": []}})
        path = self.project.root / "music/caption.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("完整歌曲，自然收尾", encoding="utf-8")

    def args(self, *args):
        return mv.build_parser().parse_args(args)

    def song_settings(self, *args, stored=None):
        return music.settings(self.args("music", "demo", *args), stored or {}, self.cfg["music"])

    def test_song_target_and_limit_are_separate_and_legacy_keeps_meaning(self):
        self.assertEqual(self.song_settings(), (60, 90))
        self.assertEqual(self.song_settings("--target-duration", "45"), (45, 75))
        self.assertEqual(self.song_settings("--duration", "45"), (45, 45))
        self.assertEqual(self.song_settings(stored={"target_duration_sec": 45, "generation_max_duration_sec": 45}), (45, 45))
        self.assertEqual(self.song_settings("--target-duration", "60", "--max-duration", "75"), (60, 75))
        self.assertEqual(self.song_settings(stored={"target_duration_sec": 50, "generation_max_duration_sec": 80}), (50, 80))
        self.assertEqual(self.song_settings("--target-duration", "40", stored={"generation_max_duration_sec": 90}), (40, 70))

    def test_bad_music_parameters_rejected_without_submission(self):
        for options in [("--target-duration", "0"), ("--target-duration", "nan"),
                        ("--max-duration", "inf"), ("--max-duration", "59"),
                        ("--duration", "60", "--max-duration", "90")]:
            with self.subTest(options=options), self.assertRaises(MVError):
                self.song_settings(*options)

    def test_music_dry_run_does_not_update_project_or_call_comfy(self):
        before = self.project.project_file.read_bytes()
        with patch.object(comfy, "run_kind") as run, redirect_stdout(StringIO()):
            mv.cmd_music(self.args("music", "demo", "--dry-run"), self.cfg)
        run.assert_not_called()
        self.assertEqual(before, self.project.project_file.read_bytes())

    def test_music_records_real_duration_near_limit_and_prompt_id(self):
        def run(cfg, kind, values, uploads, subfolder, dest, stem):
            self.assertEqual(values["max_duration"], 90)
            path = dest / f"{stem}.wav"
            wav(path, 89.99)
            write_json(dest / f"{stem}.run.json", {"prompt_id": "song-job"})
            return [path]
        with patch.object(comfy, "run_kind", side_effect=run), redirect_stdout(StringIO()):
            mv.cmd_music(self.args("music", "demo"), self.cfg)
        song = self.project.load()["music"]
        take = song["takes"][0]
        self.assertEqual(song["target_duration_sec"], 60)
        self.assertAlmostEqual(take["duration_sec"], 89.99)
        self.assertTrue(take["near_limit"])
        self.assertEqual(take["ending_review"], "pending_listen")
        self.assertEqual(take["prompt_id"], "song-job")

    def test_successful_take_survives_probe_failure(self):
        path = self.project.root / "music/takes/take-1.wav"
        wav(path, 2)
        with patch.object(comfy, "run_kind", return_value=[path]), \
             patch.object(music, "inspect", side_effect=MVError("probe missing")), redirect_stdout(StringIO()):
            mv.cmd_music(self.args("music", "demo"), self.cfg)
        take = self.project.load()["music"]["takes"][0]
        self.assertTrue(self.project.path(take["file"]).is_file())
        self.assertEqual(take["probe_error"], "probe missing")

    def test_music_check_uses_original_recorded_limit(self):
        path = self.project.root / "music/takes/take-1.wav"
        wav(path, 4.99)
        meta = self.project.load()
        meta["music"]["takes"] = [{"id": "take-1", "file": self.project.rel(path), "max_duration": 5}]
        self.project.save(meta)
        with redirect_stdout(StringIO()):
            mv.cmd_music_check(self.args("music-check", "demo"), self.cfg)
        self.assertTrue(self.project.load()["music"]["takes"][0]["near_limit"])

    def test_export_blocks_short_timeline_before_creating_files(self):
        path = self.project.root / "music/song.wav"
        wav(path, 6)
        meta = self.project.load()
        meta["music"]["file"] = self.project.rel(path)
        self.project.save(meta)
        self.project.save_shots({"shots": [shots.new_shot(1, 0, 4, "1")]})
        with self.assertRaisesRegex(MVError, "截断歌曲"):
            media.package(self.project, self.cfg)
        with patch.object(media, "ffmpeg_bin", return_value="ffmpeg"), \
             patch.object(media, "_run") as run, self.assertRaisesRegex(MVError, "截断歌曲"):
            media.roughcut(self.project, self.cfg, False)
        run.assert_not_called()
        self.assertFalse((self.project.root / "final").exists())
        self.assertEqual(music.require_full_song(self.project, self.cfg, 6), 6)

    def test_wan_frame_grid_and_h3_remain_distinct(self):
        video = VIDEO_PROFILES["wan5b"]
        self.assertEqual(video_frames(5, video), 121)
        self.assertEqual(video_frames(1, video), 25)
        self.assertEqual(video_frames(9, video), 121)
        self.assertEqual(video_frames(5, VIDEO_PROFILES["h3"]), 124)
        with self.assertRaises(MVError):
            video_frames(5, dict(video, max_frames=124))

    def test_profile_dry_run_then_change_preserves_history_and_clips(self):
        shot = shots.new_shot(1, 0, 5, "1")
        shot["clip"]["takes"] = [{"id": "take-1", "file": "old.mp4", "model": "minimax-h3"}]
        self.project.save_shots({"shots": [shot]})
        original = self.project.project_file.read_bytes()
        with redirect_stdout(StringIO()):
            mv.cmd_video_profile(self.args("video-profile", "demo", "wan5b", "--dry-run"), self.cfg)
            self.assertEqual(self.project.project_file.read_bytes(), original)
            mv.cmd_video_profile(self.args("video-profile", "demo", "wan5b"), self.cfg)
        self.assertEqual(self.project.video()["model"], "wan2.2-5b")
        self.assertEqual(self.project.load()["video_history"][0]["video"]["model"], "minimax-h3")
        self.assertEqual(self.project.load_shots()["shots"][0]["clip"], shot["clip"])

    def test_profile_rejects_flf2v_and_overlong_shots_without_changing_state(self):
        for shot in [dict(shots.new_shot(1, 0, 4, "1"), workflow="flf2v"), shots.new_shot(1, 0, 6, "1")]:
            self.project.save_shots({"shots": [shot]})
            before = self.project.project_file.read_bytes()
            with self.assertRaises(MVError):
                mv.cmd_video_profile(self.args("video-profile", "demo", "wan5b"), self.cfg)
            self.assertEqual(before, self.project.project_file.read_bytes())

    def test_wan_clips_use_new_graph_and_record_model_and_true_frame_duration(self):
        meta = self.project.load(); meta["video"] = VIDEO_PROFILES["wan5b"]; self.project.save(meta)
        shot = dict(shots.new_shot(1, 0, 5, "1"), motion_prompt="缓慢转头")
        path = self.project.root / "frames/S01.png"
        path.parent.mkdir(parents=True); path.write_bytes(b"placeholder")
        shot["frame"]["selected"] = self.project.rel(path)
        self.project.save_shots({"shots": [shot]})
        def run(cfg, kind, values, uploads, subfolder, dest, stem):
            self.assertEqual(kind, "wan5b-i2v")
            spec, graph, _ = comfy.load_kind(cfg, kind)
            graph = comfy.apply_params(graph, spec, dict(values, image="frame.png"))
            self.assertEqual(graph["55"]["inputs"]["length"], 121)
            self.assertEqual(graph["57"]["inputs"]["fps"], 24)
            self.assertEqual(graph["8"]["class_type"], "VAEDecodeTiled")
            p = dest / f"{stem}.mp4"; p.parent.mkdir(parents=True); p.write_bytes(b"video")
            return [p]
        with patch.object(comfy, "run_kind", side_effect=run), redirect_stdout(StringIO()):
            mv.cmd_clips(self.args("clips", "demo"), self.cfg)
        take = self.project.load_shots()["shots"][0]["clip"]["takes"][0]
        self.assertEqual(take["model"], "wan2.2-5b")
        self.assertAlmostEqual(take["duration_sec"], 121 / 24)


class ServerValidationTest(unittest.TestCase):
    def test_run_records_submitted_values_outputs_and_id(self):
        with TemporaryDirectory() as tmp:
            cfg = copy.deepcopy(DEFAULT_CONFIG); cfg["_root"] = tmp
            spec, graph, _ = comfy.load_kind(cfg, "music")
            client = Mock(); client.url = "http://test:8188"
            client.object_info.return_value = {n["class_type"]: {"input": {}} for n in graph.values()}
            client.get_json.return_value = {"queue_running": [], "queue_pending": []}
            client.system_stats.return_value = {"system": {}, "devices": []}
            client.queue.return_value = "job-123"
            def wait(prompt_id, on_poll):
                self.assertEqual(prompt_id, "job-123"); on_poll()
                return {"outputs": {"35": {"audio": [{"filename": "song.wav", "type": "output"}]}}}
            client.wait.side_effect = wait
            def download(item, dest): wav(dest, 1); return dest
            client.download.side_effect = download
            with patch.object(comfy.ComfyClient, "from_config", return_value=client), redirect_stdout(StringIO()):
                files = comfy.run_kind(cfg, "music", {"caption": "song", "max_duration": 90, "seed": 42},
                                       {}, "mv", Path(tmp), "take-1")
            self.assertTrue(files[0].is_file())
            submitted = client.queue.call_args.args[0]
            self.assertEqual(submitted["37:13"]["inputs"]["max_duration"], 90)
            record = read_json(Path(tmp) / "take-1.run.json")
            self.assertEqual(record["prompt_id"], "job-123")
            self.assertEqual(record["status"], "success")
            self.assertEqual(record["parameters"]["max_duration"], 90)
            self.assertEqual(record["files"], ["take-1.wav"])

    def test_wait_failure_preserves_id_and_incomplete_status(self):
        with TemporaryDirectory() as tmp:
            cfg = copy.deepcopy(DEFAULT_CONFIG); cfg["_root"] = tmp
            _, graph, _ = comfy.load_kind(cfg, "music")
            client = Mock(); client.url = "http://test:8188"
            client.object_info.return_value = {n["class_type"]: {"input": {}} for n in graph.values()}
            client.get_json.return_value = {"queue_running": [], "queue_pending": []}
            client.system_stats.return_value = {"system": {}, "devices": []}
            client.queue.return_value = "still-running"
            client.wait.side_effect = MVError("timeout")
            with patch.object(comfy.ComfyClient, "from_config", return_value=client), \
                 redirect_stdout(StringIO()), self.assertRaisesRegex(MVError, "timeout"):
                comfy.run_kind(cfg, "music", {"caption": "song", "max_duration": 90},
                               {}, "mv", Path(tmp), "take-1")
            record = read_json(Path(tmp) / "take-1.run.json")
            self.assertEqual(record["prompt_id"], "still-running")
            self.assertEqual(record["status"], "incomplete")
            client.download.assert_not_called()

    def test_missing_weights_and_out_of_range_duration_fail_preflight(self):
        workflow = {"e": {"class_type": "Encode", "inputs": {"max_duration": 400}},
                    "m": {"class_type": "UNETLoader", "inputs": {"unet_name": "missing"}}}
        info = {"Encode": {"input": {"required": {"max_duration": ["FLOAT", {"min": .04, "max": 360}]}}},
                "UNETLoader": {"input": {"required": {"unet_name": [["installed"], {}]}}}}
        problems = comfy.validate_server(workflow, info)
        self.assertEqual(len(problems), 2)
        self.assertIn("不静默截断", problems[0])
        self.assertIn("缺少模型", problems[1])

    def test_live_preflight_rejection_does_not_upload_free_or_submit(self):
        with TemporaryDirectory() as tmp:
            cfg = copy.deepcopy(DEFAULT_CONFIG); cfg["_root"] = tmp
            client = Mock(); client.object_info.return_value = {}
            with patch.object(comfy.ComfyClient, "from_config", return_value=client), self.assertRaises(MVError):
                comfy.run_kind(cfg, "music", {"caption": "p", "max_duration": 90}, {}, "mv", Path(tmp), "take-1")
            client.upload.assert_not_called(); client.queue.assert_not_called(); client._request.assert_not_called()


class RunMonitorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.cfg = copy.deepcopy(DEFAULT_CONFIG); self.cfg["_root"] = self.tmp.name
        self.client = Mock(); self.client.url = "http://test.local:8188"
        self.client.get_json.return_value = {"queue_running": [], "queue_pending": []}
        self.client.system_stats.return_value = {"system": {"ram_total": 100, "ram_free": 20},
                                                "devices": [{"index": 0, "vram_total": 12, "vram_free": 3}]}
        self.path = Path(self.tmp.name) / "take-1.run.json"

    def monitor(self, kind="music"):
        return RunMonitor(self.client, self.cfg, kind, self.path)

    def test_busy_queue_never_gets_free_request(self):
        self.client.get_json.return_value = {"queue_running": [[1]], "queue_pending": []}
        m = self.monitor()
        with redirect_stdout(StringIO()): m.prepare()
        self.client._request.assert_not_called()
        self.assertEqual(m.record["release"], "skipped_busy")

    def test_idle_stage_change_requests_free_and_same_stage_reuses_cache(self):
        m = self.monitor(); m.prepare(); m.finish("success")
        self.client._request.assert_called_once()
        self.client._request.reset_mock()
        self.monitor().prepare(); self.client._request.assert_not_called()
        self.monitor("wan5b-i2v").prepare(); self.client._request.assert_called_once()

    def test_samples_keep_peak_and_logs_exclude_prompt_text_and_secrets(self):
        m = self.monitor(); m.start({"node": {"api_key": "secret"}}, {"seed": 1, "lyrics": "private lyrics", "api_key": "secret"})
        self.client.system_stats.return_value["system"]["ram_free"] = 50
        m.submitted("job-42"); m.sample(); m.finish("success", ["take-1.wav"])
        record = read_json(self.path)
        self.assertEqual(record["sampled_ram_used_peak_bytes"], 80)
        self.assertEqual(record["sampled_vram_used_peak_bytes"], {"0": 9})
        self.assertEqual(record["prompt_id"], "job-42")
        self.assertGreaterEqual(record["resource_samples"], 3)
        text = self.path.read_text(encoding="utf-8")
        self.assertNotIn("secret", text); self.assertNotIn("private lyrics", text)

    def test_missing_telemetry_keeps_run_record_and_does_not_fail_job(self):
        self.client.system_stats.side_effect = MVError("not available")
        m = self.monitor(); m.start({}, {}); m.submitted("job"); m.finish("incomplete")
        self.assertTrue(read_json(self.path)["resources_unavailable"])
        self.assertEqual(read_json(self.path)["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
