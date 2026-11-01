"""Storyboard skeleton, validation, Markdown rendering and SRT export."""

from __future__ import annotations

import re

from .common import MVError, fmt_time, max_clip_sec, shot_limit_sec

WORKFLOWS = ("i2v", "flf2v")
CROPS = ("center", "top", "bottom", "left", "right")
ID_PATTERN = re.compile(r"^S\d{2,3}[a-z]?$")


def new_shot(index: int, start: float, end: float, bars: str) -> dict:
    return {
        "id": f"S{index:02d}",
        "start": round(start, 3),
        "end": round(end, 3),
        "bars": bars,
        "section": "",
        "lyric": "",
        "scene": "",
        "characters": [],
        "image_prompt": "",
        "motion_prompt": "",
        "camera": "",
        "workflow": "i2v",
        "crop": "center",
        "seed": None,
        "notes": "",
        "frame": {"candidates": [], "selected": None, "source": None},
        "clip": {"takes": [], "selected": None},
    }


def skeleton(analysis: dict, video: dict, bars_per_shot: int) -> dict:
    """Group bars into shots no longer than one generated clip (plus slack)."""
    limit = shot_limit_sec(video)
    duration = analysis["duration"]
    bars = analysis["bars"]
    cuts = [0.0]
    labels = []
    index = 0
    # Lead-in before the first detected downbeat becomes its own shot(s), or
    # joins the first one when it is short.
    lead = bars[0]["start"] if bars else 0.0
    if lead >= 1.0:
        while lead - cuts[-1] > limit:
            cuts.append(round(cuts[-1] + limit, 3))
            labels.append("前奏")
        cuts.append(lead)
        labels.append("前奏")
    while index < len(bars):
        take = bars_per_shot
        while take > 1 and bars[min(index + take, len(bars)) - 1]["end"] - cuts[-1] > limit:
            take -= 1
        last = min(index + take, len(bars)) - 1
        end = bars[last]["end"]
        # A single bar longer than a clip is split at the clip limit.
        while end - cuts[-1] > limit:
            cuts.append(round(cuts[-1] + limit, 3))
            labels.append(f"{bars[index]['index']}（拆分）")
        cuts.append(end)
        labels.append(f"{bars[index]['index']}" if last == index
                      else f"{bars[index]['index']}-{bars[last]['index']}")
        index = last + 1
    cuts[-1] = duration
    # Fold a tiny trailing shot into the previous one when it still fits.
    if len(cuts) > 2 and cuts[-1] - cuts[-2] < 1.0 and cuts[-1] - cuts[-3] <= limit:
        del cuts[-2]
        labels[-2] = f"{labels[-2]}+尾"
        del labels[-1]
    shots = [new_shot(i + 1, cuts[i], cuts[i + 1], labels[i]) for i in range(len(cuts) - 1)]
    return {
        "version": 1,
        "style": "",
        "negative": "",
        "characters": [],
        "shots": shots,
    }


def new_character(char_id: str) -> dict:
    return {"id": char_id, "name": "", "description": "", "prompt": "",
            "candidates": [], "ref": None}


def check(data: dict, video: dict, song_duration: float | None, draft: bool) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    clip_sec, limit = max_clip_sec(video), shot_limit_sec(video)
    shots = data.get("shots") or []
    if not shots:
        return ["shots 为空"], warnings
    char_ids = [c.get("id") for c in data.get("characters", [])]
    if len(set(char_ids)) != len(char_ids):
        errors.append("characters 中有重复的 id")
    for char in data.get("characters", []):
        if not char.get("prompt") and not draft:
            errors.append(f"角色 {char.get('id')}: prompt 为空")
    seen = set()
    previous_end = 0.0
    for position, shot in enumerate(shots):
        sid = shot.get("id", f"#{position + 1}")
        if not ID_PATTERN.match(str(sid)):
            errors.append(f"{sid}: 镜号需形如 S01 / S01a")
        if sid in seen:
            errors.append(f"{sid}: 镜号重复")
        seen.add(sid)
        start, end = shot.get("start"), shot.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            errors.append(f"{sid}: start/end 无效")
            continue
        if abs(start - previous_end) > 0.05:
            kind = "重叠" if start < previous_end else "空档"
            warnings.append(f"{sid}: 与上一镜头之间有 {abs(start - previous_end):.2f}s {kind}")
        previous_end = end
        if end - start > limit + 0.01:
            errors.append(f"{sid}: 时长 {end - start:.2f}s 超过单段上限 {limit:.2f}s，请拆分镜头")
        elif end - start > clip_sec + 0.01:
            warnings.append(f"{sid}: 片段最长 {clip_sec:.2f}s，比镜头短 {end - start - clip_sec:.2f}s；"
                            f"粗剪定格末帧，剪映中可放慢到 {clip_sec / (end - start) * 100:.0f}%")
        if shot.get("workflow", "i2v") not in WORKFLOWS:
            errors.append(f"{sid}: workflow 只能是 {'/'.join(WORKFLOWS)}")
        if shot.get("workflow") == "flf2v" and position == len(shots) - 1:
            errors.append(f"{sid}: 最后一个镜头没有下一镜头可作尾帧，不能用 flf2v")
        if shot.get("crop", "center") not in CROPS:
            errors.append(f"{sid}: crop 只能是 {'/'.join(CROPS)}")
        for char in shot.get("characters", []):
            if char not in char_ids:
                errors.append(f"{sid}: 引用了未定义的角色 {char}")
        if not draft:
            for field in ("scene", "image_prompt", "motion_prompt"):
                if not str(shot.get(field, "")).strip():
                    errors.append(f"{sid}: {field} 为空")
    if song_duration and abs(previous_end - song_duration) > 0.5:
        warnings.append(f"分镜总长 {previous_end:.2f}s 与歌曲时长 {song_duration:.2f}s 不一致")
    return errors, warnings


def render_markdown(title: str, data: dict) -> str:
    lines = [f"# {title} · 分镜表", ""]
    if data.get("style"):
        lines += [f"**视觉风格**：{data['style']}", ""]
    if data.get("characters"):
        lines += ["## 角色", "", "| id | 名称 | 描述 | 参考图 |", "| --- | --- | --- | --- |"]
        for c in data["characters"]:
            lines.append(f"| {c['id']} | {_cell(c.get('name'))} | {_cell(c.get('description'))} "
                         f"| {c.get('ref') or '未选'} |")
        lines.append("")
    lines += ["## 镜头", "",
              "| 镜号 | 时间 | 时长 | 段落 | 歌词 | 画面 | 角色 | 镜头/动作 | 关键帧 | 视频 |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in data.get("shots", []):
        motion = " / ".join(x for x in (s.get("camera"), s.get("motion_prompt")) if x)
        lines.append(
            f"| {s['id']} | {fmt_time(s['start'])}–{fmt_time(s['end'])} | {s['end'] - s['start']:.1f}s "
            f"| {_cell(s.get('section'))} | {_cell(s.get('lyric'))} | {_cell(s.get('scene'))} "
            f"| {', '.join(s.get('characters', []))} | {_cell(motion)} "
            f"| {'✓' if s['frame'].get('selected') else '—'} | {s['clip'].get('selected') or '—'} |")
    return "\n".join(lines) + "\n"


def _cell(text) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def to_srt(shots: list[dict]) -> str:
    blocks = []
    for shot in shots:
        lyric = str(shot.get("lyric") or "").strip()
        if not lyric:
            continue
        text = "\n".join(part.strip() for part in lyric.split("/") if part.strip())
        blocks.append(f"{len(blocks) + 1}\n{_srt_time(shot['start'])} --> {_srt_time(shot['end'])}\n{text}\n")
    return "\n".join(blocks)


def _srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def find_shot(data: dict, sid: str) -> tuple[int, dict]:
    for index, shot in enumerate(data["shots"]):
        if shot["id"] == sid:
            return index, shot
    raise MVError(f"没有镜头 {sid}")


def pick_shots(data: dict, ids: str | None) -> list[dict]:
    if not ids:
        return data["shots"]
    wanted = [i.strip() for i in ids.split(",") if i.strip()]
    return [find_shot(data, sid)[1] for sid in wanted]
