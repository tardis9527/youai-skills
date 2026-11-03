# ComfyUI 手动填写与执行

本 Skill 交付创作资料，用户自行运行 ComfyUI。无需提供服务地址、认证或 API JSON。以下字段按随 Skill 保留的官方 UI 模板说明；用户的节点界面不同，依据其界面、截图或本地工作流文件核对，不连接服务探测。

## 可选 UI 模板

| 模型 | 可由用户手动导入的文件 | 创作字段 |
| --- | --- | --- |
| MiniMax Music 3 | [minimax-music3.workflow.json](../workflows/minimax-music3.workflow.json) | Caption / Lyrics |
| YuE2 | [yue2.workflow.json](../workflows/yue2.workflow.json) | Style / Lyrics、mode、ABC_planning |

两份模板保留模型加载、采样和音频解码的界面子图，保存端从同一 AUDIO 并联输出 MP3 320k 与 FLAC。它们供用户选择导入，不是必须替换用户现有工作流，也不是已填写本次歌词的成品。模型文件与节点由用户自己的环境准备；本 Skill 不安装或下载。

模板来源（2026-11-02 获取/核对，2026-11-03 增加 MP3 保存分支）：

- https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_minimax_music_3.json
- https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_yue2_text2music.json

## MiniMax Music 3

1. 用户打开自己的 MiniMax Music 3 工作流，或手动导入上表模板，确认模型加载器已选对应模型。
2. 将本次完整 Caption 粘贴到 Caption / caption 控件。保留 `Global Metadata:`、`Vocal Details:`、`Arrangement:` 三部分，不粘贴标题、参数表或控制卡。
3. 将 MiniMax 版本的完整 Lyrics 粘贴到 Lyrics / lyrics 控件。歌词行号只用于资料追踪，不粘贴进模型；纯音乐按 [workflow-contract.md](workflow-contract.md) 的纯标签方案填写。
4. 将参数表的建议上限填入 `max_duration`，确认落在当前界面范围。它不是精确片长。seed 默认沿用现有控件和随机化方式；固定对照时同步文本编码与采样节点的 seed，并记录实际值。其他高级参数沿用现有工作流。
5. 检查保存节点：MP3 选择 `format=mp3`、`quality=320k`；保留另一个 `format=flac` 节点。用户已有导出选择时按其选择设置，不额外强制添加分支。
6. 用户点击运行，完成后在自己的 ComfyUI 输出中保存文件，试听末句、尾奏与歌词完整性。资料中的文件检查继续保持 PENDING，除非用户返回实际结果。

## YuE2

1. 用户打开自己的 YuE2 工作流，或手动导入上表模板，确认对应 checkpoint。
2. 将本次完整 Style 粘贴到 Style / style 控件。使用自然音乐描述，不套 MiniMax 的三个段落标识。
3. 将 YuE2 版本的完整 Lyrics 粘贴到 Lyrics / lyrics 控件；基础标签优先 `[Verse]`、`[Chorus]`。纯音乐可保持 Lyrics 为空，“保持为空”是操作说明，不是模型文本。
4. 建议 `mode=full`、`ABC_planning=开启`，除非用户明确选择其他值。若使用已展开的节点，ABC 与 Music 节点的 style、lyrics、mode 和固定 seed 应一致；官方子图的统一控件通常已维护这些关系，无需用户重复粘贴。`mode=melody` 不等于严格纯音乐。
5. 将参数表的建议上限填入音乐生成节点的 `max_duration`，保留由该节点 seconds 输出驱动 latent 的连接。seed 默认沿用工作流，固定对照时同步 ABC、Music 和 KSampler，其他高级采样参数沿用现有值。
6. 按本次导出表检查 MP3 320k 与 FLAC 保存节点，由用户点击运行并保存文件。试听是否出现非预期人声、截断或缺词；模型不能保证精确片长或严格无人声。

## 交付参数表

每个模型分别给出以下字段；无对应控件的项不要伪装成必填输入：

| 项目 | 值/策略 | 来源与填写位置 |
| --- | --- | --- |
| 目标时长 | 用户本次需求 | 决定歌词密度与结构，不保证生成器精确遵循 |
| `max_duration` | 本次上限/收尾余量建议 | 填对应文本编码或音乐生成控件；界面范围待用户核对 |
| seed | 默认沿用；固定对照时列具体值 | 记录策略，实际执行值由用户生成后补充 |
| YuE2 mode / ABC_planning | 默认 full / 开启 | 仅 YuE2 列此行，用户已选值优先 |
| 高级采样 | 沿用用户工作流 | 不将模板某个版本的默认值当成统一模型要求 |
| MP3 | 默认建议 320k 固定码率 | 在保存节点选择格式与 quality，不写进 Caption/Style |
| FLAC | 默认建议保留母版 | 从原始 AUDIO 保存，不从 MP3 转存冒充母版 |
| 采样率 | 默认沿用源音频 | 未检测前不编造 Hz，保存节点没有独立采样率控件 |

导出解释见 [audio-quality.md](audio-quality.md)。手动执行后，用户若希望继续修改，只需提供听感问题或实际参数；无需提供服务地址或凭据。
