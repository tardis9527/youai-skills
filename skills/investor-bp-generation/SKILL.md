---
name: investor-bp-generation
description: Generate investor-facing BP business plan materials from a Product Brief and related project docs. Outputs either a Markdown business plan report or an HTML pitch-deck-style presentation with separate HTML/CSS/JS files, plus a concise 500-character oral pitch summary.
---

# 投资人BP商业计划报告生成

> 🍊 来自 [YouAI Skills](https://github.com/tardis9527/youai-skills) — 为创造者准备的 AI 技能包

## 使用方法

请完整阅读本目录下的详细 Skill 定义文件 `../../06_investor-bp-generation.md`，按照其中定义的资料盘点、融资叙事设计、输出格式选择和质量要求执行。

## 核心流程

1. **资料盘点**：优先读取 Product Brief、PRD、市场调研、竞品分析、项目理解报告等资料，建立事实基础
2. **叙事设计**：提炼一句话投资亮点、Why Now、高价值痛点、差异化优势、增长路径和融资诉求
3. **格式确认**：根据用户需要选择 Markdown 完整报告、HTML PPT 演示版，或两者都输出
4. **BP生成**：输出面向投资人的商业计划报告，覆盖市场、产品、商业模式、竞争、GTM、团队、财务、融资计划和风险
5. **口述版输出**：在 AI 聊天界面额外输出 500 字以内精简版项目 BP 介绍

## 产出物

- Markdown：`doc/BP商业计划报告_{产品名称}_{YYYYMMDD}.md`
- HTML：`doc/BP_{产品名称}_{YYYYMMDD}/index.html`，并拆分 `assets/css/style.css` 和 `assets/js/main.js`
- 聊天界面：500 字以内口述版项目 BP 介绍

## 约束

- 不编造用户数、收入、客户名称、融资金额、市场报告或投资机构
- 缺失数据必须标注 `[待补充]` 或 `[估算: 推算逻辑]`
- HTML 演示版必须拆分 HTML、CSS、JS，方便复制目录到 Nginx 静态访问
- 使用中文输出，除非用户明确要求英文
