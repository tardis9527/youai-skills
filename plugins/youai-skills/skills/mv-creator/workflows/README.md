# 拖入 `.workflow.json`，不要拖入 `.params.json`

| 文件 | 用途 |
| --- | --- |
| `music.workflow.json` | MiniMax Music 3 音乐生成界面模板 |
| `i2v.workflow.json` | MiniMax H3 图生视频，仅连接首帧 |
| `flf2v.workflow.json` | MiniMax H3 首尾帧生视频，连接两张图片 |
| `music.api.json` / `i2v.api.json` / `flf2v.api.json` | 从随附模板展开的 API 执行图，脚本默认直接读取 |
| `tts-design.workflow.json` | Breeze TTS 2 音色试镜，中文音色说明和朗读文本 |
| `tts-direction.workflow.json` | Breeze TTS 2 参考音色配音，参考音频与准确转写 |
| `tts-*.api.json` | 已核对接口的脚本执行样例，不能作为界面工作流拖入；工作区导出优先 |
| `*.params.json` | 脚本参数映射，不能拖入 ComfyUI |

视频模板对应 `Image to Video (MiniMax H3)` 子图，使用 INT8 FL2VA、NVFP4 Qwen3-VL、INT8 视频 VAE 和 FP32 音频 VAE；Turbo 默认关闭，开启时为 8 步 LoRA。默认尺寸 864×1536、24fps、duration=5 秒，内部对齐为 124 帧。

项目默认没有本地工作流，脚本自动读取本目录中的 `.api.json` 和 `.params.json`，上传项目输入后注入参数即可提交，不要求用户先在界面运行或导出。只有自定义配置才需要把界面图 **Export (API)** 到工作区的 `workflows/`，同名文件优先且不被覆盖。H3 秒数计算连线保留。完整步骤和旧 Wan 项目迁移见 [工作流说明](../references/workflows.md)。

旁白流程与歌曲、视频分开运行。先 Design 试听选音色，再 Direction 固定参考逐句配音；默认 `download_if_missing=false`、`stitch_reference=none`，保留原始 FLAC。模型文件、使用限制与完整声音制作见 [旁白指南](../references/voice-guide.md)。两套模板均有中文 Note，提示词也默认中文。

## 来源与许可

来源为 [Comfy-Org/workflow_templates](https://github.com/Comfy-Org/workflow_templates)，固定版本 `c067929d7e9cc0f3fd15be348fa1a1d85da15946`：

| 本地文件 | 上游路径及调整 |
| --- | --- |
| `music.workflow.json` | `templates/audio_minimax_music_3.json`；说明节点改为中文使用介绍、参数说明和模型准备指引，生成节点及参数保持原配置 |
| `i2v.workflow.json` | 基于 `templates/video_minimax_h3_i2v.json`；改为竖屏，移除外围尺寸示例，设置输入占位图和中文单镜头提示；子图采样逻辑及权重保持上游配置，增加参数定位标题，说明节点按实际配置改为中文 |
| `flf2v.workflow.json` | 在上述 H3 模板基础上增加尾帧 LoadImage 及连线 |

视频模板保存时记录的前端版本为 `1.49.6`，音乐为 `1.48.7`，这是来源信息而非最低版本承诺。模型权重及示例图片不在技能包内。

三个音乐/视频 `.api.json` 由上述随附模板展开子图得到，沿用节点 ID 前缀、模型、采样器、分块音频解码开关、Turbo 开关和 H3 秒数计算；去掉界面布局、说明节点和前端专用控件，提示词改为中文占位内容，由项目参数替换。音乐保存沿用 MP3 / V0，动态质量输入使用 `format.quality`。本地离线校验不替代目标 ComfyUI 的节点、模型和实际生成验证。

上游 MIT 许可见 [LICENSE.Comfy-Org.txt](LICENSE.Comfy-Org.txt)。官方 H3 实现核对版本：ComfyUI `17ff1dcce963bd9f23095ec9b28febbfc4db8388` 的 `comfy_extras/nodes_minimax_h3.py`，使用 `24fps`、`17k+5` 规则。正确文件仍加载失败时，核对 ComfyUI 前后端、子图及量化权重支持。

`tts-design` / `tts-direction` 为本技能自行组织的界面图、执行图和映射，不是上述官方模板的复制。2026-11-02 按本机 ComfyUI 0.43.0 的 `/object_info` 与 Saganaki22 节点包提交 `53d899bfaa1ea37badc58f901900c068a9755116` 核对；模型及输出适用 Breeze 的独立许可证，详见旁白指南。升级节点包后先验证接口再生成。
