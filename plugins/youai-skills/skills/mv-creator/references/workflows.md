# 工作流：音乐、MiniMax H3 与可选旁白

新增 Wan5B、视频配置选择、歌曲收尾余量、缓存与运行记录见 [资源与时长优化](resource-and-duration.md)。下文 H3 设置仅适用于 H3；Wan5B 不复用其帧数与首尾帧逻辑。

## 三种 JSON 的用途

| 后缀 | 内容 | 交给谁 |
| --- | --- | --- |
| `.workflow.json` | 界面节点、连线、布局及子图 | 拖入 ComfyUI 画布 |
| `.api.json` | 以节点 ID 为键的执行图，节点包含 `class_type`、`inputs` | MV 脚本读取并提交 |
| `.params.json` | 脚本参数映射，包含 `workflow`、`params` | 脚本内部读取，不能拖入画布 |

误拖 `.params.json` 可能出现 `TypeError: e is not iterable`；改后缀不能转换格式。技能提供了真正可拖入的界面模板，来源与许可见 [workflows/README.md](../workflows/README.md)。

## 工作流与模型

| 类型 | 技能内的可拖入模板 | 技能内的 API 执行文件 | 模型 |
| --- | --- | --- | --- |
| `music` | `music.workflow.json` | `music.api.json` | MiniMax Music 3，保持原歌曲流程 |
| `i2v` | `i2v.workflow.json` | `i2v.api.json` | MiniMax H3 FL2VA，仅连接首帧 |
| `wan5b-i2v`（可选） | `wan5b-i2v.workflow.json` | `wan5b-i2v.api.json` | Wan2.2 TI2V-5B，仅首帧，分块解码 |
| `flf2v`（可选） | `flf2v.workflow.json` | `flf2v.api.json` | 同一 MiniMax H3 FL2VA，连接首尾帧 |
| `tts-design`（可选） | `tts-design.workflow.json` | `tts-design.api.json` | Breeze TTS 2 音色试镜 |
| `tts-direction`（可选） | `tts-direction.workflow.json` | `tts-direction.api.json` | Breeze TTS 2 固定参考音色配音 |

上述文件均随技能发布，位置为 `<SKILL_DIR>/workflows/`。**新项目默认没有本地工作流，脚本直接读取技能中的 API 执行图与映射，不要求用户先导出或复制文件。** 音乐与视频 API 已展开随附界面模板的子图，保留模型、采样设置、时长计算和保存节点。TTS 使用独立平铺节点；具体节点版本、模型配套目录、中文提示词、音色参考、许可和生成步骤见 [voice-guide.md](voice-guide.md)。纯歌曲项目不要求配置 TTS。

工作区配置的 `workflows_dir`（默认 `workflows/`）用于自定义覆盖：同名 `.api.json` 和 `.params.json` 分别优先于技能默认文件。已有覆盖文件不被改写；覆盖文件无效时报告错误，不静默改用默认图。没有工作区目录也能运行内置类型。显式指定其他工作流文件名时按该文件名查找，不能拿无关默认图替代。

视频模板基于官方 `Image to Video (MiniMax H3)` 子图，使用与用户截图相同的量化模型和 Turbo 配置：

| 目录（相对 ComfyUI/models/） | 文件 |
| --- | --- |
| `diffusion_models/` | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` |
| `vae/` | `minimax_h3_video_vae_int8_convrot.safetensors` |
| `vae/` | `minimax_h3_audio_vae_fp32.safetensors` |
| `loras/`（开启 Turbo 时使用） | `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` |

默认 `turbo_mode=false`，普通采样 20 步；开启 Turbo 时使用模型强度 1.0、8 步。脚本不擅自切换 Turbo、修改模型文件名或采样设置。音频 VAE 用于解码 H3 的联合音视频输出；粗剪会移除片段音轨并合入已确认的原创歌曲。

模型下载入口在模板说明节点与 [官方模型仓库](https://huggingface.co/Comfy-Org/MiniMax-H3)。本技能不包含权重，不自动下载模型或安装节点。若 INT8/NVFP4 权重加载失败，检查 ComfyUI、量化运行库和硬件支持，不自动降级为其他模型。

## 首次使用与自定义覆盖

1. 根据当前阶段选择内置 API：音乐用 `music`，单张关键帧生视频用 `i2v`，需要首尾帧时用 `flf2v`。脚本会上传图片并替换占位输入，不需要用户在界面另跑一遍。只验证实际使用的类型，如 `mv.py comfy-validate i2v --offline` 后再 `mv.py comfy-validate i2v`。
2. 默认竖屏 864×1536（宽高均为 32 的倍数），24fps；可按硬件改为 576×1024 等预览尺寸，并同步修改项目 `video`。模板无额外分辨率选择器，脚本直接注入宽高。
3. 模板的 `duration` 为秒，默认 5.0；保留内部计算节点，它将秒数对齐到 H3 的 `17k+5` 帧数网格。**不要沿用 Wan 工作流中断开计算帧数连线的操作。**
4. 只有需要自定义模型或采样配置时，才把技能中的 `.workflow.json` 拖入 ComfyUI，按用户选择调整并 Export (API) 到工作区 `workflows/<kind>.api.json`；必要时在同目录放匹配的 `.params.json`。不要改技能安装目录内的默认文件。普通界面 JSON 不能直接交给脚本。
5. `--offline` 检查格式、参数映射、H3 节点和 24fps 输出；在线验证再检查服务端节点。缺模型或接口不兼容时核对实际错误，不能把“项目本地没有 API 文件”当作生成阻塞。离线通过不代表已经在目标 GPU 上生成成功。

用户自定义的 API、配置及界面文件保存在工作区。内置 API 和用户导出的 API 节点 ID 含 `:` 属正常情况；脚本直接读取执行图，不在运行时转换界面文件。

## 时长和帧数

H3 输出 24fps，帧数对齐到 `17k+5`。本技能默认每段至少生成 124 帧（约 5.17 秒），短镜头在粗剪中裁切，以避免依赖训练范围以外的短片段。`video.max_frames` 默认 124，可设为 124–362 中符合 `17k+5` 的值。

脚本先计算覆盖镜头所需的帧数并按项目上限封顶，然后将 `frames/24` 作为秒数写入模板的 `@duration` 节点。这样内部公式返回相同帧数，不会把帧数误当秒数。镜头可再比片段长 `clip_slack_sec`（默认 0.5 秒），尾部定格补齐；更长镜头应拆分。原生片段时长按 `frames/fps` 记录。

## 从旧 Wan 工作流迁移

1. 保留已生成的视频及其选定版本，不清空 `shots.json` 或重切已确认分镜。
2. 使用技能内置 H3 API；若工作区有旧 Wan `.api.json` / `.params.json` 覆盖，先保留备份并改为其他文件名，再使用技能默认图，或按用户需求重新导出兼容 H3 的覆盖文件。旧 Wan API 不能只改权重名，脚本会拒绝将旧 API 当成 H3。
3. 对工作区配置及要继续生成的项目 `project.json`，将 `video` 更新为以下内容；`roughcut.scale` 设为 `1.25` 时默认粗剪仍为 1080×1920。仅更新工作区配置不会改写项目已保存的视频规格。

```json
{"model": "minimax-h3", "width": 864, "height": 1536, "fps": 24, "max_frames": 124, "clip_slack_sec": 0.5}
```

4. 尺寸变更后可用 `frame-select <slug> <镜号>` 从已选原图重裁，无需再次调用图片接口。运行 `shots-check <slug>` 确认时间线，再执行 `clips --dry-run` 核对数量后生成。

缺少 `video.model` 的旧配置/项目仍按 Wan 时间规则读取，生成前给出迁移提示；旧片段帧数和时长不会被批量重写。新片段追加版本，不覆盖旧视频。

## 注入参数及定位

| 类型 | 参数 | 目标 |
| --- | --- | --- |
| music | `caption`、`lyrics`、`max_duration` | `MiniMaxMusic3TextEncode` 同名输入 |
| music | `seed` | 编码器、`KSampler.seed`，可跟随 `SeedNode.seed` |
| i2v | `image` | `@image` 或连到 H3 `first_frame` 的 `LoadImage.image` |
| flf2v | `start_image`、`end_image` | `@start_image` / `@end_image`，或连到 H3 首尾帧的 LoadImage |
| 视频 | `positive` | `MiniMaxH3ImageToVideo.prompt` |
| 视频 | `width`、`height` | `MiniMaxH3ImageToVideo` 同名输入 |
| 视频 | `duration` | `@duration` 的 `PrimitiveFloat.value`（秒）；无标题时须只有一个 PrimitiveFloat |
| 视频 | `seed` | `@seed` 或 `RandomNoise.noise_seed` |
| TTS | `text`、`instruction`、`seed` 与生成设置 | `@voice` 的 Breeze Design/Direction 同名输入 |
| TTS Direction | `reference_audio`、`reference_text` | `@reference_audio` 的 `LoadAudio.audio` 和 Direction 的准确转写输入 |
| 全部 | `filename_prefix` | 保存节点的同名输入，可用 `@output` 标记 |

H3 默认没有独立 negative 输入。`shots.json.negative` 若有旧内容，将附加到正向提示的“画面约束，避免”部分；不会把不存在的输入添加到节点。动作提示只描述当前镜头，不照搬示例中的多段 SHOT 或配乐要求。

查看导出节点：

```powershell
python <SKILL_DIR>\scripts\mv.py comfy-inspect <SKILL_DIR>\workflows\i2v.api.json
```

映射示例：

```json
{
  "video_model": "minimax-h3",
  "workflow": "i2v.api.json",
  "params": {
    "positive": {"required": true, "targets": [{"class_type": "MiniMaxH3ImageToVideo", "input": "prompt"}]},
    "duration": {"targets": [{"title": "@duration", "input": "value"}]}
  }
}
```

`targets` 默认为 first，使用第一个匹配位置；`mode=all` 写入所有匹配位置。选择器支持 `id`、`title`、`class_type`、`upstream`、`where`；匹配多个节点时须明确 `multi=true`。`required` 表示调用必须提供；`optional` 表示无目标时跳过。Primitive 的 value 连线可自动跟随，但不会强行覆盖计算节点的输出。自定义平铺 H3 API 可以将映射改为 `length`，直接注入已对齐帧数，此时不得同时使用秒数计算连线。

补帧或超分仍可在工作区放 `<kind>.params.json` 与 `<kind>.api.json`，用 `comfy-run` 调用。

## 排查

| 报错 | 处理 |
| --- | --- |
| 拖入 `TypeError: e is not iterable` | 核对是 `.workflow.json`；如正确，查看前端版本、子图支持和错误报告 |
| 项目没有 `workflows/i2v.api.json` | 正常，直接读取技能内置文件；先确认技能包的 `workflows/i2v.api.json` 完整，勿要求用户导出 |
| 视频 API 不是 MiniMax H3 | 更新 API 和工作区覆盖默认映射的旧视频 `.params.json` |
| H3 需 fps=24 / max_frames 不合法 | 同步项目规格；帧数上限须满足 `17k+5`，默认 124 |
| 参数由计算连线提供，无法赋值 | H3 映射 `@duration` 秒数，不映射计算输出；其他参数定位到可写源节点 |
| 匹配到多个 PrimitiveFloat | 给实际秒数输入源节点标记 `@duration` 后重新导出 |
| 模型不在可选列表 / 缺少节点 | 核对模型目录、文件名、ComfyUI 版本及具体 node_errors |
| out of memory | 按用户选择降低 32 倍数尺寸或调整解码配置；不自动换权重 |
| 成功但没有输出 | 确认 SaveVideo 启用且 output_ext 包含实际格式 |
| 等待超时 | 查看队列，必要时调大 timeout_sec，避免盲目重复提交 |
