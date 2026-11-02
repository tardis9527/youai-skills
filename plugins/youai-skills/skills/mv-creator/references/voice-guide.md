# MV 旁白：Breeze TTS 2 创作、试听与混音

用于旁白、内心独白、画外对白和少量人物语气声。歌曲演唱继续使用 MiniMax Music 3；画面继续使用 H3；不增加对口型环节。没有叙事收益时保留纯歌曲 MV，不为使用模型而堆台词。

## 先设计，再生成

1. 简报中判断是否需要旁白，给出预填的声音方向：用途、说话人、音色描述、建议位置和台词数量。30–60 秒 MV 可先建议一个主音色、1–3 句短台词，总计约 4–10 秒；这是创作起点，不是硬性限制。
2. 歌曲参数中同步建议前奏、间奏或尾奏留白。选歌后实际试听再定旁白位置；节拍和能量分析不能识别演唱空档，不能据此自动认定某处无人声。
3. 在分镜确认时一并提交完整声音表：台词、说话人、内心/画外用途、情绪与语速、时间窗口、画面关系、是否显示字幕。内心独白优先配背影、侧脸或环境镜头，避免暗示角色嘴形同步。
4. ⏸ 用户确认声音表后才生成；音色先试听选定，再生成正式台词。不要让用户自己填写提示词或反复回答已确认的问题。
5. 正式台词逐句试听，检查音色、发音、漏字、句尾、语速和情绪，用户选定后再混音；动作语气标记也需要试听，不能当作准确可控的独立音效。

## 本版本接入的节点

接口于 2026-11-02 按本机 ComfyUI `/object_info` 和 Saganaki22 节点包提交 `53d899bfaa1ea37badc58f901900c068a9755116` 核对：

| 工作流 | 节点 | 用途 |
| --- | --- | --- |
| `tts-design` | `BreezeTTS2LoadModel` → `BreezeTTS2VoiceDesign` → `SaveAudioAdvanced` | 无参考音频的音色试镜 |
| `tts-direction` | 同一加载器 + `LoadAudio` → `BreezeTTS2VoiceDirection` → `SaveAudioAdvanced` | 固定参考音色，控制本句表演 |

不与 T8 等其他节点包接口混用。模型选择 `int8 hybrid (recommended)`，`dtype/device/attention=auto`、`decode_mode=eager`、`download_if_missing=false`；本技能不安装节点或自动下载模型。模型配套目录、配置及分词器要求见模板中文 Note 和[节点包说明](https://github.com/Saganaki22/ComfyUI-Breeze-TTS-2/blob/main/README_ZH.md)。

输出为 24kHz 单声道。保留原始 FLAC，混音统一为 48kHz 立体声 24-bit PCM WAV；重采样不增加原始音质。Direction 的 `stitch_reference=none`，避免参考录音混入新台词。

`workflows/tts-*.workflow.json` 可拖入画布；`tts-*.api.json` 是按已核对接口构造的执行样例，脚本在工作区没有同名 API 时使用它。界面配置或模型变更后，用 Export (API) 导出到工作区的 `workflows/`，优先采用用户导出。`.params.json` 仅用于注入参数。运行前：

```powershell
python <SKILL_DIR>/scripts/mv.py comfy-validate tts-design tts-direction
```

## 项目中的声音计划

有分镜后运行 `voice-init <slug>`，创建 `audio/voice-plan.json`，默认 `enabled=false`，不会覆盖旧计划。由你根据已确认的创作内容填写，启用后再生成。

```json
{
  "version": 1,
  "enabled": true,
  "binding": {"music_take": "take-1", "song_sha256": "由脚本记录", "timeline_sha256": "由脚本记录"},
  "speakers": [{
    "id": "narrator", "name": "林夏的内心声音",
    "description": "年轻女性，中低音，温暖、清晰、自然。",
    "sample_text": "那天的雨，我一直记得。后来，我终于学会了告别。",
    "reference": null, "takes": [], "selected": null
  }],
  "cues": [{
    "id": "V01", "speaker": "narrator", "kind": "inner", "mode": "direction",
    "text": "那天的雨，我一直记得。",
    "instruction": "语速稍慢，克制地回忆，句尾轻收，避免播音腔。",
    "anchor": {"shot_id": "S01", "offset_sec": 0.5},
    "window_sec": 3.0, "gain_db": 0, "duck_db": -6, "subtitle": true,
    "takes": [], "selected": null
  }]
}
```

保留 `voice-init` 实际生成的 binding，不复制示例占位值。所有音频路径相对项目根目录，参考音频也先放入项目再填写。

| 字段 | 含义 |
| --- | --- |
| `speakers[].description` | 固定音色设定，不随每句话重写 |
| `sample_text` | 音色试镜朗读文本；确认选版时核对实际发音，必要时修正参考文本 |
| `reference.file/text` | 固定参考录音及准确转写；不能将表演指令当转写 |
| `kind` | `narration` 旁白、`inner` 独白、`dialogue` 画外对白、`vocal_event` 语气声 |
| `mode` | 默认 `direction`；独立、无需保持音色的短句可显式用 `design` |
| `instruction` | 本句情绪、语速、力度和停顿；默认中文，与台词语言匹配 |
| `anchor` | 对某镜头起点加偏移，位置随镜头起点计算；允许跨镜头播放 |
| `start` | 绝对秒数；与 `anchor` 二选一 |
| `window_sec` | 此句允许占用的时间，实际音频必须放得下，且窗口不能超过 MV 结尾 |
| `gain_db` | 本句相对音量调整，默认 0 |
| `duck_db` | 旁白期间歌曲额外衰减，默认 -6dB；0 表示不压低 |
| `subtitle` | 是否显示本句字幕；纯叹气、轻笑通常设 false |
| `settings` | 可覆盖当前条目的 `cfg_scale/max_new_tokens/temperature/top_k/top_p/repetition_penalty/depth_temperature/depth_top_k/depth_top_p` |
| `takes/selected` | 脚本维护候选和选定版本；不手改生成记录或文件 |

`max_new_tokens` 默认 256，只是生成上限，不能按它承诺精确时长；长句或句尾被截断时先检查文本与该上限。模型 seed 使用 1–2147483647；0 不保证可复现，不用于本流程。

## 音色试听、正式配音与续跑

```powershell
# 先创建计划，填好声音脚本并获得确认
python <SKILL_DIR>/scripts/mv.py voice-init <slug>
python <SKILL_DIR>/scripts/mv.py voice-check <slug>

# 先给说话人做样音；--dry-run 不上传、不生成
python <SKILL_DIR>/scripts/mv.py voice <slug> --speakers --takes 2 --dry-run
python <SKILL_DIR>/scripts/mv.py voice <slug> --speakers --takes 2
python <SKILL_DIR>/scripts/mv.py voice-select <slug> narrator take-1 --speaker

# 试听选定的样音成为参考，不再为每句话重新设计音色
python <SKILL_DIR>/scripts/mv.py voice <slug> --takes 2 --dry-run
python <SKILL_DIR>/scripts/mv.py voice <slug> --takes 2
python <SKILL_DIR>/scripts/mv.py voice-select <slug> V01 take-1
python <SKILL_DIR>/scripts/mv.py voice-check <slug> --ready
python <SKILL_DIR>/scripts/mv.py mix-preview <slug>
```

每次运行前说明条目数量、候选数量和总调用次数。默认补齐当前内容所需的候选数：中断后重跑补缺，不重新生成已有候选；`--ids V01,V03` 仅为指定条目追加，`--more` 全部追加。`--speakers --ids narrator` 用于重做某个音色。每个候选即时落盘，保存 seed、工作流摘要、输入参数、文件校验和和测量时长。

参考录音可来自已选定的合成音色，或用户明确提供并有权使用的素材；不自行模仿指定真人。选定样音前人工确认朗读完整，`reference.text` 必须匹配实际声音。相同参考音色只能提高一致性，不能替代试听。

## 时间、版本与过期判断

- 生成前校验台词、说话人、工作流映射、参考录音、窗口和已知镜号。
- 已选音频按真实时长检查；超出窗口会拒绝选版/混音，先缩短台词、调整表演或扩大窗口。不会自动截断句尾、压缩时间或移动台词。
- 修改台词、音色参考、表演指令、生成参数或 API 工作流后，旧候选标为过期；只重做相关条目。
- 调整位置、字幕或音量只需重做混音，不重跑 TTS。
- 换歌、替换歌曲文件或改变分镜时间后，先重新试听与核对位置，再运行 `voice-check <slug> --bind`。它只记录“已复核当前时间线”，不会自动移动或生成内容。
- `status` 提示配音、混音和声音相关交付是否过期；混音缓存同时检查输入摘要和输出校验和。

## 混音与交付

`mix-preview` 输出到 `final/audio/`：

| 文件 | 用途 |
| --- | --- |
| `song_only.wav` | 当前混音基础音量的歌曲版，供 A/B 对比 |
| `voice_track.wav` | 已按时间线放置的整条独立旁白轨 |
| `mix.wav` | 歌曲与旁白混音 |
| `voice.srt` | 按实际选定配音时长生成的句级旁白字幕，无逐字对齐承诺 |
| `mix-manifest.json` | 当前配方、时间线、文件与缓存版本记录 |

配置 `voice.music_gain_db=-3`、`voice.voice_gain_db=0` 是试听起点；旁白期间歌曲另衰减 6dB，进入约 0.15 秒、恢复约 0.25 秒。重叠的衰减取较强值，不重复叠加；末端限幅并补偿处理延迟。逐句轻微淡入淡出。混音后仍需听手机/耳机上的可懂度，不能把峰值校验当作响度或听感验收。

启用声音后，`roughcut` 同时保留 `roughcut.mp4`（原歌曲版）和 `roughcut_voice.mp4`（旁白混音版）；`--burn-subs` 另生成字幕版，歌词下方、旁白上方。H3 片段原声继续默认移除，避免重复歌曲与对白。环境音第一版按素材需求单独规划和手工交付，不自动提取或批量生成。

`package` 增加 `06_旁白/`（逐句原始音频、声音时间表）和 `07_混音参考/`（歌曲版、旁白轨、混音），并在 `04_字幕/` 增加 `voice.srt`。导入剪映时选择“原歌曲+逐句旁白”或“整条混音”其中一种，避免重复叠加；字幕重叠与多句声音重叠会给提示，需人工确认。

无计划或 `enabled=false` 的旧项目沿用纯歌曲流程，不强制增加 Breeze 依赖。旧输出保留；关闭旁白后不要误用此前导出的混音文件，以本轮 `package.json` 和剪辑清单为准。

## 许可与使用范围

Breeze 模型及自托管输出按其研究/非商业许可证使用，商业项目需要另行取得授权；节点代码许可证不等于模型和输出许可证。参考：[模型许可证](https://huggingface.co/BreezeBlue/Breeze-TTS-2/blob/main/LICENSE)、[模型项目](https://github.com/breezeblue-ai/breeze-tts)。本模块使用独立时间线和可覆盖映射，后续可适配有合适授权的其他引擎，不将 Breeze 节点写入歌曲或 H3 画面流程。
