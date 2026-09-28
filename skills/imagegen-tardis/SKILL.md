---
name: imagegen-tardis
description: 通过自定义 OpenAI 兼容图片接口生成或编辑位图，默认使用 gpt-image-2，并在 Codex 聊天中预览和交付图片。适用于用户指定使用 Tardis 生图通道的请求。
---

# Tardis 生图

使用本目录的 `scripts/image_gen.py` 调用 `https://sub-tardis.ai-you.top/`。脚本将该站点的 `/v1` 作为默认 OpenAI 兼容 API 路径；如供应商提供不同路径，可用 `--base-url` 指定完整 API Base URL。默认模型是 `gpt-image-2`，用户指定模型时传入 `--model`，不要擅自改回默认模型。真实请求会产生供应商费用。

## 生成与编辑

1. 明确用途、主体、风格、画幅、数量、画面文字和必须保留的内容。原需求详细时只整理表达；笼统时可补足合理的构图细节，不添加未经要求的品牌、人物或文案。
2. 提示词按“用途 → 主体与场景 → 关键细节 → 构图与光线 → 必须出现的文字 → 保留或避免项”组织，按需要选用，不机械填满。编辑时写明“只改什么、保持什么不变”；多张输入图要在提示词中逐一编号和说明角色。
3. 用脚本 `generate` 生新图，`edit` 修改现有图。默认生成 PNG。用户指定模型、尺寸、质量、输出格式或保存位置时，传入对应参数；不要假定替代模型支持与 `gpt-image-2` 相同的参数。
4. 脚本只在本机从 `~/.codex/auth.json` 的 `OPENAI_API_KEY` 字段读取密钥。不要在命令行、提示词、日志或聊天回复中输出密钥。安装依赖仅需 `openai` Python 包。
5. 检查输出图片是否存在、能打开，核对主体、文字和编辑约束。除非用户要求覆盖，使用新文件名保存；项目素材还应更新项目中的引用。

从仓库根目录调用的示例；复制 Skill 后应使用实际安装路径：

```powershell
python .\skills\imagegen-tardis\scripts\image_gen.py generate --prompt '哑光陶瓷咖啡杯，真实产品摄影，柔和摄影棚光，无商标和文字' --out .\outputs\cup.png
python .\skills\imagegen-tardis\scripts\image_gen.py generate --model gpt-image-2 --size 1536x1024 --prompt '横幅产品照片' --out .\outputs\banner.png
python .\skills\imagegen-tardis\scripts\image_gen.py edit --image .\input.png --prompt '只更换背景，主体与边缘保持不变' --out .\outputs\edited.png
```

可用 `--prompt-file` 传入 UTF-8 文本文件。`--n` 生成同一提示词的多个变体；不同素材分别调用。`--dry-run` 仅检查参数和文件路径，不调用接口。运行 `python scripts/image_gen.py --help` 查看完整参数。

## Codex 交付

生成或编辑完成后，在**最终聊天回复**中直接嵌入每张交付图片，使用户在 Codex 聊天框内看到预览：

```markdown
![图片预览](C:/absolute/path/to/output.png)
[下载原图](C:/absolute/path/to/output.png)
```

把示例路径替换为脚本输出的**绝对路径**；脚本已将 Windows 路径转换为 Markdown 友好的正斜杠形式。路径含空格时用 `<...>` 包住链接目标。不要只给文件名、相对路径或 Markdown 代码块，也不要只调用 `view_image` 而省略最终回复中的图片。多张图逐张嵌入并提供各自的文件链接；如果图片无法在聊天中渲染，仍给出可访问的绝对文件链接。简要注明模型和保存位置。
