"""CapCut (剪映) hand-off package and ffmpeg rough cut."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .common import MVError, Project, ffmpeg_bin, fmt_time, now_iso, read_json, write_json
from .shots import to_srt


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

    (dest / "剪辑清单.md").write_text(_edit_list(meta, data, rows, missing, song), encoding="utf-8")
    write_json(dest / "package.json", {"created": now_iso(), "shots": len(shots), "missing": missing})
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
        clip_sec = (take["frames"] - 1) / take["fps"] if take and take.get("frames") else None
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

    if burn_subs:
        (work / "lyrics.srt").write_text(to_srt(data["shots"]), encoding="utf-8")
        font = rc.get("font") or "Microsoft YaHei"
        subbed = project.root / "final" / "roughcut_subs.mp4"
        # Relative subtitle path avoids escaping the drive colon in the filter.
        _run([ffmpeg, "-y", "-v", "error", "-i", str(out), "-vf",
              f"subtitles=lyrics.srt:force_style='FontName={font},FontSize=14,Outline=1,MarginV=40'",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p",
              "-c:a", "copy", str(subbed)], cwd=work)
        outputs.append(subbed)

    shutil.rmtree(work)
    if stills:
        print(f"  以下镜头没有选定视频，用关键帧静帧或黑场代替: {', '.join(stills)}")
    return outputs


def _even(value: float) -> int:
    return max(2, int(round(value / 2)) * 2)
