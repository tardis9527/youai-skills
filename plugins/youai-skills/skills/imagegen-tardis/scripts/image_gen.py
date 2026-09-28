#!/usr/bin/env python3
"""Generate or edit images through the configured OpenAI-compatible provider."""

from __future__ import annotations

import argparse
import base64
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from urllib.parse import urlparse
from urllib.request import urlopen


DEFAULT_BASE_URL = "https://sub-tardis.ai-you.top/v1"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_AUTH_FILE = Path.home() / ".codex" / "auth.json"
IMAGE_SUFFIXES = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "edit"))
    prompt = parser.add_mutually_exclusive_group(required=True)
    prompt.add_argument("--prompt")
    prompt.add_argument("--prompt-file", type=Path)
    parser.add_argument("--image", type=Path, action="append", default=[])
    parser.add_argument("--mask", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--auth-file", type=Path, default=DEFAULT_AUTH_FILE)
    parser.add_argument("--size")
    parser.add_argument("--quality")
    parser.add_argument("--output-format", choices=tuple(IMAGE_SUFFIXES), default="png")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _prompt(args: argparse.Namespace) -> str:
    value = args.prompt_file.read_text(encoding="utf-8-sig") if args.prompt_file else args.prompt
    value = value.strip()
    if not value:
        raise ValueError("Prompt cannot be empty")
    return value


def _validate(args: argparse.Namespace) -> tuple[str, list[Path]]:
    prompt = _prompt(args)
    if not args.model.strip():
        raise ValueError("Model cannot be empty")
    if args.n < 1 or args.n > 10:
        raise ValueError("--n must be between 1 and 10")
    if args.command == "edit" and not args.image:
        raise ValueError("edit requires at least one --image")
    if args.command == "generate" and (args.image or args.mask):
        raise ValueError("--image and --mask are only valid with edit")
    for path in [*args.image, *([args.mask] if args.mask else [])]:
        if not path.is_file():
            raise ValueError(f"Input file not found: {path}")
    base_url = urlparse(args.base_url)
    if base_url.scheme != "https" or not base_url.netloc or base_url.query or base_url.fragment:
        raise ValueError("--base-url must be an HTTPS API URL")
    if args.out.suffix.lower() != IMAGE_SUFFIXES[args.output_format]:
        raise ValueError(f"--out must end in {IMAGE_SUFFIXES[args.output_format]}")
    paths = [args.out] if args.n == 1 else [
        args.out.with_name(f"{args.out.stem}-{i}{args.out.suffix}")
        for i in range(1, args.n + 1)
    ]
    if not args.force:
        existing = [path for path in paths if path.exists()]
        if existing:
            raise ValueError(f"Output already exists: {existing[0]} (use --force to overwrite)")
    return prompt, paths


def _api_key(path: Path) -> str:
    try:
        auth = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValueError(f"Auth file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Auth file is not valid JSON: {path}") from exc
    key = auth.get("OPENAI_API_KEY") if isinstance(auth, dict) else None
    if not isinstance(key, str) or not key.strip():
        raise ValueError(f"OPENAI_API_KEY is missing in {path}")
    return key.strip()


def _image_bytes(item: object) -> bytes:
    encoded = getattr(item, "b64_json", None)
    if encoded:
        return base64.b64decode(encoded, validate=True)
    url = getattr(item, "url", None)
    if url and urlparse(url).scheme == "https":
        with urlopen(url, timeout=120) as response:
            return response.read()
    raise ValueError("Provider returned neither base64 image data nor an HTTPS image URL")


def _detected_format(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None


def run(args: argparse.Namespace) -> list[Path]:
    prompt, paths = _validate(args)
    if args.dry_run:
        for path in paths:
            print(path.resolve().as_posix())
        return paths

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai Python package to make image requests") from exc

    options = {"model": args.model, "prompt": prompt, "n": args.n,
               "output_format": args.output_format}
    if args.size:
        options["size"] = args.size
    if args.quality:
        options["quality"] = args.quality

    with OpenAI(api_key=_api_key(args.auth_file), base_url=args.base_url) as client:
        if args.command == "generate":
            result = client.images.generate(**options)
        else:
            with ExitStack() as stack:
                images = [stack.enter_context(path.open("rb")) for path in args.image]
                options["image"] = images if len(images) > 1 else images[0]
                if args.mask:
                    options["mask"] = stack.enter_context(args.mask.open("rb"))
                result = client.images.edit(**options)

    if len(result.data) != len(paths):
        raise ValueError(f"Provider returned {len(result.data)} images; expected {len(paths)}")
    image_data = [_image_bytes(item) for item in result.data]
    for data in image_data:
        if _detected_format(data) != args.output_format:
            raise ValueError("Provider returned an image with a different format than requested")
    for path, data in zip(paths, image_data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(path.resolve().as_posix())
    return paths


def main() -> int:
    args = _parser().parse_args()
    try:
        run(args)
    except Exception as exc:
        # Avoid printing provider response bodies that may contain request metadata.
        if exc.__class__.__module__.startswith("openai"):
            status = getattr(exc, "status_code", None)
            print(f"Provider request failed: {type(exc).__name__} (HTTP {status})", file=sys.stderr)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
