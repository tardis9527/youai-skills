# YouAI Skills for Codex

This directory contains Codex-ready Agent Skills for YouAI Skills.

## Install For One Project

Copy the skill folders into the target project's `.agents/skills/` directory:

```powershell
New-Item -ItemType Directory -Force -Path .agents\skills
Copy-Item -Recurse platforms\codex\skills\* .agents\skills\
```

On macOS or Linux:

```bash
mkdir -p .agents/skills
cp -r platforms/codex/skills/* .agents/skills/
```

Restart Codex or start a new Codex session after installing.

## Install For Your Codex User

Copy the skill folders into your personal Codex skills directory:

```powershell
New-Item -ItemType Directory -Force -Path $env:USERPROFILE\.codex\skills
Copy-Item -Recurse platforms\codex\skills\* $env:USERPROFILE\.codex\skills\
```

On macOS or Linux:

```bash
mkdir -p ~/.codex/skills
cp -r platforms/codex/skills/* ~/.codex/skills/
```

Restart Codex after installing global skills.

## Use In Codex

In a Codex conversation, explicitly invoke a skill with `$skill-name`, for example:

```text
$project-analysis 查询当前项目，了解项目背景和目标
$product-discovery 我想做一个团队日报 AI 助手，帮我梳理 MVP
$market-research 调研团队协作日报工具的市场和竞品
$prd-generation 根据 doc/Product_Brief_TeamLog_20260609.md 生成 PRD
$uiux-redesign 基于当前项目和产品背景，输出 UI/UX 重塑方案
$investor-bp-generation 根据产品简报和 PRD 生成融资 BP
$prototype-design 基于 PRD 输出原型草图和 AI 出图提示词
```

Codex can also discover a skill from the task description when the skill's `description` matches the request. Explicit `$skill-name` invocation is recommended when you want a specific YouAI workflow.

## Available Skills

| Skill | Purpose |
|------|---------|
| `$project-analysis` | Analyze an existing codebase and output a structured project report |
| `$product-discovery` | Turn a vague product idea into a Product Brief |
| `$market-research` | Research market, competitors, users, and risks |
| `$prd-generation` | Convert a brief or implementation plan into a PRD |
| `$uiux-redesign` | Produce a UI/UX redesign and design system plan |
| `$investor-bp-generation` | Generate investor BP materials |
| `$prototype-design` | Generate wireframes and AI image prompts for product screens |

