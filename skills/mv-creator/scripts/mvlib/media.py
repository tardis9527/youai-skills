"""CapCut (剪映) hand-off package and ffmpeg rough cut."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .common import MVError, Project, ffmpeg_bin, fmt_time, now_iso, read_json, write_json
from .shots import to_srt
from . import voice


def _selected_take(shot: dict) -> dict | None:
    selected = shot["clip"].get("selected")
    return next((t for t in shot["clip"].get("takes", []) if t["id"] == selected), None)


def _clip_file(project: Project, shot: dict) -> Path | None:
    take = _selected_take(shot)
    path = project.path(take["file"]) if take else None
    return path if path and path.is_file() else None


def _frame_file(project: Project, shot: dict) -> Path | None:
    path = project.path(shot["frame"].get("selected"))
    return path if path and path.is_file() else None


def _song_file(project: Project) -> Path | None:
    path = project.path(project.load().get("music", {}).get("file"))
    return path if path and path.is_file() else None


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-15:])
        raise MVError(f"ffmpeg 失败:\n{tail}")


def package(project: Project, cfg: dict) -> dict:
    meta = project.load()
    data = project.load_shots()
    shots = data["shots"]
    plan = voice.load_plan(project)
    voice_outputs = voice.mix(project, cfg) if plan and plan["enabled"] else []
    dest = project.root / "final" / "capcut"
    folders = {key: dest / name for key, name in (
        ("audio", "01_音乐"), ("clips", "02_视频片段"), ("frames", "03_关键帧"),
        ("subs", "04_字幕"), ("beats", "05_节拍"))}
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    ffmpeg = ffmpeg_bin(cfg)
    song = _song_file(project)
    if song:
        shutil.copy2(song, folders["audio"] / f"{project.slug}{song.suffix}")
        if ffmpeg and song.suffix.lower() not in (".wav", ".mp3"):
            _run([ffmpeg, "-y", "-v", "error", "-i", str(song), "-ar", "48000",
                  "-c:a", "pcm_s16le", str(folders["audio"] / f"{project.slug}.wav")])

    rows, missing = [], []
    for order, shot in enumerate(shots, start=1):
        stem = f"{order:02d}_{shot['id']}_{shot['start']:06.2f}-{shot['end']:06.2f}"
        clip, frame = _clip_file(project, shot), _frame_file(project, shot)
        clip_name = f"{stem}{clip.suffix}" if clip else ""
        if clip:
            shutil.copy2(clip, folders["clips"] / clip_name)
        else:
            missing.append(f"{shot['id']} 没有选定视频片段")
        if frame:
            shutil.copy2(frame, folders["frames"] / f"{order:02d}_{shot['id']}.png")
        take = _selected_take(shot)
        rows.append((order, shot, clip_name, take))

    (folders["subs"] / "lyrics.srt").write_text(to_srt(shots), encoding="utf-8-sig")
    if project.beats_file.is_file():
        beats = read_json(project.beats_file)
        lines = [f"BPM ≈ {beats['tempo']}（小节线为估算）", ""]
        lines += [f"小节 {b['index']:>3}\t{fmt_time(b['start'])}\t能量 {'#' * round(b['energy'] * 20)}"
                  for b in beats["bars"]]
        (folders["beats"] / "小节线.txt").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    voice_text = ""
    audio_fingerprint = None
    if voice_outputs:
        voices_folder = dest / "06_旁白"
        mix_folder = dest / "07_混音参考"
        voices_folder.mkdir(exist_ok=True)
        mix_folder.mkdir(exist_ok=True)
        cues = voice.resolved(project, cfg, plan)
        timeline_rows = []
        for cue in cues:
            name = f"{cue['id']}_{cue['start']:06.2f}_{cue['speaker']}{cue['file'].suffix}"
            shutil.copy2(cue["file"], voices_folder / name)
            timeline_rows.append({"id": cue["id"], "speaker": cue["speaker"], "file": f"06_旁白/{name}",
                                  "start": cue["start"], "end": cue["start"] + cue["duration_sec"],
                                  "text": cue["text"], "gain_db": cue.get("gain_db", 0),
                                  "duck_db": cue.get("duck_db", cfg.get("voice", {}).get("duck_db", -6)),
                                  "subtitle": cue.get("subtitle", True)})
        voice_text = ("\n## 旁白与混音\n\n旁白放在独立音轨，按声音时间表对齐；原片音轨静音。"
                      "07_混音参考 中的歌曲版、旁白轨和混音用于对比，不要将混音与原歌曲重复叠加。"
                      "旁白字幕放上方，歌词放下方；重叠位置需人工试听和校对。\n\n")
        settings = voice.mix_settings(cfg)
        voice_text += (f"手工还原混音：歌曲基础增益 {settings['music_gain_db']:g}dB，旁白基础增益 "
                       f"{settings['voice_gain_db']:g}dB；每句再叠加时间表 gain_db，歌曲在该句期间按 duck_db 额外降低，"
                       f"{settings['attack_sec']:g} 秒进入、{settings['release_sec']:g} 秒恢复。\n\n"
                       "| 台词 | 说话人 | 起点 | 终点 | 文件 | 文本 |\n| --- | --- | --- | --- | --- | --- |\n")
        for cue in timeline_rows:
            text = cue["text"].replace("|", "/").replace("\n", " ")
            voice_text += (f"| {cue['id']} | {cue['speaker']} | {cue['start']:.3f} | {cue['end']:.3f} "
                           f"| {cue['file']} | {text} |\n")
        write_json(voices_folder / "声音时间表.json", {"settings": settings, "cues": timeline_rows})
        (voices_folder / "声音时间表.md").write_text(voice_text, encoding="utf-8")
        for path in voice_outputs:
            shutil.copy2(path, (folders["subs"] if path.suffix == ".srt" else mix_folder) / path.name)
        manifest = project.root / "final" / "audio" / "mix-manifest.json"
        shutil.copy2(manifest, mix_folder / manifest.name)
        audio_fingerprint = read_json(manifest)["fingerprint"]
    (dest / "剪辑清单.md").write_text(_edit_list(meta, data, rows, missing, song) + voice_text, encoding="utf-8")
    write_json(dest / "package.json", {"created": now_iso(), "shots": len(shots), "missing": missing,
                                      "audio_fingerprint": audio_fingerprint})
    return {"dest": dest, "shots": len(shots), "clips": len(shots) - len(missing), "missing": missing}


def _edit_list(meta: dict, data: dict, rows: list, missing: list[str], song: Path | None) -> str:
    lines = [f"# {meta['title']} · 剪辑清单", "",
             f"- 歌曲：{('01_音乐/' + meta['slug'] + song.suffix) if song else '未选定'}",
             f"- 镜头数：{len(rows)}；视频片段按时间线顺序编号，文件名含时间线入点-出点（秒）",
             f"- 生成时间：{now_iso()}", ""]
    if missing:
        lines += ["## 未完成", ""] + [f"- {m}" for m in missing] + [""]
    lines += ["## 时间线", "",
              "| 顺序 | 镜号 | 时间线 | 镜头时长 | 片段时长 | 文件 | 段落 | 歌词 | 转场 | 备注 |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for order, shot, clip_name, take in rows:
        span = shot["end"] - shot["start"]
        clip_sec = take.get("duration_sec") if take else None
        if clip_sec is None and take and take.get("frames"):
            offset = 0 if take.get("model") == "minimax-h3" else 1
            clip_sec = (take["frames"] - offset) / take["fps"]
        clip_len = f"{clip_sec:.2f}s" if clip_sec else "—"
        transition = "首尾帧过渡" if shot.get("workflow") == "flf2v" else "硬切"
        notes = [str(shot.get("notes", "")).replace("|", "/")]
        if clip_sec and clip_sec < span - 0.01:
            notes.append(f"片段短 {span - clip_sec:.2f}s，可放慢到 {clip_sec / span * 100:.0f}%")
        lines.append(f"| {order} | {shot['id']} | {fmt_time(shot['start'])}–{fmt_time(shot['end'])} "
                     f"| {span:.2f}s | {clip_len} | {clip_name or '缺'} | {shot.get('section', '')} "
                     f"| {str(shot.get('lyric', '')).replace('|', '/')} | {transition} "
                     f"| {'；'.join(n for n in notes if n)} |")
    lines += ["", "片段时长通常略长于镜头时长：在剪映里按「时间线」列的入点对齐，裁掉片段尾部多出的部分。", ""]
    return "\n".join(lines)


def roughcut(project: Project, cfg: dict, burn_subs: bool) -> list[Path]:
    ffmpeg = ffmpeg_bin(cfg)
    if not ffmpeg:
        raise MVError("没有找到 ffmpeg，按 references/setup.md 安装，或在配置中写明 ffmpeg 路径")
    data = project.load_shots()
    plan = voice.load_plan(project)
    voice_outputs = voice.mix(project, cfg) if plan and plan["enabled"] else []
    video = project.video()
    rc = cfg["roughcut"]
    width = _even(video["width"] * rc.get("scale", 1))
    height = _even(video["height"] * rc.get("scale", 1))
    fps, crf = int(rc.get("fps", 30)), str(rc.get("crf", 20))
    work = project.root / "final" / "_roughcut_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    base_vf = (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
               f"crop={width}:{height},fps={fps},setsar=1")
    encode = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p",
              "-r", str(fps), "-video_track_timescale", "90000"]
    segments, cursor, stills = [], 0.0, []

    def black(duration: float) -> None:
        seg = work / f"seg_{len(segments) + 1:03d}.mp4"
        _run([ffmpeg, "-y", "-v", "error", "-f", "lavfi", "-i",
              f"color=c=black:s={width}x{height}:r={fps}", "-t", f"{duration:.3f}",
              "-vf", "setsar=1", *encode, str(seg)])
        segments.append(seg)

    for shot in data["shots"]:
        if shot["start"] > cursor + 0.02:
            black(shot["start"] - cursor)
        duration = shot["end"] - max(shot["start"], cursor)
        if duration <= 0:
            continue
        seg = work / f"seg_{len(segments) + 1:03d}.mp4"
        clip, frame = _clip_file(project, shot), _frame_file(project, shot)
        if clip:
            _run([ffmpeg, "-y", "-v", "error", "-i", str(clip), "-vf",
                  f"{base_vf},tpad=stop_mode=clone:stop_duration={duration:.3f}",
                  "-t", f"{duration:.3f}", *encode, str(seg)])
            segments.append(seg)
        elif frame:
            _run([ffmpeg, "-y", "-v", "error", "-loop", "1", "-i", str(frame), "-vf", base_vf,
                  "-t", f"{duration:.3f}", *encode, str(seg)])
            segments.append(seg)
            stills.append(shot["id"])
        else:
            black(duration)
            stills.append(shot["id"])
        cursor = shot["end"]

    (work / "list.txt").write_text("".join(f"file '{s.name}'\n" for s in segments), encoding="utf-8")
    out = project.root / "final" / "roughcut.mp4"
    cmd = [ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "list.txt"]
    song = _song_file(project)
    if song:
        cmd += ["-i", str(song), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "copy", "-t", f"{cursor:.3f}", "-movflags", "+faststart", str(out)]
    _run(cmd, cwd=work)
    outputs = [out]

    lyrics_text = to_srt(data["shots"])
    if burn_subs and lyrics_text.strip():
        (work / "lyrics.srt").write_text(lyrics_text, encoding="utf-8")
        font = rc.get("font") or "Microsoft YaHei"
        subbed = project.root / "final" / "roughcut_subs.mp4"
        # Relative subtitle path avoids escaping the drive colon in the filter.
        _run([ffmpeg, "-y", "-v", "error", "-i", str(out), "-vf",
              f"subtitles=lyrics.srt:force_style='FontName={font},FontSize=14,Outline=1,MarginV=40'",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p",
              "-c:a", "copy", str(subbed)], cwd=work)
        outputs.append(subbed)

    audio_fingerprint = None
    if voice_outputs:
        narrated = project.root / "final" / "roughcut_voice.mp4"
        _run([ffmpeg, "-y", "-v", "error", "-i", str(out), "-i", str(voice_outputs[2]),
              "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
              "-t", f"{cursor:.3f}", "-movflags", "+faststart", str(narrated)])
        outputs.append(narrated)
        audio_fingerprint = read_json(project.root / "final/audio/mix-manifest.json")["fingerprint"]
        voice_text = voice_outputs[3].read_text(encoding="utf-8-sig")
        if burn_subs and (lyrics_text.strip() or voice_text.strip()):
            shutil.copy2(voice_outputs[3], work / "voice.srt")
            font = rc.get("font") or "Microsoft YaHei"
            caption_filters = []
            if lyrics_text.strip():
                caption_filters.append(f"subtitles=lyrics.srt:force_style='FontName={font},FontSize=14,Outline=1,MarginV=40'")
            if voice_text.strip():
                caption_filters.append(f"subtitles=voice.srt:force_style='FontName={font},FontSize=14,Outline=1,Alignment=8,MarginV=40'")
            captions = ",".join(caption_filters)
            narrated_subs = project.root / "final" / "roughcut_voice_subs.mp4"
            _run([ffmpeg, "-y", "-v", "error", "-i", str(narrated), "-vf", captions,
                  "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p",
                  "-c:a", "copy", str(narrated_subs)], cwd=work)
            outputs.append(narrated_subs)
    write_json(project.root / "final" / "roughcut-manifest.json", {"created": now_iso(),
               "audio_fingerprint": audio_fingerprint, "files": [project.rel(p) for p in outputs]})

    shutil.rmtree(work)
    if stills:
        print(f"  以下镜头没有选定视频，用关键帧静帧或黑场代替: {', '.join(stills)}")
    return outputs


def _even(value: float) -> int:
    return max(2, int(round(value / 2)) * 2)
