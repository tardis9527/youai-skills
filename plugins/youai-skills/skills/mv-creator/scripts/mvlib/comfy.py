"""ComfyUI HTTP API client and parameter injection for API-format workflows."""

from __future__ import annotations

import copy
import json
import mimetypes
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .common import MVError, read_json, workflows_dir, SKILL_DIR

SELECTOR_KEYS = ("id", "title", "class_type", "upstream")


class ComfyClient:
    def __init__(self, url: str, timeout_sec: float = 3600, poll_interval_sec: float = 2):
        self.url = url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.poll_interval_sec = poll_interval_sec
        self.client_id = uuid.uuid4().hex

    @classmethod
    def from_config(cls, cfg: dict) -> "ComfyClient":
        c = cfg["comfyui"]
        return cls(c["url"], c.get("timeout_sec", 3600), c.get("poll_interval_sec", 2))

    def _request(self, path: str, data: bytes | None = None, headers: dict | None = None,
                 timeout: float = 60) -> bytes:
        request = Request(self.url + path, data=data, headers=headers or {},
                          method="POST" if data is not None else "GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise MVError(f"ComfyUI 返回 HTTP {exc.code}（{path}）:\n{_format_error(body)}") from exc
        except URLError as exc:
            raise MVError(f"连不上 ComfyUI {self.url}: {exc.reason}。检查地址、端口、"
                          f"--listen 启动参数和防火墙。") from exc

    def get_json(self, path: str, timeout: float = 60) -> dict:
        return json.loads(self._request(path, timeout=timeout))

    def system_stats(self) -> dict:
        return self.get_json("/system_stats", timeout=10)

    def object_info(self) -> dict:
        return self.get_json("/object_info", timeout=120)

    def upload(self, path: Path, subfolder: str) -> str:
        """Upload an input file; returns the value a LoadImage-style node expects."""
        path = Path(path)
        boundary = uuid.uuid4().hex
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        parts = [
            _form_field(boundary, "overwrite", "true"),
            _form_field(boundary, "type", "input"),
            _form_field(boundary, "subfolder", subfolder),
            (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
             f"filename=\"{path.name}\"\r\nContent-Type: {mime}\r\n\r\n").encode("utf-8")
            + path.read_bytes() + b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
        raw = self._request("/upload/image", data=b"".join(parts), timeout=300,
                            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        info = json.loads(raw)
        name = info["name"]
        return f"{info['subfolder']}/{name}" if info.get("subfolder") else name

    def queue(self, prompt: dict) -> str:
        body = json.dumps({"prompt": prompt, "client_id": self.client_id}).encode("utf-8")
        info = json.loads(self._request("/prompt", data=body,
                                        headers={"Content-Type": "application/json"}))
        if info.get("node_errors"):
            raise MVError("工作流校验失败:\n" + _format_error(json.dumps(info)))
        return info["prompt_id"]

    def wait(self, prompt_id: str) -> dict:
        started = time.monotonic()
        last_note = started
        while True:
            history = self.get_json(f"/history/{prompt_id}")
            entry = history.get(prompt_id)
            if entry:
                status = entry.get("status") or {}
                if status.get("status_str") == "error":
                    raise MVError("ComfyUI 执行失败:\n" + _execution_error(status))
                if status.get("completed") or status.get("status_str") == "success":
                    return entry
            now = time.monotonic()
            if now - started > self.timeout_sec:
                raise MVError(f"等待超时（{self.timeout_sec}s），任务 {prompt_id} 仍在 ComfyUI 队列中，"
                              f"可在 ComfyUI 界面查看。")
            if now - last_note >= 30:
                print(f"  ……仍在生成，已等待 {int(now - started)}s", flush=True)
                last_note = now
            time.sleep(self.poll_interval_sec)

    def download(self, item: dict, dest: Path) -> Path:
        query = urlencode({"filename": item["filename"], "subfolder": item.get("subfolder", ""),
                           "type": item.get("type", "output")})
        data = self._request(f"/view?{query}", timeout=600)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest


def _form_field(boundary: str, name: str, value: str) -> bytes:
    return (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n"
            f"{value}\r\n").encode("utf-8")


def _format_error(body: str) -> str:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body[:2000]
    lines = []
    error = data.get("error")
    if isinstance(error, dict):
        lines.append(f"- {error.get('message', '')} {error.get('details', '')}".rstrip())
    for node_id, info in (data.get("node_errors") or {}).items():
        for err in info.get("errors", []):
            lines.append(f"- 节点 {node_id} ({info.get('class_type')}): "
                         f"{err.get('message', '')} {err.get('details', '')}".rstrip())
    return "\n".join(lines) or body[:2000]


def _execution_error(status: dict) -> str:
    for kind, msg in status.get("messages", []):
        if kind == "execution_error":
            return (f"- 节点 {msg.get('node_id')} ({msg.get('node_type')}): "
                    f"{msg.get('exception_type', '')}: {msg.get('exception_message', '').strip()}")
    return json.dumps(status, ensure_ascii=False)[:2000]


# Workflow files ------------------------------------------------------------

def load_api_workflow(path: Path) -> dict:
    data = read_json(path)
    if isinstance(data.get("prompt"), dict):
        data = data["prompt"]
    if "nodes" in data and "links" in data:
        raise MVError(f"{path} 是界面格式的工作流。请在 ComfyUI 菜单用 Export (API) 重新导出。")
    if not data or not all(isinstance(v, dict) and "class_type" in v for v in data.values()):
        raise MVError(f"{path} 不是 API 格式的工作流（缺少 class_type）")
    return data


def spec_path(cfg: dict, kind: str) -> Path:
    for folder in (workflows_dir(cfg), SKILL_DIR / "workflows"):
        candidate = folder / f"{kind}.params.json"
        if candidate.is_file():
            return candidate
    raise MVError(f"找不到参数映射文件 {kind}.params.json（查找目录: {workflows_dir(cfg)}）")


def load_kind(cfg: dict, kind: str) -> tuple[dict, dict, Path]:
    """Return (mapping spec, API workflow, workflow path) for a workflow kind.

    Exported workflows live in the workspace so plugin updates never touch
    them; mapping specs fall back to the copies shipped with the skill.
    """
    spath = spec_path(cfg, kind)
    spec = read_json(spath)
    name = spec.get("workflow", f"{kind}.api.json")
    candidates = [workflows_dir(cfg) / name, spath.parent / name]
    wpath = next((p for p in candidates if p.is_file()), None)
    if wpath is None:
        raise MVError(f"缺少工作流 {candidates[0]}。按 references/workflows.md 从模板导出 API 格式后放到这里。")
    return spec, load_api_workflow(wpath), wpath


def node_title(node: dict) -> str:
    return (node.get("_meta") or {}).get("title", "")


def select_nodes(workflow: dict, target: dict) -> list[str]:
    if not any(key in target for key in SELECTOR_KEYS):
        raise MVError(f"映射目标缺少选择器（{'/'.join(SELECTOR_KEYS)}）: {target}")
    ids = list(workflow)
    if "id" in target:
        ids = [i for i in ids if i == str(target["id"])]
    if "title" in target:
        ids = [i for i in ids if node_title(workflow[i]) == target["title"]]
    if "class_type" in target:
        allowed = target["class_type"]
        allowed = [allowed] if isinstance(allowed, str) else allowed
        ids = [i for i in ids if workflow[i]["class_type"] in allowed]
    if "upstream" in target:
        # The node feeding <input> of a node of <class_type>, e.g. the prompt
        # encoder wired into WanImageToVideo.positive.
        up = target["upstream"]
        sources = set()
        for node in workflow.values():
            if node["class_type"] == up["class_type"]:
                link = node.get("inputs", {}).get(up["input"])
                if _is_link(link):
                    sources.add(str(link[0]))
        ids = [i for i in ids if i in sources]
    for key, value in (target.get("where") or {}).items():
        ids = [i for i in ids if workflow[i].get("inputs", {}).get(key) == value]
    return ids


def _is_link(value) -> bool:
    return isinstance(value, list) and len(value) == 2 and isinstance(value[1], int)


def _resolve_targets(workflow: dict, name: str, param: dict) -> list[tuple[str, str]]:
    """(node id, input name) pairs a parameter writes to."""
    mode = param.get("mode", "first")
    found: list[tuple[str, str]] = []
    for target in param.get("targets", []):
        ids = select_nodes(workflow, target)
        if len(ids) > 1 and not target.get("multi"):
            raise MVError(f"参数 {name} 的选择器匹配到多个节点 {ids}，请改用节点标题区分: {target}")
        found.extend((i, target["input"]) for i in ids)
        if ids and mode == "first":
            break
    return found


def apply_params(workflow: dict, spec: dict, values: dict) -> dict:
    workflow = copy.deepcopy(workflow)
    params = spec.get("params", {})
    unknown = sorted(set(values) - set(params))
    if unknown:
        raise MVError(f"映射文件中没有这些参数: {', '.join(unknown)}")
    for name, param in params.items():
        if name not in values:
            if param.get("required"):
                raise MVError(f"缺少必填参数: {name}")
            continue
        targets = _resolve_targets(workflow, name, param)
        if not targets:
            if param.get("optional"):
                continue
            raise MVError(f"参数 {name} 在工作流中没有匹配到节点，检查节点标题或映射文件")
        for node_id, input_name in targets:
            _set_input(workflow, node_id, input_name, values[name])
    return workflow


def _set_input(workflow: dict, node_id: str, input_name: str, value) -> None:
    inputs = workflow[node_id].setdefault("inputs", {})
    current = inputs.get(input_name)
    if _is_link(current):
        # Widget converted to an input and fed by a primitive node: set the source.
        source = workflow.get(str(current[0]), {})
        if "value" in source.get("inputs", {}) and not _is_link(source["inputs"]["value"]):
            source["inputs"]["value"] = value
            return
        raise MVError(f"节点 {node_id}.{input_name} 由其他节点连线提供，无法直接赋值；"
                      f"请把映射指向源节点 {current[0]}")
    inputs[input_name] = value


def validate_kind(workflow: dict, spec: dict) -> list[str]:
    problems = []
    for name, param in spec.get("params", {}).items():
        try:
            targets = _resolve_targets(workflow, name, param)
        except MVError as exc:
            problems.append(str(exc))
            continue
        if not targets and not param.get("optional"):
            problems.append(f"参数 {name} 没有匹配到节点")
        for node_id, input_name in targets:
            if input_name not in workflow[node_id].get("inputs", {}):
                problems.append(f"参数 {name}: 节点 {node_id} ({workflow[node_id]['class_type']}) "
                                f"没有输入 {input_name}")
    return problems


def describe(workflow: dict) -> list[str]:
    lines = []
    for node_id, node in sorted(workflow.items(), key=lambda kv: _sort_key(kv[0])):
        literal = {k: v for k, v in node.get("inputs", {}).items() if not _is_link(v)}
        shown = ", ".join(f"{k}={_short(v)}" for k, v in literal.items())
        title = node_title(node)
        lines.append(f"[{node_id}] {node['class_type']}" + (f"  「{title}」" if title else "")
                     + (f"\n      {shown}" if shown else ""))
    return lines


def _sort_key(node_id: str):
    return [int(p) if p.isdigit() else p for p in node_id.replace(":", " ").split()]


def _short(value) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 60 else text[:57] + "..."


def collect_outputs(entry: dict) -> list[dict]:
    """Every saved file in a history entry (skipping temp previews)."""
    files = []
    for output in (entry.get("outputs") or {}).values():
        for items in output.values():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and "filename" in item and item.get("type") != "temp":
                    files.append(item)
    return files


def run_kind(cfg: dict, kind: str, values: dict, uploads: dict[str, Path], subfolder: str,
             dest_dir: Path, dest_stem: str) -> list[Path]:
    """Upload inputs, run one workflow and download its outputs into dest_dir."""
    spec, workflow, _ = load_kind(cfg, kind)
    client = ComfyClient.from_config(cfg)
    values = dict(values)
    for name, path in uploads.items():
        print(f"  上传 {name}: {Path(path).name}", flush=True)
        values[name] = client.upload(Path(path), subfolder)
    prompt = apply_params(workflow, spec, values)
    prompt_id = client.queue(prompt)
    print(f"  已提交 {kind} 任务 {prompt_id}", flush=True)
    entry = client.wait(prompt_id)
    allowed = [e.lower() for e in spec.get("output_ext", [])]
    files = [f for f in collect_outputs(entry)
             if not allowed or Path(f["filename"]).suffix.lower() in allowed]
    if not files:
        raise MVError(f"{kind} 任务完成但没有找到输出文件（允许的扩展名: {allowed or '任意'}）")
    saved = []
    for index, item in enumerate(files, start=1):
        suffix = Path(item["filename"]).suffix
        name = f"{dest_stem}{suffix}" if len(files) == 1 else f"{dest_stem}-{index}{suffix}"
        saved.append(client.download(item, dest_dir / name))
    return saved
