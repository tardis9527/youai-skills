# 项目目录与数据结构

```
projects/<slug>/
├─ project.json            # 作品信息、视频规格、歌曲各版本与选定版本
├─ brief.md                # 创意简报
├─ music/
│  ├─ <comfyui-minimax-music 的提示词文档>.md
│  ├─ caption.txt  lyrics.txt   # 注入工作流的原文
│  ├─ takes/take-N.flac         # 各版本
│  └─ song.flac                 # 选定版本
├─ analysis/beats.json     # BPM、拍点、小节线、每小节能量
├─ storyboard/
│  ├─ shots.json           # 分镜与各镜头生成状态（核心数据）
│  └─ storyboard.md        # shots-check 生成的可读分镜表
├─ characters/
│  ├─ raw/<id>-vNN-K.png   # 角色候选
│  ├─ prompts/             # 每次生图实际使用的提示词
│  └─ <id>.png             # 选定参考图
├─ frames/
│  ├─ raw/Sxx-vNN-K.png    # 关键帧候选（Tardis 原图）
│  ├─ prompts/
│  └─ Sxx.png              # 选定并裁切到视频尺寸的关键帧
├─ clips/Sxx/take-N.mp4    # 视频片段各版本
└─ final/
   ├─ capcut/              # 剪映素材包
   ├─ roughcut.mp4         # 粗剪参考
   └─ roughcut_subs.mp4    # 带歌词字幕的粗剪（可选）
```

所有 JSON 中的文件路径都相对项目根目录，项目文件夹整体移动或换电脑后仍然有效。

## project.json

```json
{
  "version": 1,
  "title": "雨夜便利店",
  "slug": "雨夜便利店",
  "video": {"width": 720, "height": 1280, "fps": 16, "max_frames": 81},
  "music": {
    "duration_sec": 60,
    "takes": [{"id": "take-1", "file": "music/takes/take-1.flac", "seed": 123, "max_duration": 60}],
    "selected": "take-1",
    "file": "music/song.flac"
  }
}
```

## shots.json

```json
{
  "version": 1,
  "style": "电影感，冷色调霓虹夜景，35mm 胶片颗粒，浅景深",
  "negative": "",
  "characters": [
    {"id": "lead", "name": "林夏", "description": "二十出头的女生", "prompt": "黑色齐肩短发……",
     "candidates": ["characters/raw/lead-v01-1.png"], "ref": "characters/lead.png"}
  ],
  "shots": [
    {
      "id": "S01", "start": 0.0, "end": 4.21, "bars": "前奏",
      "section": "前奏", "lyric": "",
      "scene": "雨夜街道全景，便利店灯光倒映在积水里",
      "characters": [],
      "image_prompt": "……", "motion_prompt": "雨丝落下，积水中的倒影轻轻晃动", "camera": "缓慢推进",
      "workflow": "i2v", "crop": "center", "seed": null, "notes": "",
      "frame": {"candidates": ["frames/raw/S01-v01-1.png"], "selected": "frames/S01.png",
                "source": "frames/raw/S01-v01-1.png"},
      "clip": {"takes": [{"id": "take-1", "file": "clips/S01/take-1.mp4", "workflow": "i2v",
                          "seed": 42, "frames": 69, "fps": 16, "prompt": "……"}],
               "selected": "take-1"}
    }
  ]
}
```

| 字段 | 谁填写 | 说明 |
| --- | --- | --- |
| `style` | 你 | 全局视觉风格，自动附加到每张图和每段视频的提示词 |
| `negative` | 你（可空） | Wan 负面提示词；为空时沿用工作流里的设置 |
| `characters[].prompt` | 你 | 角色外貌描述，用于生成设定图 |
| `start` / `end` | 脚本骨架，可调 | 秒；镜头之间应首尾相接，单段不超过 `(max_frames-1)/fps` |
| `bars` | 脚本 | 对应的小节号，仅供参考 |
| `section` / `lyric` | 你 | 段落名与该镜头期间唱的歌词；多行用 `/` 分隔，会生成 SRT |
| `scene` | 你 | 给人看的画面描述 |
| `image_prompt` | 你 | 给 Tardis 的关键帧提示词 |
| `motion_prompt` / `camera` | 你 | 给 Wan 的动作与镜头运动 |
| `workflow` | 你 | `i2v`（默认）或 `flf2v`（首尾帧过渡到下一镜头） |
| `crop` | 你 | 关键帧裁切锚点：`center` / `top` / `bottom` / `left` / `right` |
| `seed` | 你（可空） | 固定视频 seed，多版本时依次加 1 |
| `frame` / `clip` | 脚本 | 候选、版本与选定结果；不要手工改路径，用 select 命令 |
