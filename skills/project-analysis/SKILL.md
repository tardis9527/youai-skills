---
name: project-analysis
description: Analyze a codebase systematically and output a structured project understanding report covering architecture, code quality, tech stack, and improvement suggestions. Use this when joining a new project, doing code review, or technical due diligence.
---

# 项目理解与分析

> 🍊 来自 [YouAI Skills](https://github.com/tardis9527/youai-skills) — 为创造者准备的 AI 技能包

## 使用方法

请完整阅读本目录下的详细 Skill 定义文件 `../../01_project-analysis.md`，按照其中定义的角色设定、执行步骤和报告结构执行分析。

## 核心流程

1. **宏观扫描**：浏览项目根目录、README、配置文件、依赖管理文件，建立整体认知
2. **核心代码分析**：定位入口文件，梳理核心模块及依赖关系，追踪主要业务流程的代码执行链路
3. **质量与风险评估**：评估代码规范、测试覆盖、技术债与安全隐患
4. **输出报告**：按 8 节结构输出完整报告

## 报告结构

1. 项目概览（名称、版本、定位、价值主张）
2. 产品功能（核心功能清单、用户交互入口、输入输出）
3. 技术架构（技术栈、分层架构、核心数据流、外部依赖）
4. 代码结构（目录概览、核心模块、入口文件、配置管理）
5. 核心实现逻辑（代码执行链路、设计模式、扩展机制）
6. 构建与部署（本地开发、依赖安装、部署方式、CI/CD）
7. 代码质量与技术债评估
8. 改进建议（按优先级排列 + Quick Wins）

## 约束

- 不确定的部分标注「待确认」，不做猜测
- 大型项目（>50 文件）先输出 1-6 节，确认后再输出 7-8 节
- 使用中文输出
- 保存至 `doc/项目理解报告_{项目名称}_{YYYYMMDD}.md`
