# 贡献指南

感谢你对 **YouAI Skills（柚子AI Skills）** 的关注！欢迎通过以下方式参与贡献。

## 贡献方式

### 🐛 改进现有 Skill

- 发现提示词有不合理的地方？提 Issue 或直接提 PR
- 修改 `skills/{序号}_{英文名}.md` 源文件（Single Source of Truth）
- 若改动涉及**阶段划分、关键规则或输出结构**，同步更新 `skills/{skill-name}/SKILL.md` 入口文件
- 若 Skill 自带 `references/`（静态规则）或 `knowledge/`（动态记忆），相关规则改动也要同步
- 修改 `skills/` 后运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-codex-plugin.ps1`，并提交更新后的 `plugins/youai-skills/skills/` Codex 插件包

### ✨ 贡献新 Skill

1. 在 `skills/` 目录下创建新文件，命名格式：`{序号}_{英文名}.md`
2. 必须包含 YAML 元信息头（参考现有 Skill 格式）：
   ```yaml
   ---
   名称: Skill中文名
   版本: v1.0
   适用场景: 简短描述
   前置输入: 需要什么输入
   预期产出: 输出什么
   上下游关系: 与其他Skill的关系
   ---
   ```
3. 内容结构建议包含：角色设定、执行步骤、输出格式、质量要求、禁止行为
4. 同步创建 Open Plugins 入口 `skills/{skill-name}/SKILL.md`（英文 `name` + `description` 的 YAML 头），内容保持轻量：指向源文件、列出关键规则，**不复述完整流程**，避免两处漂移
5. 该入口文件是各平台通用的：Cursor 装到 `.cursor/skills/`、Claude Code 装到 `.claude/skills/`、Codex 装到 `.agents/skills/`、Windsurf 复制成 `.windsurf/workflows/{skill-name}.md`。**不需要为每个平台维护单独副本**
6. 如需自带资料，按约定放 `skills/{skill-name}/references/`（静态、只读）与 `skills/{skill-name}/knowledge/`（动态、可写）
7. 运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-codex-plugin.ps1`，将新 Skill 打包到 Codex 插件目录

### 🌐 翻译

- 将 Skill 翻译为英文或其他语言
- 翻译文件放在 `skills/` 同级目录下，如 `skills/en/`

### 📖 补充示例

- 在 `examples/` 目录下添加使用 Skill 后的实际产出样例
- 文件命名：`example-{skill英文名}.md`

## 提交规范

- 使用 Conventional Commits：`feat:` / `fix:` / `docs:` / `chore:`
- PR 标题清晰描述改动内容
- 如果修改了 `skills/{序号}_{英文名}.md` 源文件的流程或关键规则，请同步更新对应的 `skills/{skill-name}/SKILL.md` 入口

## Skill 质量标准

一个好的 Skill 应满足：

- [ ] 有明确的角色设定（AI扮演什么角色）
- [ ] 有清晰的执行步骤（分步骤、有先后顺序）
- [ ] 有结构化的输出格式（模板、表格）
- [ ] 有行为约束（禁止行为、交互控制规则）
- [ ] 有输出约束（文件格式、命名、保存路径）
- [ ] 经过实际使用验证（不是纸上谈兵）

## 行为准则

- 尊重每一位贡献者
- 建设性地讨论和反馈
- 保持专注：本项目聚焦产品开发流程的 AI Skill
