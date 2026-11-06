# YuE2 创作与工作流契约

核实日期：2026-11-02。对应官方 `audio_yue2_text2music.json`，界面子图名称为 Text to Music (YuE2)。字段合法范围以用户节点界面为准；不能从截图重建未知节点的完整连线。

## 创作输入

- **Style**：描述主风格、律动、情绪、人声、乐器、制作听感和结构变化。正文默认中文，语言与歌词分别选择；不是已实测中文优于英文的承诺。无需套用 MiniMax 的三段英文标识。
- **Lyrics**：完整发声原文。基础段落优先使用官方模板展示的 `[Verse]`、`[Chorus]`；官方演示也出现 Intro/Bridge/Outro 和附表演描述的扩展标签，见下方分级说明。不能把 MiniMax 的完整标签清单直接承诺给 YuE2，不把括号里的制作说明当成不会唱出的文字。
- 用户原词完整保留，所有重复段展开。音乐描述与歌词结构一致，不用“同上”占位。
- 纯音乐的空 Lyrics + 无人声 Style 只作文本探索；作者更明确的器乐路线涉及实际 Vocal→Ins 乐谱转换，不是仅清空歌词或开启 ABC。谱面人声休止仍不能保证音频无人声，`mode=melody` 也不等于无歌唱。详见 [instrumental-design.md](instrumental-design.md)。

## 手动填写与节点映射

先按 [vocal-performance.md](vocal-performance.md) 一次询问 Spoken Word / Rap Verse / Ad-lib 的选择，已明确、纯器乐或委托直接出稿时按入口规则跳过。选中后自然 Style 写清相对位置、谁表演、说话感/flow/回应、伴奏变化和衔接；固定台词/衬词仅在授权后写入 Lyrics。自由衬词说明范围，不能保证逐字或背景轨归属。

2026-11-06 补充核对官方演示输入：有 `[Verse 1 – Rap]`、`[Vocal ad-libs]` 等写法，也有 Intro/Bridge/Outro。它们可作有出处的实验输入，不能再笼统说 YuE2 没有特殊人声官方用例；但不构成通用标签字典，不能承诺 `[Rap]`、`[Spoken Word]`、`[Ad-lib]` 是两模型专用且可靠的控制 token。默认仍用基础段落与自然描述，扩展实验需与原版分开记录，效果待试听。

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

### 纯器乐输入与工作流分开核对（2026-11-06 补充）

ABC 与 Music 两处必须同步本次 Style 和空 Lyrics，不能残留旧歌文本。作者乐谱路线是先规划、实际移轨并核验，再将处理后的 ABC 用于生成；常规 `ABC_planning=开启` 只有规划含义，不证明完成移轨。现有图未包含转换时如实说明，不擅加节点、下载或运行作者脚本。

第三方 `MusicLyricsInputs` 或歌词/LRC 导出可能拒绝空词、或拒绝清理标签后为空的文本。按用户提供的图离线核对，必要条件为支持空歌词、可单独保存音频并跳过歌词对齐。不能填假词绕过，不把封装报错解释为模型不支持纯音乐。无人声验收需要完整音频，不能用日志或 ASR 无识别结果替代。

可选手动导入 `../workflows/yue2.workflow.json`，其中保留官方界面子图和 MP3/FLAC 保存分支。完整步骤见 [manual-comfyui.md](manual-comfyui.md)。本 Skill 交付 Style、Lyrics 和参数表，不提交任务或维护 API 映射。用户自有工作流的控件与模板不一致时，依据其截图/工作流文件核对，不把固定节点编号当成通用接口。

## 一手资料

- 官方模板：https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_yue2_text2music.json
- 节点 schema 与 ABC 空值语义：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_yue2.py
- 时长匹配检查：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy/ldm/yue2/model.py
- 特殊人声官方示例输入：https://raw.githubusercontent.com/map-yue2/map-yue2.github.io/main/data/cases.js
- 作者器乐路线：https://github.com/multimodal-art-projection/YuE/blob/main/skills/yue2-music/instrumental/SKILL.md
- 作者生成文档与人声残留限制：https://github.com/multimodal-art-projection/YuE/blob/main/docs/generation.md

以上为实现核对记录，不代表已经在用户的 GPU 服务上完成两模型听感对比。UI 模板随 Skill 内置，手动使用时不依赖 GitHub。
