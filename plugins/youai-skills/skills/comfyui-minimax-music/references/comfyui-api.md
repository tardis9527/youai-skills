# 在线 ComfyUI 执行与无损交付

只在独立音频模式读取。Python 3.10+，脚本仅用标准库；服务器需已安装对应模型与节点。ffmpeg 用于完整解码检查，可由 `--ffmpeg` 指定现有可执行文件；没有时仍能读取 FLAC STREAMINFO，但完整解码必须标 `PENDING`。

## 地址与认证

创作内容与模型选择完成后，索取在线 ComfyUI 根地址。支持 `http://host:8188` 和 `https://host/comfy` 形式，路径前缀保留。不是网页工作流 URL，也不是 Comfy Cloud 等平台的任务 API；平台代理需核实适配后再调用，不能假定同一个 API。

- 地址通过 `COMFYUI_URL` 或 `--url` 传入；有 Bearer 认证时通过 `COMFYUI_TOKEN` 环境变量读取，不使用 URL query/userinfo 传凭据。
- 不要求用户公开密钥。让用户在当前受控环境配置，或使用可用的安全凭据渠道；不写 `.env`、run.json、Markdown 或工作流，不打印响应原文。
- 标准脚本只支持无认证或 Bearer。Cookie 登录、额外签名等不能反复尝试猜测，应说明缺少适配，继续交付已完成的创作文本。
- 不跟随重定向，防止认证被发送至其他地址。401/403/HTML 响应分别排查认证/地址，不当作模型失败。

## 使用方式

以下 `SKILL_DIR` 是已安装 Skill 的真实绝对路径；根据环境解析，不依赖仓库当前目录。Windows 使用 PowerShell 命令，其他平台使用对应语法。

先将定稿音乐描述、完整歌词分别保存为 UTF-8 `description.txt`、`lyrics.txt`，不要在 shell 中拼接长歌词。建议先在工作目录的创作产物目录保存，不写安装目录。

```powershell
# 地址与可选认证已在本次进程环境配置。
python "$SKILL_DIR/scripts/music.py" check --model minimax-music3
python "$SKILL_DIR/scripts/music.py" run --model minimax-music3 --title "歌名" --description-file "description.txt" --lyrics-file "lyrics.txt" --duration 60 --max-duration 90 --date 2026-11-02
```

上述日期、时长和上限仅为示例。`--date` 填用户本地当天日期；`--duration` 为已确认的目标，`--max-duration` 为已确认的上限/收尾余量，不机械填 60/90。上限省略时等于目标，不暗中扩展。自动 seed 为 53 位整数，写入记录；固定对照用 `--seed`。模板没有统一采样率输入，不传虚构的 sample_rate 参数。

选择 YuE2 时把 `--model` 改为 `yue2`。默认 `--mode full --abc-planning`，只有明确需要时用 `--mode melody` 或 `--no-abc-planning`。

`check` 只读，不生成；`run` 也会重新预检最终参数，保证所选时长与模型有效。运行时提交一版，不因首次连接失败自动换模型或服务。

## 工作流来源与覆盖

| 文件 | 用途 |
| --- | --- |
| `workflows/minimax-music3.workflow.json` / `yue2.workflow.json` | 可以导入 ComfyUI 的 UI 模板，分别对应两张参考截图 |
| `*.api.json` | 展开子图后的可执行 API 图；直接保存 FLAC |
| `*.params.json` | 参数到节点输入的明确映射，不是工作流，不提交服务器 |

MiniMax API 保留 tiled 解码，去掉未选中的普通解码分支和 UI 开关；Caption 编码与采样器同步 seed。YuE2 API 保留官方 checkpoint、ABC/音乐采样参数和依赖关系，去掉仅预览与透传节点。API 直接写标量 seed，替代 UI SeedNode；字幕/歌词不硬编码为用户实际输入。

所有模板离线随 Skill 分发，运行时无需下载源码。来源于 Comfy-Org 官方模板（2026-11-02 获取/核对），保留其余模型加载与采样设置；UI 的 MiniMax 基于仓库已有官方模板副本，保存格式改为 FLAC。来源：

- https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_minimax_music_3.json
- https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_yue2_text2music.json
- https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_audio.py
- https://docs.comfy.org/development/comfyui-server/comms_routes

版本不符或自定义 checkpoint 时，用工作目录中的完整覆盖目录，并在 check/run 添加 `--workflow-dir "目录"`。目录必须同时包含所选模型的 `.api.json` 与 `.params.json`，映射用明确节点 ID、class_type 和 input 校验，不对任意工作流做猜测补丁。仍必须保存原始生成音频的 FLAC。服务器 `/object_info` 返回的节点、模型选项与数值上下限是最终预检依据；缺失时在提交前停止。

## 状态、续查与错误

提交前记录唯一 run_id 和 `submitting` 状态，payload 的 `client_id` 与 `extra_data.music_run_id` 使用该 ID；响应后立刻保存 prompt_id。运行记录只存服务地址的哈希来核对续查目标，不存完整地址或认证。实际注入后的图及其 SHA256 一并保存用于复现。

```powershell
python "$SKILL_DIR/scripts/music.py" resume --run-file "output/music/日期-歌名/运行ID/run.json"
```

- 等待超时 `waiting_timeout`：原任务不取消，使用 resume。每 30 秒脚本输出简短进度，宿主 Agent 继续跟踪，不把提交成功当作交付完成。
- 提交超时/响应丢失 `submission_unknown`：resume 从最近 200 条历史与当前队列按 run_id 寻找唯一任务；找不到或不唯一时停止自动操作，不重发。可在服务器核实后用 `--prompt-id` 绑定，脚本仍校验归属；历史已清理时说明不能自动恢复。
- 显式 400/401/403/404/422 或 node_errors：记录拒绝。修正原因后新建运行；不重试原请求。
- 执行失败：记录 `generation_failed`，不输出未经脱敏的节点异常正文；根据服务器本次任务定位后，再由用户授权新版本。
- 下载/解码失败：resume 重用已生成结果；`resume --redownload` 将既有文件另存为 `.previous-随机值` 后重下载，不覆盖原件，不生成新曲。
- `downloaded_pending_decode`：音频已下载并完成文件头检查，但缺少完整解码证据；找到 ffmpeg 后 `resume --ffmpeg "路径"` 完成检查。`completed` 仅表示文件技术检查通过，听感仍需试听。
- `.running.lock` 防止同一运行被并发处理。进程异常退出留下锁时，确认旧进程已退出再移除锁；不能一遇到锁就删除。

读取 `/history/{prompt_id}` 的指定保存节点结果，仅接受 type=output 的 FLAC。下载使用服务器返回的 filename/subfolder，经 URL 编码交给 `/view`；本地文件名由已确认歌名安全化，远程名字不能控制本地写入路径。采用 `.part` 暂存并检查后替换，不把临时预览或 MP3 当作原件。

## 检查与交付

FLAC STREAMINFO 可实测采样率、声道、位深与实长，不能证明后续音频帧都可解码；ffmpeg 全量解码另列 PASS/PENDING。不要宣称 FLAC 等同于高质量听感、平台一定接受、源音频不存在失真，或已经听过用户未提供的成品。

对话交付使用本地绝对路径播放器和原件链接，附模型、实长、检测结果与 `创作记录.md`。FLAC 播放器不兼容时，可使用现有 ffmpeg 从 FLAC 生成明确标记的试听副本再播放；FLAC 原件始终单独链接。不把文件上传外部云盘，也不把公开 URL 或额外发布当作本 Skill 的默认后续动作。
