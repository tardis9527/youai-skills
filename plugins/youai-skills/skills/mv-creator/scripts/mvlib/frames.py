"""Image generation through the imagegen-tardis skill, and frame normalisation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .common import MVError, SKILL_DIR, resolve_path

TARDIS_CREDENTIALS = Path.home() / ".tardis-skill" / "imagegen-tardis" / "credentials.json"


def tardis_candidates() -> list[Path]:
    home = Path.home()
    bases = [SKILL_DIR.parent, home / ".codex" / "skills", home / ".agents" / "skills",
             home / ".claude" / "skills", home / ".cc-switch" / "skills"]
    return [base / "imagegen-tardis" / "scripts" / "image_gen.py" for base in bases]


def locate_tardis(cfg: dict) -> Path:
    configured = resolve_path(cfg, (cfg.get("tardis") or {}).get("script"))
    if configured:
        if configured.is_file():
            return configured
        raise MVError(f"配置的 tardis.script 不存在: {configured}")
    for candidate in tardis_candidates():
        if candidate.is_file():
            return candidate
    raise MVError("找不到 imagegen-tardis 的 scripts/image_gen.py。安装该 skill，"
                  "或在配置的 tardis.script 中写明路径。")


def run_tardis(cfg: dict, mode: str, prompt: str, prompt_file: Path, out: Path,
               images: list[Path], n: int) -> list[Path]:
    """Call image_gen.py in the current interpreter; returns the saved images."""
    script = locate_tardis(cfg)
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt, encoding="utf-8")
    image_cfg = cfg.get("image") or {}
    cmd = [sys.executable, str(script), mode, "--prompt-file", str(prompt_file),
           "--out", str(out), "--n", str(n), "--model", image_cfg.get("model") or "gpt-image-2"]
    if image_cfg.get("size"):
        cmd += ["--size", image_cfg["size"]]
    if image_cfg.get("quality"):
        cmd += ["--quality", image_cfg["quality"]]
    for image in images:
        cmd += ["--image", str(image)]
    print(f"  调用 Tardis {mode}（{n} 张）→ {out.name}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise MVError("Tardis 生图失败: " + (result.stderr.strip() or result.stdout.strip()))
    saved = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
    saved = [path for path in saved if path.is_file()]
    if not saved:
        raise MVError("Tardis 返回成功但没有找到输出图片")
    return saved


def orientation(width: int, height: int) -> str:
    if height > width:
        return "竖版"
    return "横版" if width > height else "方形"


def crop_note(image_size: str | None, width: int, height: int) -> str:
    """Tell the image model how much of its canvas the video crop will remove."""
    try:
        src_w, src_h = (int(v) for v in str(image_size).lower().split("x"))
    except ValueError:
        return "主体放在画面中央区域，四周留出安全边距"
    src, dst = src_w / src_h, width / height
    if abs(src - dst) < 0.01:
        return "主体放在画面中央区域"
    if src > dst:
        side = (1 - dst / src) / 2 * 100
        return f"后期会裁掉左右各约 {side:.0f}% 的画面，人物和关键物体放在中间区域"
    side = (1 - src / dst) / 2 * 100
    return f"后期会裁掉上下各约 {side:.0f}% 的画面，头部和关键物体不要贴近上下边缘"


def character_prompt(data: dict, char: dict) -> str:
    lines = [
        "用途：歌曲 MV 的角色设定参考图，后续镜头会以此图保持人物一致。",
        f"角色：{char.get('name') or char['id']}。{char['prompt']}",
    ]
    if data.get("style"):
        lines.append(f"整体视觉风格：{data['style']}")
    lines.append("构图：单人，全身站姿，正面略侧，干净的浅色纯背景，光线均匀柔和，"
                 "脸型、发型、服装与配饰清晰可辨；不出现文字、水印和其他人物。")
    return "\n".join(lines)


def shot_prompt(data: dict, shot: dict, chars: list[dict], video: dict, image_size: str | None) -> str:
    lines = [f"用途：歌曲 MV 镜头 {shot['id']} 的关键帧（会作为视频第一帧），"
             f"{orientation(video['width'], video['height'])}构图。"]
    for number, char in enumerate(chars, start=1):
        lines.append(f"参考图 {number}：角色「{char.get('name') or char['id']}」的设定图，"
                     f"保持其脸型、发型、服装和体型一致，只改变姿态、表情与所处场景。")
    lines.append(f"画面：{shot['image_prompt']}")
    if data.get("style"):
        lines.append(f"整体视觉风格：{data['style']}")
    lines.append(f"构图要求：{crop_note(image_size, video['width'], video['height'])}；"
                 f"画面像电影剧照，动作处于自然的起始姿态；不出现文字、字幕、水印和边框。")
    return "\n".join(lines)


def normalize(src: Path, dst: Path, width: int, height: int, anchor: str = "center") -> Path:
    """Crop to the video aspect ratio, then resize to the exact input size."""
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise MVError("缺少 Pillow，按 references/setup.md 安装 requirements.txt") from exc
    with Image.open(src) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    src_w, src_h = image.size
    target = width / height
    if src_w / src_h > target:
        crop_w, crop_h = round(src_h * target), src_h
        x = {"left": 0, "right": src_w - crop_w}.get(anchor, (src_w - crop_w) // 2)
        y = 0
    else:
        crop_w, crop_h = src_w, round(src_w / target)
        x = 0
        y = {"top": 0, "bottom": src_h - crop_h}.get(anchor, (src_h - crop_h) // 2)
    image = image.crop((x, y, x + crop_w, y + crop_h)).resize((width, height), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    image.save(dst, "PNG")
    return dst
