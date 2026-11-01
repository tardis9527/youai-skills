"""Config, project paths and JSON state shared by every command."""

from __future__ import annotations

import copy
import json
import math
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
CONFIG_NAME = "mv-creator.config.json"

DEFAULT_CONFIG: dict = {
    "comfyui": {"url": "http://127.0.0.1:8188", "timeout_sec": 3600, "poll_interval_sec": 2},
    "workflows_dir": "workflows",
    "projects_dir": "projects",
    "video": {"width": 720, "height": 1280, "fps": 16, "max_frames": 81, "clip_slack_sec": 0.5},
    "image": {"model": "gpt-image-2", "size": "1024x1536", "quality": None},
    "tardis": {"script": None},
    "music": {"duration_sec": 60},
    "roughcut": {"fps": 30, "scale": 1.5, "crf": 20, "font": "Microsoft YaHei"},
    "ffmpeg": None,
}


class MVError(Exception):
    """An expected failure with a message meant for the user."""


def deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def read_json(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise MVError(f"文件不存在: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MVError(f"JSON 格式错误: {path} (第 {exc.lineno} 行: {exc.msg})") from exc


def write_json(path: Path, data: dict) -> None:
    """Write atomically so an interrupted run never leaves half a state file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def find_config(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        candidate = folder / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def load_config(path: Path | None = None) -> dict:
    """Load the workspace config; fall back to defaults rooted at the cwd."""
    path = Path(path) if path else find_config()
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if path:
        cfg = deep_merge(cfg, read_json(path))
        cfg["_path"] = str(path.resolve())
        cfg["_root"] = str(path.resolve().parent)
    else:
        cfg["_path"] = None
        cfg["_root"] = str(Path.cwd().resolve())
    return cfg


def root_dir(cfg: dict) -> Path:
    return Path(cfg["_root"])


def resolve_path(cfg: dict, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(os.path.expandvars(os.path.expanduser(value)))
    return path if path.is_absolute() else root_dir(cfg) / path


def workflows_dir(cfg: dict) -> Path:
    return resolve_path(cfg, cfg.get("workflows_dir")) or SKILL_DIR / "workflows"


def ffmpeg_bin(cfg: dict, name: str = "ffmpeg") -> str | None:
    configured = resolve_path(cfg, cfg.get("ffmpeg"))
    if configured:
        # Allow either the ffmpeg executable or the folder that holds it.
        folder = configured if configured.is_dir() else configured.parent
        for candidate in (folder / f"{name}.exe", folder / name):
            if candidate.is_file():
                return str(candidate)
    return shutil.which(name)


_INVALID = re.compile(r'[\\/:*?"<>|\s]+')


def slugify(name: str) -> str:
    slug = _INVALID.sub("-", name.strip()).strip("-.")
    if not slug:
        raise MVError("作品名不能为空")
    return slug[:60]


def clip_frames(duration: float, fps: int, max_frames: int) -> int:
    """Wan-style frame counts are 4n+1; round up so the clip covers the shot."""
    needed = math.ceil(duration * fps) + 1
    frames = 4 * math.ceil((needed - 1) / 4) + 1
    return max(5, min(frames, max_frames))


def max_clip_sec(video: dict) -> float:
    return (video["max_frames"] - 1) / video["fps"]


def shot_limit_sec(video: dict) -> float:
    """Longest shot allowed: one clip plus a short tail frozen or slowed in editing."""
    return max_clip_sec(video) + video.get("clip_slack_sec", 0.5)


def fmt_time(seconds: float) -> str:
    minutes, sec = divmod(max(0.0, seconds), 60)
    return f"{int(minutes):02d}:{sec:05.2f}"


class Project:
    """A single MV under <projects_dir>/<slug>/."""

    def __init__(self, cfg: dict, slug: str):
        self.cfg = cfg
        self.slug = slug
        base = resolve_path(cfg, cfg.get("projects_dir")) or root_dir(cfg) / "projects"
        self.root = base / slug

    # Paths -----------------------------------------------------------------
    @property
    def project_file(self) -> Path:
        return self.root / "project.json"

    @property
    def shots_file(self) -> Path:
        return self.root / "storyboard" / "shots.json"

    @property
    def beats_file(self) -> Path:
        return self.root / "analysis" / "beats.json"

    def path(self, rel: str | None) -> Path | None:
        return self.root / rel if rel else None

    def rel(self, path: Path) -> str:
        return Path(path).resolve().relative_to(self.root.resolve()).as_posix()

    # State -----------------------------------------------------------------
    def exists(self) -> bool:
        return self.project_file.is_file()

    def require(self) -> "Project":
        if not self.exists():
            raise MVError(f"项目不存在: {self.root}（先运行 new 创建）")
        return self

    def load(self) -> dict:
        return read_json(self.project_file)

    def save(self, data: dict) -> None:
        data["updated"] = now_iso()
        write_json(self.project_file, data)

    def has_shots(self) -> bool:
        return self.shots_file.is_file()

    def load_shots(self) -> dict:
        if not self.has_shots():
            raise MVError(f"还没有分镜文件: {self.shots_file}（先运行 shots-init）")
        return read_json(self.shots_file)

    def save_shots(self, data: dict) -> None:
        write_json(self.shots_file, data)

    def video(self) -> dict:
        """Video settings frozen into the project at creation time."""
        return deep_merge(self.cfg["video"], self.load().get("video", {}))


def pick_candidate(project: Project, candidates: list[str], choice: str) -> Path:
    """Resolve a 1-based candidate index, or any image path the user supplies."""
    if choice.isdigit():
        index = int(choice)
        if not 1 <= index <= len(candidates):
            raise MVError(f"候选序号 {index} 超出范围（共 {len(candidates)} 个）")
        return project.path(candidates[index - 1])
    path = Path(choice)
    if not path.is_absolute():
        in_project = project.root / choice
        path = in_project if in_project.exists() else Path.cwd() / choice
    if not path.is_file():
        raise MVError(f"找不到图片: {path}")
    return path


def next_index(folder: Path, stem: str) -> int:
    """Next free N for files named <stem>-vNN*.* so reruns never overwrite."""
    pattern = re.compile(rf"^{re.escape(stem)}-v(\d+)")
    used = [int(m.group(1)) for p in folder.glob(f"{stem}-v*") if (m := pattern.match(p.name))]
    return max(used, default=0) + 1
