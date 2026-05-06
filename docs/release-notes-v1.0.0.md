# 🍊 YouAI Skills v1.0.0 — 首次发布

> 为创造者准备的 AI 技能包 — 覆盖从产品构思到 PRD 落地的结构化 AI 提示词

---

## ✨ 亮点

**在写第一行代码之前，先用 AI 把产品方向想清楚。**

YouAI Skills 是一套面向产品开发前半段（需求 → 调研 → PRD）的 AI 提示词工具包。不同于聚焦"怎么写代码"的 AI 工具，YouAI Skills 帮你解决**决定做什么**的问题。

---

## 📦 本次发布内容

### 4 个核心 Skill

| # | Skill | 说明 |
|---|-------|------|
| 01 | **项目理解与分析** | 快速理解已有代码库的架构、技术栈、质量状况 |
| 02 | **产品需求探索与定义** | 从模糊想法到结构化产品简报（Product Brief） |
| 03 | **产品市场调研分析** | 竞品分析、市场规模、用户洞察、风险评估 |
| 04 | **PRD 文档生成** | 生成可直接交付开发团队的完整 PRD |

### 多平台适配

- **Windsurf** — Workflow 格式，支持 `/` 斜杠命令触发
- **Cursor** — Rules 格式，自动作为上下文加载
- **通用** — 复制粘贴到 ChatGPT / Claude / 任何 AI 对话工具

### 工作流串联

四个 Skill 形成完整的产品开发链路，每个 Skill 的产出物可直接作为下一个的输入：

```
场景A：新产品从0开始 → 02 → 03 → 04
场景B：接手已有项目   → 01 → 04
场景C：验证产品方向   → 02 → 03 → 决策
```

---

## 🚀 快速开始

### 最简方式

1. 打开 `skills/` 目录中的 Skill 文件
2. 完整复制到你的 AI 对话中
3. 按引导开始交互

### Windsurf 用户

```bash
cp -r platforms/windsurf/workflows/ your-project/.windsurf/workflows/
```

然后在 Cascade 中输入 `/project-analysis` 等命令即可。

### Cursor 用户

```bash
cp -r platforms/cursor/rules/ your-project/.cursor/rules/
```

---

## 📋 Skill 设计特点

- **🔗 链式可组合** — 产出物串联为工作流
- **📐 结构化输出** — 定义明确的输出格式和质量标准
- **🛡️ 行为约束** — 内置角色设定、禁止行为、自检清单
- **🔄 交互式引导** — 分阶段推进，每步确认
- **🏗️ 技术栈灵活** — 默认技术栈可替换

---

## 📄 开源协议

MIT License — 自由使用、修改和分发。

---

## 🤝 参与贡献

欢迎通过以下方式参与：

- 改进现有 Skill 的提示词质量
- 贡献新场景的 Skill
- 翻译为其他语言
- 补充使用示例和最佳实践
- 新增平台适配（JetBrains AI、GitHub Copilot 等）

详见 [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**GitHub**: https://github.com/tardis9527/youai-skills
