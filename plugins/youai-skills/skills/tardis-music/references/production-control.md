# 歌曲创作控制与 MV 交接契约

这份参考用于把歌曲从“一个想法”整理成用户可手动生成的创作资料，并约定生成后的试听、分析与 MV 交接。Skill 完成于资料交付；后续实测与选版等待用户返回音频或由调用方执行。它补充模型工作流契约，不新增模型能力，也不把提示词写成精确乐谱指令。

## 先区分计划、测量、确认与未知

每个作品都要区分：

| 状态 | 含义 | 例子 |
| --- | --- | --- |
| `planned` | 创作前的意图或设计值 | 目标 BPM、预计副歌进入点、15 秒情绪曲线 |
| `measured` | 对实际音频测量得到的值 | 实际时长、估算 BPM、拍点、小节线 |
| `verified` | 人工试听或人工校对确认 | 末句完整、尾奏自然、歌词与时间线对应 |
| `pending` | 当前没有足够证据 | 人声气口、精确副歌重拍、严格无人声 |

模型可以按风格、结构和情绪生成音乐，但不能仅凭 Caption 保证精确 BPM、逐字演唱、气口位置或帧级时间。没有真实音频分析或人工试听证据时，不把这些内容写成 `measured` 或 `verified`。

## 六个阶段与闸门

### 1. 核心概念锚定

先按 [creative-intent.md](creative-intent.md) 确定创作命题、叙事视角、目标听众、音乐角色和成功标准。情绪分别记录故事、表演和能量，从开头到结尾有符合目标的变化；有意反差写明目的。短曲可按约 15 秒记录情绪，长曲按段落与关键事件补点，不机械要求密集到每一秒。目标时长变化后调整计划。

阶段产物：

- 一句话主题与一句话听感承诺；
- 情绪曲线表：时间、情绪、能量（1–5）、叙事功能；
- 目标时长、收尾余量和必须保留/避免项。

通过条件：命题、情绪终点、用途和硬约束一致。每项意图的来源区分 user_explicit、inferred、recommended、unknown；关键冲突澄清，其余合理推荐，不为控制卡字段齐全新增问卷。

### 2. 多维生成参数整理与元数据留存

先保存 [composition-guide.md](composition-guide.md) 的词曲蓝图，再把模型相关控制拆为四组，避免只写“某某风格”：

1. 风格：子类别、年代感、速度感、核心配器；
2. 人声：性别/人数、音色、咬字、表达力度、和声策略；
3. 节奏：预计 BPM、拍号感、底鼓/重拍作用、段落能量；
4. 和声与结构：调性感受、和弦走向、升调或副歌打开方式、段落顺序。

完整创作保存控制卡，含 `work_id`、`version`、`model`、目标/上限、`intent`、`blueprint`、四组控制、`structure`、`emotion_curve` 和 `timestamp_status`。记录主要 Hook 与段落功能；特殊人声使用 [vocal-performance.md](vocal-performance.md) 的 `vocal_events`，没有就留空。seed 策略记入参数表，实际 seed/工作流版本由用户执行后补充。两模型共用意图与原词，模型控制和上限分别记录；未指定字段可为空，不为了填表编造值。

`structure` 的事件至少说明稳定 `section_id`、叙事任务、表演/主奏、声部进入退出和转接；不等于成品秒表。平台研究与 [反馈学习](feedback-learning.md) 只关联相关来源 ID/项目路径，不把整份研究或个人档案塞进模型描述。

“导出每处重拍、气口的时间戳 JSON”只能作为目标接口或待测项目记录。本 Skill 不运行工作流或音频分析，没有用户返回的真实分析输出时，应写 `pending`，不能把提示词中的预期当成音频事实。

### 3. 歌词与音乐时间线双映射

歌词先按稳定的 `section_id` 和 `line_id` 编号，再映射到时间。每句记录文本、段落、预计功能和时间状态；生成后再用实际音频修正 `start_sec`、`end_sec` 与 `beat_anchor`。计划入点另存 `planned_position`，未测的实际字段为 null；既有作品不为改段落名而重编号，新增行分配新 ID。纯音乐时间线记录器乐事件，不编造歌词行。

对下游视觉或视频流程最有用的是“可追踪而非假精确”：

- 生成前：记录预计入点、段落和情绪用途；
- 生成后：由调用方的音频分析工具写入实际 BPM、拍点、小节线和能量；
- 试听后：人工确认歌词完整、气口、重拍和尾奏；
- 换歌或换版：时间线绑定 `take_id` 与音频摘要，旧时间线标记过期。

### 4. 视觉符号与风格锁定（仅视觉或视频协作）

音乐 Skill 不负责生成画面，但应把能从歌曲确定的视觉约束交给下游视觉或视频流程：主色与情绪关系、核心意象、重复出现的道具、角色动作母题、高潮段落的视觉放大方式。视觉符号必须是稳定名词，避免每个镜头换一套同义描述。

阶段产物由下游视觉或视频流程保存为 `visual_dna` 和分镜字段；音乐版本只提供来源和情绪依据，不替用户提前生成图片或视频。

### 5. 动态镜头与音画硬对齐（下游执行）

镜头入点、出点、切镜、动作和运镜使用实际 `beats.json`，优先对齐小节线和已人工确认的重拍。歌曲 Skill 只交付时间线计划、段落和情绪标记；不要声称生成器已经完成视频级逐拍同步。

### 6. 资料自查与生成后版本冻结

交付前按“意图 → 蓝图 → 段落 → 描述/Lyrics → 参数/导出”自查，尤其原词权限、人声/禁鼓等硬约束、特殊事件映射及收尾；音频检查保持 pending。用户返回结果后，分别记录文件测量、用户报告和人工试听，先判断表达目标，再检查末句、尾奏、缺词、特定人声与情绪弧线。选定 `take_id` 后冻结歌曲内容，再进入实际节拍分析和分镜。修改创建新版本，记录主维度及必要联动，不能把控制卡的计划值当实测。

## 推荐控制卡

下面是创作记录或 MV `music/` 目录可以采用的最小 JSON 结构。时间戳没有实测时保留 `null`，不要填“看起来合理”的数字。

```json
{
  "work_id": "安全化作品名",
  "version": 1,
  "take_id": null,
  "model": "MiniMax Music 3",
  "target_duration_sec": 60,
  "max_duration_sec": 90,
  "timestamp_status": "planned",
  "intent": {
    "use_case": "私人试听",
    "music_role": "歌曲主体",
    "desired_response": "从疲惫走向安定",
    "success_criteria": ["表达自然贴近", "歌词与收尾完整"],
    "source": "recommended"
  },
  "blueprint": {
    "route": "故事先行",
    "premise": "借回家的动作表达被接纳的感觉",
    "lyric_hook": "等我回来",
    "melody_intent": "主歌窄音区，副歌舒展，保留指弹动机",
    "status": "planned"
  },
  "style": {
    "genre": "温暖原声流行",
    "era": "当代",
    "instruments": ["木吉他", "低音钢琴"]
  },
  "vocal": {
    "configuration": "独唱",
    "timbre": "轻柔、贴近",
    "diction": "清晰自然",
    "breath_timestamps": {"status": "pending", "items": []}
  },
  "rhythm": {
    "planned_bpm": 92,
    "beat_timestamps": {"status": "pending", "items": []},
    "downbeat_timestamps": {"status": "pending", "items": []}
  },
  "harmony": {"progression": "待生成后听辨", "lift_point": null},
  "structure": [
    {"section_id": "V1", "function": "建立疲惫处境", "foreground": "主唱", "transition": "保留指弹进入副歌"},
    {"section_id": "C1", "function": "表达被接纳", "foreground": "舒展主唱", "transition": "回到器乐动机收束"}
  ],
  "vocal_events": [],
  "emotion_curve": [
    {"at_sec": 0, "emotion": "疲惫", "energy": 2, "function": "建立处境"},
    {"at_sec": 15, "emotion": "松动", "energy": 3, "function": "出现转机"},
    {"at_sec": 30, "emotion": "温暖", "energy": 4, "function": "副歌释放"},
    {"at_sec": 45, "emotion": "松弛", "energy": 3, "function": "回收层次"},
    {"at_sec": 60, "emotion": "安定", "energy": 2, "function": "完整收束"}
  ],
  "lyrics_timeline": {
    "status": "planned",
    "lines": [
      {"line_id": "V1-01", "section_id": "V1", "section": "Verse", "text": "", "planned_position": "第一主歌", "start_sec": null, "end_sec": null, "beat_anchor": null}
    ]
  },
  "visual_dna": {
    "status": "mv_pending",
    "palette": [],
    "motifs": [],
    "character_anchors": []
  },
  "checks": {
    "audio_metadata": "pending",
    "decode": "pending",
    "ending_review": "pending_listen",
    "lyric_completeness": "pending_listen"
  }
}
```

## 反馈时只改一个主维度

先检查表达目标与叙述是否偏离，再归到风格/配器、人声/咬字、旋律/节奏、结构/收尾或文件规格。保留已记录 seed 与其他确认内容，优先改一个主维度，必要联动如增加台词与伴奏减法需要一起说明。按 [feedback-learning.md](feedback-learning.md) 记录真实结果再复用，不把本次选择推广为永久偏好。不要用加强质量词解决编码或缺词，也不为尾奏问题重写整首歌词。
