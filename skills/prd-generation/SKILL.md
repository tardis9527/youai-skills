---
name: prd-generation
description: Transform an implementation plan or product brief into a complete, actionable PRD (Product Requirements Document) with functional specs, data models, API design, tech architecture, UI/UX standards, and iteration planning. Use this when you have a product plan and need to produce developer-ready requirements.
---

# PRD 文档生成

> 🍊 来自 [YouAI Skills](https://github.com/tardis9527/youai-skills) — 为创造者准备的 AI 技能包

## 使用方法

请完整阅读本目录下的详细 Skill 定义文件 `../../04_prd-generation.md`，按照其中定义的完整 PRD 结构、技术栈偏好和质量要求执行。

## PRD 结构（13 章）

1. 文档信息（版本、日期、状态）
2. 项目概述（背景、用户画像、价值主张、KPI）
3. 用户角色与权限矩阵
4. 信息架构（导航结构、页面层级）
5. 功能需求清单（按模块，含编号、优先级、验收标准）
6. 核心业务流程图（Mermaid）
7. 数据模型设计
8. 接口设计规范（RESTful API）
9. 技术方案与架构约束
10. 非功能性需求（性能、安全、兼容性）
11. 设计规范与 UI/UX 标准
12. 迭代规划与优先级
13. 风险与开放问题

## 默认技术栈

- **前端**：React + Ant Design + Vite + Zustand
- **后端**：NestJS + Prisma + PostgreSQL + Redis
- **移动端**：React Native（如需要）
- **部署**：Docker + docker-compose

> 技术栈可根据项目需求替换，需在 PRD 中说明替换理由。

## 质量要求

- 每个功能必须有可测试的验收标准
- 功能编号连续、术语全文一致
- 信息不足处标注 `[待确认:原因]`
- 输出完成后执行自检清单（12 项检查）

## 约束

- 分 5 段输出，每段结尾标注继续提示
- 不编造实施方案中未提及的功能
- 使用中文输出
- 保存至 `doc/PRD_{系统名称}_V1_{YYYYMMDD}.md`
