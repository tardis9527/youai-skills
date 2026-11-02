"""Per-run timing and sampled server memory; no raw prompts or credentials in logs."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from .common import MVError, now_iso, read_json, root_dir, write_json


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class RunMonitor:
    def __init__(self, client, cfg: dict, kind: str, path: Path):
        self.client, self.cfg, self.kind, self.path = client, cfg, kind, path
        self.group = ("video:wan5b" if kind == "wan5b-i2v" else "video:h3" if kind in ("i2v", "flf2v")
                      else "voice" if kind.startswith("tts-") else kind)
        self.state = root_dir(cfg) / ".mv-creator" / "runtime" / f"{digest(client.url)[:16]}.json"
        self.record = {"kind": kind, "created": now_iso(), "resource_scope": "server_system_wide_sampled",
                       "resource_samples": 0, "sampled_ram_used_peak_bytes": 0,
                       "sampled_vram_used_peak_bytes": {}, "release": "disabled"}
        self.started = time.monotonic()

    def prepare(self):
        if not self.cfg["comfyui"].get("release_between_stages", True):
            return
        try:
            previous = read_json(self.state) if self.state.is_file() else {}
            if previous.get("group") == self.group:
                self.record["release"] = "same_stage_reused"
                return
            queue = self.client.get_json("/queue", timeout=10)
            if queue.get("queue_running") or queue.get("queue_pending"):
                self.record["release"] = "skipped_busy"
                print("  ComfyUI 有在途任务，跳过缓存释放，不中断任务", flush=True)
                return
            self.client._request("/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"}, timeout=10)
            self.record["release"] = "requested_while_idle"
        except (MVError, OSError, ValueError):
            self.record["release"] = "unavailable"
            print("  缓存释放不可用，继续由 ComfyUI 管理内存", flush=True)

    def start(self, prompt, values):
        self.started = time.monotonic()
        scalar_keys = {"max_duration", "seed", "width", "height", "duration", "length", "fps",
                       "cfg_scale", "max_new_tokens", "filename_prefix"}
        self.record.update(status="prepared", prompt_sha256=digest(prompt),
                           parameters={k: v for k, v in values.items() if k in scalar_keys},
                           text_sha256={k: digest(v) for k, v in values.items()
                                        if k in ("caption", "lyrics", "positive", "negative", "text", "instruction")})
        self.sample()
        self._save()

    def submitted(self, prompt_id):
        self.record.update(prompt_id=prompt_id, status="submitted")
        self._save()

    def sample(self):
        if not self.cfg["comfyui"].get("record_resources", True):
            return
        try:
            stats = self.client.system_stats()
            system = stats.get("system", {})
            used = max(0, system.get("ram_total", 0) - system.get("ram_free", 0))
            self.record["sampled_ram_used_peak_bytes"] = max(self.record["sampled_ram_used_peak_bytes"], used)
            for device in stats.get("devices", []):
                key = str(device.get("index", device.get("name", "unknown")))
                used = max(0, device.get("vram_total", 0) - device.get("vram_free", 0))
                peaks = self.record["sampled_vram_used_peak_bytes"]
                peaks[key] = max(peaks.get(key, 0), used)
            self.record["resource_samples"] += 1
        except (MVError, OSError, ValueError, TypeError):
            self.record["resources_unavailable"] = True

    def finish(self, status, files=None):
        self.sample()
        self.record.update(status=status, elapsed_sec=round(time.monotonic() - self.started, 3), finished=now_iso())
        if files is not None:
            self.record["files"] = files
        self._save()
        if status == "success":
            try:
                write_json(self.state, {"group": self.group, "updated": now_iso()})
            except OSError:
                print("  注意: 无法保存缓存阶段记录，下次会重新检查空闲状态")

    def _save(self):
        try:
            write_json(self.path, self.record)
        except OSError:
            print("  注意: 运行记录写入失败，请保留 ComfyUI prompt ID", flush=True)
