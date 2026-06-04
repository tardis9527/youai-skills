---
name: youai-skills
description: 面向产品开发全流程的 AI 技能包 —— 包含 6 个结构化技能，覆盖项目分析、产品探索、市场调研、PRD 生成、UI/UX 设计优化与投资人 BP 生成。帮助你在写下第一行代码之前，做出正确的产品与融资决策。
---

# YouAI Skills — 产品开发 AI 技能包

> 🍊 GitHub: https://github.com/tardis9527/youai-skills

在写第一行代码之前，先用 AI 把产品方向想清楚。

## 包含 6 个 Skill

### 1. 项目理解与分析（Project Analysis）
系统性分析代码库，输出结构化项目理解报告，涵盖技术架构、代码质量、改进建议。
- 适用场景：接手新项目、代码审查、技术尽调
- 产出：8 节结构化报告

### 2. 产品需求探索与定义（Product Discovery）
六阶段交互式引导，将模糊想法转化为结构化产品简报（Product Brief）。
- 适用场景：0-1 产品构思、Hackathon、MVP 定义
- 产出：Product Brief（含用户画像、MVP 功能清单、可行性评估）

### 3. 产品市场调研分析（Market Research）
系统性竞品分析、市场规模估算、用户洞察、风险评估。
- 适用场景：评估赛道、融资前分析、验证产品方向
- 产出：3000-5000 字调研报告（含数据可信度标注）

### 4. PRD 文档生成（PRD Generation）
将实施方案转化为可落地的 PRD，含功能规格、数据模型、API 设计、迭代规划。
- 适用场景：方案转 PRD、输出开发文档
- 产出：13 章完整 PRD（含验收标准、Mermaid 流程图）

### 5. UI/UX 设计风格重塑（UI/UX Redesign）
结合产品背景与用户画像，系统性审计现有界面并输出完整设计重塑方案。
- 适用场景：界面风格优化、品牌升级、设计系统重构
- 产出：设计重塑方案（含配色/排版/组件规范、实施路线图）

### 6. 投资人BP商业计划报告生成（Investor BP Generation）
基于产品简报、PRD、市场调研和竞品分析，生成面向投资人的 BP 商业计划报告或 HTML 路演演示版。
- 适用场景：融资路演、Demo Day、投资人初次沟通、商业计划书准备
- 产出：Markdown BP 报告或 HTML PPT 演示版 + 500字以内口述版项目BP介绍

## 使用方式

1. **复制粘贴**：将 `skills/` 目录下对应的 Skill 文件完整复制到 AI 对话中
2. **Windsurf**：将 `platforms/windsurf/workflows/` 下的文件复制到项目的 `.windsurf/workflows/`
3. **Cursor**：将 `platforms/cursor/skills/` 下的目录复制到项目的 `.cursor/skills/`，通过 @Skill 触发
4. **Claude Code**：将 `platforms/claude-code/skills/` 下的目录复制到项目的 `.claude/skills/`，通过 `/` 命令触发

## 工作流串联

```
新产品从 0 开始：    产品探索 → 市场调研 → PRD 生成
接手已有项目：      项目分析 → PRD 生成
验证产品方向：      产品探索 → 市场调研 → 决策
UI/UX 设计优化：   项目分析 → 设计重塑（或 产品探索 → 设计重塑）
融资BP准备：       产品探索/市场调研/PRD → 投资人BP
```

## 核心特性

- 🔗 链式可组合 — 每个 Skill 的产出物可直接作为其他 Skill 的输入
- 📐 结构化输出 — 定义明确的输出格式和质量标准
- 🛡️ 行为约束 — 内置角色设定、禁止行为、自检清单
- 🔄 交互式引导 — 分阶段推进，每步确认
- 🏗️ 技术栈灵活 — 默认技术栈可替换

详细文档和示例请访问 GitHub 仓库。
