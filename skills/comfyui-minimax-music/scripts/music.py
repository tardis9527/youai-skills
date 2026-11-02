#!/usr/bin/env python3
"""Standalone ComfyUI music runner. Python 3.10+, standard library only."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
from http.client import HTTPException
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid

SKILL = Path(__file__).resolve().parents[1]
MODELS = ("minimax-music3", "yue2")


class MusicError(Exception):
    pass


class Rejected(MusicError):
    """The server explicitly rejected this submission, without queueing it."""


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("秒数必须是大于零的有限数字")
    return number


def safe_title(title):
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "-", title)
    name = re.sub(r"\s+", " ", name).strip(" .")[:80].rstrip(" .")
    if not name:
        name = "music"
    if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}:
        name = "song-" + name
    return name


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Do not send credentials to a redirect destination.


class Client:
    def __init__(self, url, token=None):
        parts = urlsplit(url.strip())
        if (parts.scheme not in ("http", "https") or not parts.netloc
                or parts.username or parts.password or parts.query or parts.fragment):
            raise MusicError("ComfyUI 地址必须是 HTTP(S) 服务根地址；认证用环境变量，不能放在 URL 中")
        self.url = url.strip().rstrip("/")
        self.server_id = hashlib.sha256(self.url.encode()).hexdigest()
        self.token = token
        self.opener = build_opener(NoRedirect())

    def request(self, path, data=None, timeout=60):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(self.url + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
        try:
            return self.opener.open(req, timeout=timeout)
        except HTTPError as exc:
            # Do not print response bodies: proxies and nodes may echo credentials.
            if data is not None and exc.code in (400, 401, 403, 404, 422):
                raise Rejected(f"ComfyUI 拒绝提交（HTTP {exc.code}）；检查认证、节点及参数") from None
            raise MusicError(f"ComfyUI HTTP {exc.code}；检查地址、认证及服务状态") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise MusicError("ComfyUI 请求失败或超时；检查连接后使用 resume 续查，不要重复提交") from None

    def json(self, path, data=None):
        try:
            with self.request(path, data) as response:
                return json.load(response)
        except (ValueError, UnicodeError):
            raise MusicError("ComfyUI 未返回有效 JSON；检查是否误填网页或登录页地址") from None
        except (HTTPException, OSError):
            raise MusicError("ComfyUI 响应中断；使用 resume 续查本次任务") from None

    def download(self, item, dest):
        query = urlencode({"filename": item["filename"], "subfolder": item.get("subfolder", ""), "type": "output"})
        part = dest.with_suffix(dest.suffix + ".part")
        try:
            with self.request("/view?" + query, timeout=600) as response, part.open("wb") as stream:
                shutil.copyfileobj(response, stream, length=1024 * 1024)
            # Detect an HTML response or a lossy file before replacing the local file.
            flac_info(part)
            part.replace(dest)
        except (HTTPException, OSError, TimeoutError):
            raise MusicError("音频下载中断；使用 resume 重新下载本次结果") from None
        finally:
            part.unlink(missing_ok=True)


def load_workflow(model, folder=None):
    folder = Path(folder) if folder else SKILL / "workflows"
    spec = read_json(folder / f"{model}.params.json")
    graph = read_json(folder / spec["workflow"])
    if not isinstance(graph, dict) or not graph or not all(
        isinstance(n, dict) and isinstance(n.get("class_type"), str) and isinstance(n.get("inputs"), dict)
        for n in graph.values()
    ):
        raise MusicError("需要 API 格式工作流（class_type / inputs），不能提交界面 JSON")
    return spec, graph


def build_workflow(model, description, lyrics, duration, seed, prefix, mode="full", abc_planning=True, folder=None):
    if not description.strip():
        raise MusicError("音乐描述不能为空")
    if not math.isfinite(duration) or duration <= 0:
        raise MusicError("生成上限必须大于零")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**64 - 1:
        raise MusicError("seed 必须是 0 到 2^64-1 之间的整数")
    spec, graph = load_workflow(model, folder)
    values = {"description": description, "lyrics": lyrics, "max_duration": duration, "seed": seed,
              "filename_prefix": prefix, "mode": mode}
    for key, targets in spec["params"].items():
        if key not in values:
            continue
        for target in targets:
            node = graph.get(target["node"])
            if not node or node["class_type"] != target["class_type"] or target["input"] not in node["inputs"]:
                raise MusicError(f"工作流与参数映射不匹配：{key}")
            node["inputs"][target["input"]] = values[key]
    if model == "yue2" and not abc_planning:
        graph[spec["music_node"]]["inputs"]["abc"] = ""
        del graph[spec["abc_node"]]
    for output in spec["output_nodes"]:
        node = graph[output]
        if node["class_type"] != "SaveAudioAdvanced" or node["inputs"].get("format") != "flac":
            raise MusicError("独立生成工作流必须直接使用 SaveAudioAdvanced 保存 FLAC")
    return spec, graph


def preflight(client, graph):
    client.json("/system_stats")
    info = client.json("/object_info")
    for node_id, node in graph.items():
        kind = node["class_type"]
        if kind not in info:
            raise MusicError(f"服务器缺少节点：{kind}")
        schema = info[kind].get("input", {})
        fields = {**schema.get("required", {}), **schema.get("optional", {})}
        missing = set(schema.get("required", {})) - node["inputs"].keys()
        if missing:
            raise MusicError(f"节点 {node_id} ({kind}) 缺少输入：{', '.join(sorted(missing))}")
        for key, value in node["inputs"].items():
            definition = fields.get(key)
            if not definition:
                raise MusicError(f"节点 {node_id} ({kind}) 不支持输入 {key}；检查节点版本")
            dtype = definition[0]
            if isinstance(value, list):
                if len(value) != 2 or value[0] not in graph or not isinstance(value[1], int):
                    raise MusicError(f"节点 {node_id} 的连接无效：{key}")
                source = info[graph[value[0]]["class_type"]]
                outputs = source.get("output", [])
                if value[1] < 0 or value[1] >= len(outputs) or (isinstance(dtype, str) and dtype != "*" and outputs[value[1]] != dtype):
                    raise MusicError(f"节点 {node_id} 的连接类型不匹配：{key}")
                continue
            if isinstance(dtype, list) and value not in dtype:
                # Report field rather than all model choices or private paths.
                raise MusicError(f"节点 {node_id} ({kind}) 的 {key} 不在服务器可选项中；检查模型文件及选项")
            if dtype == "COMFY_DYNAMICCOMBO_V3":
                options = definition[1].get("options", [])
                if value not in [option["key"] for option in options]:
                    raise MusicError(f"节点 {node_id} 的 {key} 不在动态选项中；检查保存格式支持")
            if dtype == "STRING" and not isinstance(value, str):
                raise MusicError(f"节点 {node_id} 的 {key} 必须为文本")
            if dtype == "BOOLEAN" and not isinstance(value, bool):
                raise MusicError(f"节点 {node_id} 的 {key} 必须为布尔值")
            if dtype in ("INT", "FLOAT"):
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise MusicError(f"节点 {node_id} 的 {key} 必须为有限数字")
                if dtype == "INT" and not isinstance(value, int):
                    raise MusicError(f"节点 {node_id} 的 {key} 必须为整数")
                limits = definition[1] if len(definition) > 1 else {}
                if value < limits.get("min", -math.inf) or value > limits.get("max", math.inf):
                    raise MusicError(f"节点 {node_id} 的 {key} 超出服务器范围；不要自动截断参数")


def flac_info(path):
    """Read native FLAC STREAMINFO; metadata validation is not a decoding test."""
    with Path(path).open("rb") as stream:
        if stream.read(4) != b"fLaC":
            raise MusicError("输出不是原生 FLAC，不能按无损原文件交付")
        header = stream.read(4)
        if len(header) != 4 or header[0] & 127 != 0 or int.from_bytes(header[1:], "big") != 34:
            raise MusicError("FLAC STREAMINFO 无效")
        data = stream.read(34)
        if len(data) != 34:
            raise MusicError("FLAC 文件不完整")
        packed = int.from_bytes(data[10:18], "big")
        rate, channels, bits, samples = packed >> 44, ((packed >> 41) & 7) + 1, ((packed >> 36) & 31) + 1, packed & (2**36 - 1)
        if not rate or not samples or Path(path).stat().st_size <= 42:
            raise MusicError("FLAC 音频为空或时长无效")
        return {"codec": "flac", "sample_rate": rate, "channels": channels,
                "bits_per_sample": bits, "duration_sec": samples / rate, "metadata_check": "PASS"}


def verify_audio(path, limit, ffmpeg="ffmpeg"):
    result = flac_info(path)
    result["near_limit"] = result["duration_sec"] >= limit - max(.25, limit * .01)
    result["ending_review"] = "PENDING_LISTEN"
    result["decode_check"] = "PENDING"
    executable = shutil.which(ffmpeg)
    if executable:
        try:
            process = subprocess.run([executable, "-v", "error", "-xerror", "-i", str(path), "-map", "0:a:0", "-f", "null", "-"],
                                     capture_output=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired):
            raise MusicError("FLAC 解码检查未完成，使用 resume 重试检查") from None
        if process.returncode:
            raise MusicError("FLAC 完整解码检查失败，保留任务记录以便重新下载或排查")
        result["decode_check"] = "PASS"
    return result


@contextmanager
def run_lock(folder):
    lock = Path(folder) / ".running.lock"
    try:
        fd = lock.open("x", encoding="utf-8")
    except FileExistsError:
        raise MusicError("本次运行已有进程在处理；异常退出时核实旧进程已结束后再移除 .running.lock") from None
    try:
        with fd:
            fd.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def recover_prompt(client, state):
    matches = set()
    history = client.json("/history?max_items=200")
    for prompt_id, entry in history.items():
        prompt = entry.get("prompt", [])
        if len(prompt) > 3 and (prompt[3] or {}).get("music_run_id") == state["run_id"]:
            matches.add(prompt_id)
    queue = client.json("/queue")
    for item in queue.get("queue_running", []) + queue.get("queue_pending", []):
        if len(item) > 3 and (item[3] or {}).get("music_run_id") == state["run_id"]:
            matches.add(item[1])
    if len(matches) != 1:
        raise MusicError("提交结果仍不明确；请在服务器核对任务。不会自动重发，可用 resume --prompt-id 绑定核实后的任务")
    return matches.pop()


def collect_outputs(entry, spec):
    items = []
    for node_id in spec["output_nodes"]:
        for outputs in (entry.get("outputs", {}).get(node_id) or {}).values():
            if not isinstance(outputs, list):
                continue
            for item in outputs:
                if (isinstance(item, dict) and item.get("type") == "output" and
                        isinstance(item.get("filename"), str) and item["filename"].lower().endswith(".flac")):
                    items.append(item)
    if not items:
        raise MusicError("任务已结束，但指定保存节点没有 FLAC 输出；检查保存节点，不要重复提交歌曲")
    return items


def record(folder, state):
    lines = [f"# {state['title']}", "", f"- 模型：{state['model']}", f"- seed：{state['seed']}",
             f"- 目标时长：{state['target_duration_sec']} 秒；生成上限：{state['max_duration']} 秒",
             f"- 运行状态：{state['status']}", f"- Prompt ID：{state.get('prompt_id', '尚未获得')}", "",
             "## 音乐描述", "", (folder / "description.txt").read_text(encoding="utf-8"), "",
             "## 完整歌词", "", (folder / "lyrics.txt").read_text(encoding="utf-8"), "", "## 音频检查", ""]
    for item in state.get("files", []):
        lines.extend([f"- 文件：{item['file']}", f"- 检测：{json.dumps(item['inspection'], ensure_ascii=False)}"])
    lines.extend(["", "FLAC 保留生成音频数据；采样率沿用来源。听感、歌词完整性和结尾仍需试听。", ""])
    (folder / "创作记录.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(folder / "run.json", state)


def continue_run(client, folder, state, timeout=3600, poll=3, ffmpeg="ffmpeg", prompt_id=None):
    if client.server_id != state["server_id"]:
        raise MusicError("续查地址与原任务不一致；请使用原 ComfyUI 服务地址")
    if prompt_id:
        if state.get("prompt_id") and state["prompt_id"] != prompt_id:
            raise MusicError("不能覆盖已记录的 prompt_id")
        entry = client.json("/history/" + prompt_id).get(prompt_id)
        queue = client.json("/queue")
        rows = [entry.get("prompt", [])] if entry else []
        rows += queue.get("queue_running", []) + queue.get("queue_pending", [])
        if not any(len(row) > 3 and row[1] == prompt_id and (row[3] or {}).get("music_run_id") == state["run_id"] for row in rows):
            raise MusicError("指定 prompt_id 不属于本次运行，不能绑定")
        state["prompt_id"] = prompt_id
    if not state.get("prompt_id"):
        if state["status"] not in ("submitting", "submission_unknown"):
            raise MusicError("本次运行没有已提交的任务；修正预检问题后使用 run 创建新运行")
        state["prompt_id"] = recover_prompt(client, state)
    if not state.get("outputs"):
        state["status"] = "waiting"
        record(folder, state)
        start, last_note = time.monotonic(), time.monotonic()
        while True:
            entry = client.json("/history/" + state["prompt_id"]).get(state["prompt_id"])
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error" or any(m[0] in ("execution_error", "execution_interrupted") for m in status.get("messages", [])):
                    state["status"] = "generation_failed"
                    record(folder, state)
                    raise MusicError("ComfyUI 执行失败；查看服务器本次任务错误，不会自动重发")
                if status.get("completed") or status.get("status_str") == "success":
                    break
            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                state["status"] = "waiting_timeout"
                record(folder, state)
                raise MusicError("等待超时，服务器任务未取消；使用 resume 继续查询")
            if time.monotonic() - last_note >= 30:
                print(f"仍在等待本次歌曲，已等待 {int(elapsed)} 秒", flush=True)
                last_note = time.monotonic()
            time.sleep(min(poll, max(0, timeout - elapsed)))
        state["outputs"] = collect_outputs(entry, state["spec"])
    state["status"] = "downloading"
    state["files"] = []
    record(folder, state)
    files = []
    for index, item in enumerate(state["outputs"], 1):
        name = safe_title(state["title"]) + (f"-{index}" if len(state["outputs"]) > 1 else "") + ".flac"
        dest = folder / name
        # Recheck an existing file on resume; a prior interrupted download is a .part.
        if not dest.exists():
            client.download(item, dest)
        inspection = verify_audio(dest, state["max_duration"], ffmpeg)
        files.append({"file": name, "inspection": inspection})
    state["files"] = files
    state["status"] = "completed" if all(i["inspection"]["decode_check"] == "PASS" for i in files) else "downloaded_pending_decode"
    record(folder, state)
    for item in files:
        print(json.dumps({"file": str((folder / item["file"]).resolve()), **item["inspection"]}, ensure_ascii=False))
    print(f"运行记录：{(folder / 'run.json').resolve()}")


def parser():
    p = argparse.ArgumentParser(description="ComfyUI MiniMax Music 3 / YuE2 → FLAC")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("check", "run", "resume"):
        s = sub.add_parser(command)
        s.add_argument("--url", help="优先使用 COMFYUI_URL；不写入运行记录")
        if command != "resume":
            s.add_argument("--model", choices=MODELS, required=True)
            s.add_argument("--workflow-dir", type=Path, help="可选的完整 API 工作流与映射覆盖目录")
            s.add_argument("--mode", choices=("full", "melody"), default="full")
            s.add_argument("--abc-planning", action=argparse.BooleanOptionalAction, default=True)
        if command == "run":
            s.add_argument("--title", required=True)
            s.add_argument("--description-file", type=Path, required=True)
            s.add_argument("--lyrics-file", type=Path, required=True)
            s.add_argument("--duration", type=positive, required=True, help="目标秒数，不保证准确片长")
            s.add_argument("--max-duration", type=positive, help="生成上限；省略时等于目标秒数，不暗中增加")
            s.add_argument("--seed", type=int)
            s.add_argument("--output-dir", type=Path, default=Path("output/music"))
            s.add_argument("--date", help="用户本地日期 YYYY-MM-DD，默认执行环境本地日期")
        if command in ("run", "resume"):
            s.add_argument("--timeout", type=positive, default=3600)
            s.add_argument("--poll-interval", type=positive, default=3)
            s.add_argument("--ffmpeg", default="ffmpeg", help="完整解码检查所用的 ffmpeg 路径")
        if command == "resume":
            s.add_argument("--run-file", type=Path, required=True)
            s.add_argument("--prompt-id", help="仅绑定经核实属于本次运行的任务")
            s.add_argument("--redownload", action="store_true", help="重新下载本次输出，保留原有文件")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        url = args.url or os.environ.get("COMFYUI_URL")
        if not url:
            raise MusicError("请提供在线 ComfyUI 地址（COMFYUI_URL 或 --url）")
        client = Client(url, os.environ.get("COMFYUI_TOKEN"))
        if args.command == "check":
            _, graph = build_workflow(args.model, "连接检查", "[Instrumental]", 60, 0, "audio/check",
                                      args.mode, args.abc_planning, args.workflow_dir)
            preflight(client, graph)
            print("PASS：服务、节点、模型及模板参数可用（未提交生成任务）")
            return 0
        if args.command == "resume":
            folder = args.run_file.resolve().parent
            with run_lock(folder):
                state = read_json(args.run_file)
                if client.server_id != state["server_id"]:
                    raise MusicError("续查地址与原任务不一致；请使用原 ComfyUI 服务地址")
                if args.redownload:
                    total = len(state.get("outputs", []))
                    for index in range(1, total + 1):
                        name = safe_title(state["title"]) + (f"-{index}" if total > 1 else "") + ".flac"
                        original = folder / name
                        if original.exists():
                            original.rename(original.with_name(original.name + ".previous-" + uuid.uuid4().hex[:8]))
                continue_run(client, folder, state, args.timeout, args.poll_interval, args.ffmpeg, args.prompt_id)
            return 0
        title = args.title.strip()
        if not title:
            raise MusicError("作品名称不能为空")
        limit = args.max_duration if args.max_duration is not None else args.duration
        if limit < args.duration:
            raise MusicError("生成上限不能小于目标时长")
        seed = args.seed if args.seed is not None else secrets.randbits(53)
        run_id = uuid.uuid4().hex
        day = args.date or datetime.now().astimezone().strftime("%Y-%m-%d")
        if datetime.strptime(day, "%Y-%m-%d").strftime("%Y-%m-%d") != day:
            raise MusicError("日期必须采用 YYYY-MM-DD")
        spec, graph = build_workflow(args.model, args.description_file.read_text(encoding="utf-8-sig"),
                                    args.lyrics_file.read_text(encoding="utf-8-sig"), limit, seed,
                                    "audio/music-" + run_id, args.mode, args.abc_planning, args.workflow_dir)
        preflight(client, graph)
        folder = args.output_dir.resolve() / (day + "-" + safe_title(title)) / run_id
        folder.mkdir(parents=True, exist_ok=False)
        state = {"run_id": run_id, "server_id": client.server_id, "title": title, "model": args.model,
                 "seed": seed, "target_duration_sec": args.duration, "max_duration": limit,
                 "mode": args.mode if args.model == "yue2" else None,
                 "abc_planning": args.abc_planning if args.model == "yue2" else None,
                 "created_at": datetime.now().astimezone().isoformat(), "status": "prepared", "spec": spec,
                 "workflow_sha256": hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest()}
        with run_lock(folder):
            (folder / "description.txt").write_text(args.description_file.read_text(encoding="utf-8-sig"), encoding="utf-8")
            (folder / "lyrics.txt").write_text(args.lyrics_file.read_text(encoding="utf-8-sig"), encoding="utf-8")
            write_json(folder / "workflow.api.json", graph)
            state["status"] = "submitting"
            record(folder, state)
            print(f"运行记录：{folder / 'run.json'}", flush=True)
            try:
                result = client.json("/prompt", {"prompt": graph, "client_id": run_id, "extra_data": {"music_run_id": run_id}})
                if result.get("node_errors") or result.get("error"):
                    raise Rejected("工作流被拒绝；查看服务器节点校验结果")
                state["prompt_id"] = result["prompt_id"]
            except Rejected:
                state["status"] = "submission_rejected"
                record(folder, state)
                raise
            except (MusicError, KeyError, OSError, ValueError):
                state["status"] = "submission_unknown"
                record(folder, state)
                raise MusicError("提交结果不明确，已保留记录；使用 resume 核查，不要重复运行 run") from None
            record(folder, state)
            continue_run(client, folder, state, args.timeout, args.poll_interval, args.ffmpeg)
        return 0
    except (MusicError, OSError, ValueError, KeyError) as exc:
        # OS/JSON errors can contain input data; only print our curated messages.
        message = str(exc) if isinstance(exc, MusicError) else "本地文件、JSON 或运行记录无效；检查输入及目录权限"
        print("ERROR：" + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
