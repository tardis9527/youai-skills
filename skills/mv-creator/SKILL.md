---
name: mv-creator
description: 基于 ComfyUI API 与 Tardis 生图，按"创意简报 → 原创歌曲（作词作曲与 AI 演唱） → 节拍分镜 → 角色与关键帧 → 图生视频 → 剪映素材与粗剪"全流程制作歌曲 MV（默认 30–60 秒竖屏剧情短片，不对口型）。适用于从零创作 AI 歌曲 MV、续做已有 MV 项目、重跑某个镜头或重新导出剪映素材；歌曲提示词交给 comfyui-minimax-music，生图交给 imagegen-tardis。不用于 ComfyUI 安装维护、模型下载或对口型数字人视频。
---

# 歌曲 MV 创作流水线

像 MV 导演兼制片一样，带用户把一个想法做成可交给剪映精剪的整套素材。默认中文沟通。创作内容（歌词、分镜、提示词）由你和用户讨论确定；生成、上传、下载、裁切、拼接全部交给本 skill 的脚本，状态写进项目文件，不只留在聊天里。

## 约定

- `<SKILL_DIR>` 指本 SKILL.md 所在目录。所有命令用 `python <SKILL_DIR>/scripts/mv.py <命令>`，在**用户工作区根目录**（放 `mv-creator.config.json` 的目录）执行。示例按 Windows PowerShell 书写。
- 依赖两个 skill：**imagegen-tardis**（所有生图/改图）与 **comfyui-minimax-music**（歌曲 Caption 与 Lyrics）。脚本会通过子进程调用 imagegen-tardis 的 `image_gen.py`，你仍需先读它的 SKILL.md，按其提示词规则写图片提示词、按其流程配置密钥。
- ComfyUI 可以在另一台电脑上，地址写在配置的 `comfyui.url`。脚本负责上传输入、提交 API 工作流、等待完成并把输出下载回项目目录。
- 每个命令运行后，都以命令输出为准汇报结果：成功说成功，失败贴出关键报错，不粉饰。

## 开始之前

1. 工作区没有 `mv-creator.config.json` 时运行 `mv.py init-config`，再请用户确认 `comfyui.url`。
2. 新机器首次使用、或任何命令报环境错误时运行 `mv.py doctor`，按 [references/setup.md](references/setup.md) 逐项处理。不要替用户安装软件或改系统设置，给出命令让用户确认。
3. 需要调用 ComfyUI 前，确认 `mv.py comfy-validate` 通过。工作流 JSON 由用户从官方模板导出，放在工作区的 `workflows/`（不放进 skill 安装目录），规则见 [references/workflows.md](references/workflows.md)；不要自行修改其中的模型文件名或采样参数。

## 项目与断点续跑

- 新作品：`mv.py new "<作品名>"`，在 `projects/<slug>/` 下建立目录、`project.json` 与创意简报模板。
- 续做：先运行 `mv.py status <slug>`，按它给出的"下一步"推进；不要凭聊天记忆判断进度。
- 目录结构与 `project.json`、`shots.json` 字段见 [references/project-schema.md](references/project-schema.md)。修改 `shots.json` 时保持字段结构，改完运行 `mv.py shots-check <slug>`。
- 已被用户确认的内容（选定的歌、镜头、关键帧、视频片段）不擅自重做或覆盖；重跑只针对用户指定的镜头。

## 阶段与确认点

每轮只推进当前阶段最需要确定的 1–2 件事。带 ⏸ 的步骤必须等用户明确选择后再进入下一阶段；用户说"你来定"时在其委托范围内代选并注明。

**先替用户写好，再请用户确认。** 简报、歌曲参数、分镜和所有生图/生视频提示词都由你根据已确定的信息起草完整版本，用户只需确认或指出要改的地方；不要把空白模板或一连串开放问题丢给用户。调用其他 skill 准备素材时同样如此：先把能从 MV 上下文推出的输入整理好交给它，只留下真正需要用户选择的项目。提示词一律用中文。

### 1. 创意简报

根据用户的想法直接起草完整的 `projects/<slug>/brief.md`（模板已生成）：主题与情绪、目标时长（默认 30–60 秒）、画幅（默认 9:16 竖屏）、歌曲方向（曲风、人声、语言、副歌 hook）、视觉风格关键词、主要角色、四段故事（起承转合）。用户只有一句话时，先给 2–3 个不同方向的创意种子供选，选定后再起草全文；推断出的内容标为"建议"。⏸ 简报确认后再写歌。

### 2. 歌曲（原创演唱歌曲）

MV 的歌是从零创作、带人声演唱的完整原创歌曲，不是背景配乐：歌词、旋律和演唱都要新写，画面围绕这首歌展开。

1. 按 [references/music-handoff.md](references/music-handoff.md) 把简报转换成 comfyui-minimax-music 需要的选择状态，**一次性给出预填好的参数卡**（作品名称候选、用途、时长、听感、人声、歌词方向、文件格式、采样率与 seed 策略），每项标明来源和推荐理由。⏸ 用户回复"确认"或只改个别项即可。
2. 参数确认后，按 **comfyui-minimax-music** 的规则写出 Caption 与完整 Lyrics，并按它的模板保存 Markdown 文档到 `projects/<slug>/music/`。它的创作规则和自查照常执行；已在参数卡中确认的项目不再重复提问。
3. 把成稿的 Caption、Lyrics 原样分别写入 `music/caption.txt`、`music/lyrics.txt`（UTF-8，与文档一致，不加说明文字）。
4. 生成前告知将跑几版、预计占用 GPU 的时间，然后运行 `mv.py music <slug> --takes 4 --duration <秒>`。seed 由脚本每版随机并记录在 `project.json`，可复现。
5. ⏸ 列出各版文件的绝对路径请用户试听，用户选定后运行 `mv.py music-select <slug> <take-N>`。不满意时按 comfyui-minimax-music 的"听后修改"归类问题，只改相关字段再跑。

### 3. 节拍分析与分镜

1. `mv.py analyze <slug>`：估算 BPM、拍点、小节线和每小节能量，写入 `analysis/beats.json`。
2. `mv.py shots-init <slug> --bars-per-shot 2`：按小节切出镜头时间骨架（单个片段最长 81 帧/16fps ≈ 5 秒，镜头最多再长 0.5 秒，由剪辑定格或放慢补齐）。已有 `shots.json` 时它会拒绝覆盖，需要重切先征得用户同意再加 `--force`。
3. 按 [references/storyboard-guide.md](references/storyboard-guide.md) 填写全局 `style`、`characters` 和每个镜头的 `section`、`lyric`、`scene`、`characters`、`image_prompt`、`motion_prompt`、`camera`、`workflow`。可合并或拆分镜头，但时间要连续且每段不超时。
4. `mv.py shots-check <slug>` 校验并生成 `storyboard/storyboard.md`。⏸ 把分镜表给用户确认。

### 4. 角色与关键帧（Tardis 生图，产生费用，一次确认）

图片提示词不需要用户写：`characters[].prompt` 和各镜头的 `image_prompt` 已在分镜阶段由你起草，脚本会自动补上用途、角色参考图编号说明、全局风格和裁切安全区，组成符合 imagegen-tardis 规则的完整提示词（保存在 `prompts/` 目录，用户想看时再展示）。

1. 先用 `chars`/`frames` 加 `--dry-run` 核对并告知本阶段总调用次数（角色数 + 镜头数，每次 `--n` 张），然后一口气完成生成：
   - 角色设定图：`mv.py chars <slug> --n 2`。
   - 逐张查看候选，挑出与角色描述最贴合、脸部最清晰的一张作为**暂定参考图**：`mv.py char-select <slug> <角色id> <序号>`。
   - 关键帧：`mv.py frames <slug> --n 2`。有角色的镜头自动走 `edit` 并带上暂定参考图，保持人物一致。
2. ⏸ **一次确认角色与关键帧**：在回复中按 imagegen-tardis 的交付方式嵌入全部候选图（绝对路径），先列角色候选并标出暂定选择，再按镜号列关键帧候选。请用户一次回复，例如"角色用 2；S01 选 1，S02 选 2，S04 重做：人物再靠近镜头"。
3. 按回复执行：
   - 选定关键帧：`mv.py frame-select <slug> <镜号> <序号或图片路径>`。脚本按项目画幅裁切并缩放为视频输入尺寸（如 720×1280），所见即所得；构图需要偏上/偏下时把镜头的 `crop` 设为 `top`/`bottom`，再运行 `frame-select <slug> <镜号>`（省略序号即按原图重裁）。
   - 用户换了角色参考图：重新 `char-select`，再对用到该角色、且用户没有明确保留的镜头 `frames --shots ...` 重做（先说明调用次数）。
   - 用户要求重做的镜头：只改该镜头的 `image_prompt`，`frames --shots ...` 后只展示这些镜头的新候选。
4. 所有镜头都选定关键帧后再进入下一阶段。

### 5. 图生视频（ComfyUI，耗时）

1. 用 `mv.py clips <slug> --takes 2 --dry-run` 核对并告知待生成镜头数、每镜头几版，然后去掉 `--dry-run` 运行。默认跳过已有视频的镜头；`--shots` 指定镜头时总会新增版本；`--more` 给所有镜头追加版本。任务串行执行、逐个落盘，中断后重跑同一命令即可续上。
2. `workflow` 为 `flf2v` 的镜头使用首尾帧工作流，用下一镜头的关键帧作为尾帧，用于转场；需要下一镜头先选好关键帧。
3. ⏸ 列出各镜头视频路径请用户挑选，`mv.py clip-select <slug> <镜号> <take-N>`。动作崩坏时只改该镜头的 `motion_prompt`（动作更简单、一个镜头一件事），再 `--shots` 重跑。

### 6. 交付：剪映素材与粗剪

1. `mv.py package <slug>`：在 `final/capcut/` 整理按时间顺序编号的视频片段、关键帧、歌曲（有 ffmpeg 时另转 WAV）、按镜头时间生成的 `lyrics.srt`、小节线时间表和《剪辑清单.md》。
2. `mv.py roughcut <slug>`（需要 ffmpeg）：按分镜时间把选定片段裁切/定格到对应时长、拼接并合入歌曲，输出 `final/roughcut.mp4` 作为剪辑参考；缺视频的镜头用关键帧静帧代替。加 `--burn-subs` 另出一版烧录歌词字幕。
3. 把素材目录、粗剪路径和清单中的未完成项告诉用户，并按 [references/capcut-handoff.md](references/capcut-handoff.md) 给出剪映导入步骤。

## 通用规则

- **花钱或耗时的操作先说数量**：Tardis 生图按次计费；ComfyUI 生成占用 GPU。用户确认范围后再跑，不擅自加量。
- 密钥只由 imagegen-tardis 的 `configure` 流程保存，不在命令行、提示词、日志或回复中出现。
- 脚本报错时先读报错：ComfyUI 返回 `node_errors` 多为模型文件名、缺节点或参数映射问题，按 [references/workflows.md](references/workflows.md) 排查并告诉用户，不擅自改工作流里的模型和采样设置。
- 单段视频时长受工作流帧数上限约束；超长镜头拆分，不要靠拉长帧数硬撑。
- 用户换方向时只调整受影响的阶段与镜头，保留其余已确认内容。
- 其他 ComfyUI 工作流（补帧、超分等）可用通用命令 `mv.py comfy-run <kind> --upload <参数>=<文件> --set <参数>=<值> --out <目录>` 调用，映射规则同上。
