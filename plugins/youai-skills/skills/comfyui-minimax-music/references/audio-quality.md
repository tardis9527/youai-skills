# 制作听感、文件规格与上传检查

用户提到高音质、发布、码率、采样率或上传失败时读取本文件。只要求创作文本时，不把文件检查变成完成提示词的前置条件，也不自动执行生成、转码、上传或联系平台。

## 需求来源与适用范围

用户于 2026-10-30 提供的截图提示上传失败，文字为“音质不低于320KBps，采样率不低于44.1KHz”。截图未显示平台名称，也没有列出格式、位深、声道或响度要求；不能据此补出某个平台的完整发布规范。

音频码率通常以 kbps（千比特/秒）表示；KB/s 表示千字节/秒，二者不能混用。本技能将 320 kbps 作为这张截图对应的常见音频导出目标，并明确原文单位不严谨、平台含义待核对；如果平台确实要求 320 KB/s，就不能声称 320 kbps 已达标。44.1 kHz 对应 44,100 Hz。用户提供了更明确或更新的规则时，以其规则为准。

截图里的“发布至电台”和联系入口仅是平台文案，不代表用户要求改变发布渠道或代为联系。不要默认执行这些动作。

## 听感写进 Caption

把具体听感自然写入 `Global Metadata` 或 `Vocal Details`，与编制和情绪一致。下面是可选择的自写片段，不是必须整段附加的咒语：

歌曲中强调主唱与伴奏的清晰关系：

```text
Keep the lead vocal present and intelligible, with clear separation from the accompaniment. Maintain a balanced low end, smooth high frequencies, and natural dynamics as the chorus opens up.
```

纯音乐中强调声部、瞬态与高潮余量：

```text
Give the main melodic instrument a clear foreground position, with distinct supporting layers and controlled low frequencies. Preserve natural transients and leave room for the final build to expand.
```

有意采用 lo-fi 或磁带质感时保留风格：

```text
Retain the intended tape warmth and gentle background hiss, while keeping the melody intelligible and the bass from masking the other instruments.
```

只选符合当前作品的 1–2 句；人声、音色、空间和动态描述不应相互冲突。不要加入 `320 kbps`、`44.1 kHz`、`24-bit` 等文件指标来代替编码设置，不用“无损”“4K 音质”“保证过审”等无法由文本保证的承诺，也不一律增加立体声宽度、极高响度或强限制处理。

## 导出目标单独交付

生成参数与文件保存设置分开列出。以下仅针对这张截图，在平台格式规则尚未核实时作为建议，不表示实际文件已经合格：

| 项目 | 建议与条件 | 需要验证什么 |
| --- | --- | --- |
| 留存文件 | 保留原始生成文件；可从生成的音频数据保存 FLAC 等无损编码副本 | 无损编码只保留输入数据，不恢复此前丢失的声音细节 |
| MP3 发布副本 | 平台接受 MP3 时，目标 320 kbps；若编码器提供模式选择，采用固定码率 CBR | 实际编码格式和码率；`V0` 属于可变码率质量档位，不等于固定 320 kbps |
| 采样率 | 目标至少 44,100 Hz；原生 48,000 Hz 等更高且被平台支持的值可以保留 | 实际音频流采样率；不能仅根据 Caption 或文件名推断 |
| 无损格式发布 | 仅在平台明确支持时考虑 WAV/FLAC | 具体格式、编码、位深等规则；不要把有损 MP3 的 320 kbps 档位套成无损文件的统一质量标准 |
| 验证状态 | 没有成品就写“导出目标，文件待检查”；有检测结果再给结论 | 不把建议值写成检测值，不承诺一定通过上传审核 |

实际节点映射见 [workflow-contract.md](workflow-contract.md) 的“音频保存与导出字段”。未知节点时仅给目标值，标注“具体保存控件待映射”，不要凭空添加 `sample_rate`、`bit_depth` 等控件。模型原生输出采样率也不能根据保存节点的格式选项推定。

优先从生成时的原始音频数据或可用无损来源制作发布副本，避免多次有损编码。把低码率 MP3 转成 320 kbps 或 FLAC，不会恢复已经丢失的细节；升采样也不会恢复来源中不存在的高频信息。若仅存低质文件，说明来源限制与重新取得原始文件的选择，不把格式转换说成音质修复，也不自行生成新曲。

## 上传失败时的最短检查路径

1. 先提取报错中明确的门槛，核对平台是否接受当前格式。已有文件或工作流资料能回答时，不重复采访作品方向；必要时只索取保存节点和文件属性等最少信息。
2. 检查实际文件的音频编码、采样率和码率，再核对保存节点。上传失败本身不能证明编曲或歌词有问题。
3. 若只是导出设置不符，优先从原始来源重新导出；若规格已满足，继续查看平台的具体错误，不随意改歌词、seed 或声音风格。
4. 技术规格满足后，仍需试听主唱/主旋律清晰度、非预期失真、爆音、突兀截断与过长静音等问题。未拿到或未试听音频时明确该部分未验证；用户保留的艺术效果不按缺陷处理。

用户提供本地音频并需要检查时，可使用已安装的 `ffprobe` 只读查看；未安装时，可让用户查看播放器/编辑器中的编码属性，不为给提示词自动安装工具。PowerShell 示例：

```powershell
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels,bit_rate:format=format_name,duration,bit_rate -of json 'D:\Music\song.mp3'
```

替换为实际路径，读取 JSON，不能仅看扩展名或文件体积。`sample_rate` 的单位是 Hz，`bit_rate` 的单位是 bit/s；例如 320,000 bit/s 对应 320 kbps。容器总码率与音频流码率可能不同，优先查看音频流；若字段缺失或为 `N/A`，标为无法据此判断，不能自动判失败或用容器总码率冒充音频码率。接近目标值的舍入差异结合编码设置核实，不仅凭一个显示数字作过严断言。

检查元数据只能确认文件技术信息，不能证明听感、原始来源质量或平台审核结果。只返回与任务有关的检测值，避免输出文件中无关的个人标签。

## 一手查证入口

本文件的听感措辞是创作建议；节点信息与工具语法可通过以下官方资料复核。平台要求来自用户截图，未作为通用官方标准发布。

- ComfyUI 音频解码与保存节点：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_audio.py
- FFprobe 的 `show_entries`、`select_streams` 与 JSON 输出：https://ffmpeg.org/ffprobe.html
- FFmpeg 编码选项：https://ffmpeg.org/ffmpeg-codecs.html
