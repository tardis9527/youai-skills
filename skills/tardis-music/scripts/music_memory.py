"""Project-local music memory. Standard library only; no network or audio execution."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
import tempfile


SCHEMA_VERSION = 2
KINDS = {"persona", "preference", "work", "lesson"}
EVIDENCE = {"user_explicit", "text_review", "user_reported", "audio_measured",
            "user_verified", "platform_observed"}
STATES = {"active", "candidate", "supported", "disputed", "superseded"}
TOKEN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,95}\Z")
REQUIRED = {"id", "kind", "persona_id", "scope", "summary", "evidence",
            "status", "updated_at"}
OPTIONAL = {"future_use", "work_id", "version", "stage", "outcome", "details",
            "derived_from", "supersedes"}


def token(value):
    return isinstance(value, str) and bool(TOKEN.fullmatch(value))


def work_token(value):
    # Work ids already used by prompt/MV documents may contain Chinese titles.
    return (isinstance(value, str) and 0 < len(value) <= 160 and value == value.strip()
            and value not in {".", ".."} and not value.endswith(".")
            and not re.search(r'[\\/:*?"<>|\x00-\x1f\x7f]', value))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_entry(entry):
    require(isinstance(entry, dict), "Each entry must be an object")
    require(REQUIRED <= entry.keys() <= REQUIRED | OPTIONAL, "Invalid entry fields")
    require(token(entry["id"]) and token(entry["persona_id"]), "Invalid entry/persona id")
    require(entry["kind"] in KINDS and entry["status"] in STATES, "Invalid kind/status")
    scopes = entry["scope"]
    require(isinstance(scopes, list) and scopes and
            all(s == "*" or token(s) for s in scopes), "Invalid scope tags")
    require(len(scopes) == len(set(scopes)), "Duplicate scope tags")
    require(isinstance(entry["summary"], str) and entry["summary"].strip(), "Empty summary")
    require(isinstance(entry["updated_at"], str) and
            re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["updated_at"]), "Use local YYYY-MM-DD")
    date.fromisoformat(entry["updated_at"])
    evidence = entry["evidence"]
    require(isinstance(evidence, dict) and set(evidence) == {"type", "summary"},
            "Evidence requires type and summary")
    require(evidence["type"] in EVIDENCE and isinstance(evidence["summary"], str)
            and evidence["summary"].strip(), "Invalid/empty evidence")
    if "details" in entry:
        require(isinstance(entry["details"], dict), "details must be an object")
    if "work_id" in entry and entry["work_id"] is not None:
        require(work_token(entry["work_id"]), "Invalid work id")
    if "version" in entry:
        require(type(entry["version"]) is int and entry["version"] > 0, "Invalid version")
    derived = entry.get("derived_from", [])
    require(isinstance(derived, list) and all(token(i) for i in derived)
            and len(derived) == len(set(derived)), "Invalid derived_from ids")
    require(entry.get("supersedes") is None or token(entry["supersedes"]),
            "Invalid supersedes id")
    if entry["kind"] in {"persona", "preference"}:
        require(entry["status"] in {"active", "superseded"} and
                entry.get("future_use") is True and evidence["type"] == "user_explicit",
                "Persona/preferences require explicit future-use evidence")
    elif entry["kind"] == "work":
        require(entry["status"] in {"active", "superseded"} and work_token(entry.get("work_id")),
                "Work requires work_id and active/superseded status")
        require(type(entry.get("version")) is int and entry["version"] > 0, "Work requires version")
        stage = entry.get("stage")
        require(stage in {"text_ready", "user_selected", "audio_reviewed", "released"},
                "Invalid work stage")
        require(entry.get("outcome") in {"pending", "positive", "negative", "mixed", "unknown"},
                "Invalid work outcome")
        if stage in {"text_ready", "user_selected"}:
            require(entry["outcome"] == "pending", "Text/selection is not audio success")
        if stage != "text_ready":
            allowed = {
                "user_selected": {"user_explicit", "user_reported", "user_verified"},
                "audio_reviewed": {"user_reported", "audio_measured", "user_verified"},
                "released": {"user_reported", "platform_observed"},
            }
            require(evidence["type"] in allowed[stage], "Evidence does not support work stage")
    else:
        require(entry["status"] in {"candidate", "supported", "disputed", "superseded"},
                "Lessons need an explicit confidence state")
        require(derived, "Lesson requires source record ids")


def validate_store(store):
    require(isinstance(store, dict) and set(store) == {"schema_version", "entries"}
            and store["schema_version"] == SCHEMA_VERSION and isinstance(store["entries"], list),
            "Unknown/corrupt knowledge schema; existing file was not changed")
    by_id = {}
    for entry in store["entries"]:
        validate_entry(entry)
        require(entry["id"] not in by_id, "Duplicate entry id")
        by_id[entry["id"]] = entry
    for entry in store["entries"]:
        for ref in entry.get("derived_from", []):
            require(ref in by_id and ref != entry["id"], "Missing/self-derived record")
            require(by_id[ref]["persona_id"] == entry["persona_id"], "Cross-persona derivation")
        previous = entry.get("supersedes")
        if previous:
            require(previous in by_id and previous != entry["id"], "Missing/self supersedes")
            old = by_id[previous]
            require(old["kind"] == entry["kind"] and old["persona_id"] == entry["persona_id"]
                    and set(old["scope"]) == set(entry["scope"]), "Supersedes scope mismatch")
            require(old["status"] == "superseded", "Old entry must be superseded")
        if entry["kind"] == "lesson" and entry["status"] == "supported":
            sources = [by_id[r] for r in entry.get("derived_from", [])]
            works = {s.get("work_id") for s in sources if s["kind"] == "work"
                     and s.get("stage") in {"audio_reviewed", "released"}
                     and s.get("outcome") in {"positive", "negative", "mixed"}}
            works.discard(None)
            require(len(works) >= 2 and entry["evidence"]["type"] != "text_review",
                    "Supported lesson needs feedback from at least two distinct works")
    # Prevent dependency cycles so forgetting can remove derived knowledge reliably.
    visiting, visited = set(), set()

    def visit(entry_id):
        require(entry_id not in visiting, "Cyclic record references")
        if entry_id in visited:
            return
        visiting.add(entry_id)
        item = by_id[entry_id]
        refs = item.get("derived_from", []) + ([item["supersedes"]] if item.get("supersedes") else [])
        for ref in refs:
            visit(ref)
        visiting.remove(entry_id)
        visited.add(entry_id)

    for entry_id in by_id:
        visit(entry_id)
    return store


def knowledge_path(root):
    base = Path(root).resolve()
    skill = Path(__file__).resolve().parents[1]
    require(not base.is_relative_to(skill), "Use a project output root, not the Skill directory")
    learning = (base / "_learning").resolve()
    require(learning.is_relative_to(base), "Learning directory escapes output root")
    path = learning / "knowledge.json"
    require(not path.is_symlink(), "Refusing a symlink knowledge file")
    return path


def read_store(path):
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": []}
    return validate_store(json.loads(path.read_text(encoding="utf-8-sig")))


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.parent / ".knowledge.lock"
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError:
        raise ValueError("Memory is locked; no changes made. Check the active writer before retrying.") from None
    try:
        with handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def write_store(path, store):
    validate_store(store)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".knowledge-", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            json.dump(store, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        require(read_store(path) == store, "Knowledge read-back mismatch")
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def record(root, entries):
    path = knowledge_path(root)
    require(isinstance(entries, list) and entries, "Provide at least one real record")
    for entry in entries:
        validate_entry(entry)
    with locked(path):
        store = read_store(path)
        by_id = {e["id"]: e for e in store["entries"]}
        for entry in entries:
            if entry["id"] in by_id:
                require(by_id[entry["id"]] == entry, "Existing id differs; create a new id with supersedes")
                continue
            previous = entry.get("supersedes")
            if previous:
                require(previous in by_id and by_id[previous]["status"] != "superseded",
                        "Supersedes must name a current record")
                by_id[previous]["status"] = "superseded"
            store["entries"].append(entry)
            by_id[entry["id"]] = entry
        write_store(path, store)
    return {"saved": str(path), "record_ids": [e["id"] for e in entries]}


def recall(root, persona_id, scopes, kind=None):
    require(token(persona_id) and scopes and all(token(s) for s in scopes),
            "Specify a persona and at least one concrete scope")
    entries = read_store(knowledge_path(root))["entries"]
    return [e for e in entries if e["persona_id"] == persona_id
            and ("*" in e["scope"] or set(e["scope"]) & set(scopes))
            and e["status"] != "superseded" and (kind is None or e["kind"] == kind)]


def forget(root, ids):
    require(ids and all(token(i) for i in ids), "Specify exact record ids")
    path = knowledge_path(root)
    if not path.exists():
        return {"removed_ids": []}
    with locked(path):
        store = read_store(path)
        existing = {e["id"] for e in store["entries"]}
        require(set(ids) <= existing, "Some ids do not exist; no changes made")
        removed = set(ids)
        # Remove lessons derived from forgotten facts, including transitive derivations.
        while True:
            dependents = {e["id"] for e in store["entries"]
                          if set(e.get("derived_from", [])) & removed}
            if dependents <= removed:
                break
            removed |= dependents
        store["entries"] = [e for e in store["entries"] if e["id"] not in removed]
        for entry in store["entries"]:
            if entry.get("supersedes") in removed:
                entry["supersedes"] = None
        write_store(path, store)
    return {"removed_ids": sorted(removed)}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("recall", "record", "forget"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True, help="Project music output root")
        if name == "recall":
            command.add_argument("--persona", required=True)
            command.add_argument("--scope", action="append", required=True)
            command.add_argument("--kind", choices=sorted(KINDS))
        elif name == "record":
            command.add_argument("--input", required=True, help="UTF-8 JSON entry or list of entries")
        else:
            command.add_argument("--id", action="append", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "recall":
            result = recall(args.root, args.persona, args.scope, args.kind)
        elif args.command == "record":
            entries = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
            result = record(args.root, entries if isinstance(entries, list) else [entries])
        else:
            result = forget(args.root, args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(f"Memory error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
