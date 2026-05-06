# 🚀 YouAI Skills 分发指南

本文档记录如何将 YouAI Skills 发布到各个 Skill Hub 平台，让更多人发现和使用。

---

## 分发平台总览

| 平台 | 类型 | 提交方式 | 覆盖工具 | 优先级 |
|------|------|---------|---------|--------|
| [cursor.directory](https://cursor.directory) | 社区 Hub（最大） | 网站提交 GitHub 仓库 URL | Cursor + Windsurf | 🔴 高 |
| [Skills Directory](https://www.skillsdirectory.com) | 策展目录 | 网站提交 | Claude / 通用 | 🟡 中 |
| [awesome-cursor-skills](https://github.com/spencerpauly/awesome-cursor-skills) | GitHub Awesome List | 提交 PR | Cursor | 🟡 中 |
| [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | GitHub Awesome List | 提交 PR | Cursor | 🟢 低 |
| [prompts.chat](https://github.com/f/prompts.chat) | Prompt 社区 | 提交 PR | 通用 | 🟢 低 |

---

## 仓库结构（已适配 Open Plugins 标准）

```
youai-skills/
├── .plugin/
│   └── plugin.json          # Open Plugins 标准清单（含 GitHub 链接）
├── skills/                   # 🎯 核心 Skill 源文件
│   ├── 01_project-analysis.md
│   ├── 02_product-discovery.md
│   ├── 03_market-research.md
│   ├── 04_prd-generation.md
│   ├── project-analysis/     # Open Plugins SKILL.md 格式
│   │   └── SKILL.md
│   ├── product-discovery/
│   │   └── SKILL.md
│   ├── market-research/
│   │   └── SKILL.md
│   └── prd-generation/
│       └── SKILL.md
├── rules/                    # Cursor Rules (.mdc 格式)
│   ├── project-analysis.mdc
│   ├── product-discovery.mdc
│   ├── market-research.mdc
│   └── prd-generation.mdc
├── platforms/                # 各平台原生适配版本
│   ├── windsurf/workflows/
│   └── cursor/rules/
└── ...
```

cursor.directory 自动检测以下路径：

| 组件类型 | 检测路径 | 状态 |
|---------|---------|------|
| Rules | `rules/*.mdc` | ✅ 已创建 |
| Skills | `skills/*/SKILL.md` | ✅ 已创建 |
| Plugin 清单 | `.plugin/plugin.json` | ✅ 已创建 |

---

## 平台一：cursor.directory（最高优先级）

**cursor.directory** 是 Cursor 和 Windsurf 社区最大的共享平台，支持 Plugins、Rules、Skills、MCP Servers 等。

### 提交步骤

1. 访问 [cursor.directory/plugins/new](https://cursor.directory/plugins/new)
2. 使用 GitHub 或 Google 账号登录
3. 粘贴仓库 URL：`https://github.com/tardis9527/youai-skills`
4. 网站会自动检测仓库中的组件：
   - `rules/*.mdc` → 4 条 Rules
   - `skills/*/SKILL.md` → 4 个 Skills
   - `.plugin/plugin.json` → 插件元信息（含 GitHub 链接 = 自动宣传）
5. 点击 **Submit**

### 宣传效果

- `plugin.json` 中的 `homepage` 和 `repository` 字段直接链接到 GitHub 仓库
- 每个 SKILL.md 和 .mdc 文件的 description 中包含 GitHub 链接
- 用户在 cursor.directory 上看到插件后，可以直接跳转到你的 GitHub 仓库

---

## 平台二：Skills Directory

**skillsdirectory.com** 是一个策展型 Agent Skills 目录，主要面向 Claude 用户。

### 提交步骤

1. 访问 [skillsdirectory.com/submit](https://www.skillsdirectory.com/submit)
2. 使用 GitHub 账号登录
3. 为每个 Skill 分别提交（4 个 Skill = 4 次提交）
4. 每个提交中：
   - 粘贴对应 Skill 的完整内容（如 `skills/01_project-analysis.md`）
   - 添加描述，包含 GitHub 仓库链接
   - 选择分类：`Development` / `Planning & Architecture`

---

## 平台三：awesome-cursor-skills

**GitHub Awesome List**，通过 PR 提交。

### 提交步骤

1. Fork [spencerpauly/awesome-cursor-skills](https://github.com/spencerpauly/awesome-cursor-skills)
2. 在 README.md 的 `Planning & Architecture` 分类下添加：

```markdown
- [YouAI Skills](https://github.com/tardis9527/youai-skills) - AI Skills for product development workflow. 4 skills covering project analysis, product discovery, market research, and PRD generation. Helps you make the right product decisions before writing the first line of code.
```

3. 提交 PR，标题：`Add YouAI Skills - Product Development AI Skills Pack`

---

## 平台四：awesome-cursorrules

### 提交步骤

1. Fork [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)
2. 添加你的 rules 到对应分类
3. 提交 PR

---

## GitHub 宣传策略

所有打包文件中都已嵌入 GitHub 仓库链接：

| 文件 | 宣传位置 |
|------|---------|
| `.plugin/plugin.json` | `homepage` + `repository` 字段 |
| `skills/*/SKILL.md` | 每个文件顶部的 YouAI Skills 链接 |
| `rules/*.mdc` | 每个 description 中的 GitHub 链接 |

### 额外宣传渠道（手动）

- **GitHub Topics**：在仓库 Settings 中添加 `youai` `ai-skills` `prompt-engineering` `cursor` `windsurf` `product-management`
- **技术社区发帖**：
  - 掘金 / V2EX / 少数派 — 写一篇介绍文章
  - Reddit r/cursor、r/windsurf — 英文介绍帖
  - Product Hunt — 作为开源工具提交

---

## 操作清单

- [ ] 提交到 cursor.directory（粘贴 GitHub URL）
- [ ] 提交到 skillsdirectory.com（4 个 Skill 分别提交）
- [ ] 提交 PR 到 awesome-cursor-skills
- [ ] 提交 PR 到 awesome-cursorrules
- [ ] GitHub 仓库添加 Topics 标签
- [ ] 创建 GitHub Release v1.0.0（可用 docs/release-notes-v1.0.0.md）
- [ ] 可选：技术社区发文宣传
