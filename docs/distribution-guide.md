# YouAI Skills 分发与推广指南

[项目首页](../README.md) · [体验教程](../examples/teamlog-walkthrough.md) · [English walkthrough](../examples/teamlog-walkthrough_en.md)

本指南为仓库维护者提供定位、分享素材、渠道候选和效果记录方法。以下平台为候选渠道，不代表已经完成收录或核验当前提交入口；发布前查看其最新规则。

## 主推定位

**一句话介绍：** 在写代码前，把一句产品想法变成产品简报、PRD 和原型设计方案。

**首批用户：** 使用 AI 编程工具的独立开发者、个人项目作者和 Hackathon 团队。

**主推链路：** `product-discovery → prd-generation → prototype-design`。其余七个 Skill 作为其他场景的入口，可单独介绍。

说明交付边界：Skill 免费开源，AI 服务和图片接口可能收费；产出用于起草与评审。真实图片为可选项，默认体验不要求配置图片接口。

## 可复用的介绍素材

### GitHub About 描述建议

仓库首页右侧 About 的描述需要维护者手动设置；修改下面的文案不会自动改变 GitHub 设置。

中文：

> 在写代码前，把产品想法变成简报、PRD 和原型方案。面向独立开发者的 10 个开源 AI Skill，支持 Codex、Claude Code、Cursor 和 Windsurf。

英文：

> Turn product ideas into briefs, PRDs, and prototype plans. 10 open-source AI skills for indie builders using Codex, Claude Code, Cursor, or Windsurf.

建议 Topics（在仓库首页 About 的编辑入口设置，按相关性选用）：

```text
ai-skills
agent-skills
product-discovery
product-management
prd
prototype-design
codex
claude-code
cursor
windsurf
```

### 中文社区介绍草稿

> 用 AI 做个人项目时，需求没想清楚，后面写代码就容易反复返工。
>
> 我整理了一套开源工作流 YouAI Skills，帮助你在写代码前，把产品想法逐步整理成产品简报、PRD 和原型设计方案。
>
> 可以先体验三个 Skill：需求探索 → PRD 生成 → 原型设计。仓库附有虚构产品 TeamLog 的精简样例和可复制的体验教程，展示用户、MVP、验收标准、页面状态之间如何衔接。
>
> 支持 Codex、Claude Code、Cursor 和 Windsurf；也可直接复制完整提示词到 AI 对话中。Skill 内容 MIT 开源，运行所需的 AI 服务费用按各自服务计算。
>
> 仓库：https://github.com/tardis9527/youai-skills
>
> 如果工作流对你有帮助，欢迎 Star；也欢迎反馈安装和文档交接中遇到的问题。

这段文案可用于项目介绍。发技术文章时，还应附可学走的方法、关键截图和产物节选；目前没有真实运行录屏，不能写成“已经实测节省了多少时间”。

### 英文目录条目

```markdown
- [YouAI Skills](https://github.com/tardis9527/youai-skills) — Turn product ideas into briefs, PRDs, and prototype plans. 10 open-source AI skills for indie builders, with a guided workflow and fictional TeamLog samples. Supports Codex, Claude Code, Cursor, and Windsurf. Skill definitions are currently in Chinese; an English README and walkthrough are available.
```

避免声称提供完整英文 Skill。正式拓展英文用户前，优先翻译主推三条 Skill 并验证一个英文完整案例。

## 展示案例的准备方式

目前可分享的是 [体验教程](../examples/teamlog-walkthrough.md) 和 [精简样例](../examples/README.md)，不是已经验证的用户成果。真实案例按以下步骤整理：

1. 在新演示项目中实际运行主推工作流，记录工具、模型及仓库版本。
2. 保存原始输入、关键回答、完整产品简报、PRD 和原型方案。
3. 记录人工修改及剩余问题，指标和耗时只引用实际测量。
4. 录制 60–90 秒演示：需求 → 追问 → MVP → 验收标准 → 线框与失败状态。
5. 同一案例拆成 README 演示、技术文章、短视频及社区分享，按渠道调整标题和重点。

视频、截图和资料发布前脱敏。现有 TeamLog 样例中的数据只用于演示，不作为市场结论或实际效果引用。

## 渠道候选

| 优先级 | 渠道 | 适合的材料 | 提交前检查 |
|---|---|---|---|
| 高 | 已参与的独立开发者 / AI 编程社群 | 实际案例、体验教程、具体反馈问题 | 群规和分享频率 |
| 高 | 掘金 / V2EX 等开发者社区 | 可复现的方法文章与产物节选 | 分区和自荐规则 |
| 高 | [cursor.directory](https://cursor.directory) | 简洁定位、安装路径、示例 | 当前是否接受 Skills / Plugins，支持的清单格式 |
| 中 | [Skills Directory](https://www.skillsdirectory.com) | 单个主推 Skill 的用途与样例 | 当前入口、字段及收录规则 |
| 中 | [awesome-cursor-skills](https://github.com/spencerpauly/awesome-cursor-skills) | 英文目录条目 | 活跃度、分类与贡献指南 |
| 中 | B站 / 小红书 | 一段实际运行录屏或案例图解 | 展示结果是否真实，是否方便找到仓库 |
| 后续 | X / Reddit 等英文社区 | 已验证的英文工作流案例 | 社区自荐规则和语言可用性 |
| 可选 | [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) / [prompts.chat](https://github.com/f/prompts.chat) | 与目录主题匹配的具体条目 | 本项目是 Skills，不能直接冒充 Rules；仅提交匹配内容 |

先测试两个目标用户匹配的渠道，再根据反馈扩大分发。目录收录和海外发布均需实际操作后才能标记完成。

## 仓库的分发文件

当前共有 **10 个 Skill**，入口位于 `skills/*/SKILL.md`。

| 文件 | 用途 |
|---|---|
| [.plugin/plugin.json](../.plugin/plugin.json) | 插件元信息、关键词及仓库链接；平台是否识别由其规则决定 |
| [.agents/plugins/marketplace.json](../.agents/plugins/marketplace.json) | Codex 插件市场清单 |
| [plugins/youai-skills/.codex-plugin/plugin.json](../plugins/youai-skills/.codex-plugin/plugin.json) | Codex 插件描述与安装包入口 |
| `skills/` | Skill 源文件、通用入口及支撑资料 |
| `plugins/youai-skills/skills/` | 由同步脚本生成的完整 Codex 安装包 |
| [README](../README.md) / [English README](../README_en.md) | 对外定位、结果预览与首次使用入口 |
| [体验教程](../examples/teamlog-walkthrough.md) | 可复制的输入与人工检查点 |

修改源 Skill 后重新生成插件包并运行同步检查，详细命令见 [使用指南](./usage-guide.md#产物校验与仓库维护)。

## 两周执行与记录

| 阶段 | 工作 | 完成依据 |
|---|---|---|
| 第 1–3 天 | 实际运行一个完整案例并录屏 | 有原始输入、完整产物与修改记录 |
| 第 4–5 天 | 以干净目录验证安装，检查首页体验 | 新用户能找到安装和第一次调用路径 |
| 第 6–10 天 | 一篇主文章，两个渠道版本 | 记录帖子链接、发布时间和反馈 |
| 第 11–14 天 | 修复体验问题并复盘 | 根据反馈确定下一案例或继续投入的渠道 |

GitHub Traffic 通常只保留近期数据，应定期记录。它能辅助判断访问和来源，不能精确归因每个 Star；clone 数也不等于安装人数。

记录字段：

| 日期 | 渠道 / 帖子链接 | 仓库浏览量 / 独立访客 | 当日净增 Star | 实际试用反馈 | 下一步 |
|---|---|---|---|---|---|
| 发布日 | 填实际链接 | 填 GitHub Traffic 数据 | 填实际净增 | 填用户反馈 | 填改进动作 |

多渠道发布时保留时间记录；需要比较来源可使用各渠道独立的可统计入口，不能假定给 GitHub URL 加参数就能在 Traffic 中获得完整归因。

访问少时检查选题和渠道；有访问但缺少试用时检查价值表达与首页；有人试用却反复卡住时优先修复安装和交接流程。避免刷 Star、互 Star 和与主题无关的批量宣传。

## 发布检查清单

- [ ] 中英文介绍、插件描述、Skill 数量和当前版本一致。
- [ ] 在新项目验证主推流程的安装与首次调用。
- [ ] 示例区分虚构结构参考和实际运行记录。
- [ ] 分享素材注明语言支持、运行条件和费用边界。
- [ ] 当前安装路径来自使用指南，不复用旧版本发布文档中的命令。
- [ ] 设置 GitHub About 描述和相关 Topics。
- [ ] 选择两个匹配渠道，检查发布规则并记录链接。
- [ ] 根据当前版本准备 Release 说明，不直接复用首次发布的 v1.0.0 内容。
- [ ] 发布后持续处理真实反馈，记录两周结果。

[release-notes-v1.0.0.md](./release-notes-v1.0.0.md) 保留首次发布的历史内容，不能作为当前版本安装指南。
