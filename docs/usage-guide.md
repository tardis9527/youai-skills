# 📖 YouAI Skills 详细使用指南

本指南帮助你快速上手 YouAI Skills，并在实际项目中高效使用。

---

## 目录

- [核心概念](#核心概念)
- [使用方式](#使用方式)
  - [方式一：直接复制到任意 AI 工具](#方式一直接复制到任意-ai-工具)
  - [方式二：Windsurf（推荐）](#方式二windsurf推荐)
  - [方式三：Cursor](#方式三cursor)
  - [方式四：Claude Code](#方式四claude-code)
- [六个 Skill 详解](#六个-skill-详解)
- [工作流组合指南](#工作流组合指南)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 核心概念

### 什么是 Skill？

Skill 是一份精心设计的**结构化 AI 提示词**，包含：

- **角色设定** — 让 AI 扮演特定专家角色
- **执行步骤** — 分阶段引导 AI 完成任务
- **输出格式** — 规定产出物的结构和质量标准
- **行为约束** — 限制 AI 的越界行为，减少幻觉

### Skill vs 普通提示词

| 维度 | 普通提示词 | YouAI Skill |
|------|-----------|-------------|
| 输出稳定性 | 每次结果差异大 | 结构化模板，输出一致 |
| 质量控制 | 依赖使用者追问 | 内置自检清单和禁止行为 |
| 可复用性 | 一次性使用 | 跨项目复用 |
| 上下游衔接 | 独立使用 | 产出物可串联为工作流 |

---

## 使用方式

### 方式一：直接复制到任意 AI 工具

适用于 ChatGPT、Claude、豆包、Kimi 等任何支持长文本输入的 AI 对话工具。

**步骤**：

1. 打开 `skills/` 目录下对应的 Skill 文件（如 `01_project-analysis.md`）
2. **完整复制**文件内容（包括 YAML 头部元信息）
3. 粘贴到 AI 对话框中
4. 按 Skill 中的引导开始交互

**提示**：
- 建议在新对话中使用，避免上下文干扰
- 一次只使用一个 Skill，不要在同一对话中混合多个 Skill
- 如果使用的 AI 工具支持"系统提示词"功能，可将 Skill 内容设为系统提示词

### 方式二：Windsurf（推荐）

Windsurf 的 Workflow 功能可以将 Skill 注册为斜杠命令，使用体验最佳。

**安装**：

```bash
# 在你的项目根目录下创建 .windsurf/workflows/ 目录
mkdir -p .windsurf/workflows/

# 将 YouAI Skills 的 Windsurf 适配文件复制过去
cp platforms/windsurf/workflows/*.md your-project/.windsurf/workflows/
```

**使用**：

在 Windsurf 的 Cascade 对话框中输入 `/` 即可看到可用的 Skill 命令：

| 命令 | 对应 Skill |
|------|-----------|
| `/project-analysis` | 项目理解与分析 |
| `/product-discovery` | 产品需求探索与定义 |
| `/market-research` | 市场调研分析 |
| `/prd-generation` | PRD 文档生成 |
| `/uiux-redesign` | UI/UX 设计风格重塑 |
| `/investor-bp-generation` | 投资人BP商业计划报告生成 |

**提示**：
- Windsurf Workflow 中的 Skill 已针对 Cascade 做了格式适配
- 使用 `/project-analysis` 时，确保当前工作区已打开目标项目
- 使用 `/prd-generation` 时，建议先把实施方案文档放在项目的 `doc/` 目录下

### 方式三：Cursor（推荐）

Cursor 的 **Agent Skills** 功能（`.cursor/skills/{skill-name}/SKILL.md`）是 Skill 的正确使用方式，与 Rules 不同——Skill 由用户通过 @Skill 显式触发，适合产品开发这类阶段性工作流。

**安装**：

```bash
# 在你的项目根目录下创建 .cursor/skills/ 目录
mkdir -p .cursor/skills/

# 将 YouAI Skills 的 Cursor 适配目录复制过去
cp -r platforms/cursor/skills/* your-project/.cursor/skills/
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path .cursor\skills
Copy-Item -Recurse platforms\cursor\skills\* .cursor\skills\
```

**使用**：

1. 在 Cursor Agent 对话中输入 `@`，选择对应 Skill（如 `@project-analysis`、`@prd-generation`）
2. 描述你的需求，Agent 会先拉取 GitHub 上的完整 Skill 定义，再按流程执行
3. 一次对话建议只启用一个 Skill，避免工作流冲突

**提示**：
- Skill 入口文件轻量，完整定义从 `https://raw.githubusercontent.com/tardis9527/youai-skills/main/skills/` 远程读取，统一管理
- 若业务项目也克隆了 youai-skills 仓库，会优先使用本地 `skills/0X_*.md`
- 不要将 Skill 放入 `.cursor/rules/`，Rules 用于持久性编码规范，不适合阶段性产品工作流

### 方式四：Claude Code

Claude Code 的 **Agent Skills** 功能（`.claude/skills/{skill-name}/SKILL.md`）与 Cursor 一致，由用户通过 `/` 命令显式触发，适合产品开发这类阶段性工作流。每个 Skill 入口都设置了 `disable-model-invocation: true`，表示仅在用户主动调用时执行，不会被模型自动触发。

**安装**：

```bash
# 在你的项目根目录下创建 .claude/skills/ 目录
mkdir -p .claude/skills/

# 将 YouAI Skills 的 Claude Code 适配目录复制过去
cp -r platforms/claude-code/skills/* your-project/.claude/skills/
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path .claude\skills
Copy-Item -Recurse platforms\claude-code\skills\* .claude\skills\
```

**使用**：

1. 在 Claude Code 对话中输入 `/`，选择对应 Skill（如 `/project-analysis`、`/prd-generation`）
2. 描述你的需求，Claude Code 会先读取本地 `skills/0X_*.md`（不存在则从 GitHub 远程拉取）的完整定义，再按流程执行
3. 一次对话建议只启用一个 Skill，避免工作流冲突

**提示**：
- Skill 入口文件轻量，完整定义优先读本地 `skills/`，否则从 `https://raw.githubusercontent.com/tardis9527/youai-skills/main/skills/` 远程读取，统一管理
- 若业务项目也克隆了 youai-skills 仓库，会优先使用本地 `skills/0X_*.md`
- Skill 适合阶段性产品工作流，长期编码规范请使用 `CLAUDE.md` 而非 Skill

---

## 六个 Skill 详解

### 01 项目理解与分析

> 📂 文件：`skills/01_project-analysis.md`

**何时使用**：
- 接手一个新项目，需要快速了解全貌
- 做代码审查或技术尽调
- 评估一个开源项目是否值得采用

**输入**：一个已有的代码仓库（需要 AI 能访问代码文件）

**产出**：结构化项目理解报告，包含 8 个章节：
1. 项目概览
2. 产品功能
3. 技术架构
4. 代码结构
5. 核心实现逻辑
6. 构建与部署
7. 代码质量与技术债评估
8. 改进建议

**使用技巧**：
- 在 AI IDE（Windsurf/Cursor）中使用效果最好，AI 可以直接读取代码
- 如果项目较大（>50 个源码文件），AI 会先输出 1-6 节并征求确认
- 产出报告可直接作为 04_prd-generation 的参考输入

---

### 02 产品需求探索与定义

> 📂 文件：`skills/02_product-discovery.md`

**何时使用**：
- 你脑中有一个模糊的产品想法，想理清楚
- Hackathon 快速出方案
- 定义 MVP 范围

**输入**：你脑中的产品想法（可以很模糊）

**产出**：产品简报（Product Brief），包含 8 个章节：
1. 产品定位
2. 用户角色（1-3 个）
3. MVP 功能清单
4. 核心用户旅程
5. 可行性评估与技术约束
6. 明确排除项
7. 开放问题
8. 下一步行动

**使用技巧**：
- 这是一个**交互式** Skill，AI 会分 6 个阶段提问，不要跳过
- 阶段一的提问至关重要，尽量详细回答
- 如果你说"都要做"，AI 会追问你优先级——这是故意的
- 每个阶段结束时 AI 会输出阶段交付物并征求确认

---

### 03 产品市场调研分析

> 📂 文件：`skills/03_market-research.md`

**何时使用**：
- 评估一个赛道是否值得进入
- 融资前做市场分析
- 验证产品方向是否靠谱

**输入**：产品方向或名称（可来自 02 的产出）

**产出**：3000-5000 字的调研分析报告，包含 8 个章节：
1. 行业与市场背景
2. 竞品分析（3-5 款）
3. 目标用户与需求洞察
4. 功能场景拆解
5. 案例研究（3 个标杆）
6. 问题清单与风险预判
7. 方法论应用
8. 结论与建议

**使用技巧**：
- AI 的训练数据有时效性限制，报告中会用 `[公开信息]` / `[推测]` / `[估算]` 标注数据可信度
- 建议用 AI 报告作为**起点**，再用真实数据验证关键假设
- 分段输出，每次 1-2 章节，回复"继续"获取下一部分

---

### 04 PRD 文档生成

> 📂 文件：`skills/04_prd-generation.md`

**何时使用**：
- 已有产品简报或实施方案，需要转化为可落地的 PRD
- 需要输出给开发团队可直接执行的需求文档

**输入**：实施方案文档或产品简报（可来自 02/03 的产出）

**产出**：完整的 PRD 文档，包含 13 个章节：
1. 文档信息
2. 项目概述
3. 用户角色与权限矩阵
4. 信息架构
5. 功能需求清单（带编号、优先级、验收标准）
6. 核心业务流程图（Mermaid）
7. 数据模型设计
8. 接口设计规范
9. 技术方案与架构约束
10. 非功能性需求
11. 设计规范与 UI/UX 标准
12. 迭代规划
13. 风险与开放问题

**使用技巧**：
- 这是内容最丰富的 Skill，分 5 段输出，回复"继续"逐段获取
- 内置了默认技术栈偏好（React + NestJS + PostgreSQL），可根据你的项目替换
- AI 会在正式生成 PRD 前先输出"需求确认摘要"供你审核
- 输出完成后包含自检清单，确保无遗漏

---

### 05 UI/UX 设计风格重塑

> 📂 文件：`skills/05_uiux-redesign.md`

**何时使用**：
- 已有项目界面需要风格优化或品牌升级
- 需要系统性审计 UI/UX 问题
- 需要建立配色、排版、组件、动效等设计规范

**输入**：已有项目代码仓库 + 产品背景信息（可来自 01/02 的产出）。

**产出**：UI/UX 设计重塑方案，包含设计背景、现状审计、设计策略、设计规范、实施方案、风险策略和附录。

**使用技巧**：
- AI 会先理解产品上下文，再审计现有 UI 实现
- 设计建议应回溯到用户群体和产品目标
- 产出可作为 PRD 或前端改版的设计约束输入

---

### 06 投资人BP商业计划报告生成

> 📂 文件：`skills/06_investor-bp-generation.md`

**何时使用**：
- 已有产品简报，需要生成融资 BP 或商业计划书
- 准备投资人初次沟通、Demo Day 或路演材料
- 希望把 PRD、市场调研、竞品分析整合成投资人能快速理解的材料

**输入**：Product Brief 为主，可选 PRD、市场调研报告、竞品分析、项目理解报告、团队/财务/融资资料。

**产出**：
1. Markdown 完整 BP 报告，保存到 `doc/BP商业计划报告_{产品名称}_{YYYYMMDD}.md`
2. 或 HTML PPT 演示版，保存到 `doc/BP_{产品名称}_{YYYYMMDD}/`
3. AI 聊天界面额外输出 500 字以内口述版项目 BP 介绍

**使用技巧**：
- 先确认输出 Markdown、HTML，还是两者都要
- HTML 版本会拆分 `index.html`、`assets/css/style.css`、`assets/js/main.js`，可直接复制目录到 Nginx 静态访问
- 融资、收入、市场规模、客户名称等数据不能编造，缺失时会标注 `[待补充]`

---

## 工作流组合指南

### 场景 A：新产品从 0 开始

```
02 产品需求探索 → 03 市场调研 → 04 PRD 生成
```

1. 用 02 把模糊想法梳理成 Product Brief
2. 用 03 对产品方向做市场调研和竞品分析
3. 将 Product Brief + 调研报告一起喂给 04，生成完整 PRD

### 场景 B：接手已有项目

```
01 项目分析 → 04 PRD 生成
```

1. 用 01 快速理解项目代码和架构
2. 基于项目理解报告 + 新需求方案，用 04 生成 PRD

### 场景 C：验证产品方向

```
02 产品需求探索 → 03 市场调研 → 决策
```

1. 用 02 明确产品定位和 MVP 范围
2. 用 03 验证市场空间和竞争格局
3. 基于调研结论决定是否继续推进

### 场景 D：单独使用

每个 Skill 也可以独立使用，无需串联。例如：
- 只用 01 做代码审查
- 只用 03 做竞品分析
- 只用 04 把已有方案转为 PRD
- 只用 06 把已有 Product Brief 转为融资 BP

### 场景 E：融资 BP 准备

```
02 产品需求探索 → 03 市场调研 → 06 投资人BP生成
```

1. 用 02 明确产品定位、目标用户、MVP 和核心价值
2. 用 03 补充市场空间、竞品格局和风险判断
3. 将 Product Brief、市场调研、PRD、团队/财务资料一起提供给 06，生成 Markdown BP 或 HTML 路演演示版

---

## 最佳实践

### 1. 充分提供上下文

AI 的输出质量取决于你给的输入质量。使用 Skill 时：
- 尽可能详细地回答 AI 的追问
- 提供已有的文档、链接、参考资料
- 如果有竞品，主动告诉 AI

### 2. 分阶段确认，不要一口气跑完

大部分 Skill 设计了分阶段输出和确认机制：
- 每个阶段产出后，仔细审核再说"继续"
- 发现方向偏了，及时纠正，不要等到最后
- 可以随时回退到前一阶段

### 3. AI 输出是起点，不是终点

- Skill 产出的报告是**高质量初稿**，不是最终成品
- 关键数据、假设需要你自己验证
- 市场调研报告中标注 `[推测]` 的部分需补充真实数据

### 4. 产出物要保存和版本管理

- 所有 Skill 约定将产出保存到 `doc/` 目录
- 建议将产出文件纳入 Git 版本管理
- 文件命名已包含日期，便于追溯

---

## 常见问题

### Q: AI 不按 Skill 定义的格式输出怎么办？

可能原因：
- 输入内容太少，AI 没有足够上下文
- 对话上下文太长，Skill 指令被"冲淡"

解决方法：
- 在新对话中重新开始
- 提醒 AI："请按照 Skill 定义的格式输出"
- 使用 Windsurf Workflow 或 Cursor @Skill 触发，格式更稳定

### Q: 项目太大，AI 分析不完怎么办？

01_project-analysis 内置了大项目处理策略：
- >50 个源码文件时，先输出概览章节（1-6），确认后再输出评估章节（7-8）
- 可以要求 AI 聚焦特定模块深入分析

### Q: 我的技术栈不是 React + NestJS，怎么用 04_prd-generation？

04 的技术栈偏好是默认值，可以替换：
- 在对话开头告诉 AI 你的技术栈
- AI 会在"需求确认"阶段让你确认技术选型
- PRD 中会标注替换理由

### Q: 可以用英文输出吗？

目前 Skill 默认中文输出。如需英文：
- 在对话开头说明"请用英文输出"
- 或等待社区贡献英文版 Skill（欢迎 PR！）

### Q: 如何贡献新 Skill？

参考 [CONTRIBUTING.md](../CONTRIBUTING.md)，核心要求：
1. 在 `skills/` 下创建源文件
2. 包含 YAML 元信息头
3. 包含角色设定、执行步骤、输出格式、行为约束
4. 同步创建 Windsurf 和 Cursor 的适配版本
