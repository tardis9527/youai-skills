"""Isolated behavior checks for project-local music memory; no real user records."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/tardis-music/scripts/music_memory.py"
SPEC = importlib.util.spec_from_file_location("music_memory", SCRIPT)
memory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(memory)


def item(record_id="W-1", **changes):
    entry = {
        "id": record_id, "kind": "work", "persona_id": "default",
        "scope": ["private-memorial"], "summary": "模拟结案，不是真实用户偏好",
        "evidence": {"type": "text_review", "summary": "只检查文本"},
        "status": "active", "updated_at": "2026-11-05", "work_id": "work-1",
        "version": 1, "stage": "text_ready", "outcome": "pending",
    }
    entry.update(changes)
    return entry


def preference(record_id="P-1", **changes):
    entry = {key: value for key, value in item(record_id).items()
             if key not in {"work_id", "version", "stage", "outcome"}}
    entry.update(kind="preference", future_use=True,
                 evidence={"type": "user_explicit", "summary": "模拟用户明确说以后这类歌都这样"})
    entry.update(changes)
    return entry


def reviewed(record_id, work_id, **changes):
    return item(record_id, work_id=work_id, stage="audio_reviewed", outcome="negative",
                evidence={"type": "user_reported", "summary": "模拟用户报告尾奏不足"}, **changes)


def lesson(record_id="L-1", **changes):
    entry = preference(record_id, kind="lesson", status="candidate", derived_from=["W-1"])
    entry.pop("future_use")
    entry.update(evidence={"type": "user_reported", "summary": "仅限所列模拟作品"})
    entry.update(changes)
    return entry


class MusicMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "output"

    def save(self, *entries):
        return memory.record(self.root, deepcopy(list(entries)))

    def recall(self, **changes):
        args = dict(root=self.root, persona_id="default", scopes=["private-memorial"])
        args.update(changes)
        return memory.recall(**args)

    def test_empty_recall_does_not_create_personal_files(self):
        self.assertEqual(self.recall(), [])
        self.assertFalse(self.root.exists())

    def test_persona_scope_and_project_are_isolated(self):
        self.save(preference(), preference("P-2", persona_id="brand-b"),
                  preference("P-3", scope=["activity-opening"]),
                  preference("P-4", scope=["*"]))
        self.assertEqual({e["id"] for e in self.recall()}, {"P-1", "P-4"})
        self.assertEqual(self.recall(root=Path(self.temp.name) / "other"), [])

    def test_long_term_memory_needs_future_intent_and_explicit_evidence(self):
        for changes in ({"future_use": False}, {"evidence": {"type": "text_review", "summary": "猜的"}}):
            for kind in ("persona", "preference"):
                with self.assertRaises(ValueError):
                    self.save(preference(kind=kind, **changes))
        self.assertFalse(memory.knowledge_path(self.root).exists())

    def test_text_or_selection_cannot_be_recorded_as_audio_success(self):
        for stage in ("text_ready", "user_selected"):
            with self.assertRaises(ValueError):
                self.save(item(stage=stage, outcome="positive"))

    def test_stage_requires_appropriate_evidence(self):
        for stage in ("user_selected", "audio_reviewed", "released"):
            with self.assertRaises(ValueError):
                self.save(item(stage=stage))

    def test_closeout_preserves_versions_and_unknown_results(self):
        self.save(item(), item("W-2", version=2))
        self.assertEqual([e["version"] for e in self.recall()], [1, 2])
        self.assertTrue(all(e["outcome"] == "pending" for e in self.recall()))

    def test_chinese_work_id_remains_compatible_with_existing_documents(self):
        self.save(item(work_id="回家的灯"))
        self.assertEqual(self.recall()[0]["work_id"], "回家的灯")

    def test_same_record_retry_is_idempotent(self):
        self.save(preference())
        self.save(preference())
        self.assertEqual(len(self.recall()), 1)
        with self.assertRaises(ValueError):
            self.save(preference(summary="different"))

    def test_supersedes_preserves_history_without_reusing_it(self):
        self.save(preference())
        self.save(preference("P-2", supersedes="P-1", summary="模拟长期改变"))
        self.assertEqual([e["id"] for e in self.recall()], ["P-2"])
        stored = memory.read_store(memory.knowledge_path(self.root))["entries"]
        self.assertEqual(stored[0]["status"], "superseded")

    def test_supersedes_cannot_change_persona_or_scope(self):
        self.save(preference())
        for changes in ({"persona_id": "other"}, {"scope": ["activity-opening"]}):
            with self.assertRaises(ValueError):
                self.save(preference("P-2", supersedes="P-1", **changes))
        self.assertEqual(self.recall()[0]["status"], "active")

    def test_invalid_batch_keeps_existing_bytes(self):
        self.save(item())
        path = memory.knowledge_path(self.root)
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            self.save(preference(), lesson(derived_from=["missing"]))
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((path.parent / ".knowledge.lock").exists())
        self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_derivation_rejects_cross_persona_and_cycles(self):
        self.save(item())
        with self.assertRaises(ValueError):
            self.save(lesson(persona_id="other"))
        with self.assertRaises(ValueError):
            self.save(lesson("L-1", derived_from=["L-2"]), lesson("L-2", derived_from=["L-1"]))

    def test_repeated_takes_from_one_work_do_not_support_general_lesson(self):
        self.save(reviewed("W-1", "work-1"), reviewed("W-2", "work-1"))
        with self.assertRaises(ValueError):
            self.save(lesson(status="supported", derived_from=["W-1", "W-2"]))

    def test_text_only_works_do_not_support_general_lesson(self):
        self.save(item(), item("W-2", work_id="work-2"))
        with self.assertRaises(ValueError):
            self.save(lesson(status="supported", derived_from=["W-1", "W-2"]))

    def test_unresolved_audio_reports_do_not_support_general_lesson(self):
        self.save(item("W-1", stage="audio_reviewed", outcome="unknown",
                       evidence={"type": "user_reported", "summary": "刚运行，听感还没判断"}),
                  reviewed("W-2", "work-2"))
        with self.assertRaises(ValueError):
            self.save(lesson(status="supported", derived_from=["W-1", "W-2"]))

    def test_negative_observations_can_support_limited_lesson(self):
        self.save(reviewed("W-1", "work-1"), reviewed("W-2", "work-2"))
        self.save(lesson(status="supported", derived_from=["W-1", "W-2"]))
        self.assertEqual(self.recall(kind="lesson")[0]["status"], "supported")
        self.save(lesson("L-2", status="disputed", supersedes="L-1"))
        self.assertEqual(self.recall(kind="lesson")[0]["status"], "disputed")
        self.assertEqual(self.recall(kind="preference"), [])

    def test_forget_removes_dependent_lessons_and_preserves_unrelated_records(self):
        self.save(item(), preference(), lesson(), lesson("L-2", derived_from=["L-1"]))
        result = memory.forget(self.root, ["W-1"])
        self.assertEqual(result["removed_ids"], ["L-1", "L-2", "W-1"])
        self.assertEqual([e["id"] for e in self.recall()], ["P-1"])
        self.assertNotIn("summary", result)

    def test_forget_does_not_resurrect_superseded_preference(self):
        self.save(preference())
        self.save(preference("P-2", supersedes="P-1"))
        memory.forget(self.root, ["P-2"])
        self.assertEqual(self.recall(), [])

    def test_corrupt_or_future_schema_is_not_overwritten(self):
        path = memory.knowledge_path(self.root)
        path.parent.mkdir(parents=True)
        for text in ("broken json", '{"schema_version": 99, "entries": []}'):
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError):
                self.save(item())
            self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_existing_lock_stops_writer(self):
        path = memory.knowledge_path(self.root)
        path.parent.mkdir(parents=True)
        lock = path.parent / ".knowledge.lock"
        lock.write_text("test writer", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.save(item())
        self.assertTrue(lock.exists())
        self.assertFalse(path.exists())

    def test_replace_failure_keeps_original_and_cleans_temp_file(self):
        self.save(item())
        path = memory.knowledge_path(self.root)
        original = path.read_bytes()
        with patch.object(memory.os, "replace", side_effect=OSError("simulated write failure")):
            with self.assertRaises(OSError):
                self.save(preference())
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse((path.parent / ".knowledge.lock").exists())
        self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_ids_are_data_not_paths_and_install_dir_is_rejected(self):
        with self.assertRaises(ValueError):
            self.save(item("../escape"))
        with self.assertRaises(ValueError):
            memory.knowledge_path(SCRIPT.parent.parent)

    def test_cli_records_recalls_and_forgets_real_files(self):
        source = Path(self.temp.name) / "input.json"
        source.write_text(json.dumps(item(), ensure_ascii=False), encoding="utf-8")

        def cli(*args):
            result = subprocess.run([sys.executable, str(SCRIPT), *args, "--root", str(self.root)],
                                    capture_output=True, encoding="utf-8", check=True)
            return json.loads(result.stdout)

        self.assertEqual(cli("record", "--input", str(source))["record_ids"], ["W-1"])
        self.assertEqual(cli("recall", "--persona", "default", "--scope", "private-memorial")[0]["id"], "W-1")
        self.assertEqual(cli("forget", "--id", "W-1")["removed_ids"], ["W-1"])


if __name__ == "__main__":
    unittest.main()
