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

## 人声选择与纯器乐的前置核对

资料准备时按入口规则问一次 Spoken Word / Rap Verse / Ad-lib 是否需要；这里直接沿用结果，不再次询问。选中的固定台词和衬词须实际出现在 Lyrics，表演/位置/伴奏变化在描述，制作说明不粘进歌词。

无歌词不等于无人声；严格纯器乐按 [instrumental-design.md](instrumental-design.md) 的输入策略和兼容检查处理。用户自定义 `MusicLyricsInputs`、歌词导出/LRC 节点可能拒绝空词或纯标签，要依据用户提供的图离线核对；未知标 pending，拒绝时写明 blocked 与需允许空词/单独保存音频/跳过对齐，不能填“无歌词”或假唱词绕过。这里不自动修改或替换工作流。

## MiniMax Music 3

粘贴前先对照资料中的意图与段落表：人声、禁鼓/无人声、原词与结尾要求要与输入一致。若文档同时有“导演版歌词”和“模型版 Lyrics”，只复制模型版；导演版的方括号情绪/编曲标注只用于人工复盘，并已映射到 Caption/Style。rap/旁白的表演和衔接位于描述中，事件卡、角色标题、行号和研究数据不一起复制；没有已核实标签时不自行补 `[Rap]` 等标记。

1. 用户打开自己的 MiniMax Music 3 工作流，或手动导入上表模板，确认模型加载器已选对应模型。
2. 将本次完整 Caption 粘贴到 Caption / caption 控件。默认英文，保留 `Global Metadata:`、`Vocal Details:`、`Arrangement:` 三部分；用户已选其他描述语言时保留选择。不粘贴中文释义、标题、参数表或控制卡，歌词保持已选原语言。
3. 将 MiniMax 版本的完整 Lyrics 粘贴到 Lyrics / lyrics 控件。歌词行号只用于资料追踪，不粘贴进模型；纯音乐按已核对的 [纯标签或空词方案](workflow-contract.md) 填写，两种均需整条保存链路兼容。
4. 将参数表的建议上限填入 `max_duration`，确认落在当前界面范围。它不是精确片长。seed 默认沿用现有控件和随机化方式；固定对照时同步文本编码与采样节点的 seed，并记录实际值。其他高级参数沿用现有工作流。
5. 检查保存节点：MP3 选择 `format=mp3`、`quality=320k`；保留另一个 `format=flac` 节点。用户已有导出选择时按其选择设置，不额外强制添加分支。
6. 用户在工作流已确认兼容后点击运行，完成后保存文件。歌曲听末句、尾奏与歌词完整性，特殊人声按事件逐项验收；纯器乐要完整试听排查人声。资料中的实际文件检查保持 PENDING，除非用户返回真实结果。

## YuE2

1. 用户打开自己的 YuE2 工作流，或手动导入上表模板，确认对应 checkpoint。
2. 将本次完整 Style 粘贴到 Style / style 控件。默认英文自然音乐描述，用户已选其他描述语言时保留选择；不套 MiniMax 的三个段落标识，不粘贴代码块外的中文释义，不翻译已选原词。
3. 将 YuE2 版本的完整 Lyrics 粘贴到 Lyrics / lyrics 控件；基础标签优先 `[Verse]`、`[Chorus]`。纯音乐在兼容图中保持真正空白，“保持为空”不粘进输入。这只是文本探索；采用作者乐谱路线须另核对实际移轨及处理后的 ABC，不以清空 Lyrics 冒充已实现该路线。
4. 常规图建议 `mode=full`、`ABC_planning=开启`，用户已选或已核对的器乐乐谱路线优先。若使用已展开的节点，ABC 与 Music 节点的 style、lyrics、mode 和固定 seed 应一致，清除两处旧歌残留；官方子图的统一控件通常维护这些关系。`mode=melody` 不是无人声开关，开启规划也不等于完成 Vocal→Ins 转换。
5. 将参数表的建议上限填入音乐生成节点的 `max_duration`，保留由该节点 seconds 输出驱动 latent 的连接。seed 默认沿用工作流，固定对照时同步 ABC、Music 和 KSampler，其他高级采样参数沿用现有值。
6. 按本次导出表和无歌词兼容状态检查保存节点，已确认兼容后由用户手动运行。歌曲查缺词/截断与所选人声事件；纯器乐完整试听非预期人声及尾奏，不能仅凭 ASR 没识别到字判定无人声。模型不能保证精确片长或严格无人声。

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

反馈时优先判断表达目标是否正确，再听核心句/动机、特殊人声进入退出、段落衔接、末句与尾奏。用户口述、实际文件检测与人工试听分别记录，按 [feedback-learning.md](feedback-learning.md) 形成有来源的版本修改；用户未返回证据时不把检查标为通过。
