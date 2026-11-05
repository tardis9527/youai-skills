# 音频质量与手动导出建议

本参考用于整理提示词资料中的导出表，或解释用户手动生成后的文件问题。本 Skill 不连接 ComfyUI、不提交任务、不下载音频，也不自动转码。完整手动操作见 [manual-comfyui.md](manual-comfyui.md)。

## 默认建议与用户选择

默认在资料中列出 **MP3 / 320 kbps 固定码率、保留 FLAC 母版、沿用源采样率**，来源标为“Skill 默认建议，待手动设置”，无需逐项提问。用户或 MV 调用方已有格式、码率、采样率选择时保留。文件大小或指定平台要求与默认建议冲突时，再围绕冲突补充选择。

MP3 是有损编码，不能称为“无损 MP3”。320 kbps 是高码率分享方案，不证明歌曲听感好、歌词完整或一定符合发布规则。FLAC 用于无损编码留存与后期，从原始 AUDIO 保存；把 MP3 转成 FLAC 或提高码率不会恢复丢失的细节，升采样也不会增加原本不存在的信息。

| 方案 | 填写方式与取舍 |
| --- | --- |
| 默认高音质 MP3 | SaveAudioAdvanced 界面选择 format=mp3、quality=320k；检查目标文件，不只改扩展名 |
| 用户要求较小 MP3 | 可解释 128k 或 V0 的取舍；用户明确改选后按所选值填写 |
| 用户选择 V0 | 属于可变码率方案，平均码率会变化，不能要求平均值达到固定 320 kbps |
| FLAC 母版 | 另一个保存节点选择 format=flac，与 MP3 分支连接同一原始 AUDIO |
| 采样率 | 默认沿用来源；保存节点没有独立 sample_rate 控件，未知实际值写未检测，不凭空填写 44.1/48 kHz |
| 指定平台 | 按该平台本次真实要求列目标；不把历史截图中的门槛套用到其他作品 |

2026-11-03 已核对官方 nodes_audio.py 与 _ui.py：SaveAudioAdvanced 支持 flac / mp3 / opus，MP3 质量选项为 V0 / 128k / 320k；320k 通过 libmp3lame 设置 bit_rate=320000，并从输入音频读取采样率。旧 SaveAudioMP3 仅有 quality，没有独立 format 控件，当前源码标为 deprecated。实际用户安装版本不同，以其界面为准。

## 听感写进模型描述

制作听感与文件规格分开。MiniMax 放在 Caption 的 Global Metadata / Vocal Details / Arrangement 中，YuE2 自然写入 Style；只选适合作品的 1–2 个描述，保留用户有意采用的 lo-fi 或失真艺术效果。

歌曲可写：

```text
主唱清晰地处于前景，与伴奏保持明确层次。低频均衡，高频平顺；副歌展开时保留自然动态与演唱空间。
```

纯音乐可写：

```text
主旋律乐器清晰地处于前景，支撑声部各有层次。保留自然起音和受控低频，为最后一段的展开留出空间。
```

不要把 320 kbps、44.1 kHz、24-bit 等文件指标写进 Caption/Style 来代替保存节点设置，也不提供“无损”“4K 音质”“保证过审”等提示词承诺。

## 交付导出表

| 项目 | 目标/策略 | 来源/填写位置 | 实际结果 | 状态 |
| --- | --- | --- | --- | --- |
| 格式/码率 | MP3 / 320 kbps CBR | 默认建议；SaveAudioAdvanced 的 format 与 quality | 未生成、未检测 | PENDING |
| 无损留存 | FLAC | 默认建议；原始 AUDIO 的另一保存分支 | 未生成、未检测 | PENDING |
| 采样率 | 沿用源音频 | 默认建议；无独立保存控件 | 未检测 | PENDING |
| 时长 | 用户目标与上限分别记录 | 创作意图 / max_duration | 未生成 | PENDING |
| 试听 | 末句、尾奏、缺词、非预期失真 | 用户手动生成后检查 | 未试听 | PENDING |

有用户选择时替换上述默认值与来源。目标不是实测值；提示词资料 ready 不需要这些检查通过。不要声称已经保存、解码或试听了尚不存在的音频。

## 用户返回文件或上传报错后

1. 确认用户本次发布目标、选择的规格与明确报错。只有文件规格问题时，不改歌词、声线、结构或 seed。
2. 依据用户提供的本地文件属性或本地文件检查编码、码率、采样率、声道和时长，再对照其保存节点。没有实际文件或证据时保持 PENDING，不从扩展名/体积推断合格。
3. 设置不符时，给用户从原始 AUDIO 或已有无损来源重新导出的填写步骤；不自动打开服务或重跑歌曲。来源只剩低码率 MP3 时说明限制，不把重编码说成修复。
4. 技术规格满足后，歌词完整性、末句、尾奏与听感仍需试听。没有试听证据时明确未核实，不承诺平台通过。

用户明确要求检查本地文件且环境已有 ffprobe 时，可只读查看；没有时说明缺少实测证据，不为整理提示词安装工具：

```powershell
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels,bit_rate:format=format_name,duration,bit_rate -of json 'D:\Music\song.mp3'
```

读取 JSON 中与任务相关的字段。bit_rate 单位为 bit/s，320000 对应 320 kbps；优先音频流码率，不把容器总码率冒充流码率。字段缺失或 N/A 时不猜数值；单个平均值不能证明每帧都是 CBR。文件元数据检查也不能证明听感质量或已经完整解码。

## 一手查证入口

- 音频保存节点：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_audio.py
- 实际编码实现：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_api/latest/_ui.py
- FFprobe 字段与 JSON 输出：https://ffmpeg.org/ffprobe.html
