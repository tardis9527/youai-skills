# 歌曲完整性与本地视频资源优化

## 歌曲：目标长度与生成上限

`target_duration_sec` 决定歌词密度、段落和编曲；`generation_max_duration_sec` 才映射为 `MiniMaxMusic3TextEncode.max_duration`。新任务默认预留 `music.ending_buffer_sec=30` 秒，目标 60 秒时上限为 90 秒。余量是测试起点，不保证精确片长或完整演唱。Caption 应安排完整末句、自然收束与尾奏；不要靠加上限承载明显超量歌词。

```powershell
python <SKILL_DIR>/scripts/mv.py music <slug> --target-duration 60 --max-duration 90 --takes 1 --dry-run
python <SKILL_DIR>/scripts/mv.py music <slug> --target-duration 60 --max-duration 90 --takes 1
python <SKILL_DIR>/scripts/mv.py music-check <slug>
```

默认先生成 1 版。已有项目的 `music.duration_sec` 作为目标长度读取；旧版 `--duration 45` 仍表示 45 秒生成上限，不会悄悄加余量。`--max-duration` 可显式设定上限；不能和 `--duration` 同时使用。指定新目标但没指定上限时重新按余量计算；不指定参数时沿用已经保存的新上限。上限小于目标时需同时明确调整目标，旧版参数除外。

生成前读取目标服务的 `/object_info`，验证实际节点范围；越界报错，不静默封顶。ComfyUI 0.43.0 本机节点的参数上限为 360 秒，这是节点合法范围，不是完整演唱或质量承诺，其他版本以实际接口为准。

每版记录目标、提交上限、seed、实际文件时长/采样率/声道、`near_limit`、`ending_review=pending_listen`。距上限不超过 `max(0.25秒, 上限的1%)` 时提示可能未收尾；不接近上限也必须试听末句与尾奏，自动测时不能判断歌词是否完整。探测失败保留已生成文件与版本，标记待检测，不自动再生成。`music-check` 可补测旧版本。

选歌、分析、分镜均使用实际完整音频。`package` 和 `roughcut` 在产生交付文件前测量已选歌曲；若歌曲比分镜终点长超过 0.05 秒则拒绝导出，先补齐时间线。需要短版时另存经试听确认的剪辑音频，不覆盖完整歌曲。粗剪 manifest 记录歌曲实长与时间线长度。

## 视频：显式选择配置

| profile | 模型 | 尺寸 | fps / 上限帧数 | 用途 |
| --- | --- | --- | --- | --- |
| `wan5b` | Wan2.2 TI2V-5B | 576×1024 | 24 / 121 | 本地候选；普通 20 步、CFG 5、uni_pc/simple、配套 VAE 分块解码 |
| `h3` | MiniMax H3 | 864×1536 | 24 / 124 | 保留当前配置；资源充足机器上使用 |
| `h3-preview` | MiniMax H3 | 576×1024 | 24 / 124 | H3 低分辨率试片，权重占用仍然存在 |

配置均为显式选择。新项目可 `new "作品名" --video-profile wan5b`；未指定时仍沿用工作区配置，不宣称已经通过本机质量验收。现有项目用以下命令先预览再切换：

```powershell
python <SKILL_DIR>/scripts/mv.py video-profile <slug> wan5b --dry-run
python <SKILL_DIR>/scripts/mv.py video-profile <slug> wan5b
python <SKILL_DIR>/scripts/mv.py frame-select <slug> S01
python <SKILL_DIR>/scripts/mv.py shots-check <slug>
python <SKILL_DIR>/scripts/mv.py comfy-validate wan5b-i2v
python <SKILL_DIR>/scripts/mv.py clips <slug> --shots S01 --takes 1 --dry-run
```

切换保留视频历史及 `video_history`，不自动重切分镜或重跑素材。尺寸改变后从已选原图对每个待生成镜头运行 `frame-select`，无需再次生图。已有片段仍按原规格使用；需要新模型版本时显式指定 `--shots`，默认续跑会跳过已有片段。

Wan5B 使用独立的 `wan5b-i2v.workflow.json`、`.api.json`、`.params.json`，不是将 H3 API 改权重名称。帧数按 `4n+1` 对齐，原生片段时长为 `frames/24`；旧 `wan2.2` 数据仍保留历史 `(frames-1)/fps` 的展示规则，生成前应显式选配置。

**Wan5B 仅支持单首帧。** 有 `flf2v` 或过长镜头时配置切换会拒绝；先人工调整分镜或保留 H3，不能静默改成硬切。H3 继续使用自己的 `17k+5` 帧数网格与首尾帧流程。H3 Turbo 主要减少采样计算时间，不解决权重占用。

Wan 模型需单独准备到目标 ComfyUI 的 `models/`，技能不自动安装或下载：

| 目录 | 模型文件 |
| --- | --- |
| `diffusion_models/` | `wan2.2_ti2v_5B_fp16.safetensors` |
| `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` |
| `vae/` | `wan2.2_vae.safetensors` |

按 [ComfyUI 官方 Wan2.2 指南](https://docs.comfy.org/tutorials/video/wan/wan2_2) 获取配套文件。官方所述低显存运行依赖模型卸载机制；不能据此保证所有分辨率、帧数和其他进程占用下都能成功。初次不要混用第三方量化或加速 LoRA。

## 缓存与运行记录

`comfyui.release_between_stages=true`：歌曲、H3、Wan5B、旁白之间切换时，查询 `/queue`；仅空闲时请求 `/free` 释放模型和缓存。有在途或排队任务就跳过；不调用 `/interrupt`，同阶段复用模型。释放请求由 ComfyUI 调度处理，不保证释放瞬间或降低权重本身的大小。禁用该项即可完全交给服务端管理。阶段记录保存在工作区 `.mv-creator/runtime/`，不含服务 URL 或凭据；不修改启动参数及系统设置。

所有 `comfy-run` / 歌曲 / 视频 / 旁白任务在输出目录保存 `<take>.run.json`：prompt ID、工作流与提交图摘要、数值参数、提示文本摘要、状态、耗时和资源采样。原始提示文本、密钥和完整工作流不写入日志。`comfyui.record_resources=false` 可关闭资源采样。

资源来自 `/system_stats`，在等待轮询时采样，记录系统 RAM 和各 GPU 已用显存的采样最大值。**这是整台服务机器的采样值**，包含其他进程；不能当作本任务独占、瞬时精确峰值或共享显存统计。API 不支持时记录 unavailable，生成仍可继续。失败或超时保留 prompt ID 与状态；先查队列和历史，不能盲目重复提交。预检失败不上传、不释放模型、不提交任务。

## 三镜头验收

使用同一套已确认关键帧，先选人物近景、人物动作、环境运镜三个代表镜头，每镜头 1 版；提前说明实际调用数，不默认全量重跑。比较人物身份、服装、手脚、闪烁、背景变形、运镜与构图，同时查看 `.run.json` 的耗时和资源采样。

先运行 `clips --shots S01,S02,S03 --takes 1 --dry-run`，再在已确认范围内生成。镜号应替换为实际代表镜头。未安装模型或服务有在途任务时只完成预检，不抢占运行中的任务。样片通过后才考虑更高合法分辨率，并再次确认资源和画质；分块解码也要检查接缝和时间连续性。

用户确认样片达标后，可把验收后的 `video` 配置写入该工作区 `mv-creator.config.json`，作为以后新项目默认；已有项目不自动迁移。若 Wan5B 质量不达标，保留 H3；质量优先时把同一 H3 工作流放到资源更充足的远端 ComfyUI，并在独立工作区配置其 URL，先验证远端节点与模型，不自动产生云端费用。
