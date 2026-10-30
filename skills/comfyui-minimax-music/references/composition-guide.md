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

## 示例 A：从模糊想法开始

用户：“想做首送给毕业朋友的歌，但不懂音乐。”

合适的第一轮：

> 先定这首歌留下的感觉：你更想表达不舍、感谢，还是对下一段旅程的期待？歌词想用中文，还是其他语言？

不要在这一轮同时追问 BPM、调性、拍号、种子、混响、全部乐器和完整故事。下一轮根据回答提出听感方案；如果用户已经说了语言，就不要重问。

## 示例 B：已足够明确的短歌需求

用户：“给我一首 60 秒左右的中文暖心歌，轻柔女声、木吉他、不要鼓，主题是下班终于回家。歌词你写，直接给官方模板能用的完整文本。”

直接交付，不继续采访。下面展示一份完整的短歌文本；60 秒只是生成目标，不是保证时长。

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

可另附一句“建议保留原始生成音频及无损编码副本，发布版按平台要求导出”。这只是文件保存建议，不能据此声称成品已通过音质检查。涉及截图中的上传要求时，按 [audio-quality.md](audio-quality.md) 单列导出目标，不把数字写入上面的 Caption。

## 示例 C：严格纯音乐

用户：“40 秒科普视频配乐，轻快钢琴、拨弦，不能有人声，也不能抢解说。”

跳过歌手与歌词采访。Caption 的 Vocal Details 可写：

```text
Vocal Details: Strictly instrumental. No singing, humming, spoken voice, choir, or vocal samples. A light piano motif carries the melody, with restrained plucked-string responses. Keep the melodic activity sparse enough to leave room for narration added separately.
```

正式交付时还需补全 Global Metadata 和 Arrangement，不能只交这一段。Lyrics 可使用 `[Intro]`、`[Instrumental]`、`[Outro]` 的纯标签文本；参数建议注明 40 秒是上限设置，成品可能提前结束。
