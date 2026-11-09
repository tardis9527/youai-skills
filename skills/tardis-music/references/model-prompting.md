# YuE2 / MiniMax Music 3 提示词研究与编写指南

核实日期：2026-11-09。适用于本 Skill 的手动 ComfyUI 文本交付。下列链接指向可变的官方分支；模型、节点或文档更新后需重新核实。未运行模型、未做中英文听感对照；官方写法、作者示例和本 Skill 的编写建议分开标注。

## 研究结论与证据

| 结论 | 证据级别与来源 | 对本 Skill 的影响 |
| --- | --- | --- |
| 本次目标是 MiniMax Music 3；H3 是生成原生音频视频的另一模型 | 官方说明 [S1][S2]；用户已澄清名称混淆 | 不把 H3 的视频分镜、参考素材语法混入歌曲提示词 |
| Music 3 使用音乐描述和歌词两路输入，支持自然短描述及三部分结构化 Caption | 官方模型说明 [S1] | 全曲优先结构化；短需求不为凑篇幅编造参数 |
| Music 3 官方改写指南默认英文；其完整 Caption 建议约 250–450 英文词 | 官方提示词建议 [S3]，不是模型输入下限 | 默认英文输入、中文解释；简单短曲允许更短，用户指定中文则保留 |
| YuE2 官方文档将 Style 用于曲风、配器、人声、演唱语言、速度，Lyrics 用于实际唱词与段落 | 官方生成文档 [S4] | 描述和歌词分开，Style 不套 Music 3 三段格式 |
| YuE2 官方请求示例及展示集使用英文音乐描述，包括非英语演唱案例 | 作者示例 [S5][S6]，不是语言优劣实验 | 英文 Style 作为本 Skill 的默认起点；不称英文为官方强制要求或已证实最佳 |
| YuE2 长文本会压缩可生成音乐的时长预算 | ComfyUI 当前实现 [S7] | 优先简洁、无矛盾的 Style，不照搬长 Caption；不虚构固定字符上限 |
| 描述、标签不能保证逐字、精确速度/结构；ABC 规划也不是无人声开关 | 官方限制及实现 [S1][S4][S7] | 文本检查与音频验收分开，保留现有器乐和工作流兼容性检查 |

Music 3 官方称为开放权重并使用 Community License [S8]；“开源大模型”不能自动等同于无条件商用。此处只辨明发布形态，不替用户的实际用途作许可结论。

## 中文还是英文

将三件事独立决定：**沟通语言**默认中文；**模型音乐描述**默认英文；**Lyrics 与演唱语言**遵循用户选择。英文 Caption/Style 完全可以搭配中文歌词。`Mandopop` 表示曲风，`sung in Mandarin Chinese` 表示演唱语言，两者不互相替代；粤语需要明确 `sung in Cantonese`，不因叫 C-pop 就推断方言。

- Music 3：默认英文依据官方改写指南 [S3]。用户明确要中文 Caption 时照做，不擅改成英文，也不声称中文不支持。
- YuE2：默认英文是与作者示例对齐的工作约定 [S5][S6]；本轮未发现能证明英文优于中文的受控对照。用户选择中文时保留。
- 中文文化词用可理解的音乐描述配合必要名称，如 `guofeng pop with guzheng ornamentation`，再说明古筝做什么。不要把“国风”机械翻成 `Chinese traditional music`，也不自动添加戏腔。
- 英译只转换音乐说明；保留原词、方言字形、实际台词和获授权的衬词。不把中文歌词转拼音，不为英文自然流畅改写受保护原文。
- 交付一个明确标识的模型输入版本。中文释义放代码块外，避免把中英两份全文一并粘贴。同一用户明确要双语对照时才另给标明用途的第二版。

## 从创作意图生成模型输入

仅做提示词改写或语言咨询时直接处理，不重新启动完整歌曲咨询；完整创作仍遵循入口的咨询与来源规则。

1. **保留约束**：提取已确认的曲风、演唱语言、人声范围、主奏、时长与禁止项；识别全局要求和局部事件，未知项不伪称用户要求。
2. **确定主次**：选择主曲风及确有需要的一个融合方向；为关键乐器指定主旋律、和声、低频、节奏或回应职责。这是编写建议，不是模型限制。
3. **把感受变成动作**：把“越来越燃”改成哪段加入鼓贝斯、哪段拉开音区；把“高级”改成实际需要的声部与空间选择。不要仅堆形容词。
4. **对齐段落**：先列实际 Lyrics 段落，描述每段的进入、退出、增强、减法和结尾。器乐用声部事件代替唱词；不添加歌词中没有且未获授权的新段落。
5. **分别编码**：Music 3 分三部分展开；YuE2 压缩为自然 Style，保留辨识点与关键变化。两版表达同一作品，不要求字数相同。
6. **检查一致性**：描述、歌词、事件卡、控制卡的语言、人声和结构一致；移除重述、互斥指令、原词引用和无关参数。原词不进入 Caption 的故事摘要。

需要参考风格时，可沿 [S9] 官方曲风路由查一个主类，必要时补一个融合类；只读最相关的少量示例。不下载或扫描整个模板库，不复制模板句子、精确 BPM、调号、人声或原词。参考资料不覆盖用户选择。

## 常用中英关键词

以下是本 Skill 整理的音乐术语与组合素材，**不是官方特殊 token、按频率排序的统计或遵循率保证**。按作品挑选并写成有关系的自然句，不把整表粘贴。精确 BPM/调性仅在已知、已选或明确委托且有理由时使用。

| 维度 | 可选词与中文含义 | 如何用 |
| --- | --- | --- |
| 流行与原声 | `Mandopop` 华语流行；`acoustic pop` 原声流行；`indie folk` 独立民谣；`singer-songwriter` 唱作取向 | 主身份配一个明确制作取向，不用情绪词替代曲风 |
| 节奏与电子 | `contemporary R&B` 当代 R&B；`neo-soul` 新灵魂；`synth-pop` 合成器流行；`lo-fi hip-hop` 低保真嘻哈；`ambient` 氛围 | ambient 不自动等于无旋律/无人声，lo-fi 不自动等于文件低码率 |
| 其他风格 | `indie rock` 独立摇滚；`cinematic orchestral` 电影管弦；`guofeng pop` 国风流行；`bossa nova` 波萨诺瓦 | 国风说明民族乐器与流行主体的关系；电影感不自动加合唱 |
| 速度与律动 | `slow, unhurried` 舒缓从容；`mid-tempo` 中速；`laid-back groove` 松弛律动；`syncopated` 切分；`straight eighths` 平直八分；`swing feel` 摇摆感；`half-time feel` 半拍感 | 速度、节拍、节奏型分开；半拍感不必改变标称 BPM |
| 情绪与发展 | `intimate` 亲近；`wistful` 惆怅怀想；`bittersweet` 苦乐交织；`restrained` 克制；`uplifting` 昂扬；`gradual build` 渐进增强 | 将“主歌克制→副歌舒展”落实到表演和配器 |
| 人声配置 | `solo female/male lead` 女/男声独唱；`duet` 对唱；`unison backing vocals` 齐唱衬底；`layered harmonies` 叠层和声 | 只加入已选声部；不把“宽广”自动变成多人合唱 |
| 音色与唱法 | `breathy` 气声；`warm low register` 温暖低音区；`clear diction` 清晰咬字；`conversational delivery` 交谈式演唱；`restrained vibrato` 克制颤音 | 气声和咬字可兼容，但避免同句要求极轻耳语及强力嘶吼 |
| 特殊表演 | `spoken-word passage` 念白段；`rhythmic rap verse` 节奏说唱主歌；`call-and-response` 呼应；`brief wordless ad-libs` 短无词衬唱 | 写相对位置、内容权限和接回方式；不是 `[Rap]` 等标签生效保证 |
| 主奏与和声 | `fingerpicked acoustic guitar` 指弹木吉他；`felt piano` 毡音钢琴；`guzheng` 古筝；`erhu` 二胡；`warm synth pad` 温暖合成器铺底 | 例如主奏负责动机、钢琴只在句间回应，避免每件乐器都抢旋律 |
| 节奏声部 | `rounded bass` 圆润贝斯；`brushed drums` 鼓刷；`soft kick` 轻底鼓；`tight snare` 紧实军鼓；`four-on-the-floor` 四拍底鼓 | 禁鼓作品不因轻柔氛围就自动加鼓刷；贝斯进入/退出写明段落 |
| 段落动作 | `sparse verse` 稀疏主歌；`wider chorus` 展开的副歌；`strip back in the bridge` 桥段做减法；`return to the opening motif` 回归开场动机 | 用动词连接段落，比仅列 verse/chorus 更有指向 |
| 收尾 | `resolved final chord` 稳定解决的终止和弦；`natural decay` 自然衰减；`short instrumental outro` 短器乐尾奏；`seamless loop` 无缝循环意图 | 完整终止与无缝循环按用途择一；循环点、尾音长度仍待音频核实 |
| 制作听感 | `close, dry lead vocal` 贴近少混响主唱；`restrained room reverb` 克制室内混响；`warm, balanced mix` 温暖均衡混音；`space between phrases` 乐句留白 | 听感词不等于编码设置；MP3、FLAC、采样率放参数/导出表 |
| 严格器乐 | `instrumental only` 纯器乐；`piano carries the lead melody` 钢琴承载主旋律；`no singing, humming, spoken voice or vocal samples` 排除各类人声 | 先写正向声部职责再写必要排除；无词人声获允许时不套此禁令 |

## 两模型怎样写得不同

### MiniMax Music 3

保留 `Global Metadata:`、`Vocal Details:`、`Arrangement:` 的现有 ComfyUI 写法。它们是可读的描述组织方式，不是必须逐字符一致的魔法 token。详细字段见 [workflow-contract.md](workflow-contract.md)。

- 全局：主风格、律动、整体情绪与制作方向；不要把歌词内容写成情节梗概。
- 人声：演唱语言、已选配置、音色/表演和必要和声；纯器乐改写主旋律承担者。
- 编曲：按真实段落讲声部生命周期和过渡，不为满足完整歌模板增加不需要的桥段/说唱。
- 官方完整改写建议的篇幅是参考。短曲只需表达有效变化；具体输入预算取决于实际接口，不将 API token 数换算成通用字数。

### YuE2

先写演唱语言与主风格，再写人声、核心乐器、律动、旋律意图和少量段落变化；完整的自然短段落或清楚的逗号短语均可。先保证信息无歧义，不追求某一固定长度。详细字段见 [yue2-guide.md](yue2-guide.md)。

- 与 Music 3 共用创作意图，重新组织 Style，不整段复制三部分 Caption。
- 写“主歌近似交谈，副歌旋律舒展”这类可理解意图；不要把精确音符、换轨操作或采样参数写成风格口号。
- 更换歌词/语言可能改变 ABC 规划；展开图时同步 ABC 与 Music 的 Style/Lyrics。规划开关和采样参数另列。
- 若用户已经提供并要求保留 ABC，文本不得承诺仅改 Style 就能重写已固定的旋律/和声。指出需核对谱面与目标是否一致；本 Skill 不自动编辑或提交乐谱。

## 原创组合示例

以下为本 Skill 编写的示意，不是官方模板、实测成功配方或本次用户创作选择。完整同曲双模型示例及中文歌词见 [prompt-document-template.md](prompt-document-template.md)。

“治愈、空灵、高级、电影感、洗脑”可以先澄清/推荐为：“原声流行，贴近的普通话主唱；指弹吉他承载短动机，钢琴只做句间回应；主歌克制，副歌略展开；最后回到开场动机”。每个形容词都落到可检查的听感或音乐动作。

**仅第一主歌说唱，副歌回旋律演唱**，前提是用户已选表演且歌词内容获授权：

```text
The first verse uses a clear, conversational Mandarin rap delivery with space for breaths. The chorus returns to a sustained, melodic vocal line. Keep the backing sparse under the rap; add the selected rhythm section as the chorus opens.
```

这是一段局部描述素材：Music 3 将唱法归 Vocal Details、段落变化归 Arrangement；YuE2 合并到 Style。不是要求把全部文字放入 Lyrics，也不自动授权新增说唱歌词。

**阅读用严格纯器乐**，以用户已选钢琴和弦乐为例：

```text
A quiet instrumental chamber piece for reading. A soft piano carries a recurring melody; low strings provide a slow harmonic bed without competing for attention. Begin with piano alone, add the strings gradually, then return to the opening motif and a gently resolved ending. No singing, humming, spoken voice or vocal samples.
```

该段可作 YuE2 Style 起点；Music 3 应分配到三部分。它不证明纯器乐输入/保存链路已兼容，更不代表完成 YuE2 的 Vocal→Ins 移轨；仍按 [instrumental-design.md](instrumental-design.md) 核对。

## 语言与写法的最小验证

只在用户愿意手动试听时建议对照，不把抽卡作为交付前置条件：

1. 同一模型/版本/工作流、相同歌词/标签、时长上限和参数，固定并记录相关 seed；只将音乐描述做语义等价的中文/英文两版。避免翻译时额外加乐器、BPM 或和声。
2. YuE2 明确比较哪一层：重做 ABC 比较“语言对规划及音频的整体影响”；固定同一份 ABC 比较“相同乐谱下描述对渲染的影响”。两种结果不能混为一谈。Style/Lyrics 在图中对应位置保持一致，实际 ABC 单独记录。
3. 对比咬字/漏词、指定表演、乐器与段落变化、主旋律/Hook、尾奏；按本首目标判断。单个 seed 不足以形成普遍语言结论，多 seed 复核由用户决定。
4. 记录描述语言、歌词语言、模型/checkpoint 与节点版本、完整输入、seed、规划开关、ABC 是否固定、输出路径和反馈来源。没有实际音频时结论为 `pending`，只存文本决定。

将条件性结果写入 [feedback-learning.md](feedback-learning.md) 的作品/经验记录，保留失败与反例，不从一次偏好生成“中文永远差/英文永远好”的规则。

## 一手资料索引

- [S1] MiniMax Music 3 模型说明、双输入与限制：https://github.com/MiniMax-AI/MiniMax-Music3/blob/main/README.md
- [S2] MiniMax H3 模型说明：https://github.com/MiniMax-AI/MiniMax-H3/blob/main/README.md
- [S3] Music 3 官方 Caption 改写 Skill，特别是 Output Contract：https://github.com/MiniMax-AI/MiniMax-Music3/blob/main/skills/music-caption-rewriter/SKILL.md
- [S4] YuE2 官方生成文档：https://github.com/multimodal-art-projection/YuE/blob/main/docs/generation.md
- [S5] YuE2 官方请求示例：https://github.com/multimodal-art-projection/YuE/blob/main/examples/song.json
- [S6] YuE2 作者展示集输入（含非英语歌词）：https://github.com/map-yue2/map-yue2.github.io/blob/main/data/cases.js
- [S7] ComfyUI YuE2 当前节点实现：https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_yue2.py
- [S8] ComfyUI Music 3 指南与权重许可说明：https://docs.comfy.org/tutorials/audio/minimax/minimax-music-3
- [S9] Music 3 官方曲风路由：https://github.com/MiniMax-AI/MiniMax-Music3/blob/main/skills/music-caption-rewriter/references/genre-router.md
