"""Voice planning, continuation, waveform mixing and old-project compatibility."""

import argparse
import copy
from contextlib import redirect_stdout
from io import StringIO
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import wave

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/mv-creator/scripts"
sys.path.insert(0, str(SCRIPTS))
import mv
from mvlib import comfy, media, shots, voice
from mvlib.common import DEFAULT_CONFIG, MVError, Project, read_json, write_json

FFMPEG = os.environ.get("MV_TEST_FFMPEG") or shutil.which("ffmpeg")


def tone(path, seconds=1, freq=300, amp=0.1, rate=24000):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes(b"".join(struct.pack("<h", round(32767 * amp * math.sin(2*math.pi*freq*i/rate)))
                                    for i in range(round(seconds*rate))))


class VoiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = copy.deepcopy(DEFAULT_CONFIG)
        self.cfg["_root"] = self.tmp.name
        self.cfg["ffmpeg"] = FFMPEG
        self.project = Project(self.cfg, "demo")
        self.project.save({"title": "测试", "slug": "demo", "video": dict(DEFAULT_CONFIG["video"]),
                           "music": {"selected": "take-1", "file": "music/song.wav"}})
        tone(self.project.root / "music/song.wav", 6, 220)
        scene = [shots.new_shot(1, 0, 3, "1"), shots.new_shot(2, 3, 6, "2")]
        scene[0]["lyric"] = "唱词"
        self.project.save_shots({"shots": scene})
        voice.init_plan(self.project)
        self.plan = voice.load_plan(self.project)
        self.plan["enabled"] = True
        tone(self.project.root / "audio/ref.wav", 1)
        self.plan["speakers"][0]["reference"] = {"file": "audio/ref.wav", "text": "参考声音。"}
        self.plan["cues"] = [{"id": "V01", "speaker": "narrator", "kind": "inner", "mode": "direction",
                              "text": "那天的雨。", "instruction": "语速稍慢，克制。",
                              "anchor": {"shot_id": "S01", "offset_sec": 2}, "window_sec": 2.5,
                              "takes": [], "selected": None, "subtitle": True}]
        self.save()

    def save(self):
        write_json(self.project.root / voice.PLAN, self.plan)

    def selected(self, span=1):
        cue = self.plan["cues"][0]
        tone(self.project.root / "audio/takes/V01/take-1.wav", span, 500)
        path = self.project.root / "audio/takes/V01/take-1.wav"
        fingerprint = voice.request(self.project, self.cfg, cue, self.plan["speakers"][0])[3]
        cue["takes"] = [{"id": "take-1", "file": self.project.rel(path), "sha256": voice.file_hash(path),
                         "fingerprint": fingerprint, **voice.probe(path, self.cfg)}]
        cue["selected"] = "take-1"
        self.save()
        return cue

    def test_old_project_has_no_plan_and_disabled_package_works(self):
        (self.project.root / voice.PLAN).unlink()
        self.assertIsNone(voice.load_plan(self.project))
        result = media.package(self.project, self.cfg)
        self.assertEqual(result["clips"], 0)
        self.assertFalse((result["dest"] / "06_旁白").exists())

    def test_init_never_overwrites(self):
        with self.assertRaisesRegex(MVError, "已存在"):
            voice.init_plan(self.project)

    def test_anchor_allows_voice_to_cross_shot_and_missing_anchor_fails(self):
        cue = self.selected(2)
        self.assertEqual(voice.cue_start(cue, self.project.load_shots()["shots"]), 2)
        errors, warnings = voice.check(self.project, self.cfg, self.plan, True)
        self.assertEqual(errors, [])
        self.assertTrue(any("歌词字幕" in w for w in warnings))
        cue["anchor"]["shot_id"] = "missing"
        self.assertTrue(voice.check(self.project, self.cfg, self.plan, True)[0])

    def test_overflow_never_truncates_or_selects(self):
        cue = self.selected(3)
        cue["selected"] = None
        with self.assertRaisesRegex(MVError, "长于声音窗口"):
            voice.select(self.project, self.cfg, self.plan, "V01", "take-1")
        cue["selected"] = "take-1"
        self.assertTrue(any("超出窗口" in e for e in voice.check(self.project, self.cfg, self.plan, True)[0]))

    def test_text_reference_settings_and_workflow_invalidate_but_position_does_not(self):
        cue = self.selected()
        original = cue["takes"][0]["fingerprint"]
        for field, value in (("text", "改变台词"), ("instruction", "微笑"), ("settings", {"temperature": 0.8})):
            saved = copy.deepcopy(cue)
            cue[field] = value
            self.assertNotEqual(voice.request(self.project, self.cfg, cue, self.plan["speakers"][0])[3], original)
            cue.clear(); cue.update(saved)
        cue["anchor"]["offset_sec"] = 1
        cue["gain_db"] = -2
        self.assertEqual(voice.request(self.project, self.cfg, cue, self.plan["speakers"][0])[3], original)
        tone(self.project.root / "audio/ref.wav", 0.5)
        self.assertNotEqual(voice.request(self.project, self.cfg, cue, self.plan["speakers"][0])[3], original)
        spec, graph, _ = comfy.load_kind(self.cfg, "tts-direction")
        graph["1"]["inputs"]["model"] = "bf16 (best quality)"
        write_json(Path(self.tmp.name) / "workflows/tts-direction.api.json", graph)
        self.assertNotEqual(voice.request(self.project, self.cfg, cue, self.plan["speakers"][0])[3], original)

    def test_binding_requires_review_without_regenerating_audio(self):
        self.selected()
        scene = self.project.load_shots()
        scene["shots"][0]["end"] = 2.8
        scene["shots"][1]["start"] = 2.8
        self.project.save_shots(scene)
        self.assertTrue(any("voice-check --bind" in e for e in voice.check(self.project, self.cfg, self.plan, True)[0]))
        self.plan["binding"] = voice.binding(self.project)
        self.assertEqual(voice.check(self.project, self.cfg, self.plan, True)[0], [])

    def test_audio_replacement_detected(self):
        cue = self.selected()
        tone(self.project.path(cue["takes"][0]["file"]), 0.5)
        self.assertTrue(any("改写" in e for e in voice.check(self.project, self.cfg, self.plan, True)[0]))

    def test_invalid_plan_and_paths_and_numbers(self):
        for ident in ("../x", "a/b", ""):
            self.plan["cues"][0]["id"] = ident
            self.save()
            with self.assertRaises(MVError): voice.load_plan(self.project)
        for value in (float("nan"), True, "2"):
            with self.assertRaises(MVError): voice.number(value, "time")
        with self.assertRaises(MVError): voice.local_file(self.project, "../../outside.wav")

    def test_reference_and_workflow_contract_validation(self):
        speaker = self.plan["speakers"][0]
        speaker["reference"]["text"] = ""
        with self.assertRaisesRegex(MVError, "准确转写"):
            voice.request(self.project, self.cfg, self.plan["cues"][0], speaker)
        _, graph, _ = comfy.load_kind(self.cfg, "tts-direction")
        graph["2"]["inputs"]["stitch_reference"] = "before"
        self.assertTrue(voice.validate_workflow(graph, True))
        graph["1"]["inputs"]["download_if_missing"] = True
        self.assertEqual(len(voice.validate_workflow(graph, True)), 2)

    def test_multiple_voices_overlap_and_subtitles_warn(self):
        self.selected()
        other = copy.deepcopy(self.plan["cues"][0]); other["id"] = "V02"
        self.plan["cues"].append(other)
        errors, warnings = voice.check(self.project, self.cfg, self.plan, True)
        self.assertFalse(errors)
        self.assertTrue(any("声音重叠" in w for w in warnings))
        captions = voice.srt(voice.resolved(self.project, self.cfg, self.plan))
        self.assertIn("00:00:02,000 --> 00:00:03,000", captions)
        other["subtitle"] = False
        captions = voice.srt(voice.resolved(self.project, self.cfg, self.plan))
        self.assertEqual(captions.count("-->"), 1)

    def test_dry_run_has_no_generation_or_upload(self):
        before = (self.project.root / voice.PLAN).read_bytes()
        with patch.object(comfy, "run_kind") as run:
            voice.generate(self.project, self.cfg, self.plan, dry_run=True)
            run.assert_not_called()
        self.assertEqual((self.project.root / voice.PLAN).read_bytes(), before)

    def test_interrupted_generation_resumes_and_explicit_ids_append(self):
        calls = []
        def run(config, kind, values, uploads, subfolder, dest, stem):
            calls.append(values["seed"])
            if len(calls) == 2:
                raise MVError("interrupted")
            path = dest / f"{stem}.wav"; tone(path)
            return [path]
        with patch.object(comfy, "run_kind", side_effect=run), patch.object(voice, "ffmpeg_bin", return_value="ffprobe"):
            with self.assertRaisesRegex(MVError, "interrupted"):
                voice.generate(self.project, self.cfg, self.plan, seed=42, takes=2)
            plan = voice.load_plan(self.project)
            self.assertEqual(len(plan["cues"][0]["takes"]), 1)
            voice.generate(self.project, self.cfg, plan, seed=42, takes=2)
            voice.generate(self.project, self.cfg, plan, seed=42, takes=2)
            self.assertEqual(calls, [42, 43, 43])
            voice.generate(self.project, self.cfg, plan, ids="V01", seed=50, takes=1)
            self.assertEqual(len(plan["cues"][0]["takes"]), 3)
            self.assertEqual(calls[-1], 50)

    def test_audition_selection_sets_reference(self):
        item = self.plan["speakers"][0]
        path = self.project.root / "audio/auditions/narrator/take-1.wav"; tone(path)
        item["takes"] = [{"id": "take-1", "file": self.project.rel(path), "text": item["sample_text"],
                          "sha256": voice.file_hash(path),
                          "fingerprint": voice.request(self.project, self.cfg, item, item, True)[3]}]
        voice.select(self.project, self.cfg, self.plan, item["id"], "take-1", True)
        self.assertEqual(item["reference"]["file"], self.project.rel(path))

    def test_status_reports_voice_staleness(self):
        self.selected()
        (self.project.root / "brief.md").write_text("test", encoding="utf-8")
        self.plan["cues"][0]["text"] = "改过的台词"; self.save()
        output = StringIO()
        with redirect_stdout(output):
            mv.cmd_status(argparse.Namespace(slug="demo"), self.cfg)
        self.assertIn("需要重做/重选配音", output.getvalue())
        self.assertIn("[ ] 旁白", output.getvalue())

    @unittest.skipUnless(FFMPEG, "MV_TEST_FFMPEG or ffmpeg required for waveform integration")
    def test_real_mix_alignment_duck_recovery_peak_and_cache(self):
        self.selected()
        outputs = voice.mix(self.project, self.cfg)
        self.assertEqual(len(outputs), 4)
        def pcm(path):
            proc = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "48000", "-"], capture_output=True, check=True)
            import array
            values = array.array('f'); values.frombytes(proc.stdout)
            return values
        song, narration, mixed = [pcm(p) for p in outputs[:3]]
        self.assertEqual(len(narration), 6 * 48000)
        self.assertLess(max(abs(x) for x in narration[:int(1.99*48000)]), 0.0001)
        self.assertGreater(max(abs(x) for x in narration[int(2.1*48000):int(2.9*48000)]), 0.05)
        def rms(data, start, end):
            part = data[round(start*48000):round(end*48000)]
            return math.sqrt(sum(x*x for x in part)/len(part))
        music_component = [m-v for m,v in zip(mixed, narration)]
        self.assertAlmostEqual(rms(music_component, 2.1, 2.9)/rms(song, 2.1, 2.9), 10**(-6/20), delta=0.02)
        self.assertAlmostEqual(rms(mixed, 4, 5)/rms(song, 4, 5), 1, delta=0.02)
        self.assertLessEqual(max(abs(x) for x in mixed), 0.951)
        stamp = outputs[2].stat().st_mtime_ns
        voice.mix(self.project, self.cfg)
        self.assertEqual(outputs[2].stat().st_mtime_ns, stamp)
        self.plan["cues"][0]["gain_db"] = -4; self.save()
        voice.mix(self.project, self.cfg)
        self.assertNotEqual(outputs[2].stat().st_mtime_ns, stamp)

    @unittest.skipUnless(FFMPEG, "ffmpeg required")
    def test_package_and_roughcut_include_independent_voice_and_both_videos(self):
        self.selected()
        self.cfg["roughcut"].update(scale=0.1, fps=12)
        self.cfg["voice"]["voice_gain_db"] = 2
        result = media.package(self.project, self.cfg)
        dest = result["dest"]
        self.assertTrue((dest / "06_旁白/声音时间表.json").is_file())
        self.assertEqual(read_json(dest / "06_旁白/声音时间表.json")["settings"]["voice_gain_db"], 2)
        self.assertTrue((dest / "04_字幕/voice.srt").is_file())
        self.assertTrue((dest / "07_混音参考/mix.wav").is_file())
        paths = media.roughcut(self.project, self.cfg, True)
        self.assertEqual({p.name for p in paths}, {"roughcut.mp4", "roughcut_voice.mp4", "roughcut_subs.mp4", "roughcut_voice_subs.mp4"})
        self.assertTrue(all(p.is_file() for p in paths))
        manifest = read_json(self.project.root / "final/roughcut-manifest.json")
        self.assertTrue(manifest["audio_fingerprint"])

    @unittest.skipUnless(FFMPEG, "ffmpeg required")
    def test_narrated_subtitles_without_lyrics_and_legacy_empty_subtitles(self):
        self.selected()
        scene = self.project.load_shots()
        for shot in scene["shots"]:
            shot["lyric"] = ""
        self.project.save_shots(scene)
        self.cfg["roughcut"].update(scale=0.1, fps=12)
        paths = media.roughcut(self.project, self.cfg, True)
        self.assertEqual({p.name for p in paths}, {"roughcut.mp4", "roughcut_voice.mp4", "roughcut_voice_subs.mp4"})
        self.assertTrue(all(p.is_file() for p in paths))
        self.plan["enabled"] = False
        self.save()
        paths = media.roughcut(self.project, self.cfg, True)
        self.assertEqual([p.name for p in paths], ["roughcut.mp4"])

    @unittest.skipUnless(FFMPEG, "ffmpeg required")
    def test_loud_overlapping_voices_are_limited_and_duck_does_not_stack(self):
        cue = self.selected()
        path = self.project.path(cue["takes"][0]["file"])
        tone(path, 1, 500, amp=0.9)
        cue["takes"][0]["sha256"] = voice.file_hash(path)
        other = copy.deepcopy(cue)
        other["id"] = "V02"
        self.plan["cues"].append(other)
        self.save()
        expr = voice.duck_expression(voice.resolved(self.project, self.cfg, self.plan), voice.mix_settings(self.cfg))
        gain = eval(expr.replace("if(", "choose("), {"__builtins__": {}}, {
            "t": 2.5, "pow": pow, "min": min, "lt": lambda a, b: a < b,
            "choose": lambda condition, yes, no: yes if condition else no})
        self.assertAlmostEqual(gain, 10**(-6/20))
        outputs = voice.mix(self.project, self.cfg)
        proc = subprocess.run([FFMPEG, "-v", "error", "-i", str(outputs[2]), "-f", "f32le", "-ac", "2", "-"], capture_output=True, check=True)
        import array
        values = array.array('f'); values.frombytes(proc.stdout)
        peak = max(abs(x) for x in values)
        self.assertGreater(peak, 0.9)
        self.assertLessEqual(peak, 0.951)


if __name__ == "__main__":
    unittest.main()
