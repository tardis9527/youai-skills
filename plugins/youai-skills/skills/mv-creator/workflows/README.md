# 拖入 `.workflow.json`，不要拖入 `.params.json`

| 文件 | 用途 |
| --- | --- |
| `music.workflow.json` | MiniMax Music 3 音乐生成界面模板 |
| `i2v.workflow.json` | MiniMax H3 图生视频，仅连接首帧 |
| `flf2v.workflow.json` | MiniMax H3 首尾帧生视频，连接两张图片 |
| `*.params.json` | 脚本参数映射，不能拖入 ComfyUI |

视频模板对应 `Image to Video (MiniMax H3)` 子图，使用 INT8 FL2VA、NVFP4 Qwen3-VL、INT8 视频 VAE 和 FP32 音频 VAE；Turbo 默认关闭，开启时为 8 步 LoRA。默认尺寸 864×1536、24fps、duration=5 秒，内部对齐为 124 帧。

配置本机模型与输入图片后，用 **Export (API)** 导出为 `music.api.json`、`i2v.api.json` 或 `flf2v.api.json`，放入工作区的 `workflows/`。H3 秒数计算连线可原样保留，无需断开。完整步骤和旧 Wan 项目迁移见 [工作流说明](../references/workflows.md)。

## 来源与许可

来源为 [Comfy-Org/workflow_templates](https://github.com/Comfy-Org/workflow_templates)，固定版本 `c067929d7e9cc0f3fd15be348fa1a1d85da15946`：

| 本地文件 | 上游路径及调整 |
| --- | --- |
| `music.workflow.json` | `templates/audio_minimax_music_3.json`；说明节点改为中文使用介绍、参数说明和模型准备指引，生成节点及参数保持原配置 |
| `i2v.workflow.json` | 基于 `templates/video_minimax_h3_i2v.json`；改为竖屏，移除外围尺寸示例，设置输入占位图和中文单镜头提示；子图采样逻辑及权重保持上游配置，增加参数定位标题，说明节点按实际配置改为中文 |
| `flf2v.workflow.json` | 在上述 H3 模板基础上增加尾帧 LoadImage 及连线 |

视频模板保存时记录的前端版本为 `1.49.6`，音乐为 `1.48.7`，这是来源信息而非最低版本承诺。模型权重及示例图片不在技能包内。

上游 MIT 许可见 [LICENSE.Comfy-Org.txt](LICENSE.Comfy-Org.txt)。官方 H3 实现核对版本：ComfyUI `17ff1dcce963bd9f23095ec9b28febbfc4db8388` 的 `comfy_extras/nodes_minimax_h3.py`，使用 `24fps`、`17k+5` 规则。正确文件仍加载失败时，核对 ComfyUI 前后端、子图及量化权重支持。
