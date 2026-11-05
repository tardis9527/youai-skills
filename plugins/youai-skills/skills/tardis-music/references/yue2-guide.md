# YuE2 创作与工作流契约

核实日期：2026-11-02。对应官方 `audio_yue2_text2music.json`，界面子图名称为 Text to Music (YuE2)。字段合法范围以用户节点界面为准；不能从截图重建未知节点的完整连线。

## 创作输入

- **Style**：描述主风格、律动、情绪、人声、乐器、制作听感和结构变化。正文默认中文，语言与歌词分别选择；不是已实测中文优于英文的承诺。无需套用 MiniMax 的三段英文标识。
- **Lyrics**：完整演唱原文。基础段落优先使用官方模板展示的 `[Verse]`、`[Chorus]`；其他标签需核对当前模型资料或实测，不能把 MiniMax 的完整标签清单直接承诺给 YuE2。不把括号里的制作说明当成不会唱出的文字。
- 用户原词完整保留，所有重复段展开。音乐描述与歌词结构一致，不用“同上”占位。
- 纯音乐可先用空 Lyrics 与明确的无人声 Style 测试，记录为创作策略；没有已核实的“纯音乐”硬开关，不承诺绝无人声。`mode=melody` 也不等于无歌唱。

## 手动填写与节点映射

词曲蓝图中的特殊表演按 [vocal-performance.md](vocal-performance.md) 写入自然 Style，明确相对段落、叙事目的、表演、伴奏与衔接；获授权台词才放 Lyrics。没有本模型依据时不添加 `[Rap]`、`[Spoken]`、`[Whisper]`，也不把 MiniMax 的 `[Bridge]` 等完整清单照搬。无法确定映射时保留计划并注明待试听，不保证精确时间或逐句切换。全局约束、局部事件和 Lyrics 结构保持一致。

| 字段 | 工作流行为 |
| --- | --- |
| checkpoint | `CheckpointLoaderSimple.ckpt_name=yue2_3b_int8_convrot.safetensors`；由用户确认界面中已选对应 checkpoint；名称不符时标注待核对，不自动切换或下载 |
| Style / Lyrics | 粘贴到官方子图的 Style / Lyrics 控件；若节点已展开，ABC 与 Music 两处的 style / lyrics 应一致 |
| seed | 沿用工作流现有设置；固定对照时提醒用户将 ABC、音乐生成与 KSampler 同步为同一记录值；固定值不保证跨版本或硬件逐样本一致 |
| mode | `full` / `melody`，两生成节点同步；默认沿用官方模板 full，不将其包装为音质等级 |
| ABC_planning | 建议保持官方子图 ABC_planning 开启；用户明确关闭时通过界面开关设置，保留工作流现有分支，不由本 Skill 改图或调用脚本 |
| max_duration | 填写音乐生成的 max_duration 控件；2026-11-02 源码快照的范围为 0.04–900 秒，但长提示词可能减少可用时长，也可能提前结束。最终遵循用户节点界面的合法范围，不能据此保证长歌完整性 |
| latent 秒数 | 来自 `YuE2GenerateMusic` 的 seconds 输出，不直接把目标时长写入 EmptyYuE2LatentAudio，避免 token 与 latent 长度不匹配 |
| 音频与保存 | Checkpoint 提供 MODEL、CLIP、VAE；KSampler → VAEDecodeAudio → 两个并联 SaveAudioAdvanced（MP3 320k + FLAC 母版）；沿用源采样率 |

可选手动导入 `../workflows/yue2.workflow.json`，其中保留官方界面子图和 MP3/FLAC 保存分支。完整步骤见 [manual-comfyui.md](manual-comfyui.md)。本 Skill 交付 Style、Lyrics 和参数表，不提交任务或维护 API 映射。用户自有工作流的控件与模板不一致时，依据其截图/工作流文件核对，不把固定节点编号当成通用接口。

## 一手资料

- 官方模板：https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_yue2_text2music.json
- 节点 schema 与 ABC 空值语义：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_yue2.py
- 时长匹配检查：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy/ldm/yue2/model.py

以上为实现核对记录，不代表已经在用户的 GPU 服务上完成两模型听感对比。UI 模板随 Skill 内置，手动使用时不依赖 GitHub。
