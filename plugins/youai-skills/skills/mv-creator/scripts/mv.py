#!/usr/bin/env python3
"""mv-creator: song MV pipeline on ComfyUI (music, image-to-video) and Tardis (images)."""

from __future__ import annotations

import argparse
import importlib
import json
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mvlib import audio, comfy, frames, media, voice, music as songlib  # noqa: E402
from mvlib import shots as shotlib  # noqa: E402
from mvlib.common import (  # noqa: E402
    CONFIG_NAME, SKILL_DIR, MVError, Project, ffmpeg_bin, fmt_time, load_config, max_clip_sec,
    next_index, now_iso, pick_candidate, read_json, shot_limit_sec, slugify, write_json,
    validate_video, video_frames, VIDEO_PROFILES,
)

PROJECT_DIRS = ("music/takes", "analysis", "storyboard", "characters/raw", "frames/raw",
                "frames/prompts", "clips", "final")
SEED_MAX = 2**32 - 1
DRY_RUN_HELP = "只校验并列出将生成的内容与调用次数，不实际生成"


def _abs(path: Path) -> str:
    return Path(path).resolve().as_posix()


def _project(cfg: dict, slug: str) -> Project:
    return Project(cfg, slug).require()


def _take_seed(base: int | None, offset: int) -> int:
    """A fixed seed steps by one per take so takes differ yet stay reproducible."""
    if base is None:
        return random.randint(0, SEED_MAX)
    return (int(base) + offset) % (SEED_MAX + 1)


# Setup ---------------------------------------------------------------------

def cmd_init_config(args, cfg):
    target = Path.cwd() / CONFIG_NAME
    if target.exists() and not args.force:
        raise MVError(f"{target} 已存在；确认要覆盖时加 --force")
    data = read_json(SKILL_DIR / "assets" / "config.example.json")
    if args.url:
        data["comfyui"]["url"] = args.url
    write_json(target, data)
    workflows = Path.cwd() / data["workflows_dir"]
    workflows.mkdir(parents=True, exist_ok=True)
    print(f"已创建 {_abs(target)}\nComfyUI 地址: {data['comfyui']['url']}（不对时直接编辑该文件）\n"
          f"默认使用技能自带的 API 工作流；自定义覆盖文件可放到: {_abs(workflows)}")


def cmd_doctor(args, cfg):
    failed = False

    def report(level: str, text: str) -> None:
        nonlocal failed
        failed = failed or level == "FAIL"
        print(f"[{level}] {text}")

    version = sys.version_info
    report("OK" if version >= (3, 10) else "FAIL",
           f"Python {version.major}.{version.minor}.{version.micro}  ({sys.executable})")
    for module, purpose in (("PIL", "关键帧裁切"), ("librosa", "节拍分析"),
                            ("soundfile", "音频读取"), ("openai", "Tardis 生图")):
        try:
            mod = importlib.import_module(module)
            report("OK", f"{module} {getattr(mod, '__version__', '')}（{purpose}）")
        except ImportError:
            report("FAIL", f"缺少 {module}（{purpose}）：pip install -r {_abs(SKILL_DIR / 'requirements.txt')}")
    for name in ("ffmpeg", "ffprobe"):
        found = ffmpeg_bin(cfg, name)
        report("OK" if found else "WARN", f"{name}: {found or '未找到（粗剪和 WAV 转换需要）'}")

    report("OK" if cfg["_path"] else "WARN",
           f"配置: {cfg['_path'] or f'未找到 {CONFIG_NAME}，使用默认值（运行 init-config 创建）'}")
    try:
        report("OK", f"imagegen-tardis: {_abs(frames.locate_tardis(cfg))}")
    except MVError as exc:
        report("FAIL", str(exc))
    report("OK" if frames.TARDIS_CREDENTIALS.is_file() else "WARN",
           "Tardis 密钥文件" + ("已配置" if frames.TARDIS_CREDENTIALS.is_file()
                              else "未配置：按 imagegen-tardis 的 configure 流程保存"))

    client = comfy.ComfyClient.from_config(cfg)
    object_info = None
    try:
        stats = client.system_stats()
        devices = ", ".join(f"{d.get('name', '?')} {d.get('vram_total', 0) / 2**30:.0f}GB"
                            for d in stats.get("devices", []))
        version_text = stats.get("system", {}).get("comfyui_version", "")
        report("OK", f"ComfyUI {client.url} {version_text}  {devices}")
        object_info = client.object_info()
    except MVError as exc:
        report("FAIL", str(exc).splitlines()[0])
    video_kind = "wan5b-i2v" if cfg["video"].get("model") == "wan2.2-5b" else "i2v"
    _check_workflows(cfg, object_info, report, ("music", video_kind, "flf2v", "tts-design", "tts-direction"))
    if failed:
        raise MVError("环境检查未通过，按上面的 FAIL 项处理（详见 references/setup.md）")


def _check_workflows(cfg, object_info, report, kinds=("music", "i2v", "flf2v")):
    for kind in kinds:
        optional = kind in ("flf2v", "tts-design", "tts-direction")
        try:
            spec, workflow, path = comfy.load_kind(cfg, kind)
        except MVError as exc:
            report("WARN" if optional else "FAIL", f"工作流 {kind}: {exc}")
            continue
        problems = comfy.validate_kind(workflow, spec)
        if kind in ("tts-design", "tts-direction"):
            problems.extend(voice.validate_workflow(workflow, kind == "tts-direction"))
        if kind in ("i2v", "flf2v") and not spec.get("video_model"):
            problems.extend(comfy.validate_h3_workflow(workflow))
        if object_info is not None:
            problems.extend(comfy.validate_server(workflow, object_info))
        if problems:
            report("WARN" if kind.startswith("tts-") else "FAIL",
                   f"工作流 {kind} ({path.name}):\n  - " + "\n  - ".join(problems))
        else:
            report("OK", f"工作流 {kind}: {_abs(path)} 参数映射有效")


# Project -------------------------------------------------------------------

def cmd_new(args, cfg):
    slug = args.slug or slugify(args.title)
    project = Project(cfg, slug)
    if project.exists():
        raise MVError(f"项目已存在: {project.root}")
    for rel in PROJECT_DIRS:
        (project.root / rel).mkdir(parents=True, exist_ok=True)
    template = (SKILL_DIR / "assets" / "brief-template.md").read_text(encoding="utf-8")
    (project.root / "brief.md").write_text(template.replace("{{title}}", args.title), encoding="utf-8")
    project.save({
        "version": 1, "title": args.title, "slug": slug, "created": now_iso(),
        "video": dict(VIDEO_PROFILES[args.video_profile] if getattr(args, "video_profile", None) else cfg["video"]),
        "music": {"duration_sec": cfg["music"]["duration_sec"],
                  "target_duration_sec": cfg["music"]["duration_sec"],
                  "takes": [], "selected": None, "file": None},
    })
    print(f"已创建项目 {slug}: {_abs(project.root)}\n下一步: 填写 brief.md")


def cmd_status(args, cfg):
    project = _project(cfg, args.slug)
    meta = project.load()
    music = meta.get("music", {})
    template = (SKILL_DIR / "assets" / "brief-template.md").read_text(encoding="utf-8")
    brief = (project.root / "brief.md").read_text(encoding="utf-8")
    caption, lyrics = project.root / "music" / "caption.txt", project.root / "music" / "lyrics.txt"
    selected = music.get("selected")
    beats = read_json(project.beats_file) if project.beats_file.is_file() else None
    data = project.load_shots() if project.has_shots() else None
    beats_stale, shots_stale = _stale(beats, selected), _stale(data, selected)
    rows = [
        ("创意简报", brief.strip() != template.replace("{{title}}", meta["title"]).strip(),
         "填写 brief.md 并与用户确认"),
        ("歌曲提示词", _nonempty(caption) and _nonempty(lyrics),
         "用 comfyui-minimax-music 成稿，写入 music/caption.txt 与 music/lyrics.txt"),
        (f"歌曲生成（{len(music.get('takes', []))} 版）", bool(music.get("takes")), f"music {args.slug} --takes 1"),
        (f"选定歌曲（{music.get('selected') or '未选'}）", bool(music.get("file")),
         f"music-select {args.slug} <take-N>"),
        ("节拍分析" + ("（基于旧歌曲）" if beats_stale else ""), bool(beats) and not beats_stale,
         f"analyze {args.slug}"),
        ("分镜骨架" + (f"（基于旧歌曲 {data['take']}）" if shots_stale else ""),
         bool(data) and not shots_stale,
         f"征得用户同意后 shots-init {args.slug} --force 重切；或按新节拍手动调整时间，"
         f"再把 shots.json 的 take 改为 {selected}" if shots_stale
         else f"shots-init {args.slug} --bars-per-shot 2"),
    ]
    if data:
        errors, _ = shotlib.check(data, project.video(), None, draft=False)
        chars = data.get("characters", [])
        shots = data["shots"]
        refs = sum(1 for c in chars if c.get("ref"))
        picked_frames = sum(1 for s in shots if s["frame"].get("selected"))
        picked_clips = sum(1 for s in shots if s["clip"].get("selected"))
        rows += [
            (f"分镜内容（{len(errors)} 个问题）", not errors, f"补全 shots.json 后运行 shots-check {args.slug}"),
            (f"角色参考图（{refs}/{len(chars)}）", refs == len(chars),
             f"chars {args.slug} --n 1，再 char-select"),
            (f"关键帧（{picked_frames}/{len(shots)}）", picked_frames == len(shots),
             f"frames {args.slug} --n 1，再 frame-select"),
            (f"视频片段（{picked_clips}/{len(shots)}）", picked_clips == len(shots),
             f"clips {args.slug} --takes 1，再 clip-select"),
        ]
    rows += [
        ("剪映素材包", (project.root / "final" / "capcut" / "package.json").is_file(), f"package {args.slug}"),
        ("粗剪参考", (project.root / "final" / "roughcut.mp4").is_file(), f"roughcut {args.slug}"),
    ]
    plan = voice.load_plan(project)
    if plan and plan["enabled"]:
        errors, warnings = voice.check(project, cfg, plan, ready=True)
        voice_done = not errors and bool(plan["cues"])
        rows.insert(-2, (f"旁白（{len(plan['cues'])} 句）", voice_done,
                         f"voice-check {args.slug}，再试听、voice-select 与 mix-preview"))
        for message in errors + warnings:
            print(f"[声音] {message}")
        manifest = project.root / "final" / "audio" / "mix-manifest.json"
        mix_done = voice_done and manifest.is_file()
        if mix_done:
            record = read_json(manifest)
            mix_done = record.get("fingerprint") == voice.mix_fingerprint(project, cfg, plan)
            mix_done = mix_done and set(record.get("outputs", {})) == {"song_only.wav", "voice_track.wav", "mix.wav", "voice.srt"}
            mix_done = mix_done and all((manifest.parent / name).is_file() and
                                       voice.file_hash(manifest.parent / name) == checksum
                                       for name, checksum in record.get("outputs", {}).items())
        rows.insert(-2, ("旁白混音", mix_done, f"mix-preview {args.slug}"))
        expected = read_json(manifest).get("fingerprint") if mix_done else None
        for label, path in (("剪映素材包", project.root / "final/capcut/package.json"),
                            ("粗剪参考", project.root / "final/roughcut-manifest.json")):
            current = bool(expected and path.is_file() and read_json(path).get("audio_fingerprint") == expected)
            rows = [(name, current if name == label else done, hint) for name, done, hint in rows]
    print(f"{meta['title']}（{args.slug}）  {_abs(project.root)}")
    next_step = None
    for label, done, hint in rows:
        print(f"  [{'x' if done else ' '}] {label}")
        if not done and next_step is None:
            next_step = hint
    print(f"下一步: {next_step}" if next_step else "全部完成。")


def _nonempty(path: Path) -> bool:
    return path.is_file() and bool(path.read_text(encoding="utf-8-sig").strip())


def _stale(record: dict | None, selected: str | None) -> bool:
    """True when beats/shots were built from a song take other than the selected one."""
    return bool(record and record.get("take") and record["take"] != selected)


# Music ---------------------------------------------------------------------

def cmd_music(args, cfg):
    if args.takes < 1:
        raise MVError("--takes 必须大于零")
    project = _project(cfg, args.slug)
    meta = project.load()
    folder = project.root / "music"
    caption, lyrics = folder / "caption.txt", folder / "lyrics.txt"
    if not _nonempty(caption):
        raise MVError(f"缺少 {caption}（用 comfyui-minimax-music 成稿后写入）")
    music = meta.setdefault("music", {"takes": []})
    target, duration = songlib.settings(args, music, cfg["music"])
    if getattr(args, "dry_run", False):
        print(f"目标约 {target:g}s，生成上限 {duration:g}s；{args.takes} 次音乐生成（不提交）")
        return
    music.update(duration_sec=target, target_duration_sec=target, generation_max_duration_sec=duration)
    values = {"caption": caption.read_text(encoding="utf-8-sig").strip(),
              "lyrics": lyrics.read_text(encoding="utf-8-sig").strip() if lyrics.is_file() else "",
              "max_duration": int(duration) if float(duration).is_integer() else duration}
    for take_index in range(args.takes):
        number = max((int(t["id"].split("-")[1]) for t in music.get("takes", [])), default=0) + 1
        seed = _take_seed(args.seed, take_index)
        values.update(seed=seed, filename_prefix=f"mv-creator/{args.slug}/take-{number}")
        print(f"生成 take-{number}（seed {seed}，上限 {duration}s）", flush=True)
        saved = comfy.run_kind(cfg, "music", values, {}, f"mv-creator/{args.slug}",
                               folder / "takes", f"take-{number}")
        music.setdefault("takes", []).append({"id": f"take-{number}", "file": project.rel(saved[0]),
                                              "seed": seed, "max_duration": duration,
                                              "target_duration_sec": target, "created": now_iso()})
        # Save the successful generation even if probing or a later take fails.
        project.save(meta)
        take = music["takes"][-1]
        try:
            take.update(songlib.inspect(saved[0], cfg, duration))
        except MVError as exc:
            take.update(ending_review="pending_listen", probe_error=str(exc))
            print(f"  注意: 成品已保存，时长未检测：{exc}")
        run_log = saved[0].parent / f"take-{number}.run.json"
        if run_log.is_file():
            take["run_log"] = project.rel(run_log)
            take["prompt_id"] = read_json(run_log).get("prompt_id")
        project.save(meta)
        if take.get("near_limit"):
            print("  注意: 成品接近生成上限，可能尚未完整收尾；请试听最后一句及尾奏，不自动判定完整。")
        print(f"  已保存 {_abs(saved[0])}", flush=True)


def cmd_music_check(args, cfg):
    project = _project(cfg, args.slug)
    meta = project.load()
    for take in meta.get("music", {}).get("takes", []):
        take.update(songlib.inspect(project.path(take["file"]), cfg, take.get("max_duration")))
        print(f"{take['id']}: {take['duration_sec']:.3f}s，"
              + ("接近上限，请试听收尾" if take["near_limit"] else "未接近上限，仍需试听收尾"))
    project.save(meta)


def cmd_video_profile(args, cfg):
    project = _project(cfg, args.slug)
    video = dict(VIDEO_PROFILES[args.profile])
    validate_video(video)
    if project.has_shots():
        data = project.load_shots()
        if video["model"] == "wan2.2-5b" and any(s.get("workflow") == "flf2v" for s in data["shots"]):
            raise MVError("Wan5B 仅支持 i2v；项目有 flf2v 镜头，请先人工调整分镜或保留 H3")
        if any(s["end"] - s["start"] > shot_limit_sec(video) + 1e-6 for s in data["shots"]):
            raise MVError("新配置的单段时长不足，请先拆分过长镜头；不自动重切已确认分镜")
    print(json.dumps(video, ensure_ascii=False, indent=2))
    if args.dry_run:
        print("仅预览，未更改项目")
        return
    meta = project.load()
    meta.setdefault("video_history", []).append({"video": meta.get("video", {}), "changed": now_iso()})
    meta["video"] = video
    project.save(meta)
    print("已更新项目视频配置；请运行 frame-select 从所选原图重裁关键帧，再 clips --dry-run。已有视频保留。")


def cmd_music_select(args, cfg):
    project = _project(cfg, args.slug)
    meta = project.load()
    music = meta["music"]
    take = next((t for t in music.get("takes", []) if t["id"] == args.take), None)
    if not take:
        raise MVError(f"没有 {args.take}，可选: {', '.join(t['id'] for t in music.get('takes', [])) or '无'}")
    previous = music.get("selected")
    src = project.path(take["file"])
    dest = project.root / "music" / f"song{src.suffix}"
    for old in (project.root / "music").glob("song.*"):
        if old != dest:
            old.unlink()
    shutil.copy2(src, dest)
    music.update(selected=take["id"], file=project.rel(dest))
    project.save(meta)
    print(f"已选定 {take['id']} → {_abs(dest)}")
    if project.beats_file.is_file() and previous != take["id"]:
        print("注意: 已有节拍分析基于之前的歌曲，需要重新运行 analyze"
              + ("；分镜时间也要按新节拍重切或调整" if project.has_shots() else ""))


# Analysis and storyboard ----------------------------------------------------

def cmd_analyze(args, cfg):
    project = _project(cfg, args.slug)
    music = project.load().get("music", {})
    song = project.path(music.get("file"))
    if not song or not song.is_file():
        raise MVError("还没有选定歌曲（music-select）")
    result = audio.analyze(song, args.beats_per_bar)
    result["take"] = music.get("selected")
    write_json(project.beats_file, result)
    print(f"时长 {result['duration']}s，BPM ≈ {result['tempo']}，{len(result['bars'])} 小节 → {_abs(project.beats_file)}")
    print("\n".join(audio.energy_sketch(result["bars"])))


def cmd_shots_init(args, cfg):
    project = _project(cfg, args.slug)
    if project.has_shots() and not args.force:
        raise MVError(f"{project.shots_file} 已存在；重切会丢失已填写内容，确认后加 --force")
    if not project.beats_file.is_file():
        raise MVError("缺少节拍分析（先运行 analyze）")
    video = project.video()
    beats = read_json(project.beats_file)
    selected = project.load().get("music", {}).get("selected")
    if _stale(beats, selected):
        raise MVError(f"节拍分析基于 {beats['take']}，当前歌曲是 {selected}：先重新运行 analyze")
    data = shotlib.skeleton(beats, video, args.bars_per_shot)
    data["take"] = beats.get("take")
    project.save_shots(data)
    print(f"已生成 {len(data['shots'])} 个镜头骨架（片段最长 {max_clip_sec(video):.2f}s，"
          f"镜头最长 {shot_limit_sec(video):.2f}s）→ {_abs(project.shots_file)}")
    for shot in data["shots"]:
        print(f"  {shot['id']}  {fmt_time(shot['start'])}–{fmt_time(shot['end'])}  "
              f"{shot['end'] - shot['start']:.2f}s  小节 {shot['bars']}")


def cmd_shots_check(args, cfg):
    project = _project(cfg, args.slug)
    data = project.load_shots()
    duration = read_json(project.beats_file)["duration"] if project.beats_file.is_file() else None
    errors, warnings = shotlib.check(data, project.video(), duration, args.draft)
    out = project.root / "storyboard" / "storyboard.md"
    out.write_text(shotlib.render_markdown(project.load()["title"], data), encoding="utf-8")
    for w in warnings:
        print(f"[WARN] {w}")
    for e in errors:
        print(f"[FAIL] {e}")
    print(f"分镜表: {_abs(out)}")
    if errors:
        raise MVError(f"分镜有 {len(errors)} 个问题需要修正")
    print(f"校验通过：{len(data['shots'])} 个镜头")


# Characters and keyframes ----------------------------------------------------

def cmd_chars(args, cfg):
    project = _project(cfg, args.slug)
    data = project.load_shots()
    chars = data.get("characters", [])
    if args.ids:
        wanted = [i.strip() for i in args.ids.split(",")]
        chars = [c for c in chars if c["id"] in wanted]
        if len(chars) != len(wanted):
            raise MVError(f"未定义的角色: {set(wanted) - {c['id'] for c in chars}}")
    else:
        chars = [c for c in chars if not c.get("candidates")]
    if not chars:
        print("没有需要生成的角色（已有候选的角色用 --ids 指定重做）")
        return
    for char in chars:
        if not char.get("prompt"):
            raise MVError(f"角色 {char['id']} 的 prompt 为空")
    print(f"将为 {len(chars)} 个角色生成设定图，每个 {args.n} 张（{len(chars)} 次 Tardis 调用）："
          f"{', '.join(c['id'] for c in chars)}", flush=True)
    if args.dry_run:
        return
    folder = project.root / "characters" / "raw"
    for char in chars:
        number = next_index(folder, char["id"])
        out = folder / f"{char['id']}-v{number:02d}.png"
        prompt_file = project.root / "characters" / "prompts" / f"{char['id']}-v{number:02d}.txt"
        saved = frames.run_tardis(cfg, "generate", frames.character_prompt(data, char),
                                  prompt_file, out, [], args.n)
        char.setdefault("candidates", []).extend(project.rel(p) for p in saved)
        project.save_shots(data)
        _print_candidates(project, char["id"], char["candidates"])


def cmd_char_select(args, cfg):
    project = _project(cfg, args.slug)
    data = project.load_shots()
    char = next((c for c in data.get("characters", []) if c["id"] == args.char_id), None)
    if not char:
        raise MVError(f"没有角色 {args.char_id}")
    src = pick_candidate(project, char.get("candidates", []), args.choice)
    dest = project.root / "characters" / f"{char['id']}{src.suffix.lower()}"
    shutil.copy2(src, dest)
    char["ref"] = project.rel(dest)
    project.save_shots(data)
    print(f"角色 {char['id']} 参考图 → {_abs(dest)}")
    used = [s["id"] for s in data["shots"] if char["id"] in s.get("characters", []) and s["frame"]["candidates"]]
    if used:
        print(f"注意: 这些镜头的关键帧候选基于旧参考图生成: {', '.join(used)}")


def cmd_frames(args, cfg):
    project = _project(cfg, args.slug)
    data = project.load_shots()
    video = project.video()
    targets = shotlib.pick_shots(data, args.shots) if args.shots else \
        [s for s in data["shots"] if not s["frame"].get("candidates")]
    chars = {c["id"]: c for c in data.get("characters", [])}
    for shot in targets:
        if not shot.get("image_prompt"):
            raise MVError(f"{shot['id']} 的 image_prompt 为空")
        for cid in shot.get("characters", []):
            if not chars.get(cid, {}).get("ref"):
                raise MVError(f"{shot['id']} 用到角色 {cid}，但还没有选定参考图（char-select）")
    if not targets:
        print("没有需要生成的镜头（已有候选的镜头用 --shots 指定重做）")
        return
    print(f"将为 {len(targets)} 个镜头生成关键帧，每个 {args.n} 张（{len(targets)} 次 Tardis 调用）："
          f"{', '.join(s['id'] for s in targets)}", flush=True)
    if args.dry_run:
        return
    folder = project.root / "frames" / "raw"
    for shot in targets:
        refs = [chars[cid] for cid in shot.get("characters", [])]
        number = next_index(folder, shot["id"])
        out = folder / f"{shot['id']}-v{number:02d}.png"
        prompt = frames.shot_prompt(data, shot, refs, video, cfg["image"].get("size"))
        prompt_file = project.root / "frames" / "prompts" / f"{shot['id']}-v{number:02d}.txt"
        images = [project.path(c["ref"]) for c in refs]
        saved = frames.run_tardis(cfg, "edit" if images else "generate", prompt, prompt_file,
                                  out, images, args.n)
        shot["frame"].setdefault("candidates", []).extend(project.rel(p) for p in saved)
        project.save_shots(data)
        _print_candidates(project, shot["id"], shot["frame"]["candidates"])


def cmd_frame_select(args, cfg):
    project = _project(cfg, args.slug)
    data = project.load_shots()
    _, shot = shotlib.find_shot(data, args.shot)
    if args.choice:
        src = pick_candidate(project, shot["frame"].get("candidates", []), args.choice)
    else:
        # Re-crop the previously chosen original, e.g. after changing `crop`.
        source = shot["frame"].get("source")
        src = (Path(source) if Path(source).is_absolute() else project.path(source)) if source else None
        if not src or not src.is_file():
            raise MVError(f"{shot['id']} 没有可重裁的原图，请指定候选序号或图片路径")
    video = project.video()
    dest = project.root / "frames" / f"{shot['id']}.png"
    frames.normalize(src, dest, video["width"], video["height"], shot.get("crop", "center"))
    shot["frame"].update(selected=project.rel(dest), source=_relish(project, src))
    project.save_shots(data)
    print(f"{shot['id']} 关键帧 → {_abs(dest)}（{video['width']}×{video['height']}，裁切 {shot.get('crop', 'center')}）")
    if shot["clip"].get("takes"):
        print("注意: 该镜头已有的视频片段基于旧关键帧生成")


def _relish(project: Project, path: Path) -> str:
    try:
        return project.rel(path)
    except ValueError:
        return _abs(path)


def _print_candidates(project: Project, label: str, candidates: list[str]) -> None:
    print(f"{label} 候选:")
    for index, rel in enumerate(candidates, start=1):
        print(f"  {index}. {_abs(project.path(rel))}")


# Clips ---------------------------------------------------------------------

def _motion_prompt(data: dict, shot: dict) -> str:
    parts = [shot["motion_prompt"].strip()]
    if shot.get("camera"):
        parts.append(f"镜头运动：{shot['camera']}")
    if data.get("style"):
        parts.append(f"风格：{data['style']}")
    return "。".join(p.rstrip("。") for p in parts if p)


def cmd_clips(args, cfg):
    if args.takes < 1:
        raise MVError("--takes 必须大于零")
    project = _project(cfg, args.slug)
    data = project.load_shots()
    video = project.video()
    shots = data["shots"]
    if args.shots:
        targets = shotlib.pick_shots(data, args.shots)
    elif args.more:
        targets = list(shots)
    else:
        targets = [s for s in shots if not s["clip"].get("takes")]
    plans = []
    for shot in targets:
        index, _ = shotlib.find_shot(data, shot["id"])
        frame = project.path(shot["frame"].get("selected"))
        if not frame or not frame.is_file():
            raise MVError(f"{shot['id']} 还没有选定关键帧（frame-select）")
        if not shot.get("motion_prompt"):
            raise MVError(f"{shot['id']} 的 motion_prompt 为空")
        kind = shot.get("workflow", "i2v")
        if video.get("model") == "wan2.2-5b":
            if kind != "i2v":
                raise MVError(f"{shot['id']}: Wan5B 仅支持单图 i2v，不自动降级首尾帧镜头")
            kind = "wan5b-i2v"
        uploads = {"image": frame}
        if kind == "flf2v":
            nxt = shots[index + 1] if index + 1 < len(shots) else None
            end = project.path(nxt["frame"].get("selected")) if nxt else None
            if not end or not end.is_file():
                raise MVError(f"{shot['id']} 使用首尾帧，需要下一镜头先选定关键帧")
            uploads = {"start_image": frame, "end_image": end}
        plans.append((shot, kind, uploads))
    if not plans:
        print("没有需要生成的镜头（--shots 指定重做，--more 给所有镜头追加版本）")
        return
    validate_video(video)
    for shot, _, _ in plans:
        if shot["end"] - shot["start"] > shot_limit_sec(video) + 1e-6:
            raise MVError(f"{shot['id']} 超过单段上限，请先拆分镜头或调整 max_frames")
    specs = {}
    for _, kind, _ in plans:
        if kind in specs:
            continue
        spec, workflow, _ = comfy.load_kind(cfg, kind)
        problems = comfy.validate_kind(workflow, spec)
        if spec.get("video_model") != video["model"]:
            problems.append(f"工作流模型 {spec.get('video_model')} 与项目 {video['model']} 不一致")
        if problems:
            raise MVError(f"工作流 {kind} 校验失败:\n" + "\n".join(dict.fromkeys(problems)))
        if not ({"duration", "length"} & set(spec.get("params", {}))):
            raise MVError(f"工作流 {kind} 缺少 duration 或 length 参数映射")
        specs[kind] = spec
    print(f"将生成 {len(plans)} 个镜头 × {args.takes} 版 = {len(plans) * args.takes} 段视频", flush=True)
    if args.dry_run:
        for shot, kind, _ in plans:
            length = video_frames(shot["end"] - shot["start"], video)
            print(f"  {shot['id']}  {kind}  {length} 帧  × {args.takes} 版")
        return
    for shot, kind, uploads in plans:
        duration = shot["end"] - shot["start"]
        length = video_frames(duration, video)
        params = specs[kind]["params"]
        values = {"positive": _motion_prompt(data, shot), "width": video["width"],
                  "height": video["height"]}
        if "duration" in params:
            values["duration"] = length / video["fps"]
        else:
            values["length"] = length
        if "fps" in params:
            values["fps"] = video["fps"]
        if data.get("negative"):
            if "negative" in params:
                values["negative"] = data["negative"]
            else:
                values["positive"] += f"。画面约束，避免：{data['negative']}"
        for take_index in range(args.takes):
            takes = shot["clip"].setdefault("takes", [])
            number = max((int(t["id"].split("-")[1]) for t in takes), default=0) + 1
            seed = _take_seed(shot.get("seed"), take_index)
            values.update(seed=seed, filename_prefix=f"mv-creator/{args.slug}/{shot['id']}")
            print(f"{shot['id']} take-{number}：{kind}，{length} 帧，seed {seed}", flush=True)
            saved = comfy.run_kind(cfg, kind, values, uploads, f"mv-creator/{args.slug}",
                                   project.root / "clips" / shot["id"], f"take-{number}")
            takes.append({"id": f"take-{number}", "file": project.rel(saved[0]), "workflow": kind,
                          "seed": seed, "frames": length, "fps": video["fps"],
                          "model": video["model"], "duration_sec": length / video["fps"],
                          "prompt": values["positive"], "created": now_iso()})
            run_log = saved[0].parent / f"take-{number}.run.json"
            if run_log.is_file():
                takes[-1].update(run_log=project.rel(run_log), prompt_id=read_json(run_log).get("prompt_id"))
            project.save_shots(data)
            print(f"  已保存 {_abs(saved[0])}", flush=True)


def cmd_clip_select(args, cfg):
    project = _project(cfg, args.slug)
    data = project.load_shots()
    _, shot = shotlib.find_shot(data, args.shot)
    takes = shot["clip"].get("takes", [])
    if not any(t["id"] == args.take for t in takes):
        raise MVError(f"{shot['id']} 没有 {args.take}，可选: {', '.join(t['id'] for t in takes) or '无'}")
    shot["clip"]["selected"] = args.take
    project.save_shots(data)
    print(f"{shot['id']} 选定 {args.take}")


# Delivery ------------------------------------------------------------------

def cmd_package(args, cfg):
    project = _project(cfg, args.slug)
    result = media.package(project, cfg)
    print(f"剪映素材 → {_abs(result['dest'])}（{result['clips']}/{result['shots']} 个镜头有视频）")
    for item in result["missing"]:
        print(f"  [WARN] {item}")


def cmd_roughcut(args, cfg):
    project = _project(cfg, args.slug)
    for path in media.roughcut(project, cfg, args.burn_subs):
        print(f"粗剪 → {_abs(path)}")


# Optional voice production --------------------------------------------------

def _voice_plan(project):
    plan = voice.load_plan(project)
    if plan is None:
        raise MVError("尚无声音计划，先运行 voice-init，再按 references/voice-guide.md 填写")
    return plan


def cmd_voice_init(args, cfg):
    print(f"已创建声音计划: {_abs(voice.init_plan(_project(cfg, args.slug)))}（默认关闭）")


def cmd_voice_check(args, cfg):
    project = _project(cfg, args.slug)
    plan = _voice_plan(project)
    if args.bind:
        plan["binding"] = voice.binding(project)
    errors, warnings = voice.check(project, cfg, plan, args.ready)
    for message in warnings:
        print(f"[WARN] {message}")
    for message in errors:
        print(f"[FAIL] {message}")
    if errors:
        raise MVError(f"声音计划有 {len(errors)} 个问题")
    if args.bind:
        write_json(project.root / voice.PLAN, plan)
    print(f"声音计划校验通过，{'已启用' if plan['enabled'] else '未启用'}；{len(plan['cues'])} 句旁白")


def cmd_voice(args, cfg):
    project = _project(cfg, args.slug)
    plan = _voice_plan(project)
    if not args.speakers:
        errors, warnings = voice.check(project, cfg, plan)
        # Stale or overlong previous takes may be replaced explicitly.
        repairable = ("需要重做/重选配音", "超出窗口", "选定音频已被改写")
        blocking = [e for e in errors if not any(word in e for word in repairable)]
        if blocking:
            raise MVError("\n".join(blocking))
        for warning in warnings:
            print(f"[WARN] {warning}")
    voice.generate(project, cfg, plan, args.ids, speakers=args.speakers, takes=args.takes,
                   more=args.more, dry_run=args.dry_run, seed=args.seed)


def cmd_voice_select(args, cfg):
    project = _project(cfg, args.slug)
    voice.select(project, cfg, _voice_plan(project), args.id, args.take, args.speaker)


def cmd_mix_preview(args, cfg):
    for path in voice.mix(_project(cfg, args.slug), cfg):
        print(f"混音素材 → {_abs(path)}")


# Generic ComfyUI --------------------------------------------------------------

def cmd_comfy_inspect(args, cfg):
    print("\n".join(comfy.describe(comfy.load_api_workflow(Path(args.workflow)))))


def cmd_comfy_validate(args, cfg):
    object_info = None
    if not args.offline:
        object_info = comfy.ComfyClient.from_config(cfg).object_info()
    failed = []

    def report(level, text):
        if level == "FAIL" or (level == "WARN" and args.kinds):
            failed.append(text)
        print(f"[{level}] {text}")

    _check_workflows(cfg, object_info, report, tuple(args.kinds) or ("music", "i2v", "flf2v"))
    if failed:
        raise MVError("工作流校验未通过")


def _parse_pairs(pairs: list[str], what: str) -> dict:
    result = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise MVError(f"{what} 需要 <参数>=<值> 格式: {pair}")
        key, value = pair.split("=", 1)
        result[key] = value
    return result


def cmd_comfy_run(args, cfg):
    values = {}
    for key, raw in _parse_pairs(args.set, "--set").items():
        try:
            values[key] = json.loads(raw)
        except json.JSONDecodeError:
            values[key] = raw
    uploads = {k: Path(v) for k, v in _parse_pairs(args.upload, "--upload").items()}
    for key, path in uploads.items():
        if not path.is_file():
            raise MVError(f"--upload {key} 文件不存在: {path}")
    saved = comfy.run_kind(cfg, args.kind, values, uploads, args.subfolder, Path(args.out), args.name)
    for path in saved:
        print(f"已保存 {_abs(path)}")


# CLI -----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help=f"配置文件路径（默认向上查找 {CONFIG_NAME}）")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, func, help_text):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=func)
        return p

    p = add("init-config", cmd_init_config, "在当前目录创建配置文件")
    p.add_argument("--url", help="ComfyUI 地址，如 http://192.168.1.20:8188")
    p.add_argument("--force", action="store_true")
    add("doctor", cmd_doctor, "检查 Python 依赖、ffmpeg、Tardis、ComfyUI 与工作流")

    p = add("new", cmd_new, "新建 MV 项目")
    p.add_argument("title")
    p.add_argument("--slug", help="项目目录名（默认由作品名生成）")
    p.add_argument("--video-profile", choices=VIDEO_PROFILES, help="显式选择视频配置；默认沿用工作区")
    p = add("video-profile", cmd_video_profile, "切换项目视频配置，保留既有素材")
    p.add_argument("slug")
    p.add_argument("profile", choices=VIDEO_PROFILES)
    p.add_argument("--dry-run", action="store_true", help=DRY_RUN_HELP)
    p = add("status", cmd_status, "查看项目进度与下一步")
    p.add_argument("slug")

    p = add("music", cmd_music, "用 ComfyUI 音乐工作流生成歌曲")
    p.add_argument("slug")
    p.add_argument("--takes", type=int, default=1)
    p.add_argument("--duration", type=float, help="旧版生成上限秒数，兼容保留；新任务用 --max-duration")
    p.add_argument("--target-duration", type=float, help="目标片长，仅用于安排创作与记录")
    p.add_argument("--max-duration", type=float, help="生成上限；未设时目标时长加收尾余量")
    p.add_argument("--dry-run", action="store_true", help=DRY_RUN_HELP)
    p.add_argument("--seed", type=int, help="固定起始 seed，多版时依次加 1（默认每版随机）")
    p = add("music-check", cmd_music_check, "测量已生成歌曲时长并提示临近上限")
    p.add_argument("slug")
    p = add("music-select", cmd_music_select, "选定一版歌曲")
    p.add_argument("slug")
    p.add_argument("take")

    p = add("analyze", cmd_analyze, "节拍/小节/能量分析")
    p.add_argument("slug")
    p.add_argument("--beats-per-bar", type=int, default=4)
    p = add("shots-init", cmd_shots_init, "按小节生成分镜时间骨架")
    p.add_argument("slug")
    p.add_argument("--bars-per-shot", type=int, default=2)
    p.add_argument("--force", action="store_true")
    p = add("shots-check", cmd_shots_check, "校验分镜并生成 storyboard.md")
    p.add_argument("slug")
    p.add_argument("--draft", action="store_true", help="只检查时间结构，允许提示词为空")

    p = add("chars", cmd_chars, "用 Tardis 生成角色设定图候选")
    p.add_argument("slug")
    p.add_argument("--ids", help="逗号分隔的角色 id（默认只做还没有候选的角色）")
    p.add_argument("--n", type=int, default=1, help="每个角色生成张数（默认 1）")
    p.add_argument("--dry-run", action="store_true", help=DRY_RUN_HELP)
    p = add("char-select", cmd_char_select, "选定角色参考图")
    p.add_argument("slug")
    p.add_argument("char_id")
    p.add_argument("choice", help="候选序号，或图片路径")
    p = add("frames", cmd_frames, "用 Tardis 生成镜头关键帧候选")
    p.add_argument("slug")
    p.add_argument("--shots", help="逗号分隔的镜号（默认只做还没有候选的镜头）")
    p.add_argument("--n", type=int, default=1, help="每个镜头生成张数（默认 1）")
    p.add_argument("--dry-run", action="store_true", help=DRY_RUN_HELP)
    p = add("frame-select", cmd_frame_select, "选定关键帧并裁切到视频尺寸")
    p.add_argument("slug")
    p.add_argument("shot")
    p.add_argument("choice", nargs="?", help="候选序号，或图片路径；省略时按当前 crop 重裁上次选定的原图")

    p = add("clips", cmd_clips, "用 ComfyUI 图生视频工作流生成镜头片段")
    p.add_argument("slug")
    p.add_argument("--shots", help="逗号分隔的镜号（指定后总会新增版本）")
    p.add_argument("--takes", type=int, default=1, help="每个镜头生成版数（默认 1）")
    p.add_argument("--more", action="store_true", help="给所有镜头追加版本")
    p.add_argument("--dry-run", action="store_true", help=DRY_RUN_HELP)
    p = add("clip-select", cmd_clip_select, "选定镜头视频版本")
    p.add_argument("slug")
    p.add_argument("shot")
    p.add_argument("take")

    p = add("package", cmd_package, "整理剪映素材包")
    p.add_argument("slug")
    p = add("roughcut", cmd_roughcut, "用 ffmpeg 按分镜拼出粗剪参考")
    p.add_argument("slug")
    p.add_argument("--burn-subs", action="store_true", help="另出一版烧录歌词字幕")

    p = add("voice-init", cmd_voice_init, "创建可选的旁白声音计划（默认关闭）")
    p.add_argument("slug")
    p = add("voice-check", cmd_voice_check, "检查旁白台词、音色参考与时间窗口")
    p.add_argument("slug")
    p.add_argument("--ready", action="store_true", help="要求全部配音已选定且可混音")
    p.add_argument("--bind", action="store_true", help="复核时间后绑定当前歌曲及分镜，不自动移动旁白")
    p = add("voice", cmd_voice, "生成音色试镜或逐句配音")
    p.add_argument("slug")
    p.add_argument("--speakers", action="store_true", help="音色试镜，使用说话人的 sample_text")
    p.add_argument("--ids", help="逗号分隔的说话人或台词 id；指定后追加版本")
    p.add_argument("--takes", type=int, default=2)
    p.add_argument("--more", action="store_true", help="全部追加版本")
    p.add_argument("--seed", type=int, help="正整数 seed；多个候选依次递增")
    p.add_argument("--dry-run", action="store_true", help=DRY_RUN_HELP)
    p = add("voice-select", cmd_voice_select, "选定旁白或音色样音")
    p.add_argument("slug")
    p.add_argument("id")
    p.add_argument("take")
    p.add_argument("--speaker", action="store_true", help="选定音色样音，并设为固定参考声音")
    p = add("mix-preview", cmd_mix_preview, "混合歌曲与旁白，另附歌曲版及独立旁白轨")
    p.add_argument("slug")

    p = add("comfy-inspect", cmd_comfy_inspect, "列出 API 工作流中的节点、标题与参数")
    p.add_argument("workflow", help="API 格式工作流 JSON 路径")
    p = add("comfy-validate", cmd_comfy_validate, "校验工作流参数映射与 ComfyUI 节点")
    p.add_argument("kinds", nargs="*", help="工作流类型，默认 music i2v flf2v")
    p.add_argument("--offline", action="store_true", help="不连接 ComfyUI，只检查映射")
    p = add("comfy-run", cmd_comfy_run, "运行任意已映射的工作流")
    p.add_argument("kind")
    p.add_argument("--set", action="append", help="<参数>=<值>，值可写 JSON")
    p.add_argument("--upload", action="append", help="<参数>=<本地文件>")
    p.add_argument("--out", default=".", help="输出目录")
    p.add_argument("--name", default="output", help="输出文件名（不含扩展名）")
    p.add_argument("--subfolder", default="mv-creator", help="ComfyUI input 下的上传子目录")
    return parser


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args()
    try:
        cfg = load_config(args.config)
        args.func(args, cfg)
    except MVError as exc:
        sys.stdout.flush()
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        sys.stdout.flush()
        print("已中断；已完成的部分已保存，重跑同一命令可继续。", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
