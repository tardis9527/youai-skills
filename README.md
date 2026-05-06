# 🍊 YouAI Skills — 柚子AI Skills

**为创造者准备的 AI 技能包** — 一套覆盖从产品构思到 PRD 落地的结构化 AI 提示词，适配主流 AI IDE。

[English](./README_en.md) | 中文

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![Windsurf](https://img.shields.io/badge/Windsurf-Compatible-00C4B4)](./platforms/windsurf/)
[![Cursor](https://img.shields.io/badge/Cursor-Compatible-7C3AED)](./platforms/cursor/)

---

## ✨ 为什么需要这个项目？

大多数 AI 编程提示词聚焦在"怎么写代码"，但**决定做什么远比怎么写代码更重要**。

这套 Skill Pack 覆盖了产品开发的**前半段关键决策流程**，帮助你用 AI 完成从模糊想法到可落地 PRD 的全过程——**在写第一行代码之前，先把方向搞对**。

---

## 🔗 工作流全景

四个 Skill 形成一条完整的产品开发链路，每个 Skill 的产出物可直接作为下一个 Skill 的输入：

```
┌─────────────────────────────────────────────────────────────────┐
│                      YouAI Skills                              │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 01 项目   │    │ 02 需求   │    │ 03 市场   │    │ 04 PRD   │  │
│  │ 理解分析  │    │ 探索定义  │───▶│ 调研分析  │───▶│ 文档生成  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │                │                               ▲        │
│       │ 已有项目        │ 新产品                        │        │
│       └────────────────┴───────────────────────────────┘        │
│                                                                 │
│  场景A：新产品从0开始 ──▶ 02 → 03 → 04                          │
│  场景B：接手已有项目 ──▶ 01 → 04                                │
│  场景C：验证产品方向 ──▶ 02 → 03 → 决策                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Skill 清单

| # | Skill | 使用场景 | 输入 | 产出 |
|---|-------|---------|------|------|
| 01 | [项目理解与分析](./skills/01_project-analysis.md) | 接手新项目、代码审查、技术尽调 | 已有代码仓库 | 结构化项目理解报告 |
| 02 | [产品需求探索与定义](./skills/02_product-discovery.md) | 从0到1产品孵化、MVP定义 | 模糊的产品想法 | Product Brief（产品简报） |
| 03 | [产品市场调研分析](./skills/03_market-research.md) | 赛道评估、竞品分析、方向验证 | 产品方向/名称 | 调研分析报告 |
| 04 | [PRD 文档生成](./skills/04_prd-generation.md) | 实施方案转PRD、功能详细设计 | 实施方案文档 | 完整可落地的PRD |

---

## 🚀 快速开始

### 方式一：直接使用（任何 AI 工具）

1. 打开 [`skills/`](./skills/) 目录中对应的 Skill 文件
2. 将完整内容复制到你的 AI 对话中（ChatGPT / Claude / 任何 AI）
3. 按提示词中的引导开始交互

### 方式二：Windsurf（推荐）

将 `platforms/windsurf/workflows/` 下的文件复制到你项目的 `.windsurf/workflows/` 目录：

```bash
# 复制 Windsurf workflows
cp -r platforms/windsurf/workflows/ your-project/.windsurf/workflows/
```

然后在 Windsurf 中使用 `/` 命令触发：
- `/project-analysis` — 项目理解与分析
- `/product-discovery` — 产品需求探索
- `/market-research` — 市场调研分析
- `/prd-generation` — PRD 文档生成

### 方式三：Cursor

将 `platforms/cursor/rules/` 下的文件复制到你项目的 `.cursor/rules/` 目录：

```bash
# 复制 Cursor rules
cp -r platforms/cursor/rules/ your-project/.cursor/rules/
```

在 Cursor 中开始对话时，相关 Skill 会自动作为上下文加载。

---

## 📋 Skill 特点

- **🔗 链式可组合** — 4个Skill形成工作流，产出物可串联
- **📐 结构化输出** — 每个Skill定义了明确的输出格式和质量标准
- **🛡️ 行为约束** — 内置角色设定、禁止行为、自检清单，减少AI胡说
- **🔄 交互式引导** — 分阶段推进，每步确认，避免方向跑偏
- **🏗️ 技术栈灵活** — PRD Skill 内置常用技术栈偏好，支持按项目需求替换
- **📱 多端覆盖** — 支持 Web + 移动端（React Native）的完整产品设计

---

## 🗂️ 项目结构

```
youai-skills/
├── README.md                 # 项目介绍（中文）
├── README_en.md              # 项目介绍（English）
├── LICENSE                   # MIT 开源协议
├── CONTRIBUTING.md           # 贡献指南
│
├── skills/                   # 🎯 核心 Skill 文件（Source of Truth）
│   ├── 01_project-analysis.md
│   ├── 02_product-discovery.md
│   ├── 03_market-research.md
│   └── 04_prd-generation.md
│
├── platforms/                # 各平台适配版本
│   ├── windsurf/workflows/   # Windsurf workflow 格式
│   └── cursor/rules/         # Cursor rules 格式
│
├── examples/                 # 使用示例（产出样例）
│
└── docs/                     # 文档
    └── usage-guide.md        # 详细使用指南
```

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

本项目采用 [MIT License](./LICENSE) 开源。你可以自由使用、修改和分发，但请保留原作者署名。

---

## ⭐ Star History

如果这个项目对你有帮助，请给一个 Star ⭐ 支持！

---

> **YouAI 理念**：在写第一行代码之前，先用 AI 把产品方向想清楚。 🍊
