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
                "--credential-file", str(root / "missing-credentials.json"),
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

    def test_saved_credential_file_is_used(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            credentials = root / "credentials.json"
            credentials.write_text(json.dumps({"api_key": "saved-key"}), encoding="utf-8")
            self.assertEqual(module._api_key(credentials), "saved-key")

    def test_legacy_auth_file_requires_explicit_path(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            auth = root / "auth.json"
            auth.write_text(json.dumps({"OPENAI_API_KEY": "legacy-key"}), encoding="utf-8")
            self.assertEqual(module._api_key(root / "missing.json", auth_path=auth), "legacy-key")

    def test_explicit_legacy_file_overrides_saved_credential(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            credentials = root / "credentials.json"
            auth = root / "auth.json"
            credentials.write_text(json.dumps({"api_key": "saved-key"}), encoding="utf-8")
            auth.write_text(json.dumps({"OPENAI_API_KEY": "legacy-key"}), encoding="utf-8")
            self.assertEqual(module._api_key(credentials, auth_path=auth), "legacy-key")

    def test_missing_key_requires_user_configuration(self):
        with TemporaryDirectory() as temp_dir:
            credential_path = Path(temp_dir) / "missing.json"
            with self.assertRaisesRegex(ValueError, "Ask the user") as context:
                module._api_key(credential_path)
            self.assertNotIn("test-key", str(context.exception))

    def test_configure_saves_key_without_printing_it(self):
        with TemporaryDirectory() as temp_dir:
            credential_path = Path(temp_dir) / "nested" / "credentials.json"
            args = module._parser().parse_args([
                "configure", "--credential-file", str(credential_path),
            ])
            with patch.object(module.getpass, "getpass", return_value="  saved-key  "):
                with patch("builtins.print") as output:
                    module.run(args)
            self.assertEqual(json.loads(credential_path.read_text(encoding="utf-8")), {
                "api_key": "saved-key",
            })
            self.assertNotIn("saved-key", " ".join(str(call) for call in output.call_args_list))

    def test_configure_rejects_empty_key(self):
        with TemporaryDirectory() as temp_dir:
            args = module._parser().parse_args([
                "configure", "--credential-file", str(Path(temp_dir) / "credentials.json"),
            ])
            with patch.object(module.getpass, "getpass", return_value="  "):
                with self.assertRaisesRegex(ValueError, "cannot be empty"):
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
                "--credential-file", str(root / "missing-credentials.json"),
                "--auth-file", str(auth), "--out", str(root / "edited.png"),
            ])
            with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=FakeOpenAI)}):
                module.run(args)
            self.assertEqual(FakeOpenAI.last_client.images.method, "edit")
            self.assertEqual(FakeOpenAI.last_client.images.options["image"].name, str(source))


if __name__ == "__main__":
    unittest.main()
