# 环境准备

## 推荐方案：Python 3.12 + 工作区虚拟环境

mv-creator 和 imagegen-tardis 共用一个虚拟环境：`frames`/`chars` 命令会用**当前 Python 解释器**调用 imagegen-tardis 的脚本，所以只需要装一次依赖。

```powershell
# 1. 安装 Python 3.12（已有 3.10+ 可跳过）。安装后重开终端
winget install -e --id Python.Python.3.12

# 2. 在工作区根目录建立虚拟环境并安装依赖
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -r <SKILL_DIR>\requirements.txt

# 3. 安装 ffmpeg（粗剪、转 WAV 需要），安装后重开终端
winget install -e --id Gyan.FFmpeg
```

之后所有命令都用 `.\.venv\Scripts\python <SKILL_DIR>\scripts\mv.py ...`；激活虚拟环境（`.\.venv\Scripts\Activate.ps1`）后也可以直接用 `python`。PowerShell 拒绝运行激活脚本时，直接写 `.venv\Scripts\python` 的完整路径即可，不必修改执行策略。

ffmpeg 不在 PATH 上时，在配置里写 `"ffmpeg": "D:/tools/ffmpeg/bin"`（ffmpeg.exe 所在目录或其完整路径）。旁白混音同样需要 ffmpeg；FLAC 时长测量使用 soundfile，或同目录的 ffprobe。优先使用已有工具，缺少时再按用户授权准备。

## 配置文件 `mv-creator.config.json`

在工作区根目录运行 `mv.py init-config --url http://<ComfyUI 机器 IP>:8188` 生成。

| 字段 | 说明 |
| --- | --- |
| `comfyui.url` | ComfyUI 地址。ComfyUI 桌面版默认端口 8000，便携版/源码版默认 8188 |
| `comfyui.timeout_sec` | 单个任务最长等待时间 |
| `workflows_dir` | 可选自定义覆盖目录，默认工作区的 `workflows/`；同名 `.api.json` / `.params.json` 优先，缺少时自动读取 skill 内置文件，无需项目预先提供工作流 |
| `projects_dir` | 项目目录，相对配置文件所在目录 |
| `video.model` | 新项目为 `minimax-h3`；旧配置缺少此项时识别为旧 Wan 配置，生成前提示迁移 |
| `video.width/height` | H3 宽高为 32 的倍数，默认竖屏 864×1536，横屏交换宽高；低分辨率预览可用 576×1024 |
| `video.fps` / `video.max_frames` | H3 为 24fps，默认 124 帧（约 5.17 秒），帧数为 `17k+5`；本技能支持上限 124–362 帧。CreateVideo 也必须为 24fps |
| `video.clip_slack_sec` | 镜头可比单个片段长出的秒数（默认 0.5），尾部在剪辑时定格或放慢 |
| `image.size` | 向 Tardis 请求的尺寸。竖屏 `1024x1536`、横屏 `1536x1024` |
| `tardis.script` | imagegen-tardis 的 `image_gen.py` 路径；`null` 时自动查找同级 skill 目录与 `~/.codex/skills` 等常见位置 |
| `roughcut` | 粗剪输出：帧率、放大倍数（864×1536 的 1.25 倍为 1080×1920）、画质、字幕字体 |
| `voice.design_workflow/direction_workflow` | 可选旁白工作流，默认 `tts-design` / `tts-direction` |
| `voice.generation` | 默认 `cfg_scale=4`、`max_new_tokens=256`，可在声音条目的 `settings` 覆盖；token 上限不代表精确时长 |
| `voice.music_gain_db/voice_gain_db` | 混音基础增益，默认歌曲 -3dB、旁白 0dB |
| `voice.duck_db/attack_sec/release_sec` | 旁白期间歌曲额外降低 -6dB，0.15 秒进入、0.25 秒恢复；每句可覆盖降音值 |

新项目创建时会把 `video` 设置写入 `project.json`，之后改配置不影响已有项目。

## 可选 Breeze TTS 2

仅在声音计划启用后使用。接口对应 Saganaki22 的 `ComfyUI-Breeze-TTS-2`，需要 `BreezeTTS2LoadModel`、`BreezeTTS2VoiceDesign`、`BreezeTTS2VoiceDirection`，以及 ComfyUI 原生 `LoadAudio` 和 `SaveAudioAdvanced`。模型配套文件与许可见 [voice-guide.md](voice-guide.md) 和模板中文 Note。加载器默认禁止自动下载；本技能不安装节点或下载模型。

模板 `tts-design.workflow.json` 用于音色试镜，`tts-direction.workflow.json` 用于参考音色配音。对应 `.api.json` 可直接作为脚本样例，用户导出到工作区的同名 API 优先。先运行 `mv.py comfy-validate tts-design tts-direction` 核对当前服务接口。`doctor` 把这两个可选类型的缺依赖标为警告，纯歌曲项目仍可继续。

参考录音经 ComfyUI 上传接口传送，无需两台电脑共享目录；录音和准确转写均保存在项目内。生成输出保留 24kHz 单声道 FLAC，交付混音为 48kHz 立体声 24-bit PCM WAV。

## 画幅：在 mv-creator 这一侧统一处理

Tardis 的出图尺寸是固定档位（竖屏 1024×1536，即 2:3），视频要 9:16。处理方式：

1. 生图提示词自动加上"后期会裁掉左右各约 8%"的构图提醒（按 `image.size` 和 `video` 自动计算）。
2. `frame-select` 时用 Pillow 按镜头的 `crop`（默认居中）裁成 9:16 并缩放到 `video` 尺寸，保存为 `frames/Sxx.png`。
3. ComfyUI 拿到的就是尺寸正确的图；`width/height` 同时注入到 `MiniMaxH3ImageToVideo` 节点。

这样做的好处：用户挑图时看到的就是最终进入视频的画面；画幅只在配置一处维护；换工作流或换生图模型都不用改裁切逻辑。

## ComfyUI 在另一台电脑上

- 启动时允许局域网访问：便携版在启动参数加 `--listen 0.0.0.0 --port 8188`；桌面版在设置中开启局域网监听。
- Windows 防火墙放行该端口（只在可信局域网中开放）。
- 在运行 Codex 的电脑上验证：浏览器打开 `http://<IP>:8188` 能看到界面，再运行 `mv.py doctor`。
- 脚本通过 `/upload/image` 上传关键帧到 ComfyUI 的 `input/mv-creator/<项目>/`，输出从 `/view` 下载回本机项目目录，两台机器不需要共享文件夹。

## 在 Codex 中使用

- 通过 youai-skills 插件安装，或把 `plugins/youai-skills/skills/` 复制到 `.agents/skills/`。mv-creator 与 imagegen-tardis、comfyui-minimax-music 在同一个 skills 目录下，脚本能自动找到 imagegen-tardis。
- 导出的工作流、配置和作品都放在你自己的工作区，不放进 skill 安装目录，插件更新不会覆盖它们。
- 脚本需要访问网络（局域网里的 ComfyUI 和 Tardis 接口）。Codex 沙箱默认可能禁止命令联网：在 Codex 配置中为工作区开启网络访问，或在命令请求授权时批准。
- 生成视频是长任务（每段几分钟），`clips` 逐段落盘，被中断后重跑同一命令即可接着做。

## Tardis 密钥

按 imagegen-tardis 的 SKILL.md 运行它的 `configure` 命令保存密钥（隐藏输入）。`doctor` 只检查密钥文件是否存在，不读取内容。

## doctor 常见结果

| 结果 | 处理 |
| --- | --- |
| 缺少 librosa / PIL / openai | 确认用的是 `.venv` 里的 Python，重新 `pip install -r requirements.txt` |
| 连不上 ComfyUI | 检查地址、端口、`--listen`、防火墙；ComfyUI 是否已启动 |
| 工作流缺失 | 内置类型先检查技能包中的 `.api.json` 是否完整，项目没有本地文件属于正常情况；仅自定义类型需提供 API，见 [workflows.md](workflows.md) |
| ComfyUI 缺少节点 | 在 ComfyUI Manager 中安装缺失的自定义节点，或更新 ComfyUI |
| 可选旁白工作流警告 | 不使用旁白可继续；使用时核对 Breeze 节点包及模型配套文件，再验证指定 TTS 类型 |
| 配音保存后无法测量时长 | 配置现有 ffprobe 或 soundfile；不要仅按 token 数推测音频时长 |
