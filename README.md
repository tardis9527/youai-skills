# 🍊 YouAI Skills — 柚子AI Skills

**为创造者准备的 AI 技能包** — 一套覆盖从产品构思、PRD 落地、原型设计图到融资 BP 准备的结构化 AI 提示词，适配主流 AI IDE。

[English](./README_en.md) | 中文

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![Windsurf](https://img.shields.io/badge/Windsurf-Compatible-00C4B4)](./docs/usage-guide.md)
[![Cursor](https://img.shields.io/badge/Cursor-Compatible-7C3AED)](./docs/usage-guide.md)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-D97757)](./docs/usage-guide.md)
[![Codex](https://img.shields.io/badge/Codex-Compatible-111827)](./docs/usage-guide.md)

---

## ✨ 为什么需要这个项目？

大多数 AI 编程提示词聚焦在"怎么写代码"，但**决定做什么远比怎么写代码更重要**。

这套 Skill Pack 覆盖产品开发中的决策、设计、内容创作与图片制作，帮助你用 AI 完成从模糊想法到可落地 PRD、再到投资人 BP 的全过程。

---

## 🔗 工作流全景

十个 Skill 覆盖产品开发、内容传播与图片制作，相关产出物可作为其他 Skill 的输入：

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           YouAI Skills                                  │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 01 项目   │  │ 02 需求   │  │ 03 市场   │  │ 04 PRD   │  │ 05 UI/UX │  │
│  │ 理解分析  │  │ 探索定义  │─▶│ 调研分析  │─▶│ 文档生成  │  │ 设计重塑  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│       │              │             │              │            │         │
│       │ 已有项目      │ 新产品       │ 融资前分析    │ 产品方案    │ 品牌表达 │
│       └──────────────┴─────────────┴──────────────┴────────────┘         │
│                              ▼                                           │
│                  ┌──────────┐   ┌──────────┐   ┌──────────┐             │
│                  │ 06 投资人 │   │ 07 原型与 │   │ 08 公众号 │             │
│                  │ BP 生成   │   │ 设计图    │   │ 自进化写作│             │
│                  └──────────┘   └──────────┘   └──────────┘             │
│                                                                          │
│  场景A：新产品从0开始      ──▶ 02 → 03 → 04                              │
│  场景B：接手已有项目      ──▶ 01 → 04                                    │
│  场景C：验证产品方向      ──▶ 02 → 03 → 决策                             │
│  场景D：UI/UX 设计优化   ──▶ 01 → 05（或 02 → 05）                      │
│  场景E：融资BP准备       ──▶ 02/03/04 → 06                              │
│  场景F：原型与设计图出图  ──▶ 04 → 07（或 02 → 07）                      │
│  场景G：公众号内容写作    ──▶ 08（独立，可接 02/03 素材）                 │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Skill 清单

| # | Skill | 使用场景 | 输入 | 产出 |
|---|-------|---------|------|------|
| 01 | [项目理解与分析](./skills/01_project-analysis.md) | 接手新项目、代码审查、技术尽调 | 已有代码仓库 | 结构化项目理解报告 |
| 02 | [产品需求探索与定义](./skills/02_product-discovery.md) | 从0到1产品孵化、MVP定义、Hackathon快速出方案 | 模糊的产品想法 | Product Brief（产品简报，11 节） |
| 03 | [产品市场调研分析](./skills/03_market-research.md) | 赛道评估、竞品分析、方向验证 | 产品方向/名称 | 调研分析报告 |
| 04 | [PRD 文档生成](./skills/04_prd-generation.md) | 实施方案转PRD、功能详细设计 | 实施方案文档 | 完整可落地的PRD |
| 05 | [UI/UX 设计风格重塑](./skills/05_uiux-redesign.md) | 界面风格优化、品牌升级、设计系统重构 | 已有项目 + 产品背景 | UI/UX 设计重塑方案 |
| 06 | [投资人BP商业计划报告生成](./skills/06_investor-bp-generation.md) | 融资路演、投资人沟通、商业计划书准备 | Product Brief + PRD/市场/竞品资料 | Markdown BP 或 HTML 演示版 + 口述版 |
| 07 | [产品原型与界面设计图提示词生成](./skills/07_prototype-design.md) | 产品界面设计、原型设计、设计稿/出图提示词生成 | PRD / 产品简报 | 原型交互草图 + 各页面 AI 出图提示词（中英双语，统一风格） |
| 08 | [公众号文章自进化写作](./skills/08_wechat-writer.md) | 写公众号文章、起标题大纲、去 AI 味、润色成个人文风 | 一个写作主题（可选参考文章/风格偏好） | 通过六维评分自审的公众号定稿 + 沉淀到本地知识库的学习记录 |
| 09 | [朋友圈文案自进化写作](./skills/09_moments-writer.md) | 写朋友圈配文、发圈文案、去朋友圈"塑料感" | 一个发圈场景（可选人设风格/篇幅偏好） | 3-5 条通过轻量检查表自审的候选文案 + 沉淀到本地知识库的学习记录 |
| 10 | [Tardis 生图](./skills/imagegen-tardis/SKILL.md) | 通过自定义供应商生成或编辑图片 | 图片需求；本机 Codex API Key | 图片文件及聊天内预览、下载链接 |

---

## 🚀 快速开始

### 方式一：直接使用（任何 AI 工具）

1. 打开 [`skills/`](./skills/) 目录中对应的 Skill 文件
2. 将完整内容复制到你的 AI 对话中（ChatGPT / Claude / 任何 AI）
3. 按提示词中的引导开始交互

### 方式二：Windsurf（推荐）

Windsurf 的 Workflow 需要 `.windsurf/workflows/` 下的扁平 `.md` 文件，把每个 Skill 入口复制成同名 workflow：

```bash
# 复制 Windsurf workflows
mkdir -p your-project/.windsurf/workflows
for d in skills/*/; do cp "$d/SKILL.md" "your-project/.windsurf/workflows/$(basename "$d").md"; done
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path .windsurf\workflows
Get-ChildItem skills -Directory | ForEach-Object { Copy-Item "$($_.FullName)\SKILL.md" ".windsurf\workflows\$($_.Name).md" }
```

然后在 Windsurf 中使用 `/` 命令触发：
- `/project-analysis` — 项目理解与分析
- `/product-discovery` — 产品需求探索
- `/market-research` — 市场调研分析
- `/prd-generation` — PRD 文档生成
- `/uiux-redesign` — UI/UX 设计风格重塑
- `/investor-bp-generation` — 投资人BP商业计划报告生成
- `/prototype-design` — 产品原型与界面设计图提示词生成
- `/wechat-writer` — 公众号文章自进化写作
- `/moments-writer` — 朋友圈文案自进化写作

### 方式三：Cursor（推荐）

将 `skills/` 下的各 Skill 目录复制到你项目的 `.cursor/skills/` 目录：

```bash
# 复制 Cursor Agent Skills
mkdir -p your-project/.cursor/skills/
cp -r skills/*/ your-project/.cursor/skills/
```

在 Cursor Agent 对话中通过 **@Skill** 选择对应 Skill 触发（如 `@project-analysis`）。Skill 定义会从 GitHub 远程拉取，无需拷贝完整 `skills/` 源文件。

### 方式四：Claude Code（推荐）

将 `skills/` 下的各 Skill 目录复制到你项目的 `.claude/skills/` 目录：

```bash
# 复制 Claude Code Agent Skills
mkdir -p your-project/.claude/skills/
cp -r skills/*/ your-project/.claude/skills/
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path .claude\skills
Get-ChildItem skills -Directory | Copy-Item -Recurse -Destination .claude\skills\
```

在 Claude Code 对话中通过 `/` 命令触发对应 Skill（如 `/project-analysis`）。Skill 入口轻量，完整定义优先读本地 `skills/`，否则从 GitHub 远程拉取。

### 方式五：Codex（推荐）

**通过插件市场安装（适合从 Git 仓库分发）**：在 Codex 的「添加插件市场」中填入来源 `https://github.com/tardis9527/youai-skills.git`，Git 引用填 `main`，稀疏路径留空。添加市场后，在市场中安装 `youai-skills` 插件，并开启新会话。该插件包含全部 10 个 Skill 及其完整定义。

命令行也可以添加市场并安装插件：

```powershell
codex plugin marketplace add https://github.com/tardis9527/youai-skills.git --ref main
codex plugin add youai-skills@youai-skills
```

**直接安装 Skill**：将 `skills/` 下的各 Skill 目录复制到你项目的 `.agents/skills/` 目录：

```powershell
# 复制 Codex Agent Skills（项目级）
New-Item -ItemType Directory -Force -Path .agents\skills
Get-ChildItem skills -Directory | Copy-Item -Recurse -Destination .agents\skills\
```

如需在当前用户的所有 Codex 项目中复用，可复制到个人 Codex skills 目录：

```powershell
# 复制 Codex Agent Skills（个人级）
New-Item -ItemType Directory -Force -Path $env:USERPROFILE\.agents\skills
Get-ChildItem skills -Directory | Copy-Item -Recurse -Destination $env:USERPROFILE\.agents\skills\
```

安装后重启 Codex 或开启新会话。在 Codex 对话中通过 `$skill-name` 显式触发，例如：
- `$project-analysis` — 项目理解与分析
- `$product-discovery` — 产品需求探索
- `$market-research` — 市场调研分析
- `$prd-generation` — PRD 文档生成
- `$uiux-redesign` — UI/UX 设计风格重塑
- `$investor-bp-generation` — 投资人BP商业计划报告生成
- `$prototype-design` — 产品原型与界面设计图提示词生成
- `$wechat-writer` — 公众号文章自进化写作
- `$moments-writer` — 朋友圈文案自进化写作
- `$imagegen-tardis` — 使用自定义供应商生成或编辑图片，并在 Codex 聊天中预览和下载（需本机 `~/.codex/auth.json`）

---

## 📋 Skill 特点

- **🔗 链式可组合** — 10个Skill可按需求串联，产出物可复用
- **📐 结构化输出** — 每个Skill定义了明确的输出格式和质量标准
- **🛡️ 行为约束** — 内置角色设定、禁止行为、自检清单，减少AI胡说
- **🔄 交互式引导** — 分阶段推进，每步确认，避免方向跑偏
- **🏗️ 技术栈灵活** — PRD Skill 内置常用技术栈偏好，支持按项目需求替换
- **📱 多端覆盖** — 支持 Web + 移动端（React Native）的完整产品设计

---

## 🗂️ 项目结构

```
youai-skills/
├── .plugin/plugin.json       # Open Plugins 标准清单
├── .agents/plugins/marketplace.json # Codex 插件市场清单
├── plugins/youai-skills/     # Codex 插件安装包（由 scripts/sync-codex-plugin.ps1 同步）
│   ├── .codex-plugin/plugin.json
│   └── skills/              # 10 个 Skill 与完整定义的打包副本
├── scripts/sync-codex-plugin.ps1 # 更新源 Skill 后重新生成安装包
├── README.md                 # 项目介绍（中文）
├── README_en.md              # 项目介绍（English）
├── LICENSE                   # MIT 开源协议
├── CONTRIBUTING.md           # 贡献指南
│
├── skills/                   # 🎯 唯一来源：Skill 源文件 + Open Plugins SKILL.md 入口
│   ├── 01_project-analysis.md
│   ├── 02_product-discovery.md
│   ├── 03_market-research.md
│   ├── 04_prd-generation.md
│   ├── 05_uiux-redesign.md
│   ├── 06_investor-bp-generation.md
│   ├── 07_prototype-design.md
│   ├── 08_wechat-writer.md
│   ├── 09_moments-writer.md
│   ├── project-analysis/     # SKILL.md 入口，可直接装到各平台的 skills 目录
│   ├── product-discovery/    # 自带 references/（痛点库+可行性清单）与 knowledge/（团队画像+历史复盘）
│   ├── market-research/
│   ├── prd-generation/
│   ├── uiux-redesign/
│   ├── investor-bp-generation/
│   ├── prototype-design/
│   ├── wechat-writer/        # 自带 references/（规则+风格）与 knowledge/（自进化记忆）
│   ├── moments-writer/       # 自带 references/（规则+风格）与 knowledge/（自进化记忆）
│   └── imagegen-tardis/     # 自定义供应商生图 Skill，含 API 调用脚本
│
├── examples/                 # 使用示例（产出样例）
│
└── docs/                     # 文档
    ├── usage-guide.md        # 详细使用指南（含各平台安装方式）
    └── distribution-guide.md # 分发指南
```

> 📌 **单一来源**：`skills/` 是 Skill 源目录。修改后运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-codex-plugin.ps1` 更新 Codex 插件包，再提交两处变更。插件副本会移除 Codex 不支持的 `disable-model-invocation: true` 字段。Cursor / Claude Code / Codex 也可直接安装源目录中的入口；Windsurf 复制成 `.windsurf/workflows/{name}.md`。

---

## 🤝 贡献

欢迎贡献新的 Skill 或改进现有 Skill！请参阅 [CONTRIBUTING.md](./CONTRIBUTING.md)。

你可以贡献的方向：
- 🐛 改进现有 Skill 的提示词质量
- ✨ 贡献新场景的 Skill（如：技术方案设计、API设计、测试用例生成等）
- 🌐 翻译 Skill 为其他语言
- 📖 补充使用示例和最佳实践
- 🔌 新增平台适配（如 JetBrains AI、GitHub Copilot 等）

---

## 📄 开源协议

本项目采用 [MIT License](./LICENSE) 开源。

---

## ⭐ Star History

如果这个项目对你有帮助，请给一个 Star ⭐ 支持！

---

> **YouAI 理念**：在写第一行代码之前，先用 AI 把产品方向想清楚。 🍊
