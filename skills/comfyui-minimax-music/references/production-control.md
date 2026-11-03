# 歌曲创作控制与 MV 交接契约

这份参考用于把歌曲从“一个想法”推进到可生成、可试听、可分析、可交给 MV 的版本。它补充模型工作流契约，不新增模型能力，也不把提示词写成精确乐谱指令。

## 先固定三类事实

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

先确定主题、叙事视角、目标听众、使用场景和情绪终点。把情绪写成从开头到结尾的变化，而不是只写一个形容词。短曲按约 15 秒一个点记录情绪，例如 `0s`、`15s`、`30s`、`45s`、`60s`；目标时长变化后重新采样这些点。

阶段产物：

- 一句话主题与一句话听感承诺；
- 情绪曲线表：时间、情绪、能量（1–5）、叙事功能；
- 目标时长、收尾余量和必须保留/避免项。

通过条件：主题、情绪终点和用途不互相冲突。没有通过时，不急着堆乐器或高级参数。

### 2. 多维歌曲生成与元数据留存

把生成控制拆为四组，避免只写“某某风格”：

1. 风格：子类别、年代感、速度感、核心配器；
2. 人声：性别/人数、音色、咬字、表达力度、和声策略；
3. 节奏：预计 BPM、拍号感、底鼓/重拍作用、段落能量；
4. 和声与结构：调性感受、和弦走向、升调或副歌打开方式、段落顺序。

生成前保存一份控制卡，至少含 `work_id`、`version`、`model`、`target_duration_sec`、`max_duration_sec`、`style`、`vocal`、`rhythm`、`harmony`、`structure`、`emotion_curve` 和 `timestamp_status`。`seed`、实际工作流摘要和生成版本写入运行记录。

“导出每处重拍、气口的时间戳 JSON”只能作为目标接口或待测项目记录。当前内置 ComfyUI 音乐工作流只负责生成和保存音频，若没有真实分析输出，应写 `pending`，不能把提示词中的预期当成音频事实。

### 3. 歌词与音乐时间线双映射

歌词先按稳定的 `section_id` 和 `line_id` 编号，再映射到时间。每句记录文本、段落、预计功能和时间状态；生成后再用实际音频修正 `start_sec`、`end_sec` 与 `beat_anchor`。

对 MV 最有用的是“可追踪而非假精确”：

- 生成前：记录预计入点、段落和情绪用途；
- 生成后：由 `mv-creator analyze` 写入实际 BPM、拍点、小节线和能量；
- 试听后：人工确认歌词完整、气口、重拍和尾奏；
- 换歌或换版：时间线绑定 `take_id` 与音频摘要，旧时间线标记过期。

### 4. 视觉符号与风格锁定（仅 MV 协作）

音乐 Skill 不负责生成画面，但应把能从歌曲确定的视觉约束交给 MV：主色与情绪关系、核心意象、重复出现的道具、角色动作母题、高潮段落的视觉放大方式。视觉符号必须是稳定名词，避免每个镜头换一套同义描述。

阶段产物由 `mv-creator` 保存为 `visual_dna` 和分镜字段；音乐版本只提供来源和情绪依据，不替用户提前生成图片或视频。

### 5. 动态镜头与音画硬对齐（下游执行）

镜头入点、出点、切镜、动作和运镜使用实际 `beats.json`，优先对齐小节线和已人工确认的重拍。歌曲 Skill 只交付时间线计划、段落和情绪标记；不要声称生成器已经完成视频级逐拍同步。

### 6. 统一校验与版本冻结

选版前检查文件编码、时长、采样率、声道、解码状态；试听确认末句、尾奏、歌词完整性和整体情绪弧线。选定 `take_id` 后冻结歌曲内容，再进入节拍分析和分镜。任何修改都创建新版本，并说明只改变了哪个维度。

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
  "emotion_curve": [
    {"at_sec": 0, "emotion": "疲惫", "energy": 2, "function": "建立处境"},
    {"at_sec": 15, "emotion": "松动", "energy": 3, "function": "出现转机"},
    {"at_sec": 30, "emotion": "温暖", "energy": 4, "function": "副歌释放"},
    {"at_sec": 60, "emotion": "安定", "energy": 2, "function": "完整收束"}
  ],
  "lyrics_timeline": {
    "status": "planned",
    "lines": [
      {"line_id": "V1-01", "section": "Verse", "text": "", "start_sec": null, "end_sec": null, "beat_anchor": null}
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

把“听起来不对”归到一个主问题：风格/配器、人声/咬字、节奏/推进、结构/收尾、文件规格。保留 seed 和其他已确认内容，先只改对应字段再生成新版。不要用加强质量词解决时间线、编码或歌词完整性问题，也不要为了修一个尾奏问题重写整首歌词。
