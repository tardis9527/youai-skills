# MiniMax Music 3 与 ComfyUI 字段契约

核实日期：2026-10-29。适用对象是官方开源 MiniMax Music 3 的 ComfyUI 模板，不是对任何同名第三方 API 节点的通用承诺。普通创作可以使用这份快照；涉及新版本能力、陌生节点或与用户界面不一致的字段时，优先核对其工作流及当前官方资料。无法联网时说明未核实部分，继续整理能够确定的文本。

## 已核实的输入与限制

| 项目 | 官方模板/实现中的行为 | 创作时如何使用 |
| --- | --- | --- |
| 文本编码节点 | `MiniMaxMusic3TextEncode`，可被封装在子图中 | 根据 `type` / `class_type` 和字段识别，不依赖固定节点编号；UI JSON 的子图可能在 `definitions.subgraphs` 中 |
| `caption` | 音乐描述文本 | 推荐分 Global Metadata、Vocal Details、Arrangement 三部分 |
| `lyrics` | 歌词文本及段落标签 | 原语言歌词与音乐说明分开；不要向用户暴露内部特殊 token |
| `max_duration` | 最大时长，单位秒；模型可以提前结束 | 先让用户选择目标长度，再映射到合法上限；约 300 秒是该模型的单次能力边界，不能把它当作推荐或默认片长 |
| `seed` | 随机生成控制；模板可以共享给编码与采样节点 | 根据用户选择做固定对照或新变体；沿用时核对生成后是否自动 randomize/increment，不强制所有创作固定 seed |
| `tiled_decode` | 模板可能以此标题暴露分块音频解码开关 | 仅在相应控件存在且用户关心显存时说明；不保证每个版本字段名相同 |
| 高级采样参数 | 当前编码节点有 `cfg_scale`、`top_k`；模板内部另有采样器 | 默认沿用工作流；不要把编码参数与采样器 CFG 混为一谈 |
| negative prompt | 官方模板用 `ConditioningZeroOut` 产生采样器的 negative conditioning | 这不等于有可粘贴文本的负面提示词框，不凭空输出负面提示词字段 |

默认值并非稳定契约：核实时编码节点 schema 默认 `max_duration=120`，下载模板的实际值为 `60`，模板注释还出现 `120`。因此交付时写用户要求或明确标注的建议值，不宣称所有模板有统一默认时长。

模型对结构、速度、调性和乐器的遵循属于生成控制，不是严格乐谱执行。精确到帧的片长、指定 BPM、严格调性和完整歌词演唱均应通过实际成品确认；需要严格片长时可在生成后剪辑，但不要自动扩大为剪辑任务。

超过约 300 秒的需求应说明当前模型单次限制，再由用户选择缩短或分段后制作；不能静默截断或填写超限参数。参数合法范围最终以用户节点版本为准。

## Caption 的三部分

- `Global Metadata:` 主风格与必要的融合风格、速度感、情绪走向和整体制作质感。用户指定 BPM/调性时保留；未指定时不需要填满所有音乐属性。
- `Vocal Details:` 人声配置、音色、表达力度与和声处理。纯音乐写明无唱词、无哼唱、无背景人声，并指出主旋律乐器。
- `Arrangement:` 按实际段落先后描述进入、退出、层次与过渡，不只列器材或乐器清单。

英文是本技能的默认交付习惯，不是已核实的唯一可用输入语言。歌词使用用户选定语言；不要为写英文 Caption 而翻译中文歌词。

## 段落标签与纯音乐

官方资料列举的标签：

```text
[Intro]
[Verse]
[Pre-Chorus]
[Chorus]
[Post-Chorus]
[Bridge]
[Instrumental]
[Solo]
[Outro]
```

只用作品需要的标签。结构、编曲和演唱指令尽量在 Caption 中表达；避免未经核实的扩展标签、Suno 特定语法、图片权重语法或特殊 token。若原词含 `[Chorus: drums enter]` 等扩展指令，保留其音乐意图到 Arrangement，Lyrics 可规范为 `[Chorus]`，不改写演唱原文。

严格纯音乐默认给出仅含必要段落标签的 Lyrics，例如：

```text
[Intro]
[Instrumental]
[Outro]
```

这是本技能的保守创作建议，不是模型官方定义的“纯音乐开关”，也不保证成品绝无人声。编码层能够接收空字符串；是否让 Lyrics 留空应结合用户模板与实测，不能推广为所有 API 均允许空词。

## 适配其他工作流

确认实际模型、节点类型、文本字段语义、时长单位及范围；不要只凭 `prompt` 这个名字猜它是风格还是歌词。对 API 节点的字数限制、纯音乐标志、模型 ID、认证和费用，必须查其真实 schema/文档，未查明则不输出确定数值或承诺。

只有一个文本框时，先给分开的创作文本，并说明待确认映射；未经证据不要把两块拼进一个框。用户只需要提示词时，不把工作流安装、显卡配置或 API Key 设为前置条件。

## 音频保存与导出字段

本节单独核实于 2026-10-30，依据官方 `comfy_extras/nodes_audio.py`；不改变上文音乐模型字段的核实日期。保存节点不是 Caption 编码节点，是否存在及名称以用户安装版本为准。

| 节点/环节 | 官方实现中的字段与行为 | 使用边界 |
| --- | --- | --- |
| `SaveAudio` | 基础保存实现默认使用 `flac` | 可用于保留生成音频的无损编码副本；不是把低质来源恢复成高质量母带 |
| `SaveAudioAdvanced` | `format` 提供 `flac`、`mp3`、`opus`；选择 `mp3` 后，`quality` 有 `V0`、`128k`、`320k`，默认 `V0` | 按用户选择的格式与质量映射；`V0`、`128k`、`320k` 都可以是有效选择，不强制改默认值为最高档。保存后对照已选目标检查实际文件 |
| `SaveAudioMP3` | `quality` 有 `V0`、`128k`、`320k`，schema 默认 `V0`；该节点在当前源码中标为 deprecated | 只设置用户所选 `quality`，不添加不存在的格式控件；保留旧工作流，不擅自迁移节点 |
| 采样率 | 上述保存节点没有独立的 `sample_rate` 输入；音频数据携带采样率，解码值来自实际 VAE/音频数据 | 允许用户选择沿用来源或指定目标，实际值待文件检测；有转换要求时明确另需支持的重采样环节，不把某一数值设为所有作品最低要求 |

用户版本不同或使用第三方保存节点时，先核对其字段。不能因为某个 Opus 选项也是 `320k` 就认定平台接受 Opus；不能因为选了 FLAC 就推定文件和发布规则全部合格。格式、码率、采样率的解释与只读检查方法见 [audio-quality.md](audio-quality.md)。

2026-10-30 另核对实际编码助手 `comfy_api/latest/_ui.py`：MP3 分支使用 `libmp3lame`；`V0` 走 `qscale` 分支，`320k` 设置 `bit_rate=320000`。它从输入音频读取采样率，不提供可由 Caption 修改的采样率设置。以上是界面操作说明；`SaveAudioAdvanced` 的动态 `format` 输入在 API JSON 中可以是嵌套结构，不能直接把界面里的 `format=mp3` 写成对所有工作流通用的 JSON 补丁。

## 将本次参数选择映射到工作流

先记录用户已选参数，再给实际控件与限制；缺少目标时先引导选择，不能通过节点默认值推断用户意愿。任何示例的时长、码率或采样率都不是默认方案。

| 选择项 | 映射原则 |
| --- | --- |
| 时长与片长精度 | 目标时长决定歌词密度与结构，`max_duration` 仅控制生成上限；用户选精确片长时说明需成品检查，必要的剪辑另按任务范围处理 |
| 听感 | 写入 Caption；不转换成不存在的统一质量开关 |
| 格式与编码质量 | MP3 映射到用户选定的 `quality`，FLAC/Opus 则映射各自支持的格式选项；不在无损格式上套 MP3 码率档位 |
| 采样率 | 用户选沿用时保留来源；明确指定目标时先检测来源与工具能力，只有需要转换才改变 |
| 变体策略 | 用户选复现/对照时固定并核对各 seed 控件；用户选探索新变体时按实际支持方式更换，不混淆策略与具体 seed 数值 |

用户需要文件验证时，读取实际输出的格式、采样率、声道、码率与时长，只对照本次所选方案；没有目标或检测结果时写 `PENDING`。若不一致，先核对实际保存节点、路径和时间，再讨论重导出，不回头强化 Caption 来解决编码问题。平台门槛仅在该发布目标下附加检查。

## 一手资料

- ComfyUI 使用指南：https://docs.comfy.org/tutorials/audio/minimax/minimax-music-3
- 官方工作流：https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_minimax_music_3.json
- 节点实现与参数：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_minimax_music.py
- 文本预处理：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy/ldm/minimax_music/prompt.py
- 模型说明与生成限制：https://github.com/MiniMax-AI/MiniMax-Music3
- 官方 Caption 编写说明：https://github.com/MiniMax-AI/MiniMax-Music3/blob/main/skills/music-caption-rewriter/SKILL.md
- 官方音频保存与解码节点：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_audio.py
- 官方音频保存助手：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_api/latest/_ui.py

这些是查证入口，不是需要安装的依赖。本技能自行完成创作引导与文本整理，不依赖另一个 Caption 技能或其模板库。
