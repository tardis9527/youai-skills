"""Optional, versioned Breeze narration and a song-aligned audio mix."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import re
import subprocess
import tempfile
import wave
from pathlib import Path

from . import comfy
from .common import MVError, Project, SKILL_DIR, ffmpeg_bin, now_iso, read_json, write_json

PLAN = "audio/voice-plan.json"
SETTING_NAMES = {"cfg_scale", "max_new_tokens", "temperature", "top_k", "top_p",
                 "repetition_penalty", "depth_temperature", "depth_top_k", "depth_top_p"}
ID = re.compile(r"[A-Za-z0-9_-]+\Z")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def local_file(project: Project, rel: str) -> Path:
    if not isinstance(rel, str) or not rel.strip():
        raise MVError("声音文件路径为空")
    path = (project.root / rel).resolve()
    if not path.is_relative_to(project.root.resolve()):
        raise MVError("声音文件需保存在项目目录内，再填写相对路径")
    if not path.is_file():
        raise MVError(f"声音文件不存在: {path}")
    return path


def number(value, label: str, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise MVError(f"{label} 需为有限数值")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise MVError(f"{label} 超出范围 {minimum}–{maximum}")
    return float(value)


def load_plan(project: Project) -> dict | None:
    path = project.root / PLAN
    if not path.is_file():
        return None
    plan = read_json(path)
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise MVError("voice-plan.json 需为 version=1 的对象")
    if not isinstance(plan.get("enabled"), bool):
        raise MVError("voice-plan.json 的 enabled 需为 true 或 false")
    for name in ("speakers", "cues"):
        rows = plan.get(name)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise MVError(f"voice-plan.json 的 {name} 需为对象数组")
        ids = [row.get("id") for row in rows]
        if any(not isinstance(i, str) or not ID.fullmatch(i) for i in ids) or len(ids) != len(set(ids)):
            raise MVError(f"{name} 的 id 需唯一，只能含英文字母、数字、下划线和连字符")
        for row in rows:
            if not isinstance(row.get("takes", []), list) or any(not isinstance(t, dict) for t in row.get("takes", [])):
                raise MVError(f"{row['id']}.takes 需为对象数组")
            if not isinstance(row.get("settings", {}), dict):
                raise MVError(f"{row['id']}.settings 需为对象")
    for speaker in plan["speakers"]:
        if speaker.get("reference") is not None and not isinstance(speaker["reference"], dict):
            raise MVError(f"{speaker['id']}.reference 需为对象或 null")
    return plan


def timeline(project: Project) -> tuple[list[dict], float]:
    shots = project.load_shots()["shots"]
    if not shots:
        raise MVError("需要先建立分镜时间线")
    end = max(number(s["end"], "镜头 end", 0) for s in shots)
    if end <= 0:
        raise MVError("分镜时间线为空")
    return shots, end


def binding(project: Project) -> dict:
    shots, _ = timeline(project)
    music = project.load().get("music", {})
    song = project.path(music.get("file"))
    return {"music_take": music.get("selected"),
            "song_sha256": file_hash(song) if song and song.is_file() else None,
            "timeline_sha256": digest([(s["id"], s["start"], s["end"]) for s in shots])}


def init_plan(project: Project) -> Path:
    path = project.root / PLAN
    if path.exists():
        raise MVError(f"{path} 已存在，保留现有声音计划")
    plan = read_json(SKILL_DIR / "assets" / "voice-plan.example.json")
    plan["binding"] = binding(project)
    write_json(path, plan)
    return path


def cue_start(cue: dict, shots: list[dict]) -> float:
    if "anchor" not in cue:
        return number(cue.get("start"), f"{cue['id']}.start", 0)
    if "start" in cue:
        raise MVError(f"{cue['id']} 只能设置 start 或 anchor 其中一个")
    anchor = cue["anchor"]
    if not isinstance(anchor, dict):
        raise MVError(f"{cue['id']}.anchor 需为对象")
    shot = next((s for s in shots if s["id"] == anchor.get("shot_id")), None)
    if shot is None:
        raise MVError(f"{cue['id']} 关联镜头不存在: {anchor.get('shot_id')}")
    offset = number(anchor.get("offset_sec", 0), f"{cue['id']}.offset_sec")
    return number(shot["start"] + offset, f"{cue['id']} 解析后的开始时间", 0)


def _speaker(plan: dict, speaker_id: str) -> dict:
    row = next((s for s in plan["speakers"] if s["id"] == speaker_id), None)
    if row is None:
        raise MVError(f"未定义说话人: {speaker_id}")
    return row


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MVError(f"{label} 不能为空")
    return value.strip()


def request(project: Project, cfg: dict, item: dict, speaker: dict,
            audition: bool = False) -> tuple[str, dict, dict, str]:
    mode = "design" if audition else item.get("mode", "direction")
    if mode not in ("design", "direction"):
        raise MVError(f"不支持的配音模式: {mode}")
    voice_cfg = cfg.get("voice", {})
    kind = voice_cfg.get(f"{mode}_workflow", f"tts-{mode}")
    values = {"text": _text(speaker.get("sample_text") if audition else item.get("text"), "朗读文本"),
              "instruction": _text(speaker.get("description"), "音色描述") if mode == "design" else ""}
    if not audition:
        delivery = _text(item.get("instruction"), f"{item['id']} 表演指令")
        values["instruction"] = (values["instruction"] + "。" + delivery).strip("。")
    settings = copy.deepcopy(voice_cfg.get("generation", {}))
    if not isinstance(settings, dict) or not isinstance(item.get("settings", {}), dict):
        raise MVError("语音 settings / generation 需为对象")
    settings.update(item.get("settings", {}))
    if set(settings) - SETTING_NAMES:
        raise MVError(f"不支持的语音生成参数: {sorted(set(settings) - SETTING_NAMES)}")
    values.update(settings)
    uploads = {}
    reference = None
    if mode == "direction":
        ref = speaker.get("reference") or {}
        path = local_file(project, ref.get("file"))
        values["reference_text"] = _text(ref.get("text"), "参考录音准确转写")
        uploads["reference_audio"] = path
        reference = {"sha256": file_hash(path), "text": values["reference_text"]}
    spec, workflow, _ = comfy.load_kind(cfg, kind)
    fingerprint = digest({"kind": kind, "values": values, "reference": reference,
                          "workflow": workflow, "mapping": spec})
    return kind, values, uploads, fingerprint


def probe(path: Path, cfg: dict) -> dict:
    """Read the real sample count; no duration inferred from text or token limits."""
    try:
        with wave.open(str(path), "rb") as stream:
            result = {"duration_sec": stream.getnframes() / stream.getframerate(),
                      "sample_rate": stream.getframerate(), "channels": stream.getnchannels()}
    except (wave.Error, EOFError):
        try:
            import soundfile as sf
            info = sf.info(str(path))
            result = {"duration_sec": info.frames / info.samplerate,
                      "sample_rate": info.samplerate, "channels": info.channels}
        except ImportError:
            exe = ffmpeg_bin(cfg, "ffprobe")
            if not exe:
                raise MVError("测量旁白需 soundfile 或 ffprobe；按 requirements.txt 配置依赖") from None
            proc = subprocess.run([exe, "-v", "error", "-select_streams", "a:0", "-show_entries",
                                   "stream=sample_rate,channels,duration:format=duration", "-of", "json", str(path)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
            try:
                if proc.returncode:
                    raise ValueError()
                data = json.loads(proc.stdout)
                stream = data["streams"][0]
                duration = stream.get("duration") or data.get("format", {}).get("duration")
                result = {"duration_sec": float(duration),
                          "sample_rate": int(stream["sample_rate"]), "channels": int(stream["channels"])}
            except (ValueError, TypeError, KeyError, IndexError):
                raise MVError(f"无法测量音频: {path.name}") from None
        except (RuntimeError, ValueError) as exc:
            raise MVError(f"无法读取音频 {path.name}: {exc}") from exc
    number(result["duration_sec"], f"{path.name} 时长", 0.001)
    return result


def _selected(item: dict) -> dict | None:
    return next((t for t in item.get("takes", []) if t.get("id") == item.get("selected")), None)


def check(project: Project, cfg: dict, plan: dict, ready: bool = False) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    shots, duration = timeline(project)
    if plan.get("binding") != binding(project):
        (errors if ready else warnings).append("歌曲或分镜时间已改变；复核声音位置后运行 voice-check --bind")
    intervals = []
    for speaker in plan["speakers"]:
        if not speaker.get("description"):
            errors.append(f"{speaker['id']} 缺少音色 description")
    for cue in plan["cues"]:
        try:
            start = cue_start(cue, shots)
            window = number(cue.get("window_sec"), f"{cue['id']}.window_sec", 0.01)
            if start + window > duration + 0.001:
                raise MVError(f"{cue['id']} 声音窗口超过时间线末尾 {duration:.2f}s")
            _text(cue.get("text"), f"{cue['id']} 台词")
            _text(cue.get("instruction"), f"{cue['id']} 表演指令")
            if cue.get("kind", "narration") not in ("narration", "inner", "dialogue", "vocal_event"):
                raise MVError(f"{cue['id']} kind 需为 narration/inner/dialogue/vocal_event")
            speaker = _speaker(plan, cue.get("speaker"))
            number(cue.get("gain_db", 0), f"{cue['id']}.gain_db", -60, 12)
            number(cue.get("duck_db", cfg.get("voice", {}).get("duck_db", -6)), "duck_db", -30, 0)
            if not isinstance(cue.get("subtitle", True), bool):
                raise MVError(f"{cue['id']}.subtitle 需为布尔值")
            take = _selected(cue)
            _, _, _, fingerprint = request(project, cfg, cue, speaker)
            if not take:
                (errors if ready else warnings).append(f"{cue['id']} 尚未选定旁白版本")
                intervals.append((start, start + window, cue))
                continue
            if take.get("fingerprint") != fingerprint:
                raise MVError(f"{cue['id']} 台词、音色、表演或生成参数已改变，需要重做/重选配音")
            path = local_file(project, take.get("file"))
            if take.get("sha256") != file_hash(path):
                raise MVError(f"{cue['id']} 选定音频已被改写，需要重选版本")
            span = probe(path, cfg)["duration_sec"]
            if span > window + 0.001:
                raise MVError(f"{cue['id']} 配音 {span:.2f}s 超出窗口 {window:.2f}s；缩短台词、重做或调整位置，不截断音频")
            intervals.append((start, start + span, cue))
        except (MVError, TypeError, AttributeError) as exc:
            # Missing reference is a preparation item, but a delivery must be complete.
            message = str(exc)
            target = warnings if not ready and message.startswith(("声音文件路径为空", "参考录音准确转写")) else errors
            target.append(f"{cue['id']}: {message}")
    for i, (start, end, cue) in enumerate(intervals):
        for other_start, other_end, other in intervals[i + 1:]:
            if max(start, other_start) < min(end, other_end):
                warnings.append(f"{cue['id']} 与 {other['id']} 声音重叠，请试听确认")
        overlap = [s["id"] for s in shots if s.get("lyric") and max(start, s["start"]) < min(end, s["end"])]
        if overlap:
            warnings.append(f"{cue['id']} 与歌词字幕窗口重叠（{', '.join(overlap)}）；试听确认歌词可辨" +
                            ("，字幕分上下显示" if cue.get("subtitle", True) else ""))
    return errors, warnings


def generate(project: Project, cfg: dict, plan: dict, ids: str | None = None, *,
             speakers: bool = False, takes: int = 2, more: bool = False,
             dry_run: bool = False, seed: int | None = None) -> None:
    if not plan["enabled"]:
        raise MVError("声音计划未启用；确认使用旁白后将 enabled 设为 true")
    if takes < 1 or takes > 10:
        raise MVError("--takes 需在 1–10 之间")
    if seed is not None and (seed < 1 or seed > 2**31 - 1):
        raise MVError("Breeze seed 需在 1–2147483647 之间；0 不保证可复现")
    rows = plan["speakers" if speakers else "cues"]
    wanted = set(ids.split(",")) if ids else None
    if wanted and wanted - {i["id"] for i in rows}:
        raise MVError(f"未定义的声音条目: {sorted(wanted - {i['id'] for i in rows})}")
    targets = [i for i in rows if i["id"] in wanted] if wanted else rows
    jobs = []
    for item in targets:
        speaker = item if speakers else _speaker(plan, item.get("speaker"))
        kind, values, uploads, fingerprint = request(project, cfg, item, speaker, speakers)
        count = takes if wanted or more else max(0, takes - sum(t.get("fingerprint") == fingerprint for t in item.get("takes", [])))
        if not count:
            continue
        spec, workflow, _ = comfy.load_kind(cfg, kind)
        problems = comfy.validate_kind(workflow, spec) + validate_workflow(workflow, kind.endswith("direction"))
        if problems:
            raise MVError(f"{kind} 工作流无效: " + "；".join(problems))
        comfy.apply_params(workflow, spec, dict(values, seed=1, filename_prefix="mv-creator/voice",
                                              **{k: "reference.flac" for k in uploads}))
        jobs.append((item, kind, values, uploads, fingerprint, digest(workflow), count))
    print(f"将生成 {len(jobs)} {'个音色样音' if speakers else '句配音'}，共 {sum(j[-1] for j in jobs)} 次 Breeze 调用（补齐候选或追加）", flush=True)
    if dry_run:
        for item, kind, values, _, _, _, count in jobs:
            print(f"  {item['id']} / {kind} / {count} 版：{values['text']}")
        return
    # Require a way to measure FLAC before consuming GPU time.
    if jobs:
        try:
            import soundfile  # noqa: F401
        except ImportError:
            if not ffmpeg_bin(cfg, "ffprobe"):
                raise MVError("先配置 soundfile 或 ffprobe，以便保存后测量配音时长") from None
    for item, kind, values, uploads, fingerprint, workflow_hash, count in jobs:
        folder = project.root / "audio" / ("auditions" if speakers else "takes") / item["id"]
        completed = sum(t.get("fingerprint") == fingerprint for t in item.get("takes", [])) if not wanted and not more else 0
        for index in range(count):
            used = [int(t["id"].split("-")[-1]) for t in item.get("takes", [])]
            if folder.is_dir():
                used += [int(m.group(1)) for p in folder.iterdir() if (m := re.match(r"take-(\d+)", p.name))]
            take_id = f"take-{max(used, default=0) + 1}"
            current_seed = (seed - 1 + completed + index) % (2**31 - 1) + 1 if seed is not None else random.randint(1, 2**31 - 1)
            payload = dict(values, seed=current_seed, filename_prefix=f"mv-creator/{project.slug}/voice/{item['id']}/{take_id}")
            print(f"{item['id']} {take_id}，seed={current_seed}", flush=True)
            saved = comfy.run_kind(cfg, kind, payload, uploads, f"mv-creator/{project.slug}/voice/{item['id']}", folder, take_id)
            if len(saved) != 1:
                raise MVError(f"{kind} 需恰好一个音频保存输出，实际 {len(saved)} 个；文件已保留")
            record = {"id": take_id, "file": project.rel(saved[0]), "text": values["text"],
                      "seed": current_seed, "workflow": kind, "workflow_sha256": workflow_hash,
                      "parameters": values, "fingerprint": fingerprint, "sha256": file_hash(saved[0]),
                      "created": now_iso(), **probe(saved[0], cfg)}
            item.setdefault("takes", []).append(record)
            write_json(project.root / PLAN, plan)
            print(f"  已保存 {saved[0].resolve().as_posix()}（{record['duration_sec']:.2f}s）", flush=True)


def select(project: Project, cfg: dict, plan: dict, item_id: str, take_id: str, speaker: bool = False) -> None:
    item = next((i for i in plan["speakers" if speaker else "cues"] if i["id"] == item_id), None)
    take = next((t for t in item.get("takes", []) if t["id"] == take_id), None) if item else None
    if take is None:
        raise MVError(f"{item_id} 没有 {take_id}")
    owner = item if speaker else _speaker(plan, item.get("speaker"))
    if request(project, cfg, item, owner, speaker)[3] != take.get("fingerprint"):
        raise MVError("此候选基于旧台词、音色或参数，请生成新版本")
    path = local_file(project, take["file"])
    if file_hash(path) != take.get("sha256"):
        raise MVError("候选音频已被改写，请重新生成")
    if not speaker:
        if probe(path, cfg)["duration_sec"] > number(item.get("window_sec"), "window_sec", 0.01) + 0.001:
            raise MVError("配音长于声音窗口；请调整窗口或重做台词，不截断配音")
    item["selected"] = take_id
    if speaker:
        item["reference"] = {"file": take["file"], "text": take["text"]}
    write_json(project.root / PLAN, plan)
    print(f"{item_id} 已选定 {take_id}" + ("，已设为固定音色参考，请核对参考文本与实际发音一致" if speaker else ""))


def validate_workflow(workflow: dict, direction: bool) -> list[str]:
    kind = "BreezeTTS2VoiceDirection" if direction else "BreezeTTS2VoiceDesign"
    if not any(n["class_type"] == kind for n in workflow.values()):
        return [f"需使用 {kind}，不能混用其他 Breeze 节点包"]
    problems = []
    for node in workflow.values():
        if node["class_type"] == "BreezeTTS2VoiceDirection" and node["inputs"].get("stitch_reference") != "none":
            problems.append("Voice Direction 的 stitch_reference 必须为 none，避免参考录音混入台词")
        if node["class_type"] == "BreezeTTS2LoadModel" and node["inputs"].get("download_if_missing") is not False:
            problems.append("模板需 download_if_missing=false；模型按 setup 指引准备后再运行")
    return problems


def _run(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        raise MVError("音频处理失败:\n" + "\n".join(proc.stderr.splitlines()[-12:]))


def mix_settings(cfg: dict) -> dict:
    v = cfg.get("voice", {})
    return {"sample_rate": 48000,
            "music_gain_db": number(v.get("music_gain_db", -3), "music_gain_db", -60, 6),
            "voice_gain_db": number(v.get("voice_gain_db", 0), "voice_gain_db", -60, 12),
            "duck_db": number(v.get("duck_db", -6), "duck_db", -30, 0),
            "attack_sec": number(v.get("attack_sec", 0.15), "attack_sec", 0.001, 3),
            "release_sec": number(v.get("release_sec", 0.25), "release_sec", 0.001, 3)}


def resolved(project: Project, cfg: dict, plan: dict, *, warn: bool = True) -> list[dict]:
    errors, warnings = check(project, cfg, plan, ready=True)
    if warn:
        for warning in warnings:
            print(f"[WARN] {warning}")
    if errors:
        raise MVError("声音计划未就绪:\n" + "\n".join(errors))
    shots, _ = timeline(project)
    rows = []
    for cue in plan["cues"]:
        take = _selected(cue)
        path = local_file(project, take["file"])
        rows.append(dict(cue, start=cue_start(cue, shots), file=path,
                         duration_sec=probe(path, cfg)["duration_sec"], take_id=take["id"]))
    return rows


def mix_fingerprint(project: Project, cfg: dict, plan: dict) -> str:
    rows = resolved(project, cfg, plan, warn=False)
    return digest({"mixer_version": 1, "binding": binding(project), "settings": mix_settings(cfg),
                   "rows": [{k: str(r[k]) for k in ("id", "start", "duration_sec", "take_id", "text")}
                            | {"sha256": file_hash(r["file"]), "gain_db": r.get("gain_db", 0),
                               "duck_db": r.get("duck_db"), "subtitle": r.get("subtitle", True)} for r in rows]})


def duck_expression(rows: list[dict], settings: dict) -> str:
    expression = "0"
    attack, release = settings["attack_sec"], settings["release_sec"]
    for row in rows:
        start, end = row["start"], row["start"] + row["duration_sec"]
        pre, post = max(0, start - attack), end + release
        gain = row.get("duck_db", settings["duck_db"])
        # Minimum attenuation across overlaps avoids summing two duck envelopes.
        envelope = (f"if(lt(t,{pre:.6f}),0,if(lt(t,{start:.6f}),"
                    f"{gain}*(t-{pre:.6f})/{max(start-pre, 0.000001):.6f},"
                    f"if(lt(t,{end:.6f}),{gain},if(lt(t,{post:.6f}),"
                    f"{gain}*({post:.6f}-t)/{release},0))))")
        expression = f"min({expression},{envelope})"
    return f"pow(10,({expression})/20)"


def srt(rows: list[dict]) -> str:
    def stamp(t):
        ms = round(t * 1000)
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        sec, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
    captions = [r for r in sorted(rows, key=lambda r: r["start"]) if r.get("subtitle", True)]
    return "\n\n".join(f"{i}\n{stamp(r['start'])} --> {stamp(r['start']+r['duration_sec'])}\n{r['text']}"
                         for i, r in enumerate(captions, 1)) + ("\n" if captions else "")


def mix(project: Project, cfg: dict) -> list[Path]:
    plan = load_plan(project)
    if not plan or not plan["enabled"]:
        raise MVError("没有启用声音计划；纯歌曲项目直接运行 roughcut/package")
    rows = resolved(project, cfg, plan)
    if not rows:
        raise MVError("声音计划没有 cues；不需要旁白时将 enabled 设为 false")
    song = project.path(project.load().get("music", {}).get("file"))
    if not song or not song.is_file():
        raise MVError("混音前先选定歌曲")
    exe = ffmpeg_bin(cfg)
    if not exe:
        raise MVError("混音需要 ffmpeg；在配置的 ffmpeg 中填写现有可执行文件路径")
    _, duration = timeline(project)
    song_length = probe(song, cfg)["duration_sec"]
    if song_length + 0.02 < duration:
        raise MVError(f"歌曲仅 {song_length:.2f}s，短于时间线 {duration:.2f}s；请先调整时间线")
    settings = mix_settings(cfg)
    fingerprint = mix_fingerprint(project, cfg, plan)
    dest = project.root / "final" / "audio"
    dest.mkdir(parents=True, exist_ok=True)
    paths = [dest / n for n in ("song_only.wav", "voice_track.wav", "mix.wav", "voice.srt")]
    manifest = dest / "mix-manifest.json"
    if manifest.is_file() and all(p.is_file() for p in paths):
        previous = read_json(manifest)
        if previous.get("fingerprint") == fingerprint and previous.get("outputs") == {p.name: file_hash(p) for p in paths}:
            print("混音已是当前版本，复用现有输出")
            return paths
    with tempfile.TemporaryDirectory(prefix=".voice-mix-", dir=dest) as tmp:
        work = Path(tmp)
        common = ["aresample=48000", "aformat=sample_fmts=fltp:channel_layouts=stereo", "asetpts=PTS-STARTPTS"]
        song_filters = ",".join(common + [f"volume={settings['music_gain_db']}dB", f"atrim=duration={duration:.6f}"])
        limiter = "alimiter=limit=0.95:level=false:latency=true"
        _run([exe, "-y", "-v", "error", "-i", str(song), "-af", song_filters + "," + limiter,
              "-c:a", "pcm_s24le", str(work / "song_only.wav")])
        args = [exe, "-y", "-v", "error"]
        filters, labels = [], []
        for i, row in enumerate(rows):
            args += ["-i", str(row["file"])]
            gain = settings["voice_gain_db"] + row.get("gain_db", 0)
            fade = min(0.02, row["duration_sec"] / 4)
            f = common + [f"volume={gain}dB", f"afade=t=in:d={fade:.6f}",
                          f"afade=t=out:st={row['duration_sec']-fade:.6f}:d={fade:.6f}",
                          f"adelay={round(row['start']*48000)}S:all=1"]
            filters.append(f"[{i}:a]" + ",".join(f) + f"[v{i}]")
            labels.append(f"[v{i}]")
        filters.append("".join(labels) + f"amix=inputs={len(rows)}:normalize=0:dropout_transition=0,"
                       f"apad,atrim=duration={duration:.6f},{limiter}[out]")
        script = work / "voice-filter.txt"
        script.write_text(";\n".join(filters), encoding="utf-8")
        _run(args + ["-filter_complex_script", str(script), "-map", "[out]", "-c:a", "pcm_s24le", str(work / "voice_track.wav")])
        expression = duck_expression(rows, settings)
        graph = (f"[0:a]{song_filters},volume='{expression}':eval=frame[music];"
                 f"[1:a]aresample=48000[voice];[music][voice]amix=inputs=2:normalize=0:dropout_transition=0,"
                 f"{limiter},atrim=duration={duration:.6f}[out]")
        script.write_text(graph, encoding="utf-8")
        _run([exe, "-y", "-v", "error", "-i", str(song), "-i", str(work / "voice_track.wav"),
              "-filter_complex_script", str(script), "-map", "[out]", "-c:a", "pcm_s24le", str(work / "mix.wav")])
        (work / "voice.srt").write_text(srt(rows), encoding="utf-8-sig")
        for path in paths:
            (work / path.name).replace(path)
    write_json(manifest, {"fingerprint": fingerprint, "created": now_iso(), "duration_sec": duration,
                          "outputs": {p.name: file_hash(p) for p in paths}, "settings": settings,
                          "cues": [{k: (project.rel(r[k]) if k == "file" else r[k])
                                    for k in ("id", "speaker", "text", "file", "start", "duration_sec", "take_id")} for r in rows]})
    print(f"已输出歌曲版、旁白轨、混音和旁白字幕: {dest.resolve().as_posix()}")
    return paths
