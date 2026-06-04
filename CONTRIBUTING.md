# 贡献指南

感谢你对 **YouAI Skills（柚子AI Skills）** 的关注！欢迎通过以下方式参与贡献。

## 贡献方式

### 🐛 改进现有 Skill

- 发现提示词有不合理的地方？提 Issue 或直接提 PR
- 修改 `skills/` 目录下的源文件（Single Source of Truth）
- 同步更新 `platforms/` 目录下的平台适配版本

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
4. 同步创建 `platforms/windsurf/workflows/`、`platforms/cursor/skills/{skill-name}/SKILL.md` 和 `platforms/claude-code/skills/{skill-name}/SKILL.md` 下的适配版本

### 🌐 翻译

- 将 Skill 翻译为英文或其他语言
- 翻译文件放在 `skills/` 同级目录下，如 `skills/en/`

### 📖 补充示例

- 在 `examples/` 目录下添加使用 Skill 后的实际产出样例
- 文件命名：`example-{skill英文名}.md`

## 提交规范

- 使用 Conventional Commits：`feat:` / `fix:` / `docs:` / `chore:`
- PR 标题清晰描述改动内容
- 如果修改了 `skills/` 源文件，请同步更新对应的平台适配版本

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
