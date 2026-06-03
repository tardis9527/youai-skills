---
name: investor-bp-generation
description: Generate investor-facing BP business plan materials from a Product Brief and related project docs. Outputs Markdown business plan or HTML pitch-deck presentation plus a concise oral pitch summary. Use for fundraising, Demo Day, investor meetings, or when the user asks for a business plan or pitch deck.
disable-model-invocation: true
---

# 投资人BP商业计划报告生成

> 🍊 来自 [YouAI Skills](https://github.com/tardis9527/youai-skills) — 为创造者准备的 AI 技能包

请按照以下步骤生成面向投资人的 BP 商业计划材料：

## 步骤

1. **阅读 Skill 定义**：先尝试打开本地 `skills/06_investor-bp-generation.md`。如果文件不存在，请从以下 URL 读取完整 Skill 定义：https://raw.githubusercontent.com/tardis9527/youai-skills/main/skills/06_investor-bp-generation.md 。阅读后理解角色设定、资料盘点、融资叙事设计、Markdown/HTML 输出要求和禁止行为。如果 URL 也无法访问，则直接按以下核心流程执行。

2. **资料盘点**：优先读取项目中的 `doc/Product_Brief_*.md`、PRD、市场调研报告、竞品分析、项目理解报告等资料。提取产品定位、目标用户、市场机会、商业模式、牵引力、团队、融资计划等信息。

3. **关键确认**：询问用户希望输出 Markdown、HTML PPT 演示版，还是两者都要；确认项目阶段、融资目标、已有数据和目标投资人类型。若用户要求直接生成，则缺失项标注 `[待补充]`。

4. **融资叙事卡片**：先输出一句话投资亮点、Why Now、高价值痛点、解决方案、差异化优势、商业模式、增长路径、牵引力、融资诉求和投资人可能追问的问题，并征求用户确认。

5. **生成 BP 文档**：
   - Markdown：保存为 `doc/BP商业计划报告_{产品名称}_{YYYYMMDD}.md`
   - HTML：保存到 `doc/BP_{产品名称}_{YYYYMMDD}/`，必须包含 `index.html`、`assets/css/style.css`、`assets/js/main.js`、`README.md`

6. **输出口述版**：完成文档后，必须在 AI 聊天界面输出 500 字以内的精简版项目 BP 介绍，方便用户向投资人口述。

## 关键规则

- **角色**：资深融资顾问、创业公司战略顾问兼投资人 BP 撰稿人
- 不编造市场规模、收入、用户数、客户名称、融资金额或投资机构
- 所有估算数据必须标注推算逻辑
- HTML 演示版不得写成单文件，CSS 和 JS 必须独立
- BP 要突出投资亮点、市场机会、商业模式、增长路径、护城河、融资用途和风险应对
- **输出语言**：中文，除非用户明确要求英文
