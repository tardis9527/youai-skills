# 🍊 YouAI Skills — 柚子AI Skills

**在写代码前，把一句产品想法变成产品简报、PRD 和原型设计方案。**

面向独立开发者、个人项目作者和 Hackathon 团队的开源 AI Skill 工作流。支持 Codex、Claude Code、Cursor 和 Windsurf，也可将完整提示词复制到 AI 对话中使用。

[English](./README_en.md) · [体验教程](./examples/teamlog-walkthrough.md) · [安装指南](./docs/usage-guide.md) · [全部 Skill](#全部-skill)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)

## 从一句想法开始

> “我想做一个团队日报助手，让技术负责人更快了解团队进展。”

| 步骤 | Skill 帮你梳理什么 | 查看 TeamLog 样例 |
|---|---|---|
| 需求探索 | 给谁用、核心痛点、MVP 范围、如何找到首批用户 | [产品简报](./examples/example-product-discovery.md) |
| PRD 生成 | 功能、验收标准、数据模型、接口与页面的对应关系 | [PRD 节选](./examples/example-prd-generation.md) |
| 原型设计 | 页面清单、关键状态、线框布局、统一视觉风格和出图提示词 | [原型方案节选](./examples/example-prototype-design.md) |

```mermaid
flowchart LR
    A[一句产品想法] --> B[product-discovery<br/>产品简报]
    B --> C[prd-generation<br/>PRD]
    C --> D[prototype-design<br/>原型方案与出图提示词]
```

TeamLog 是虚构产品，以上为人工编写的精简结构样例，展示交付形式；不代表真实用户案例或实测效果。[按体验教程运行自己的版本 →](./examples/teamlog-walkthrough.md)

## 第一次使用

**无需安装，先体验需求探索：** 打开 [产品需求探索完整定义](./skills/02_product-discovery.md)，复制全文到一个新的 AI 对话，再发送：

```text
我想做一个面向小型技术团队的日报助手。
请按 Express 模式，先帮我明确目标用户、核心痛点和 MVP 范围。
一期先做 Web，不做 Git 自动关联；不确定的内容请标为待验证。
```

回答 AI 的追问并确认范围后，你会得到产品简报初稿。继续生成 PRD 和原型时，将上一步的文档作为输入；只有文本对话时，粘贴内容即可。[完整操作与检查点 →](./examples/teamlog-walkthrough.md)

**Codex 用户可安装完整插件包：** 在「添加插件市场」中填写以下仓库地址，Git 引用填 `main`，稀疏路径留空；然后安装 `youai-skills`，开启新会话。

```text
https://github.com/tardis9527/youai-skills.git
```

安装后发送：

```text
$product-discovery 我想做一个团队日报助手。请按 Express 模式梳理 MVP。
```

使用其他工具，或希望通过命令行、项目级目录安装？查看 [安装与使用指南](./docs/usage-guide.md)。

## 使用条件

- Skill 内容采用 MIT 协议免费开源；AI 工具订阅、模型 API 和图片接口的费用由对应服务收取。
- 主推工作流可先完成文档、线框和出图提示词。生成真实图片是可选步骤，需要额外配置图片接口。
- Skill 正文和多数样例目前为中文；英文 README 与 [英文体验教程](./examples/teamlog-walkthrough_en.md) 可用于了解流程，完整英文 Skill 翻译尚未提供。
- AI IDE 可读取文件并保存产物；纯文本对话需要手动提供参考资料、保存结果。调研所需的联网检索取决于使用的工具。
- 产出用于起草与评审。市场数据、技术决策、权限和验收标准仍需人工核对；未解决的问题应保留在开放问题表中。

## 全部 Skill

十一个 Skill 可独立使用，也可将产出文档交给下一步。首次体验建议从上面的三个核心 Skill 开始。

| Skill | 适用场景 | 主要产出 |
|---|---|---|
| [product-discovery](./skills/02_product-discovery.md) | 从模糊想法定义产品与 MVP | 产品简报、关键假设与验证计划 |
| [prd-generation](./skills/04_prd-generation.md) | 将简报或实施方案转为开发规格 | PRD、验收标准、需求追踪矩阵 |
| [prototype-design](./skills/07_prototype-design.md) | 将需求转为页面与交互方案 | 线框、设计规范、中英出图提示词；可选真实生图 |
| [project-analysis](./skills/01_project-analysis.md) | 接手已有项目、理解业务与代码 | 项目理解报告 |
| [market-research](./skills/03_market-research.md) | 评估方向、竞品与市场风险 | 调研报告与置信度标注 |
| [uiux-redesign](./skills/05_uiux-redesign.md) | 改善已有产品的界面与体验 | 设计系统规范与实施路线图 |
| [investor-bp-generation](./skills/06_investor-bp-generation.md) | 准备融资与路演材料 | Markdown BP / HTML 演示版与口述介绍 |
| [wechat-writer](./skills/08_wechat-writer.md) | 公众号写作与个人文风积累 | 定稿、配图提示词与本地学习记录 |
| [moments-writer](./skills/09_moments-writer.md) | 朋友圈文案与风格积累 | 候选文案、配图方案与本地学习记录 |
| [imagegen-tardis](./skills/imagegen-tardis/SKILL.md) | 通过自定义供应商生成或编辑图片 | 图片文件、预览与下载链接 |
| [comfyui-minimax-music](./skills/comfyui-minimax-music/SKILL.md) | 在 ComfyUI 中使用 MiniMax Music 3 创作歌曲或纯音乐 | Caption、Lyrics、工作流参数与音质导出建议 |

其他常用组合：

- **验证方向：** 需求探索 → 市场调研 → 决策 → PRD。
- **接手已有项目：** 项目分析 → PRD；需要改版时接 UI/UX 设计重塑。
- **准备融资：** 产品简报 + 市场调研 / PRD → 投资人 BP。
- **内容创作：** 公众号、朋友圈 Skill 可独立使用，图片生成按需接入。

## 为什么使用这套工作流

- **阶段确认：** 先明确用户与范围，再展开功能和设计；需求探索支持 Express / Standard / Deep 节奏。
- **文档衔接：** 下一步读取已确认的产物，减少重复解释项目背景。
- **质量检查：** PRD 和原型包含证据、状态、追踪与自检要求；未知内容需明确标注。
- **可编辑与复用：** 提示词和支撑资料保存在仓库中，可按项目调整；技术栈默认值可替换。

## 文档与贡献

- [示例索引](./examples/README.md)：查看各 Skill 的交付结构。
- [使用指南](./docs/usage-guide.md)：各平台安装、工作流和常见问题。
- [贡献指南](./CONTRIBUTING.md)：反馈问题、贡献实际案例、翻译或改进 Skill。
- [分发与推广指南](./docs/distribution-guide.md)：项目定位、分享文案和发布检查。

反馈问题时，请说明工具版本、Skill 名称、脱敏后的输入及实际结果。也欢迎分享人工修改记录，帮助改进工作流。

如果这套工作流对你有帮助，欢迎 **Star** 收藏并支持项目。

## 仓库维护

`skills/` 是唯一源目录；`plugins/youai-skills/skills/` 是由脚本生成的完整 Codex 安装包，包含入口及完整定义。更新源 Skill 后运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-codex-plugin.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-skill-sync.ps1
```

插件副本会移除 Codex 不支持的 `disable-model-invocation: true` 字段。PRD / 原型产物可使用 `scripts/validate-product-artifact.ps1` 检查结构，具体参数见使用指南。

本项目采用 [MIT License](./LICENSE)。
