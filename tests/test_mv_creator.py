"""Offline checks for the mv-creator pipeline helpers."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "mv-creator" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from mvlib import comfy, frames, shots  # noqa: E402
from mvlib.common import DEFAULT_CONFIG, MVError, clip_frames, shot_limit_sec  # noqa: E402

VIDEO = dict(DEFAULT_CONFIG["video"])


def wan_workflow() -> dict:
    """A trimmed Wan2.2 I2V graph in API format, with a primitive-fed seed."""
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": "x.png"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "pos", "clip": ["7", 0]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "neg", "clip": ["7", 0]}},
        "4": {"class_type": "WanImageToVideo", "inputs": {
            "positive": ["2", 0], "negative": ["3", 0], "start_image": ["1", 0],
            "width": 640, "height": 640, "length": 81, "batch_size": 1}},
        "5": {"class_type": "KSamplerAdvanced", "inputs": {"add_noise": "enable", "noise_seed": 1}},
        "6": {"class_type": "KSamplerAdvanced", "inputs": {"add_noise": "disable", "noise_seed": ["8", 0]}},
        "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5.safetensors"}},
        "8": {"class_type": "PrimitiveInt", "inputs": {"value": 5}},
        "9": {"class_type": "SaveVideo", "inputs": {"filename_prefix": "video/ComfyUI"}},
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
        patched = comfy.apply_params(wan_workflow(), i2v_spec(), {
            "image": "mv-creator/demo/S01.png", "positive": "雨丝落下", "negative": "模糊",
            "width": 720, "height": 1280, "length": 45, "seed": 42, "filename_prefix": "mv/S01"})
        self.assertEqual(patched["1"]["inputs"]["image"], "mv-creator/demo/S01.png")
        self.assertEqual(patched["2"]["inputs"]["text"], "雨丝落下")
        self.assertEqual(patched["3"]["inputs"]["text"], "模糊")
        self.assertEqual([patched["4"]["inputs"][k] for k in ("width", "height", "length")], [720, 1280, 45])
        self.assertEqual(patched["5"]["inputs"]["noise_seed"], 42)
        self.assertEqual(patched["8"]["inputs"]["value"], 42)  # seed fed through a primitive node
        self.assertEqual(patched["9"]["inputs"]["filename_prefix"], "mv/S01")

    def test_title_overrides_automatic_match(self):
        workflow = wan_workflow()
        workflow["10"] = {"class_type": "CLIPTextEncode", "inputs": {"text": ""}, "_meta": {"title": "@positive"}}
        patched = comfy.apply_params(workflow, i2v_spec(), {"image": "a.png", "positive": "p"})
        self.assertEqual(patched["10"]["inputs"]["text"], "p")
        self.assertEqual(patched["2"]["inputs"]["text"], "pos")

    def test_ambiguous_and_unknown_params_fail(self):
        workflow = wan_workflow()
        workflow["11"] = {"class_type": "LoadImage", "inputs": {"image": "b.png"}}
        with self.assertRaises(MVError):
            comfy.apply_params(workflow, i2v_spec(), {"image": "a.png", "positive": "p"})
        with self.assertRaises(MVError):
            comfy.apply_params(wan_workflow(), i2v_spec(), {"image": "a.png", "positive": "p", "typo": 1})

    def test_validate_reports_nothing_for_template(self):
        self.assertEqual(comfy.validate_kind(wan_workflow(), i2v_spec()), [])

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


if __name__ == "__main__":
    unittest.main()
