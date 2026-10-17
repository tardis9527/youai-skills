# 📖 YouAI Skills 安装与使用指南

[返回首页](../README.md) · [首次体验教程](../examples/teamlog-walkthrough.md) · [English walkthrough](../examples/teamlog-walkthrough_en.md)

首次使用建议先跑“需求探索 → PRD → 原型方案”。本指南提供安装路径、十个 Skill 的说明和常见问题。

## 目录

- [使用前准备](#使用前准备)
- [无需安装：直接复制完整定义](#无需安装直接复制完整定义)
- [Codex：完整插件包](#codex完整插件包)
- [Cursor 与 Claude Code：项目级安装](#cursor-与-claude-code项目级安装)
- [Codex：手动目录安装](#codex手动目录安装)
- [Windsurf：Workflow 入口](#windsurfworkflow-入口)
- [十个 Skill 详解](#十个-skill-详解)
- [工作流组合指南](#工作流组合指南)
- [产物校验与仓库维护](#产物校验与仓库维护)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 使用前准备

- Skill 内容免费开源，运行时需要自己的 AI 工具或模型服务。服务订阅、API 和图片接口可能收费。
- 主推流程可以只输出文档、线框和提示词。真实生图需另行配置，见 [imagegen-tardis](../skills/imagegen-tardis/SKILL.md)。
- Skill 目录可能包含 `references/` 和可写的 `knowledge/`，安装时应保留。再次安装前备份已有记忆，避免用仓库初始文件覆盖积累内容。
- 下方手动安装命令用于**首次安装到新项目**。已经存在同名 Skill 时，先检查差异，不能直接用复制命令覆盖。
- AI IDE 能读取项目文件；纯文本对话需要粘贴输入和手动保存产物。完整 Skill 定义和多数样例目前为中文。

## 无需安装：直接复制完整定义

1. 打开 [产品需求探索完整定义](../skills/02_product-discovery.md)，复制全文到新对话。
2. 发送需求，例如“我想做一个团队日报助手，请按 Express 模式先梳理 MVP”。
3. 回答追问并确认范围，将产品简报保存下来。
4. 下一阶段在新对话中复制 [PRD 完整定义](../skills/04_prd-generation.md)，附上简报全文。

复制的是 `skills/02_product-discovery.md` 等**完整定义**，不是只负责加载定义的 `SKILL.md` 入口。无文件系统时，记忆改为在对话中记录；可以按 [TeamLog 教程](../examples/teamlog-walkthrough.md) 继续到原型阶段。

## Codex：完整插件包

在「添加插件市场」中填入：

```text
https://github.com/tardis9527/youai-skills.git
```

Git 引用填 `main`，稀疏路径留空。添加市场后安装 `youai-skills`，并开启新会话。

支持插件命令的 Codex CLI 也可执行：

```powershell
codex plugin marketplace add https://github.com/tardis9527/youai-skills.git --ref main
codex plugin add youai-skills@youai-skills
```

插件包包含十个 Skill 的入口、完整定义和支撑文件；使用时无需再从 GitHub 下载定义。AI 模型本身和调研检索仍可能需要联网。若当前版本没有插件入口或命令，使用下面的手动目录安装。

调用示例：

```text
$product-discovery 我想做一个团队日报助手，请按 Express 模式梳理 MVP。
```

## Cursor 与 Claude Code：项目级安装

先克隆仓库。命令中的 `youaiRoot` / `youai_root` 是本仓库路径，`projectRoot` / `project_root` 是你要使用 Skill 的业务项目路径，两者分开设置。

Windows PowerShell：

```powershell
git clone https://github.com/tardis9527/youai-skills.git
Set-Location youai-skills
$youaiRoot = (Get-Location).Path
$projectRoot = 'D:\demo\my-product' # 改成你的目标项目绝对路径
```

Cursor 首次安装：

```powershell
$skillTarget = Join-Path $projectRoot '.cursor\skills'
New-Item -ItemType Directory -Force -Path $skillTarget | Out-Null
Get-ChildItem -LiteralPath (Join-Path $youaiRoot 'skills') |
    Copy-Item -Recurse -Destination $skillTarget
```

Claude Code 首次安装：

```powershell
$skillTarget = Join-Path $projectRoot '.claude\skills'
New-Item -ItemType Directory -Force -Path $skillTarget | Out-Null
Get-ChildItem -LiteralPath (Join-Path $youaiRoot 'skills') |
    Copy-Item -Recurse -Destination $skillTarget
```

macOS / Linux：

```bash
git clone https://github.com/tardis9527/youai-skills.git
cd youai-skills
youai_root="$PWD"
project_root="/absolute/path/to/my-product" # 改成你的目标项目绝对路径

# Cursor
mkdir -p "$project_root/.cursor/skills"
cp -R "$youai_root/skills/." "$project_root/.cursor/skills/"

# Claude Code
mkdir -p "$project_root/.claude/skills"
cp -R "$youai_root/skills/." "$project_root/.claude/skills/"
```

只执行你使用的平台对应的安装段。复制内容同时包含 Skill 子目录和 `01_*.md` 等完整定义，入口可从父目录加载；不用只复制轻量入口后再依赖 GitHub 远程读取。

安装后在目标项目开启新会话。Cursor 使用 Skill 选择入口（如 `@product-discovery`）；Claude Code 使用 `/product-discovery`。界面入口随工具版本可能不同，先确认能看到 Skill，再发送需求。

## Codex：手动目录安装

先按上一节克隆仓库并设置源目录、目标项目目录。Codex 使用**已生成的插件副本**，保留完整定义，并避免源入口中不受支持的 `disable-model-invocation: true` 字段。

项目级首次安装（Windows PowerShell）：

```powershell
$skillTarget = Join-Path $projectRoot '.agents\skills'
New-Item -ItemType Directory -Force -Path $skillTarget | Out-Null
Get-ChildItem -LiteralPath (Join-Path $youaiRoot 'plugins\youai-skills\skills') |
    Copy-Item -Recurse -Destination $skillTarget
```

个人级首次安装时，把上面第一行换成：

```powershell
$skillTarget = Join-Path $env:USERPROFILE '.agents\skills'
```

macOS / Linux 项目级安装：

```bash
mkdir -p "$project_root/.agents/skills"
cp -R "$youai_root/plugins/youai-skills/skills/." "$project_root/.agents/skills/"
```

个人级安装：

```bash
mkdir -p ~/.agents/skills
cp -R "$youai_root/plugins/youai-skills/skills/." ~/.agents/skills/
```

开启新会话后，通过 `$skill-name` 显式调用，十个名称见后面的 Skill 详解。插件市场安装和手动安装选一种即可，避免同时加载同名 Skill。

## Windsurf：Workflow 入口

先克隆仓库并设置 `youaiRoot` 与 `projectRoot`。Workflow 使用扁平的 `.md` 入口：

```powershell
$workflowTarget = Join-Path $projectRoot '.windsurf\workflows'
New-Item -ItemType Directory -Force -Path $workflowTarget | Out-Null
Get-ChildItem -LiteralPath (Join-Path $youaiRoot 'skills') -Directory |
    ForEach-Object {
        Copy-Item -LiteralPath (Join-Path $_.FullName 'SKILL.md') -Destination (Join-Path $workflowTarget ($_.Name + '.md'))
    }
```

macOS / Linux：

```bash
mkdir -p "$project_root/.windsurf/workflows"
for skill_dir in "$youai_root"/skills/*/; do
  cp "$skill_dir/SKILL.md" "$project_root/.windsurf/workflows/$(basename "$skill_dir").md"
done
```

在 Cascade 中使用 `/product-discovery` 等命令。此方式复制的是轻量入口，完整定义在工作区不可用时会尝试 GitHub 远程读取。需要本地资料和记忆时，向 Agent 提供本仓库中对应 Skill 目录的实际路径，例如 `D:\tools\youai-skills\skills\product-discovery`；扁平入口本身不包含这些支撑文件。生图脚本也需要完整的 `imagegen-tardis/` 目录及其运行条件。

---

## 十个 Skill 详解

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
- 在 AI IDE（Windsurf/Cursor/Codex）中使用效果最好，AI 可以直接读取代码
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

**产出**：产品简报（Product Brief），包含 11 个章节：
1. 产品背景与目标
2. 产品定位与价值主张
3. 用户角色（1-3 个）
4. MVP 功能清单
5. 核心用户旅程（含空状态/失败/中断恢复三类异常分支）
6. 成功指标（1 个北极星 + 辅助指标 + 反向指标）
7. 可行性评估与技术约束
8. 冷启动与分发路径
9. 明确排除项
10. 关键假设与验证计划
11. 下一步行动

> 文末附「下游交接校验表」，逐项确认 03 / 04 / 06 所需输入是否齐备。

**三档节奏，开场自动判定**：

| 模式 | 什么时候用 | 你要停下来确认几次 | 大概几轮 |
|------|----------|-----------------|---------|
| ⚡ Express | Hackathon、周末项目、想法已较清晰 | 2 | 4-6 |
| 🎯 Standard（默认） | 常规 0-1 产品定义 | 4 | 10-15 |
| 🔬 Deep | 要拿去融资、需团队对齐、方向没定 | 6 | 20+ |

说一句"快速出个方案"就会走 Express；中途随时可以说"加速"或"展开"切档。

**使用技巧**：
- 这是一个**交互式** Skill，但只在确认点停下来等你拍板，不会每轮都问
- 阶段一的提问至关重要，尽量详细回答；尤其是**"第一批 10 个用户从哪找"**这题
- 如果你说"都要做"，AI 会追问你优先级——这是故意的
- 如果你说"你定"，AI 会直接采用它的推荐并标注 `[AI默认]` 记入假设表，不会来回踢皮球
- 每阶段有**通过条件**，答得太空（如"目标用户是所有需要提效的人"）会被要求补具体
- 对话中断了不用重来：技能会检测 `doc/drafts/*_WIP.md` 草稿并询问是否续做
- 团队规模、技术栈、预算这些信息只需说一次，之后存进 `knowledge/team-profile.md` 复用

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

**产出**：完整的 PRD 文档，包含 14 个章节（新增需求追踪矩阵附录）：
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
14. 需求追踪矩阵

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

### 07 产品原型与界面设计图提示词生成

完整定义：[prototype-design](../skills/07_prototype-design.md)。

**输入：** 已确认的 PRD（优先）或产品简报。**产出：** 页面清单、页面状态矩阵、共享设计 Token / Style Anchor、线框与交互说明、中英出图提示词。

先确认页面范围和风格，再逐批审阅布局。真实生图是可选步骤，需明确选择并配置图片接口。详见 [TeamLog 第三步](../examples/teamlog-walkthrough.md#第三步设计页面状态和统一风格)。

### 08 公众号文章自进化写作

完整定义：[wechat-writer](../skills/08_wechat-writer.md)。

**输入：** 主题、参考资料及可选的文风偏好。**产出：** 自审后的定稿、配图提示词和本地学习记录。安装时保留 `references/` 与 `knowledge/`，定稿前仍需人工审核事实和表达。

### 09 朋友圈文案自进化写作

完整定义：[moments-writer](../skills/09_moments-writer.md)。

**输入：** 发圈场景及可选的人设、篇幅和风格。**产出：** 3–5 条候选文案、配图方案和本地学习记录。文案与配图提示词保存到项目的 `output/`，个人偏好写回安装目录的 `knowledge/`。

### 10 Tardis 生图

完整入口：[imagegen-tardis](../skills/imagegen-tardis/SKILL.md)。

**输入：** 图片需求或待编辑的本地图片。**产出：** 本地图片文件及预览、下载链接。

需要 Python 与 `openai` 包、本机密钥（优先读取 `~/.codex/auth.json` 的 `OPENAI_API_KEY`，文件不存在时读取 `~/.codex/config.toml` 的 `experimental_bearer_token`），以及可用的供应商接口；真实调用可能收费。不要把密钥粘贴到提示词或共享文档。脚本的 `--dry-run` 只检查参数和路径，不验证接口可用性。

---

## 工作流组合指南

### 场景 A：首次体验，想法到原型方案

```text
02 产品需求探索 → 04 PRD 生成 → 07 原型设计
```

1. 用 02 确认用户、MVP、成功指标及关键假设，保存产品简报。
2. 将简报交给 04，确认技术和范围后生成完整 PRD。
3. 将 PRD 交给 07，确认页面、状态与风格后生成原型方案。

需要验证赛道时，在 PRD 前加入 03 市场调研。主推流程不要求先生成真实图片。按 [TeamLog 教程](../examples/teamlog-walkthrough.md) 体验。

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

## 产物校验与仓库维护

在本仓库根目录运行，将示例路径换成实际产物的绝对路径：

```powershell
pwsh ./scripts/validate-product-artifact.ps1 -Path 'D:\demo\doc\TeamLog_PRD.md' -Type PRD
pwsh ./scripts/validate-product-artifact.ps1 -Path 'D:\demo\doc\TeamLog_Prototype.md' -Type Prototype
```

校验器检查完整文档的必需标记和未解释占位符。精简结构样例不保证通过，校验也不能替代业务、数据和设计审核。目前部分必需标记为中文，英文产物可能需要保留对应标记才能通过。

`skills/` 是唯一源目录；`plugins/youai-skills/skills/` 是生成的 Codex 安装包。更新源 Skill 后运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-codex-plugin.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-skill-sync.ps1
```

源文件与生成副本需一起更新。仅修改 README 等外围文档时无需重新同步。

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

- 产品类文档通常保存到 `doc/`；写作产物保存到 `output/`，图片保存到指定输出目录，具体以当前 Skill 的输出约束为准
- 适合共享的产物可纳入 Git；包含个人偏好或敏感信息的本地记忆应先脱敏，或排除出版本管理
- 默认文件命名包含日期，便于追溯；教程中的固定文件名只用于演示交接

---

## 常见问题

### Q: AI 不按 Skill 定义的格式输出怎么办？

可能原因：
- 输入内容太少，AI 没有足够上下文
- 对话上下文太长，Skill 指令被"冲淡"

解决方法：
- 在新对话中重新开始
- 提醒 AI："请按照 Skill 定义的格式输出"
- 使用 Windsurf Workflow、Cursor @Skill 或 Codex `$skill-name` 触发，格式更稳定

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

目前完整 Skill 定义以中文为主。可以在对话开头要求英文输出，但这不等于已经提供或验证了完整英文版 Skill。可先参考 [英文体验教程](../examples/teamlog-walkthrough_en.md)，欢迎贡献翻译。

### Q: 如何贡献新 Skill？

参考 [CONTRIBUTING.md](../CONTRIBUTING.md)，核心要求：
1. 在 `skills/` 下创建源文件
2. 包含 YAML 元信息头
3. 包含角色设定、执行步骤、输出格式、行为约束
4. 创建通用 `skills/{skill-name}/SKILL.md` 入口和所需支撑资料，再同步 Codex 插件包；无需为各平台分别维护 Skill 定义
