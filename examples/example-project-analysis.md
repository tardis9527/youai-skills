# 项目理解报告：TeamLog（团队日报助手）

> 使用 Skill：[01_project-analysis](../skills/01_project-analysis.md)
> 分析日期：2025-05-01
> 本文为精简示例，仅展示报告结构

---

## 1. 项目概览

- **项目名称**：TeamLog
- **版本**：v0.3.2
- **许可证**：MIT
- **一句话定位**：面向 10-50 人技术团队的异步日报管理工具，解决"日报写了没人看、汇总全靠人工"的问题。
- **核心价值主张**：用 AI 自动汇总团队日报，生成进度看板和风险预警，让管理者 30 秒掌握团队状态。

---

## 2. 产品功能

- **日报撰写**：结构化模板填写，支持关联 Git commit 和任务链接
- **AI 摘要**：自动提取团队日报中的关键进展、阻塞项、风险点
- **进度看板**：按项目/人员维度展示周进度
- **输入输出**：
  - 输入：团队成员每日填写日报（Web 端）
  - 输出：团队日报汇总、进度看板、风险提醒（邮件/飞书通知）

---

## 3. 技术架构

- **技术栈**：
  - 前端：React 18 + Ant Design 5 + Vite
  - 后端：NestJS + Prisma + PostgreSQL
  - AI：调用 OpenAI GPT-4o API 进行日报摘要
  - 部署：Docker Compose + 阿里云 ECS
- **系统分层**：
  - 表现层 → React SPA
  - API 层 → NestJS RESTful API
  - 业务逻辑层 → NestJS Services
  - 数据层 → PostgreSQL + Redis
  - 外部集成层 → OpenAI API、飞书 Webhook

---

## 4. 代码结构

```
teamlog/
├── apps/
│   ├── web/                # React 前端
│   │   └── src/modules/    # daily-report / dashboard / settings
│   └── server/             # NestJS 后端
│       └── src/modules/    # report / summary / notification / user
├── docker-compose.yml
└── package.json            # Yarn Workspaces
```

- **核心模块**：`report`（日报CRUD）、`summary`（AI摘要生成）、`notification`（通知推送）
- **入口文件**：`apps/server/src/main.ts`（后端）、`apps/web/src/main.tsx`（前端）

---

## 5. 核心实现逻辑

**日报提交 → AI 汇总的核心链路**：

```
用户提交日报
→ ReportController.create()
→ ReportService.create() — 存储日报到 DB
→ SummaryService.triggerDailySummary() — 每日 20:00 定时触发
→ SummaryService.callOpenAI() — 将当日所有日报拼接为 prompt，调用 GPT-4o
→ SummaryService.saveSummary() — 存储 AI 摘要
→ NotificationService.send() — 推送飞书/邮件通知
```

---

## 6. 构建与部署

- **本地开发**：`yarn dev`（concurrently 启动前后端）
- **依赖安装**：`yarn install`
- **部署方式**：`docker-compose up -d`（PostgreSQL + Redis + App）
- **CI/CD**：GitHub Actions — push to main 自动构建 Docker 镜像并部署

---

## 7. 代码质量与技术债评估

- **代码规范**：ESLint + Prettier 已配置，命名风格基本一致
- **测试覆盖**：仅后端核心模块有单元测试（覆盖率约 40%），前端无测试
- **技术债**：
  - OpenAI API Key 硬编码在 `.env` 中，无密钥轮换机制
  - 日报摘要无缓存，重复请求会重复调用 API
  - TODO/FIXME 共 12 处
- **安全隐患**：API 缺少速率限制，存在被滥用风险

---

## 8. 改进建议

| 优先级 | 问题 | 影响 | 建议方案 |
|--------|------|------|---------|
| 🔴 高 | API 无速率限制 | 可被恶意调用导致 OpenAI 费用激增 | 接入 NestJS throttler 模块 |
| 🔴 高 | 前端无测试覆盖 | 迭代频繁导致回归 bug 多 | 引入 Vitest + React Testing Library |
| 🟡 中 | AI 摘要无缓存 | 相同数据重复调用浪费 token | 基于日报内容 hash 做缓存 |
| 🟢 低 | 部署脚本缺少回滚 | 出问题需手动回滚 | 增加 `rollback.sh` 脚本 |

**Quick Wins**：接入 throttler（预计 2 小时）、添加摘要缓存（预计 4 小时）
