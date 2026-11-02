"""Song duration policy and checks; a time limit is not proof of a complete ending."""

from __future__ import annotations

import math
from pathlib import Path

from .common import MVError
from .voice import probe


def _seconds(value, name: str, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise MVError(f"{name} 必须为有限秒数")
    if value < 0 or (not allow_zero and value == 0):
        raise MVError(f"{name} 必须{'非负' if allow_zero else '大于零'}")
    return float(value)


def settings(args, stored: dict, config: dict) -> tuple[float, float]:
    target_arg = getattr(args, "target_duration", None)
    legacy = getattr(args, "duration", None)
    target = _seconds(target_arg if target_arg is not None else
                      legacy if legacy is not None else
                      stored.get("target_duration_sec", stored.get("duration_sec", config["duration_sec"])),
                      "目标时长")
    explicit = getattr(args, "max_duration", None)
    if explicit is not None and legacy is not None:
        raise MVError("--duration 是旧版上限参数，不能和 --max-duration 同时使用")
    limit = explicit if explicit is not None else legacy
    if limit is None and target_arg is None:
        limit = stored.get("generation_max_duration_sec", config.get("generation_max_duration_sec"))
    if limit is None:
        limit = target + _seconds(config.get("ending_buffer_sec", 30), "收尾余量", allow_zero=True)
    limit = _seconds(limit, "生成上限")
    # Legacy --duration also supplies the inferred target, as in old projects.
    if limit < target:
        raise MVError("生成上限不能小于目标时长；缩短作品请同时设置 --target-duration")
    return target, limit


def inspect(path: Path, cfg: dict, limit: float | None = None) -> dict:
    if not path.is_file():
        raise MVError(f"音频文件不存在: {path}")
    result = probe(path, cfg)
    actual = result["duration_sec"]
    result["near_limit"] = bool(limit is not None and actual >= limit - max(0.25, limit * 0.01))
    result["ending_review"] = "pending_listen"
    return result


def require_full_song(project, cfg: dict, timeline_end: float) -> float | None:
    meta = project.load().get("music", {})
    path = project.path(meta.get("file"))
    if not path or not path.is_file():
        return None
    actual = inspect(path, cfg)["duration_sec"]
    if actual > timeline_end + 0.05:
        raise MVError(f"歌曲实长 {actual:.3f}s，分镜只到 {timeline_end:.3f}s；导出会截断歌曲。"
                      "请按实际音频补齐分镜；如需短版，请另存经试听确认的剪辑音频并选定。")
    return actual
