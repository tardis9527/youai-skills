---
name: imagegen-tardis
description: 通过 Tardis 的 OpenAI 兼容接口生成或编辑位图，默认使用 gpt-image-2.6-sunburst，支持用 gpt-image-2.6-flare 快速试稿，并在 Codex 聊天中预览和交付图片。适用于用户指定使用 Tardis 生图通道的请求。
---

# Tardis 生图

使用本目录的 `scripts/image_gen.py` 调用 `https://sub-tardis.ai-you.top/`。脚本将该站点的 `/v1` 作为默认 OpenAI 兼容 API 路径；如供应商提供不同路径，可用 `--base-url` 指定完整 API Base URL。真实请求会产生供应商费用。

## 模型与试稿选择

| 用户意图 | 使用模型 | 脚本参数 |
| --- | --- | --- |
| 未指定模式、正式出图、最终交付 | `gpt-image-2.6-sunburst`（默认） | 不传模型参数 |
| 快速试稿、先看效果、探索构图或风格 | `gpt-image-2.6-flare` | `--draft` |
| 明确指定模型 | 用户指定的模型 | `--model <模型名>` |

- 生成和编辑均遵循同一选择规则。用户明确指定模型时优先遵循，`--model` 与 `--draft` 互斥；不要根据“快一点”等偏好覆盖其指定模型。
- 未表达试稿意图时直接用默认模型，不必每次追问。需要补充用途或风格时，可顺带提供“默认正式出图 / 快速试稿”选择；已有选择直接沿用，用户要求“转正式图 / 出最终版”时切回 Sunburst，明确指定的其他模型除外。
- 快速试稿用于确认方向，不自动降低尺寸、质量或修改用户指定的数量；未指定数量时默认 1 张，不额外生成正式版或模型对比图。
- 试稿后交付预览并注明“试稿”和实际模型。用户要求制作正式图后，用 Sunburst 生成或编辑；需要延续布局或主体时，将选中的试稿作为 `edit --image` 输入，并保留已确认的提示词、画幅、文字和约束，保存为新文件。
- 模型不可用或参数不兼容时说明实际错误，不静默换模型、删减约束或重发付费请求。不根据“试稿”名称承诺更低价格或固定速度。

## 密钥配置

脚本默认从当前用户主目录动态解析凭据路径：

```text
Path.home() / ".tardis-skill" / "imagegen-tardis" / "credentials.json"
```

首次使用或凭据无效时，先在聊天中主动向用户索取 Tardis API Key。收到用户提供的密钥后，在终端运行以下命令，通过隐藏输入完成保存，再继续原来的生成或编辑请求：

```powershell
python .\skills\imagegen-tardis\scripts\image_gen.py configure
```

配置命令会自动创建目录、原子写入凭据并避免在输出中显示密钥。不要把密钥放进命令行参数、提示词、日志或聊天回复。后续请求直接读取该凭据文件。需要测试或手动迁移时，可显式传入 `--credential-file`；`--auth-file` 和 `--config-file` 仅作为显式兼容参数，不会自动回退读取。

## 生成与编辑

1. 明确用途、主体、风格、画幅、数量、画面文字和必须保留的内容。原需求详细时只整理表达；笼统时可补足合理的构图细节，不添加未经要求的品牌、人物或文案。
2. 提示词按“用途 → 主体与场景 → 关键细节 → 构图与光线 → 必须出现的文字 → 保留或避免项”组织，按需要选用，不机械填满。编辑时写明“只改什么、保持什么不变”；多张输入图要在提示词中逐一编号和说明角色。
3. 按“模型与试稿选择”确定模型，用脚本 `generate` 生新图，`edit` 修改现有图。默认生成 PNG。用户指定尺寸、质量、输出格式或保存位置时，传入对应参数；不要假定其他模型支持相同参数。
4. 脚本只在本机读取 `~/.tardis-skill/imagegen-tardis/credentials.json` 中的 `api_key`。首次使用按“密钥配置”流程向用户索取并保存。不要在命令行、提示词、日志或聊天回复中输出密钥。安装依赖仅需 `openai` Python 包。
5. 检查输出图片是否存在、能打开，核对主体、文字和编辑约束。除非用户要求覆盖，使用新文件名保存；项目素材还应更新项目中的引用。

从仓库根目录调用的示例；复制 Skill 后应使用实际安装路径：

```powershell
python .\skills\imagegen-tardis\scripts\image_gen.py generate --prompt '哑光陶瓷咖啡杯，真实产品摄影，柔和摄影棚光，无商标和文字' --out .\outputs\cup.png
python .\skills\imagegen-tardis\scripts\image_gen.py generate --draft --size 1536x1024 --prompt '横幅产品照片，先确认构图与光线，无文字' --out .\outputs\banner-draft.png
python .\skills\imagegen-tardis\scripts\image_gen.py edit --image .\outputs\banner-draft.png --prompt '保留构图、主体与光线，完善产品材质和边缘细节，无文字' --out .\outputs\banner-final.png
python .\skills\imagegen-tardis\scripts\image_gen.py generate --model gpt-image-2.6-flare --prompt '用户明确指定 Flare 的产品照片' --out .\outputs\custom-model.png
python .\skills\imagegen-tardis\scripts\image_gen.py edit --image .\input.png --prompt '只更换背景，主体与边缘保持不变' --out .\outputs\edited.png
```

以上为独立用法示例；试稿与正式图分两次按用户需求调用，不整段批量执行。可用 `--prompt-file` 传入 UTF-8 文本文件。`--n` 生成同一提示词的多个变体；不同素材分别调用。`--dry-run` 仅检查参数和文件路径，不读取密钥、不调用接口，也不验证模型可用性。运行 `python scripts/image_gen.py --help` 查看完整参数。

## Codex 交付

生成或编辑完成后，在**最终聊天回复**中直接嵌入每张交付图片，使用户在 Codex 聊天框内看到预览：

```markdown
![图片预览](C:/absolute/path/to/output.png)
[下载原图](C:/absolute/path/to/output.png)
```

把示例路径替换为脚本输出的**绝对路径**；脚本已将 Windows 路径转换为 Markdown 友好的正斜杠形式。路径含空格时用 `<...>` 包住链接目标。不要只给文件名、相对路径或 Markdown 代码块，也不要只调用 `view_image` 而省略最终回复中的图片。多张图逐张嵌入并提供各自的文件链接；如果图片无法在聊天中渲染，仍给出可访问的绝对文件链接。简要注明试稿或正式出图、实际模型和保存位置。
