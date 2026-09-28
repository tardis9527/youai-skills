"""Offline checks for the custom image provider CLI."""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "imagegen-tardis" / "scripts" / "image_gen.py"
spec = importlib.util.spec_from_file_location("imagegen_tardis", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PNG = b"\x89PNG\r\n\x1a\n" + b"offline-test"


class FakeImages:
    def __init__(self):
        self.method = None
        self.options = None

    def generate(self, **options):
        self.method, self.options = "generate", options
        return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(PNG).decode())])

    def edit(self, **options):
        self.method, self.options = "edit", options
        return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(PNG).decode())])


class FakeOpenAI:
    last_client = None

    def __init__(self, **options):
        self.options = options
        self.images = FakeImages()
        FakeOpenAI.last_client = self

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class ImageGenTests(unittest.TestCase):
    def test_generate_uses_auth_model_and_writes_image(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            auth = root / "auth.json"
            auth.write_text(json.dumps({"OPENAI_API_KEY": "test-key"}), encoding="utf-8")
            out = root / "image.png"
            args = module._parser().parse_args([
                "generate", "--prompt", "test", "--model", "custom-model",
                "--auth-file", str(auth), "--out", str(out),
            ])
            with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=FakeOpenAI)}):
                module.run(args)
            self.assertEqual(out.read_bytes(), PNG)
            self.assertEqual(FakeOpenAI.last_client.options, {
                "api_key": "test-key", "base_url": module.DEFAULT_BASE_URL,
            })
            self.assertEqual(FakeOpenAI.last_client.images.options["model"], "custom-model")
            self.assertEqual(FakeOpenAI.last_client.images.method, "generate")
            with self.assertRaisesRegex(ValueError, "already exists"):
                module.run(args)

    def test_edit_passes_image_file(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            auth = root / "auth.json"
            auth.write_text(json.dumps({"OPENAI_API_KEY": "test-key"}), encoding="utf-8")
            source = root / "source.png"
            source.write_bytes(PNG)
            args = module._parser().parse_args([
                "edit", "--prompt", "change background", "--image", str(source),
                "--auth-file", str(auth), "--out", str(root / "edited.png"),
            ])
            with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=FakeOpenAI)}):
                module.run(args)
            self.assertEqual(FakeOpenAI.last_client.images.method, "edit")
            self.assertEqual(FakeOpenAI.last_client.images.options["image"].name, str(source))


if __name__ == "__main__":
    unittest.main()
