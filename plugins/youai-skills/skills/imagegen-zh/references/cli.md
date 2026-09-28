# CLI 备选路径

仅在用户明确要求或确认使用 CLI、Image API、指定模型或 CLI 专属参数时阅读和执行。普通生图、透明图及“批量”请求默认使用内置 `image_gen`。

## 条件与命令

- 真实 API 请求需要网络权限、环境变量 `OPENAI_API_KEY` 和 Python 包 `openai`；无须在聊天中粘贴密钥。
- `--dry-run` 只检查参数和目标路径，不调用 API，也不需要密钥或 `openai` 包。
- `generate` 生成新图；`edit` 编辑一张或多张输入图；`generate-batch` 从 JSONL 运行多个不同的生成任务。
- 使用本 Skill 自带的 `scripts/image_gen.py`，不要临时重写 API 调用脚本，也不要修改该脚本。

下面示例从 `youai-skills` 仓库根目录运行。PowerShell 的 `$ImageGenScript` 是示例变量；把 Skill 复制到 Codex 的其他加载目录后，应按实际位置调整它。

```powershell
$ImageGenScript = '.\skills\imagegen-zh\scripts\image_gen.py'
python $ImageGenScript generate --prompt '测试' --out '.\outputs\test.png' --dry-run
python -m pip install openai
```

生成、编辑、批量生成示例：

```powershell
python $ImageGenScript generate --prompt '晨光中的陶瓷咖啡杯产品摄影' --size 1024x1024 --out '.\outputs\mug.png'
python $ImageGenScript edit --image '.\input.png' --prompt '只更换背景；主体及边缘保持不变' --out '.\outputs\edited.png'
python $ImageGenScript generate-batch --input '.\prompts.jsonl' --out-dir '.\outputs\batch' --concurrency 5
```

`prompts.jsonl` 每行是一个 JSON 对象；不同素材各用一行。`--n` 用于同一提示词的多个变体。交付文件按用户指定位置保存；本项目可用 `outputs/`。不要覆盖已有文件，除非明确要求，脚本也会在已有目标文件时拒绝写入，显式 `--force` 才会覆盖。

## 默认值与关键参数

| 项目 | 默认值 / 说明 |
| --- | --- |
| 模型 | `gpt-image-2` |
| 尺寸 | `auto`；`gpt-image-2` 常用 `1024x1024`、`1536x1024`、`1024x1536`、`2048x1152`、`3840x2160` |
| 质量 | `medium`；草稿可用 `low`，成品和密集文字可用 `high` 或 `auto` |
| 格式 | `png`；也可用 `jpeg`、`webp`，压缩参数只适用于后两者 |
| 输出 | `--out` 指定单任务路径，`--out-dir` 指定目录；批量命令必须用 `--out-dir` |
| 编辑输入 | 重复 `--image` 传多图，顺序须与提示词中的“图 1、图 2”一致 |
| 遮罩 | `edit --mask`；遮罩和首张图尺寸、格式一致，都小于 50 MB，遮罩应有 alpha；效果仍受提示词影响 |
| 输入保真度 | `--input-fidelity low|high` 仅用于支持它的编辑模型，不能用于 `gpt-image-2` |

`gpt-image-2` 的自定义宽高都要是 16 的倍数，最长边不超过 3840 像素，长短边比不超过 3:1，总像素数为 655,360 到 8,294,400。4K 横图可用 `3840x2160`，竖图用 `2160x3840`。较高质量或尺寸会增加耗时和成本。

## 透明输出

CLI 的 `gpt-image-2` 不支持 `--background transparent`。需要原生透明时，向用户说明必须切换为 `gpt-image-1.5`，在用户明确同意后使用 PNG 或 WebP：

```powershell
python $ImageGenScript generate --model gpt-image-1.5 --prompt '透明背景上的干净产品抠图' --background transparent --output-format png --out '.\outputs\cutout.png'
```

如果用户接受纯色背景转 alpha，可继续用 `gpt-image-2` 生成纯色底图，再在本地使用 `scripts/remove_chroma_key.py`。这依赖 `pillow`，复杂边缘可能需要人工检查。不要将此法误称为模型原生透明输出。

## 网络与故障

网络权限由当前 Codex 环境决定，`--ask-for-approval never` 本身不会开放网络。只有用户明确选择 CLI 路径后，才处理 API Key、包安装和相关网络设置。用户未设置密钥时，指引其在本机配置 `OPENAI_API_KEY`，不要要求在对话中发送完整密钥。

若模型拒绝某参数，可在该参数不是用户硬性要求时去掉后重试；若透明是硬性要求，不能靠删除 `--background transparent` 假装完成。可通过 `python $ImageGenScript <子命令> --help` 查看完整参数。官方参数或模型能力可能更新，实际调用前以当前 API 文档和脚本帮助为准。
