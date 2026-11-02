# YuE2 创作与工作流契约

核实日期：2026-11-02。对应官方 `audio_yue2_text2music.json`，界面子图名称为 Text to Music (YuE2)。字段合法范围以目标服务 `/object_info` 为准；不能从截图重建未知节点的完整连线。

## 创作输入

- **Style**：描述主风格、律动、情绪、人声、乐器、制作听感和结构变化。正文默认中文，语言与歌词分别选择；不是已实测中文优于英文的承诺。无需套用 MiniMax 的三段英文标识。
- **Lyrics**：完整演唱原文。基础段落优先使用官方模板展示的 `[Verse]`、`[Chorus]`；其他标签需核对当前模型资料或实测，不能把 MiniMax 的完整标签清单直接承诺给 YuE2。不把括号里的制作说明当成不会唱出的文字。
- 用户原词完整保留，所有重复段展开。音乐描述与歌词结构一致，不用“同上”占位。
- 纯音乐可先用空 Lyrics 与明确的无人声 Style 测试，记录为创作策略；没有已核实的“纯音乐”硬开关，不承诺绝无人声。`mode=melody` 也不等于无歌唱。

## 内置 API 映射

| 字段 | 工作流行为 |
| --- | --- |
| checkpoint | `CheckpointLoaderSimple.ckpt_name=yue2_3b_int8_convrot.safetensors`；检查服务器可选文件，名称不符时用完整工作流覆盖，不猜相近模型 |
| Style / Lyrics | 同时注入 `YuE2GenerateABC` 与 `YuE2GenerateMusic` |
| seed | ABC、音乐生成与 KSampler 使用同一记录值；固定值不保证跨版本或硬件逐样本一致 |
| mode | `full` / `melody`，两生成节点同步；默认沿用官方模板 full，不将其包装为音质等级 |
| ABC_planning | 默认开启，音乐节点 abc 连接 ABC 节点；关闭时直接传空字符串并移除 ABC 节点，确保不会仍执行规划 |
| max_duration | 只注入音乐节点；当前源码的范围为 0.04–900 秒，但长提示词可能减少可用时长，也可能提前结束。最终遵循服务器 schema，不能据此保证长歌完整性 |
| latent 秒数 | 来自 `YuE2GenerateMusic` 的 seconds 输出，不直接把目标时长写入 EmptyYuE2LatentAudio，避免 token 与 latent 长度不匹配 |
| 音频与保存 | Checkpoint 提供 MODEL、CLIP、VAE；KSampler → VAEDecodeAudio → SaveAudioAdvanced FLAC；沿用源采样率 |

API 图展开官方子图，以直连去掉仅作透传/预览的界面节点。ABC 关闭时按脚本选择分支；`.workflow.json` 保留官方界面子图，适合导入查看，不能直接发给 `/prompt`。两种表示的 UI 节点编号不作为对外稳定接口，覆盖文件应同时维护自己的 `.params.json`。

## 一手资料

- 官方模板：https://github.com/Comfy-Org/workflow_templates/blob/main/templates/audio_yue2_text2music.json
- 节点 schema 与 ABC 空值语义：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_yue2.py
- 时长匹配检查：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy/ldm/yue2/model.py

以上为实现核对记录，不代表已经在用户的 GPU 服务上完成两模型听感对比。模板下载后随 Skill 内置，运行时不依赖 GitHub。
