# 歌词、编曲与交付示例

本文件提供创作方法和自写示例，不声明额外模型能力。按当前缺口使用，不把它变成用户必须逐项回答的清单。

## 从感受转成音乐决定

| 用户的说法 | 可以讨论的音乐方向 | 仍应尊重的区别 |
| --- | --- | --- |
| 温暖、治愈 | 柔和触键、木质音色、稀疏节奏、自然空间感 | 治愈可以平静，也可以逐步明亮 |
| 孤独但不绝望 | 主歌留白，后段增加和声或乐器层次 | 失落的故事不必一直小调、悲伤到底 |
| 燃、有力量 | 清晰重拍、推动性低音、高潮扩展音域或编制 | 摇滚、电子与管弦能量感不同 |
| 适合讲解视频 | 稳定律动、克制旋律、较低编曲密度 | 先确认是否需要留出人声解说空间 |
| 中国风 | 选择少量具体民族乐器或旋律语言，再确定现代编曲底色 | 不等于堆满古筝、二胡和戏腔；先确认用户想要的特色 |

把抽象描述落实为少量互相支持的决定。一个主风格、一种主要律动、几件核心乐器通常比多风格堆叠更易形成统一作品；显式要求的融合风格仍应保留。

## 歌词写作

- 先定一个能被记住的核心句，再安排每段的作用：主歌给场景，副歌凝练态度，桥段提供新的理解或转折。
- 多用可以看见或听见的细节；不要用一串“梦想、远方、星辰、力量”代替故事。
- 按自然语气断句，保持相邻乐句大致可唱的密度。押韵服务表达，不牺牲词义或口语顺畅。
- 副歌可以重复核心句，但后一次可以通过少量词义变化推动情感；用户指定逐字重复时照做。
- 在 Lyrics 中展开所有需要演唱的重复段。括号也可能被当成演唱文本，不写“此处鼓进入”“这里用气声”等制作备注。
- 短歌先选一个清晰画面和一次情绪变化；较长歌曲才逐步增加叙事与器乐空间。段落数量、行数都属于创作选择，不能推算成可靠秒数。
- 对用户原词，先解决段落识别与配曲适配。删行、替换措辞或改语言都不应成为未经授权的默认操作。

## 编曲写作

每个段落回答“谁在前景、节奏如何变化、下一段怎样接入”。例如：Intro 用单件乐器引题，Verse 为演唱留白，Chorus 加入低音与更宽的和声，Bridge 减法后回归；这只是一个可选弧线。

Caption 与 Lyrics 必须对应。Lyrics 没有桥段时，不在 Caption 中无故安排一段长桥段；歌词短、时长长时，可明确器乐间奏空间。对纯音乐按主题展开描述，不硬套主歌与副歌。

明确的排除条件可以写进自然语言 Caption，例如“an acoustic arrangement without drums”。它是创作约束，不是已验证的 negative prompt 功能。

## 把反馈改成可控制的音乐描述

先找问题发生的声部与段落，然后写出“保留什么、改变什么、怎样过渡”。不要同时用相反的描述控制同一声部，例如主唱既要求 extremely airy 又要求每字强烈、有力；用户确实希望段落反差时，明确各自作用的段落。

| 反馈 | Caption 应改变的内容 | 保留的内容 |
| --- | --- | --- |
| 主唱发闷、听不清字 | 主唱在前景、自然清晰的咬字；伴奏避开人声密集区、缩短混响尾音 | 原来的人声配置、歌词、整体情绪 |
| 副歌太吵、声部挤在一起 | 副歌用更开放的和弦与少量和声增加能量；减少抢旋律的叠层，控制低频与镲片 | 已确定的风格和律动；不能因此删除用户指定乐器 |
| 整首平、没有推进 | 指定第二段多一个呼应声部、副歌打开音区、桥段减法、末段自然回收等实际事件 | Lyrics 中已有的段落顺序，不凭空加段 |
| 结尾突然截断 | 最后一句结束后留短器乐收束与完整尾音；必要时重新平衡歌词密度与时长上限 | 用户指定歌词，未经授权不删词 |
| MP3 码率与预期不符 | 先核对用户已选质量与用途，再检查实际导出；没有本次门槛时不因某个数字判失败 | 歌词、声线、结构、seed |

质量口号如 `best quality, lossless, 320 kbps, perfect mastering` 不提供可靠的声部关系或编曲变化；删除其中的文件指标，把需要的听感写成具体动作。例如：

```text
Keep the lead vocal close and intelligible, with short room ambience. In each chorus, let the guitar voicings open around the vocal rather than adding competing lead lines. Keep the bass controlled and preserve the contrast between the restrained verse and the fuller chorus.
```

这是写法示例，不能作为所有风格都自动追加的固定尾缀。正式修订需返回受影响 Caption 的完整三部分；纯音乐改用主旋律乐器，lo-fi 等艺术质感继续保留。一次只测试一个问题维度，不把文本缩短或增加质量词说成经过实测的音质提升。

## 示例 A：从模糊想法开始

用户：“想做首送给毕业朋友的歌，但不懂音乐。”

合适的第一轮：

> 先定这首歌留下的感觉：你更想表达不舍、感谢，还是对下一段旅程的期待？歌词想用中文，还是其他语言？

不要在这一轮同时追问 BPM、调性、拍号、种子、混响、全部乐器和完整故事。下一轮根据回答提出听感方案；如果用户已经说了语言，就不要重问。

## 示例 B：已足够明确的短歌需求

用户：“给我一首 60 秒左右的中文暖心歌，轻柔女声、木吉他、不要鼓，主题是下班终于回家。歌词你写，直接给官方模板能用的完整文本。”

直接交付，不继续采访。60 秒来自本例用户要求，不是默认片长；文件质量未指定，可在用户“直接给”的范围内推荐或沿用并注明来源，不把推荐冒充已选。下面展示完整短歌文本，不保证实际生成时长。

Caption：

```text
Global Metadata: A warm acoustic pop miniature for a quiet evening at home. An unhurried, gently flowing pulse supports an emotional movement from end-of-day fatigue toward relief and belonging. Keep the production intimate, organic, and restrained, with soft dynamics and enough space for each phrase. Preserve natural guitar transients and a balanced low end, with clear separation between the lead vocal and accompaniment. The arrangement has no drums or percussion.

Vocal Details: One soft female lead sings in Mandarin with clear diction and a natural, close vocal tone. Keep the verse conversational and understated, then let the chorus open slightly with a warmer sustained delivery. Use restrained room ambience. There are no backing vocals, spoken interjections, or wordless vocal fills.

Arrangement: Intro establishes a simple fingerpicked acoustic-guitar figure. Verse continues with the same guitar pattern and ample space between vocal lines. Chorus gently expands the guitar voicing while a few low piano notes add warmth without increasing rhythmic density. Outro returns to the opening guitar figure and closes with a settled final chord. Maintain a coherent short form with natural transitions and a clear ending.
```

Lyrics：

```text
[Intro]

[Verse]
把今天轻轻放在门外
一盏灯正等着我回来
钥匙转过最后一圈
世界终于慢了下来

[Chorus]
回家啦 风也停下来
热汤把沉默慢慢化开
不用急着变得很厉害
今晚有人等我回来

[Outro]
```

参数建议为 `max_duration=60`，seed 沿用现有值，需要对比时固定。用户未给工作流文件时，说明按官方双文本模板整理。不要给出未经用户节点核实的其他数值。

可按用途建议保留原始生成音频或无损编码副本，文件质量选择见 [audio-quality.md](audio-quality.md)。只有用户选择了具体发布目标，才附相应平台门槛；不把历史截图的规格套入本例 Caption 或导出设置。

## 示例 C：严格纯音乐

用户：“40 秒科普视频配乐，轻快钢琴、拨弦，不能有人声，也不能抢解说。”

跳过歌手与歌词采访。Caption 的 Vocal Details 可写：

```text
Vocal Details: Strictly instrumental. No singing, humming, spoken voice, choir, or vocal samples. A light piano motif carries the melody, with restrained plucked-string responses. Keep the melodic activity sparse enough to leave room for narration added separately.
```

正式交付时还需补全 Global Metadata 和 Arrangement，不能只交这一段。Lyrics 可使用 `[Intro]`、`[Instrumental]`、`[Outro]` 的纯标签文本；参数建议注明 40 秒是上限设置，成品可能提前结束。

## 示例 D：上传失败时的正确输出范围

用户：“这首歌的 MP3 属性是 259 kbps，上传提示至少 320、44.1 kHz，我仍要在这个平台发布，帮我处理不符项。”

只有本例用户明确选择了该发布目标，才按这组门槛检查；不是所有新歌的默认要求。报错若写成 `320KBps`，需说明音频码率通常以 kbps 表示，原文单位不严谨，不能将 KB/s 与 kbps 混用。先说明码率差距，再给保存设置和检查步骤，不重新采访作品方向。输出可采用：

| 检查项 | 目标 | 当前证据 | 状态 |
| --- | --- | --- | --- |
| MP3 音频码率 | 320,000 bit/s | 属性截图显示 259 kbps，低于目标 | FAIL（截图证据，待文件实测） |
| 采样率 | 至少 44,100 Hz | 截图未显示 | PENDING |
| 码率模式 | 本例报错未指定；仅用户另有选择或平台明确要求时约束 | 截图未显示 | 未列为本次强制项 |

接着明确 `SaveAudioAdvanced` 的界面使用 `format=mp3`、`quality=320k`；若是旧 `SaveAudioMP3`，只设置 `quality=320k`。从原始/无损来源保存后检查新文件；采样率不满足时再考虑重采样，命令与限制见 [audio-quality.md](audio-quality.md)。工作流未知时将它们标为“官方节点方案，待映射到实际节点”，不要说已修改用户的工作流或文件。

以上仅是文件规格分诊示例，不代表平台审核或听感已通过；Caption 与 Lyrics 无需因 259 kbps 这一证据而改变。用户另外描述了听感缺陷时，再按相应段落/声部返回完整修订文本。

## 示例 E：先引导选择，再输出参数

主题和歌曲形式已确定，但用户没有给时长与文件用途。下一轮可问：

> 这首歌想做多长，可以给大概范围或具体秒数？文件准备自己试听、分享、后期编辑，还是发布到指定平台？

用户选择“90 秒左右、分享、小一点的 MP3”时，解释当前保存节点的 `128k` 与可变码率 `V0` 等合适选项，让用户选定；不因为“分享”自动采用最高码率。用户随后明确选“128k、采样率沿用、seed 沿用”，最终参数记录可以是：

| 项目 | 本次值/方案 | 来源与限制 |
| --- | --- | --- |
| 目标时长 | 约 90 秒 | 用户已选；不是模型保证片长 |
| `max_duration` | 90 秒 | 据用户目标映射的生成上限，成品可能提前结束 |
| 文件格式/质量 | MP3 / `128k` | 用户已选；官方保存节点方案，实际节点待映射 |
| 采样率 | 沿用源音频 | 用户已选；实际 Hz 待检测，不自动改成 44.1/48 kHz |
| seed | 沿用 | 用户已选；原值与生成后变化方式待工作流核对 |

歌词与 Arrangement 根据本例长度组织；听感沿用用户此前选择，文件验证标为 `PENDING`。不能因 128k 低于历史截图的 320k 而判 FAIL。本例若用户改选 `V0`，保留 VBR 方案，不要求它的平均码率达到固定 320 kbps；若用户改为平台发布，再核对该平台的本次规则。
