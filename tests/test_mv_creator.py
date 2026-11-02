"""Offline checks for the mv-creator pipeline helpers."""

from __future__ import annotations

import json
import copy
import argparse
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "mv-creator" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import mv  # noqa: E402
from mvlib import comfy, frames, shots, media  # noqa: E402
from mvlib.common import (  # noqa: E402
    DEFAULT_CONFIG, MVError, Project, clip_frames, shot_limit_sec, video_frames, load_config, write_json,
)

VIDEO = dict(DEFAULT_CONFIG["video"])


def h3_workflow() -> dict:
    """H3 API shape after the official subgraph is expanded, with scalar sources."""
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": "x.png"}},
        "4": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
            "prompt": "pos", "first_frame": ["1", 0], "clip": ["7", 0],
            "width": 864, "height": 1536, "length": ["10", 1]}},
        "6": {"class_type": "RandomNoise", "inputs": {"noise_seed": ["8", 0]}},
        "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"}},
        "8": {"class_type": "PrimitiveInt", "inputs": {"value": 5}},
        "9": {"class_type": "SaveVideo", "inputs": {"filename_prefix": "video/ComfyUI"}},
        "10": {"class_type": "ComfyMathExpression", "inputs": {
            "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
            "values.a": ["11", 0]}},
        "11": {"class_type": "PrimitiveFloat", "inputs": {"value": 5}, "_meta": {"title": "@duration"}},
        "12": {"class_type": "CreateVideo", "inputs": {"fps": 24}},
    }


def i2v_spec() -> dict:
    path = SCRIPTS.parent / "workflows" / "i2v.params.json"
    return json.loads(path.read_text(encoding="utf-8"))


def analysis(bpm: float, lead: float, duration: float) -> dict:
    beat = 60 / bpm
    starts = [lead + i * 4 * beat for i in range(int((duration - lead) / (4 * beat)))]
    bars = [{"index": i + 1, "start": round(s, 3),
             "end": round(starts[i + 1] if i + 1 < len(starts) else duration, 3), "energy": 0.5}
            for i, s in enumerate(starts)]
    return {"duration": duration, "bars": bars}


class ClipFramesTest(unittest.TestCase):
    def test_frames_are_4n_plus_1_and_capped(self):
        self.assertEqual(clip_frames(1.6, 16, 81), 29)
        self.assertEqual(clip_frames(2.66, 16, 81), 45)
        self.assertEqual(clip_frames(5.22, 16, 81), 81)
        for duration in (0.3, 1.0, 2.5, 4.9):
            self.assertEqual((clip_frames(duration, 16, 81) - 1) % 4, 0)

    def test_h3_uses_24fps_grid_minimum_and_cap(self):
        self.assertEqual(video_frames(1.6, VIDEO), 124)
        self.assertEqual(video_frames(5, VIDEO), 124)
        self.assertEqual(video_frames(10, VIDEO), 124)
        extended = dict(VIDEO, max_frames=362)
        self.assertEqual(video_frames(5.2, extended), 141)
        self.assertEqual(video_frames(15, extended), 362)
        for duration in (0.3, 4.9, 5.2, 8, 15):
            count = video_frames(duration, extended)
            self.assertEqual(count % 17, 5)
            seconds = count / 24
            rounded = round(seconds * 24)
            self.assertEqual(rounded + (5 - rounded % 17) % 17, count)

    def test_h3_rejects_legacy_timing_and_invalid_grid(self):
        for override in ({"fps": 16}, {"max_frames": 81}, {"max_frames": 125}, {"max_frames": 379}):
            with self.subTest(override=override), self.assertRaises(MVError):
                video_frames(5, dict(VIDEO, **override))


class SkeletonTest(unittest.TestCase):
    def test_shots_are_contiguous_and_within_limit(self):
        data = shots.skeleton(analysis(92, 1.6, 46.0), VIDEO, bars_per_shot=2)
        cuts = data["shots"]
        self.assertEqual(cuts[0]["start"], 0.0)
        self.assertEqual(cuts[-1]["end"], 46.0)
        self.assertEqual(cuts[0]["bars"], "前奏")
        for prev, cur in zip(cuts, cuts[1:]):
            self.assertAlmostEqual(prev["end"], cur["start"], places=3)
        for shot in cuts:
            self.assertLessEqual(shot["end"] - shot["start"], shot_limit_sec(VIDEO) + 1e-6)
        # 92 BPM: two bars (~5.2 s) fit within the slack, so shots stay two bars long.
        self.assertEqual(len(cuts), 10)

    def test_slow_tempo_falls_back_to_one_bar(self):
        data = shots.skeleton(analysis(70, 0.2, 40.0), VIDEO, bars_per_shot=2)
        self.assertTrue(all(s["end"] - s["start"] <= shot_limit_sec(VIDEO) + 1e-6 for s in data["shots"]))


class CheckTest(unittest.TestCase):
    def test_reports_missing_prompts_and_overlong_shots(self):
        data = {"characters": [], "shots": [shots.new_shot(1, 0, 7.0, "1-2")]}
        errors, _ = shots.check(data, VIDEO, None, draft=False)
        joined = "\n".join(errors)
        self.assertIn("超过单段上限", joined)
        self.assertIn("image_prompt 为空", joined)

    def test_flf2v_on_last_shot_is_rejected(self):
        shot = shots.new_shot(1, 0, 4.0, "1")
        shot.update(scene="s", image_prompt="i", motion_prompt="m", workflow="flf2v")
        errors, _ = shots.check({"characters": [], "shots": [shot]}, VIDEO, None, draft=False)
        self.assertTrue(any("flf2v" in e for e in errors))

    def test_srt_splits_lines(self):
        shot = shots.new_shot(1, 1.6, 6.817, "1-2")
        shot["lyric"] = "雨落在便利店门口/我没撑伞"
        self.assertEqual(shots.to_srt([shot]),
                         "1\n00:00:01,600 --> 00:00:06,817\n雨落在便利店门口\n我没撑伞\n")


class ApplyParamsTest(unittest.TestCase):
    def test_injects_into_template_without_titles(self):
        patched = comfy.apply_params(h3_workflow(), i2v_spec(), {
            "image": "mv-creator/demo/S01.png", "positive": "雨丝落下",
            "width": 864, "height": 1536, "duration": 124 / 24, "seed": 42, "filename_prefix": "mv/S01"})
        self.assertEqual(patched["1"]["inputs"]["image"], "mv-creator/demo/S01.png")
        self.assertEqual(patched["4"]["inputs"]["prompt"], "雨丝落下")
        self.assertEqual([patched["4"]["inputs"][k] for k in ("width", "height")], [864, 1536])
        self.assertEqual(patched["4"]["inputs"]["length"], ["10", 1])
        self.assertEqual(patched["11"]["inputs"]["value"], 124 / 24)
        self.assertEqual(patched["8"]["inputs"]["value"], 42)  # seed fed through a primitive node
        self.assertEqual(patched["9"]["inputs"]["filename_prefix"], "mv/S01")

    def test_duration_title_overrides_automatic_match(self):
        workflow = h3_workflow()
        # Prefer the marked duration source when another float is present.
        workflow["20"] = {"class_type": "PrimitiveFloat", "inputs": {"value": 99}}
        patched = comfy.apply_params(workflow, i2v_spec(), {"image": "a.png", "positive": "p", "duration": 6})
        self.assertEqual(patched["11"]["inputs"]["value"], 6)
        self.assertEqual(patched["20"]["inputs"]["value"], 99)

    def test_ambiguous_and_unknown_params_fail(self):
        workflow = h3_workflow()
        workflow["20"] = {"class_type": "LoadImage", "inputs": {"image": "b.png"}}
        workflow["21"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"first_frame": ["20", 0]}}
        with self.assertRaises(MVError):
            comfy.apply_params(workflow, i2v_spec(), {"image": "a.png", "positive": "p"})
        with self.assertRaises(MVError):
            comfy.apply_params(h3_workflow(), i2v_spec(), {"image": "a.png", "positive": "p", "typo": 1})

    def test_validate_reports_nothing_for_template(self):
        self.assertEqual(comfy.validate_kind(h3_workflow(), i2v_spec()), [])

    def test_music_seed_updates_shared_seed_node_and_separate_sampler(self):
        workflow = {
            "37:13": {"class_type": "MiniMaxMusic3TextEncode", "inputs": {
                "caption": "old", "lyrics": "old", "max_duration": 60, "seed": ["37:38", 0]}},
            "37:38": {"class_type": "SeedNode", "inputs": {"seed": 123}},
            "37:9": {"class_type": "KSampler", "inputs": {"seed": ["37:38", 0]}},
            "40": {"class_type": "KSampler", "inputs": {"seed": 456}},
        }
        spec = json.loads((SCRIPTS.parent / "workflows/music.params.json").read_text(encoding="utf-8"))
        self.assertEqual(comfy.validate_kind(workflow, spec), [])
        patched = comfy.apply_params(workflow, spec, {"caption": "新歌", "seed": 42})
        self.assertEqual(patched["37:38"]["inputs"]["seed"], 42)
        self.assertEqual(patched["40"]["inputs"]["seed"], 42)
        self.assertEqual(patched["37:13"]["inputs"]["seed"], ["37:38", 0])
        self.assertEqual(patched["37:9"]["inputs"]["seed"], ["37:38", 0])
        self.assertEqual(workflow["37:38"]["inputs"]["seed"], 123)

    def test_computed_width_is_reported_before_execution(self):
        workflow = h3_workflow()
        workflow["4"]["inputs"]["width"] = ["10", 1]
        problems = comfy.validate_kind(workflow, i2v_spec())
        self.assertEqual(len(problems), 1)
        self.assertIn("width", problems[0])
        self.assertIn("连线", problems[0])
        with self.assertRaises(MVError):
            comfy.apply_params(workflow, i2v_spec(), {"image": "a.png", "positive": "p", "width": 864})
        self.assertEqual(workflow["4"]["inputs"]["width"], ["10", 1])

    def test_primitive_chain_and_cycle(self):
        workflow = h3_workflow()
        workflow["8"]["inputs"]["value"] = ["20", 0]
        workflow["20"] = {"class_type": "PrimitiveInt", "inputs": {"value": 7}}
        patched = comfy.apply_params(workflow, i2v_spec(), {"image": "a.png", "positive": "p", "seed": 42})
        self.assertEqual(patched["20"]["inputs"]["value"], 42)
        workflow["20"]["inputs"]["value"] = ["8", 0]
        self.assertTrue(any("循环" in p for p in comfy.validate_kind(workflow, i2v_spec())))

    def test_ui_format_is_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui.json"
            path.write_text(json.dumps({"nodes": [], "links": []}), encoding="utf-8")
            with self.assertRaises(MVError):
                comfy.load_api_workflow(path)

    def test_collect_outputs_skips_temp_previews(self):
        entry = {"outputs": {"9": {"images": [{"filename": "S01_00001_.mp4", "type": "output"}],
                                   "animated": [True]},
                             "10": {"images": [{"filename": "preview.png", "type": "temp"}]}}}
        self.assertEqual([f["filename"] for f in comfy.collect_outputs(entry)], ["S01_00001_.mp4"])


class FramePromptTest(unittest.TestCase):
    def test_crop_note_matches_tardis_portrait_size(self):
        self.assertIn("左右各约 8%", frames.crop_note("1024x1536", 720, 1280))
        self.assertIn("上下", frames.crop_note("1024x1536", 720, 720))

    def test_shot_prompt_numbers_reference_images(self):
        data = {"style": "冷色霓虹"}
        shot = dict(shots.new_shot(1, 0, 4, "1"), image_prompt="中景，林夏站在屋檐下")
        prompt = frames.shot_prompt(data, shot, [{"id": "lead", "name": "林夏"}], VIDEO, "1024x1536")
        self.assertIn("参考图 1：角色「林夏」", prompt)
        self.assertIn("整体视觉风格：冷色霓虹", prompt)


class CommandHelpersTest(unittest.TestCase):
    def test_visual_commands_default_to_one_and_allow_explicit_variants(self):
        parser = mv.build_parser()
        for command, option, field in (("chars", "--n", "n"), ("frames", "--n", "n"),
                                       ("clips", "--takes", "takes")):
            with self.subTest(command=command):
                self.assertEqual(getattr(parser.parse_args([command, "demo"]), field), 1)
                self.assertEqual(getattr(parser.parse_args([command, "demo", option, "2"]), field), 2)
        self.assertEqual(parser.parse_args(["music", "demo"]).takes, 4)
        self.assertEqual(parser.parse_args(["voice", "demo"]).takes, 2)

    def test_frames_generate_one_per_shot_and_resume_without_duplicates(self):
        with TemporaryDirectory() as tmp:
            cfg = dict(DEFAULT_CONFIG, _root=tmp)
            project = Project(cfg, "demo")
            project.save({"video": dict(VIDEO)})
            scene = [dict(shots.new_shot(i, (i - 1) * 2, i * 2, str(i)), image_prompt="夜景")
                     for i in (1, 2)]
            project.save_shots({"shots": scene})
            args = mv.build_parser().parse_args(["frames", "demo"])
            calls = []

            def fake_tardis(config, mode, prompt, prompt_file, out, images, n):
                self.assertEqual(n, 1)
                calls.append(out)
                if len(calls) == 2:
                    raise MVError("interrupted")
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(b"image placeholder")
                return [out]

            with patch.object(frames, "run_tardis", side_effect=fake_tardis), redirect_stdout(StringIO()):
                with self.assertRaisesRegex(MVError, "interrupted"):
                    mv.cmd_frames(args, cfg)
                mv.cmd_frames(args, cfg)
                mv.cmd_frames(args, cfg)
            self.assertEqual([p.stem for p in calls], ["S01-v01", "S02-v01", "S02-v01"])
            self.assertEqual([len(s["frame"]["candidates"]) for s in project.load_shots()["shots"]], [1, 1])

    def test_fixed_seed_steps_per_take(self):
        self.assertEqual([mv._take_seed(7, i) for i in range(3)], [7, 8, 9])
        self.assertEqual(mv._take_seed(mv.SEED_MAX, 1), 0)
        self.assertTrue(0 <= mv._take_seed(None, 0) <= mv.SEED_MAX)

    def test_stale_only_when_take_differs(self):
        self.assertTrue(mv._stale({"take": "take-1"}, "take-2"))
        self.assertFalse(mv._stale({"take": "take-2"}, "take-2"))
        self.assertFalse(mv._stale({}, "take-2"))  # projects made before take was recorded
        self.assertFalse(mv._stale(None, "take-2"))


class WorkflowFilesTest(unittest.TestCase):
    def test_mapping_files_are_rejected_with_actionable_error(self):
        for path in (SCRIPTS.parent / "workflows").glob("*.params.json"):
            with self.subTest(path=path.name), self.assertRaisesRegex(MVError, "参数映射文件"):
                comfy.load_api_workflow(path)

    def test_raw_and_wrapped_api_formats_are_accepted(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            for data in (h3_workflow(), {"prompt": h3_workflow()}):
                path.write_text(json.dumps(data), encoding="utf-8-sig")
                self.assertEqual(comfy.load_api_workflow(path), h3_workflow())

    def test_malformed_json_structures_have_friendly_errors(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            for data in ([], None, 3, "invalid", {}, {"1": {"class_type": "LoadImage", "inputs": []}}):
                with self.subTest(data=data):
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(MVError):
                        comfy.load_api_workflow(path)

    def test_fresh_workspace_loads_all_bundled_workflows_without_copying(self):
        with TemporaryDirectory() as tmp:
            cfg = dict(DEFAULT_CONFIG, _root=tmp)
            for kind in ("music", "i2v", "flf2v", "tts-design", "tts-direction"):
                with self.subTest(kind=kind):
                    spec, graph, path = comfy.load_kind(cfg, kind)
                    self.assertEqual(path, SCRIPTS.parent / "workflows" / f"{kind}.api.json")
                    self.assertEqual(comfy.validate_kind(graph, spec), [])
                    # Every link resolves, including flattened subgraph boundaries.
                    for node in graph.values():
                        for value in node["inputs"].values():
                            if isinstance(value, list):
                                self.assertEqual(len(value), 2)
                                self.assertIn(value[0], graph)
                                self.assertIsInstance(value[1], int)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_workspace_api_and_mapping_override_bundled_resources(self):
        with TemporaryDirectory() as tmp:
            cfg = dict(DEFAULT_CONFIG, _root=tmp)
            folder = Path(tmp) / "workflows"
            custom = h3_workflow()
            write_json(folder / "i2v.api.json", custom)
            self.assertEqual(comfy.load_kind(cfg, "i2v")[1:], (custom, folder / "i2v.api.json"))
            spec = i2v_spec()
            spec["workflow"] = "custom.api.json"
            write_json(folder / "i2v.params.json", spec)
            write_json(folder / "custom.api.json", custom)
            loaded, graph, path = comfy.load_kind(cfg, "i2v")
            self.assertEqual(loaded, spec)
            self.assertEqual(graph, custom)
            self.assertEqual(path, folder / "custom.api.json")
            # A broken explicit override must not silently use a different graph.
            write_json(folder / "custom.api.json", {"nodes": [], "links": []})
            with self.assertRaisesRegex(MVError, "界面格式"):
                comfy.load_kind(cfg, "i2v")

    def test_workspace_mapping_can_use_bundled_api_and_explicit_missing_name_fails(self):
        with TemporaryDirectory() as tmp:
            cfg = dict(DEFAULT_CONFIG, _root=tmp)
            path = Path(tmp) / "workflows/i2v.params.json"
            spec = i2v_spec()
            write_json(path, spec)
            self.assertEqual(comfy.load_kind(cfg, "i2v")[2], SCRIPTS.parent / "workflows/i2v.api.json")
            spec["workflow"] = "missing.api.json"
            write_json(path, spec)
            with self.assertRaisesRegex(MVError, "missing.api.json"):
                comfy.load_kind(cfg, "i2v")

    def test_bundled_music_injects_prompts_duration_and_shared_seed(self):
        with TemporaryDirectory() as tmp:
            spec, graph, _ = comfy.load_kind(dict(DEFAULT_CONFIG, _root=tmp), "music")
            patched = comfy.apply_params(graph, spec, {"caption": "中文歌曲", "lyrics": "唱词",
                "max_duration": 45, "seed": 42, "filename_prefix": "mv/demo/song"})
            encoder = patched["37:13"]["inputs"]
            self.assertEqual((encoder["caption"], encoder["lyrics"], encoder["max_duration"]),
                             ("中文歌曲", "唱词", 45))
            self.assertEqual(encoder["seed"], ["37:38", 0])
            self.assertEqual(patched["37:38"]["inputs"]["seed"], 42)
            self.assertEqual(patched["37:9"]["inputs"]["seed"], ["37:38", 0])
            self.assertTrue(patched["37:43"]["inputs"]["switch"])
            output = patched["35"]["inputs"]
            self.assertEqual(output["filename_prefix"], "mv/demo/song")
            self.assertEqual((output["format"], output["format.quality"]), ("mp3", "V0"))

    def test_bundled_h3_preserves_models_sampling_duration_and_frame_inputs(self):
        with TemporaryDirectory() as tmp:
            for kind in ("i2v", "flf2v"):
                with self.subTest(kind=kind):
                    spec, graph, _ = comfy.load_kind(dict(DEFAULT_CONFIG, _root=tmp), kind)
                    ui = json.loads((SCRIPTS.parent / "workflows" / f"{kind}.workflow.json").read_text(encoding="utf-8"))
                    values = next(n for n in ui["nodes"] if "unet_name" in n.get("widgets_values_named", {}))["widgets_values_named"]
                    for node_id, key, original in (("6", "unet_name", "unet_name"), ("13", "clip_name", "clip_name"),
                                                   ("11", "vae_name", "vae_name"), ("24", "vae_name", "vae_name_1")):
                        self.assertEqual(graph[f"105:{node_id}"]["inputs"][key], values[original])
                    self.assertIs(graph["105:126"]["inputs"]["value"], False)
                    self.assertEqual(graph["105:124"]["inputs"]["value"], 20)
                    self.assertEqual(graph["105:125"]["inputs"]["value"], 8)
                    self.assertEqual(graph["105:91"]["inputs"]["fps"], 24)
                    image_params = {"image": "start.png"} if kind == "i2v" else {"start_image": "start.png", "end_image": "end.png"}
                    patched = comfy.apply_params(graph, spec, {**image_params, "positive": "转头", "duration": 124 / 24,
                                                              "width": 864, "height": 1536, "seed": 42})
                    h3 = patched["105:104"]["inputs"]
                    self.assertEqual(h3["prompt"], "转头")
                    self.assertEqual(h3["length"], ["105:107", 1])
                    self.assertEqual(patched["105:107"]["inputs"]["values.a"], ["105:111", 0])
                    self.assertEqual(patched["105:111"]["inputs"]["value"], 124 / 24)
                    self.assertEqual(patched["105:15"]["inputs"]["noise_seed"], 42)
                    self.assertEqual(patched[h3["first_frame"][0]]["inputs"]["image"], "start.png")
                    if kind == "flf2v":
                        self.assertEqual(patched[h3["last_frame"][0]]["inputs"]["image"], "end.png")
                    else:
                        self.assertNotIn("last_frame", h3)

    def test_ui_templates_have_nodes_links_and_resolvable_subgraphs(self):
        for kind in ("music", "i2v", "flf2v"):
            path = SCRIPTS.parent / "workflows" / f"{kind}.workflow.json"
            with self.subTest(kind=kind):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["version"], 0.4)
                subgraphs = data.get("definitions", {}).get("subgraphs", [])
                subgraph_ids = {graph["id"] for graph in subgraphs}
                for graph in [data, *subgraphs]:
                    self.assertIsInstance(graph["nodes"], list)
                    self.assertIsInstance(graph["links"], list)
                    nodes = {node["id"]: node for node in graph["nodes"]}
                    self.assertTrue(nodes)
                    self.assertEqual(len(nodes), len(graph["nodes"]))
                    endpoints = set(nodes)
                    for boundary in ("inputNode", "outputNode"):
                        if boundary in graph:
                            endpoints.add(graph[boundary]["id"])
                    for node in nodes.values():
                        self.assertIsInstance(node.get("inputs", []), list)
                        if len(node["type"]) == 36 and "-" in node["type"]:
                            self.assertIn(node["type"], subgraph_ids)
                    for link in graph["links"]:
                        if isinstance(link, list):
                            self.assertEqual(len(link), 6)
                            _, origin, _, target, _, _ = link
                        else:
                            origin, target = link["origin_id"], link["target_id"]
                        self.assertIn(origin, endpoints)
                        self.assertIn(target, endpoints)
                with self.assertRaisesRegex(MVError, "界面格式"):
                    comfy.load_api_workflow(path)


class H3WorkflowTest(unittest.TestCase):
    def test_both_video_templates_use_requested_models_and_frame_connections(self):
        for kind in ("i2v", "flf2v"):
            with self.subTest(kind=kind):
                data = json.loads((SCRIPTS.parent / "workflows" / f"{kind}.workflow.json").read_text(encoding="utf-8"))
                graph = data["definitions"]["subgraphs"][0]
                nodes = graph["nodes"]
                self.assertTrue(any(n["type"] == "MiniMaxH3ImageToVideo" for n in nodes))
                self.assertFalse(any("Wan" in n["type"] for n in nodes))
                main = next(n for n in data["nodes"] if n["type"] == graph["id"])
                values = main["widgets_values_named"]
                self.assertEqual(values["unet_name"], "minimax_h3_fl2va_pruned_int8_convrot.safetensors")
                self.assertEqual(values["clip_name"], "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors")
                self.assertEqual(values["vae_name"], "minimax_h3_video_vae_int8_convrot.safetensors")
                self.assertEqual(values["vae_name_1"], "minimax_h3_audio_vae_fp32.safetensors")
                self.assertIs(values["value"], False)
                self.assertEqual(values["value_2"], 8)
                self.assertEqual(main["widgets_values"], list(values.values()))
                self.assertIsNotNone(main["inputs"][0]["link"])
                self.assertEqual(main["inputs"][1]["link"] is not None, kind == "flf2v")
                frame_links = [link for link in data["links"] if link[3] == main["id"]]
                self.assertEqual(len(frame_links), 1 if kind == "i2v" else 2)
                durations = [n for n in nodes if n.get("title") == "@duration"]
                self.assertEqual(len(durations), 1)
                self.assertEqual(durations[0]["type"], "PrimitiveFloat")

    def test_h3_validation_rejects_wrong_model_and_output_fps(self):
        old = {"1": {"class_type": "WanImageToVideo", "inputs": {}}}
        self.assertTrue(any("不是 MiniMax H3" in e for e in comfy.validate_kind(old, i2v_spec())))
        workflow = h3_workflow()
        workflow["12"]["inputs"]["fps"] = 16
        self.assertTrue(any("24fps" in e for e in comfy.validate_kind(workflow, i2v_spec())))

    def test_legacy_project_and_config_are_not_reinterpreted_as_h3(self):
        with TemporaryDirectory() as tmp:
            cfg = copy.deepcopy(DEFAULT_CONFIG)
            cfg["_root"] = tmp
            project = Project(cfg, "legacy")
            old_video = {"width": 720, "height": 1280, "fps": 16, "max_frames": 81}
            project.save({"video": old_video})
            self.assertEqual(project.video()["model"], "wan2.2")
            config_path = Path(tmp) / "mv-creator.config.json"
            write_json(config_path, {"video": old_video})
            self.assertEqual(load_config(config_path)["video"]["model"], "wan2.2")
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8"))["video"], old_video)

    def test_edit_list_uses_h3_duration_and_preserves_legacy_calculation(self):
        shot = shots.new_shot(1, 0, 5, "1")
        take = {"model": "minimax-h3", "frames": 124, "fps": 24, "duration_sec": 124 / 24}
        meta = {"title": "test", "slug": "test"}
        text = media._edit_list(meta, {}, [(1, shot, "clip.mp4", take)], [], None)
        self.assertIn("5.17s", text)
        legacy = {"frames": 81, "fps": 16}
        text = media._edit_list(meta, {}, [(1, shot, "clip.mp4", legacy)], [], None)
        self.assertIn("5.00s", text)

    def test_clips_injects_h3_seconds_and_two_frames_and_resumes(self):
        with TemporaryDirectory() as tmp:
            cfg = copy.deepcopy(DEFAULT_CONFIG)
            cfg["_root"] = tmp
            project = Project(cfg, "demo")
            project.save({"video": dict(VIDEO)})
            scene = []
            for i in (1, 2):
                shot = shots.new_shot(i, (i - 1) * 2, i * 2, str(i))
                shot.update(scene="夜景", image_prompt="关键帧", motion_prompt="缓慢转头")
                shot["frame"]["selected"] = f"frames/S0{i}.png"
                path = project.path(shot["frame"]["selected"])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"offline image placeholder")
                scene.append(shot)
            scene[0]["workflow"] = "flf2v"
            project.save_shots({"shots": scene, "negative": "闪烁", "style": "电影感"})
            args = mv.build_parser().parse_args(["clips", "demo"])
            captured = []

            def fake_run(config, kind, values, uploads, subfolder, dest, stem):
                spec, graph, _ = comfy.load_kind(config, kind)
                patched = comfy.apply_params(graph, spec, dict(values, **{k: p.name for k, p in uploads.items()}))
                captured.append((kind, values, uploads, patched))
                path = dest / f"{stem}.mp4"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"offline video placeholder")
                return [path]

            with patch.object(comfy, "run_kind", side_effect=fake_run), redirect_stdout(StringIO()):
                mv.cmd_clips(args, cfg)
                mv.cmd_clips(args, cfg)
            self.assertEqual(len(captured), 2)
            kind, values, uploads, patched = captured[0]
            self.assertEqual(kind, "flf2v")
            self.assertEqual(set(uploads), {"start_image", "end_image"})
            load_images = {n["_meta"]["title"]: n["inputs"]["image"] for n in patched.values()
                           if n["class_type"] == "LoadImage"}
            self.assertEqual(load_images, {"@start_image": "S01.png", "@end_image": "S02.png"})
            self.assertEqual(values["duration"], 124 / 24)
            self.assertNotIn("length", values)
            self.assertNotIn("negative", values)
            self.assertIn("闪烁", values["positive"])
            self.assertEqual(patched["105:111"]["inputs"]["value"], 124 / 24)
            self.assertEqual([len(s["clip"]["takes"]) for s in project.load_shots()["shots"]], [1, 1])
            take = project.load_shots()["shots"][0]["clip"]["takes"][0]
            self.assertEqual(take["model"], "minimax-h3")
            self.assertEqual(take["frames"], 124)
            self.assertEqual(take["fps"], 24)
            self.assertEqual(take["duration_sec"], 124 / 24)


if __name__ == "__main__":
    unittest.main()
