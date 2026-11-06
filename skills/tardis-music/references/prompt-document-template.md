# 音乐创作提示词 Markdown 文档规范

手动执行约定：单模型文档的 `model` 填 `MiniMax Music 3` 或 `YuE2`；双模型文档用 `models` 数组，共用创作简报并分别列完整模型输入与参数。MiniMax 使用 Caption 三部分，YuE2 使用独立 Style，并按 [yue2-guide.md](yue2-guide.md) 组织文本，不混用模型标签。交付资料时固定记录 `execution: manual_by_user`、`audio_status: not_generated`；`ready` 只代表资料就绪，不要求 run.json 或音频文件。用户实际执行并返回结果后再更新音频状态与证据。

完整创作默认落地一份 UTF-8 Markdown 文档，便于复制、复用与修订。它记录创作输入，不代替 ComfyUI workflow JSON，也不表示已经生成或检测音频。

## 路径与版本规则

- 优先使用用户指定的目录；否则以当前项目或工作目录为根，保存到 `output/music-prompts/`。目录不存在时创建，不写入技能安装目录。
- 默认文件名为 `YYYY-MM-DD-安全化标题.md`，日期取用户本地当前日期，正文保留原始标题。文件名将 `\ / : * ? " < > |` 和控制字符替换为 `-`，合并连续空白并去掉末尾空格/句点；结果为空时用 `music-prompt`。最终文件名需符合运行环境限制。
- 先检查文件是否存在。同名时选取下一个可用的 `-v2.md`、`-v3.md` 等后缀，避免不同作品经安全化后发生碰撞或覆盖旧稿。修订已有文档沿用其基础文件名，版本号按已有记录递增；不重复叠加 `-v2-v3`。
- 新文件的 `version` 为 `1`，修订时递增并保留原版记录，追加本次改动。只有用户明确要求更新/覆盖指定原文件时才原地写入。
- `status` 使用 `draft` 或 `ready`：尚有未选项目或暂定标题时是 `draft`；标题及必需选择已解决、创作文本自查通过时是 `ready`。修订稿同样按完成情况判断，版本号独立记录。`ready` 仅表示提示词文档可交付，音频未检测仍为 `PENDING`。
- 保存后重新读取文件，核对元数据和各模型的描述/歌词文本。回复中提供实际绝对路径链接、状态与未核实项。无文件工具或写入失败时，返回完整 Markdown、建议文件名并说明尚未保存。

## 内容规范

推荐顺序：元数据 → 作品名称 → Music Brief（意图、成功标准、人设与假设）→ 共用词曲蓝图/控制卡/情绪曲线/段落与歌词时间线 → MiniMax Music 3（Caption、Lyrics、参数、导出、手动填写步骤）→ YuE2（Style、Lyrics、参数、导出、手动填写步骤）→ 平台策略/反馈记录/MV 交接（按需）→ 自查状态 → 版本与结案记录。指定单模型只保留该章；局部任务不强加完整结构。

- YAML front matter 至少包含 `title`、`type`（`song` 或 `instrumental`）、`model` 或 `models`、`execution`、`audio_status`、`status`、`version`、`created_at`、`updated_at`、`title_source`。日期按当前用户日期填写；修订保留创建日期，更新修改日期。字符串正确引用/转义，尤其标题中的冒号、引号、`#` 和换行；有 YAML 序列化工具时优先使用。
- 创作简报记录用途与音乐角色、受众、希望感到/记住/行动的结果、创作命题与成功标准；以及目标时长、情绪弧线、两种文本语言、歌词来源与权限、人声/主旋律、保留/避免项。区分 user_explicit、inferred、recommended、unknown，不能把推荐写成用户已选；纯音乐歌词项记“不适用”。
- 分开记录 `lyrics_policy`（none/provided/original）与 `vocal_policy`（none/wordless_only/with_words），未明确用 unknown；有无歌词不替代人声范围。保留一次特殊人声选择的 `vocal_choice.status/elements/source`，不用空事件数组冒充用户已明确拒绝。含无词人声的作品不能标为严格纯器乐；原 `type=song/instrumental` 分类保持，允许无词人声的作品在此归 song 并写清政策。
- 词曲蓝图记录所选路径、叙述视角、具体素材、主要 Hook、旋律/节奏/和声意图、声部职责。段落表记录 section_id、功能、前景/表演、声部事件、衔接与收尾；有特殊人声时另列 vocal_events 的目的、内容授权、相对位置与映射限制。普通作品保持简短，不为填表编造专业参数。
- 创作控制卡记录 `work_id`、`version`、`take_id`、目标时长与生成上限，以及风格、人声、节奏、和声四组控制项。控制项和事件必须标明 `planned`、`measured`、`verified` 或 `pending`，不能用预期值冒充实际音频测量。
- 短曲情绪曲线可按约 15 秒粒度记录时间、故事情绪、表演、能量（1–5）和叙事功能，长曲按段落与关键事件补点；目标变化后调整。注明 planned，不把曲线写成精确乐谱或成品切点。
- 歌词时间线为每句设置稳定 section_id / line_id、原文与作用；预计位置放 planned_position，未测的实际 start_sec、end_sec、beat_anchor 为 null。纯音乐记录器乐事件；不为了编号改写原文或重排已经稳定的 ID。
- MiniMax Caption/Lyrics、YuE2 Style/Lyrics 分别放完整 `text` 代码块，与本轮交付逐字一致。双模型即使歌词相同也各给完整歌词，不用“同上”“略”或省略号代替。MiniMax 保留三部分标识，YuE2 自然描述 Style，各用本模型的标签。YuE2 纯音乐 Lyrics 留空时在代码块外说明“保持为空”，不把说明粘贴进输入。
- 生成参数记录所选策略/数值、来源与真实控件的映射状态，导出表单独记录格式、质量与采样率。每项说明用户已选、明确沿用、Skill 默认建议或委托后推荐；默认 MP3 320k + FLAC 母版、源采样率与沿用工作流 seed 不必逐项提问。关键创作选择尚未解决时为 `draft`；用户界面尚未核对可标“待映射”，实际音频值标“未生成/未检测”，不阻塞资料 ready。
- 导出表区分目标、来源、实测结果与 `PASS` / `FAIL` / `PENDING`；沿用采样率时不编造 Hz。平台未指定时写“不适用”，不额外要求平台检查。只有实际完成的自查才能勾选。
- 只保存创作所需内容，不复制 API Key、令牌、凭据、签名 URL 或不必要的个人信息。

特殊人声按 [vocal-performance.md](vocal-performance.md) 附内容来源、固定文本/自由范围、相对位置、表演、伴奏变化和衔接。固定台词/衬词在 Lyrics 写全；自由即兴不伪造确定台词，记 `text=null` 与范围；制作说明不进 Lyrics。两模型分别完整返回，不用模块示例替代实际交付。

纯器乐按 [instrumental-design.md](instrumental-design.md) 记录器乐主奏与声部、输入策略（纯标签/空歌词/已核对 ABC 路线）及每个模型的 `workflow_compatibility=compatible/pending/blocked`、检查依据和待处理节点。资料 ready 与工作流可运行分开；如被歌词导出封装阻塞，显式说明，不虚构已跑通。没有图不推定兼容，只有已核对的实际移轨才能写完成 ABC 器乐路线。

Music Brief 复用 [discovery-flow.md](discovery-flow.md) 的精简模板，保留 `persona_id`、节奏、当前阶段、选择来源和关键假设，不另起重复采访；没有人设则不填虚构身份。质量检查按 [quality-review.md](quality-review.md) 区分文本 PASS 与音频 PENDING。

平台章按 [platform-patterns.md](platform-patterns.md) 记录来源/日期/窗口、观察、策略、适用限制和待验证结果，不把营销数据粘贴进模型描述。真实试听/发布反馈没有则省略；每次完整交稿仍按 [feedback-learning.md](feedback-learning.md) 保存轻量结案和 `text_review`，注明项目学习路径及实际写入的记录 ID，不初始化虚假偏好。长期偏好只保存用户明确未来适用的选择。

## 创作控制卡与时间线计划模板

以下区块可直接复制到文档中。若尚未生成音频，时间戳和试听结果保持 `null` 或 `PENDING`。

```yaml
work_id: "安全化作品名"
version: 1
take_id: null
model: "MiniMax Music 3"
target_duration_sec: 60
max_duration_sec: 90
metadata_status: planned
lyrics_policy: unknown
vocal_policy: unknown
workflow_compatibility: pending
vocal_choice:
  status: not_asked
  elements: []
  source: unknown
intent:
  use_case: ""
  music_role: ""
  audience: ""
  desired_response: ""
  success_criteria: []
  source: recommended
blueprint:
  route: ""
  premise: ""
  perspective: ""
  lyric_hook: null
  melody_intent: ""
  status: planned
style:
  genre: ""
  era: ""
  instruments: []
vocal:
  configuration: ""
  timbre: ""
  diction: ""
  breath_timestamps: {status: pending, items: []}
rhythm:
  planned_bpm: null
  beat_timestamps: {status: pending, items: []}
  downbeat_timestamps: {status: pending, items: []}
harmony:
  progression: ""
  lift_point: null
structure:
  - {section_id: "V1", function: "", foreground: "", events: [], transition: ""}
vocal_events: []
timestamp_status: planned
emotion_curve:
  - {at_sec: 0, emotion: "", energy: 1, function: ""}
lyrics_timeline:
  status: planned
  lines:
    - {line_id: "V1-01", section_id: "V1", section: "Verse", text: "", planned_position: "第一主歌", start_sec: null, end_sec: null, beat_anchor: null}
visual_dna:
  status: mv_pending
  palette: []
  motifs: []
  character_anchors: []
```

精确鼓点、气口或副歌重拍只能来自实际分析/人工校对。用户尚未生成并返回真实结果时，保留空数组和 `pending`，再由 MV 流程把选定版本绑定到 `analysis/beats.json`。

## 单模型完整格式示例

以下为人工编写的格式示例，沿用作曲指南中的“下班回家”情境。假定用户已选标题、约 60 秒、自己试听、MP3 V0、采样率与 seed 均沿用；实际节点和文件未核实。所有创作选择、日期和检查状态都需按本次任务替换，不能套为默认方案。

````markdown
---
title: "一盏灯等我回来"
type: "song"
model: "MiniMax Music 3"
status: "ready"
execution: "manual_by_user"
audio_status: "not_generated"
version: 1
created_at: "2026-10-30"
updated_at: "2026-10-30"
title_source: "用户从候选中选定"
---

# 一盏灯等我回来

## 创作简报

| 项目 | 内容 | 来源 |
| --- | --- | --- |
| 用途与目标时长 | 自己试听，约 60 秒 | 用户已选；非保证片长 |
| 主题与情绪 | 下班回家，从疲惫转向放松与安定 | 用户已选主题；按主题组织情绪 |
| 文本语言与歌词来源 | Caption 中文，Lyrics 中文，歌词从零创作 | 中文 Caption 为技能约定；中文歌词及代写为用户要求 |
| 听感、人声与乐器 | 温暖、自然贴近，轻柔女声，木吉他为主 | 用户已选；少量钢琴低音为编曲建议 |
| 结构 | 前奏 → 主歌 → 副歌 → 尾奏 | 按用户目标长度组织 |
| 必须保留 / 避免 | 保留短曲的完整收尾；全曲无鼓或打击乐 | 收尾为编曲建议；无鼓为用户要求 |

## 意图与词曲蓝图

音乐角色为个人试听的歌曲主体，目标是把下班疲惫转为被接纳的安定感；成功标准是口吻贴近、核心句可辨、末句与收尾完整。以上为根据已知主题作出的编曲推荐，不是用户已经试听的结论。

选择故事先行，以钥匙、门外与灯光作为创作设定；核心句“等我回来”由 Agent 原创。主歌窄音区与短句，副歌舒展但不增加节奏密度，指弹动机在开头和结尾呼应。无特殊人声事件。

| section_id | 功能 | 前景与声部事件 | 衔接 |
| --- | --- | --- | --- |
| I1 | 建立亲近感 | 木吉他指弹动机 | 保留指弹进入主歌 |
| V1 | 叙述疲惫与回家动作 | 女声在前景，吉他留白 | 展开和弦进入副歌 |
| C1 | 表达被接纳 | 主唱舒展，加入少量钢琴低音 | 减层回到指弹 |
| O1 | 安定收束 | 器乐动机与最终和弦 | 留自然尾音 |

所有段落位置均 planned，实际时间为空；完整控制卡采用上方模板，时间线行号不粘贴到 Lyrics。

## Caption

```text
Global Metadata: 温暖的原声流行短歌，采用舒缓、轻轻流动的律动，情绪从疲惫逐步转向放松与安定。整体声音自然、贴近而克制，为每句演唱留出空间。保留木吉他的自然拨弦细节，低频均衡，主唱与伴奏层次清楚。全曲不使用鼓或打击乐。

Vocal Details: 一位轻柔女声以普通话独唱，咬字清晰，音色自然贴近。主歌像轻声交谈，表达克制；副歌稍微展开，延长音更温暖。只保留少量自然空间感，不加入伴唱、念白或无词哼唱。

Arrangement: 前奏以简洁的木吉他指弹动机引入。主歌延续同一指弹型，在演唱乐句之间留白。副歌轻轻展开吉他和弦，加入少量钢琴低音增加温暖感，不增加节奏密度。尾奏回到开场的指弹动机，以安定的最终和弦和自然尾音结束。保持短曲结构连贯、过渡自然、收尾完整。
```

## Lyrics

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

## 生成参数与工作流映射

| 项目 | 本次方案 | 来源 / 映射状态 |
| --- | --- | --- |
| `max_duration` | 60 秒 | 根据用户目标给出的上限建议；实际控件待映射，成品可能提前结束 |
| seed | 沿用现有方式 | 用户明确沿用；数值与生成后变化方式待核对 |
| Caption 字段 | `caption` / `Caption` | 按官方双文本输入模板整理，实际工作流待映射 |
| Lyrics 字段 | `lyrics` / `Lyrics` | 按官方双文本输入模板整理，实际工作流待映射 |

## 导出设置

| 项目 | 目标 / 策略 | 来源 / 保存映射 | 实测结果 | 状态 |
| --- | --- | --- | --- | --- |
| 格式与质量 | MP3 / V0 | 用户已选；官方 SaveAudioAdvanced 方案为 format=mp3、quality=V0，实际节点待映射 | 未检测 | PENDING |
| 采样率 | 沿用源音频 | 用户明确沿用；不另行设定 Hz | 未检测 | PENDING |
| 平台要求 | 未指定平台 | 不适用 | 不适用 | 不适用 |

## 复制与映射说明

将 Caption 和 Lyrics 代码块分别复制到工作流的 caption / Caption 与 lyrics / Lyrics 输入，名称和其他章节不用粘贴。按官方双文本输入模板整理，具体字段待映射；随后手动填写 max_duration、seed 策略与保存格式，由用户点击运行并试听末句和尾奏。本文件只整理资料，尚未执行音乐生成，也未检测实际音频。

## 自查状态

- [x] 名称已选定，必需创作与导出方案已解决
- [x] Caption 与 Lyrics 的段落、人声及编制一致
- [x] 中文 Caption、完整歌词和无鼓要求已保留
- [x] 已区分用户选择、编曲建议与未知节点/文件值
- [ ] 实际工作流与音频文件检查：PENDING
- 平台检查：不适用

## 版本记录

- v1 / 2026-10-30：初版；标题由用户选定，完成提示词与参数整理，尚无实际音频检查结果。
````

## 双模型文档的 YuE2 对应章节

需要两版时，将上例 MiniMax 的 Caption、Lyrics、参数、导出与手动步骤归入 `MiniMax Music 3` 章节；顶层元数据改用 `models: ["MiniMax Music 3", "YuE2"]`，保留 `execution: manual_by_user` 与 `audio_status: not_generated`。共用创作简报、情绪曲线和歌词行号，各模型分别保存参数与上限，不把两个描述混进同一文本框。

下例延续上面的同一创作方向与歌词，展示 YuE2 的自然 Style 与基础标签。默认建议导出 MP3 320k + FLAC；若用户明确选择上例 V0，则两版均保留该选择并记录来源。

### YuE2 Style

```text
温暖的当代原声流行短歌，舒缓、轻轻流动的律动，情绪从下班后的疲惫逐步转向放松与安定。一位轻柔女声用普通话独唱，主歌贴近轻声交谈，副歌自然展开；咬字清晰，不加入伴唱、念白或无词哼唱。木吉他指弹贯穿歌曲，乐句之间保留空间，副歌以更舒展的吉他和弦及少量钢琴低音增加温暖感。全曲不使用鼓或打击乐，主唱与伴奏层次清楚，低频均衡。简短吉他引入后进入主歌与副歌，最后回到指弹动机，以安定的最终和弦和自然尾音收束。
```

### YuE2 Lyrics

```text
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
```

### YuE2 参数与手动填写

| 项目 | 本例方案 | 来源与填写位置 |
| --- | --- | --- |
| 目标时长 / max_duration | 约 60 秒 / 60 秒 | 延续本例；目标非保证片长，上限在用户界面核对 |
| mode | full | 默认建议；YuE2 mode 控件 |
| ABC_planning | 开启 | 默认建议；官方子图开关 |
| seed | 沿用现有工作流 | 本例用户已选，实际值由用户执行后记录 |
| Style / Lyrics | 分别粘贴以上完整代码块 | 官方子图对应控件；展开节点时两生成节点的文本保持一致 |
| 高级采样 | 沿用工作流 | 不把 MiniMax 参数复制到 YuE2 |

之后按本次导出表检查保存节点，用户自行点击运行并试听末句、尾奏与缺词。音频实长、编码与试听仍为 PENDING；资料 ready 不代表已经执行。完整操作见 [manual-comfyui.md](manual-comfyui.md)。
