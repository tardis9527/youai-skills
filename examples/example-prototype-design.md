# 产品原型与界面设计图提示词：TeamLog（团队日报助手）

> 使用 Skill：[07_prototype-design](../skills/07_prototype-design.md)
> 设计日期：2025-05-01
> 本文为精简示例，仅展示交付结构（实际产出会覆盖更多页面与状态）

---

## 1. 产品设计上下文

- **产品定位**：面向 10-50 人技术团队的异步日报管理工具
- **产品目标**：让管理者 30 秒掌握团队状态，提升日报"被看见"的价值
- **目标用户画像**：
  - 团队 Leader（30-40 岁，效率优先，桌面为主，偏好专业克制的数据界面）
  - 研发成员（25-35 岁，数字原住民，希望填写日报快速无负担）
- **平台覆盖**：Web 优先（桌面端），移动端只读查看
- **核心功能域**：日报撰写、AI 摘要、进度看板、通知设置
- **设计约束**：现有技术栈 React 18 + Ant Design 5，但本次出图不受组件库样式限制

---

## 2. 信息架构与页面清单

| 编号 | 页面名称 | 所属流程 | 页面目标 | 优先级 | 状态变体 |
|------|---------|---------|---------|--------|---------|
| P01 | 登录页 | 进入 | 身份认证 | 高 | 默认/错误 |
| P02 | 进度看板（首页） | 主流程 | 团队状态总览 | 高 | 默认/空/加载 |
| P03 | 日报撰写 | 主流程 | 快速填写日报 | 高 | 默认/提交成功 |
| P04 | AI 摘要详情 | 主流程 | 查看每日汇总 | 中 | 默认/生成中 |

**核心流程**：`登录(P01) → 进度看板(P02) → 日报撰写(P03) / AI 摘要详情(P04)`

---

## 3. 统一设计风格规范

### 设计调性
专业克制偏数据型，圆角柔和、留白充裕、扁平 + 轻微层次，整体气质"高效可信"。配色从"团队协作 + 效率工具"属性推导（青蓝主色传达专业与信任，暖橙强调色点亮关键动作），刻意避开通用 SaaS 蓝紫渐变。

### 🔒 全局风格基准（Style Anchor）

> 以下段落将原样拼接到每个页面的出图提示词中，保证全部页面风格一致。

- **风格关键词**：modern, clean, professional, data-dense, soft, trustworthy
- **设计参考体系**：现代 SaaS 仪表盘 / 轻量扁平 + 柔和层次
- **配色**：主色 `#1F6FEB`（青蓝，CTA/品牌）、辅助色 `#3AA0FF`、强调色 `#FF8A3D`（暖橙，关键操作/高亮）、背景 `#F5F7FA`、卡片 `#FFFFFF`、文字主 `#1B2330` / 次 `#6B7686`、成功 `#2BB673` / 警告 `#F5A623` / 错误 `#E5484D`
- **字体**：标题 Inter / 正文 Inter，中文 思源黑体，字重以 Regular + SemiBold 为主
- **圆角**：卡片 12px / 按钮 8px / 输入框 8px
- **间距与栅格**：8px 基准、12 列栅格、宽松留白
- **阴影**：柔和低饱和阴影（带轻微青蓝调），导航栏 backdrop-blur
- **图标**：线性 1.5px 描边、圆角端点
- **插画/图形**：极简几何渐变，空状态使用扁平线性插画
- **光影与质感**：干净自然光、无噪点、像素级清晰
- **视角与构图**：统一正视图（front view）
- **设备框架**：现代浏览器窗口框
- **氛围基调**：专业、清爽、可信赖的团队效率工具

---

## 4. 低保真原型交互草图（示例：P02 进度看板）

布局结构（桌面 Web，1440×900）：

```text
┌────────────────────────────────────────────────────────┐
│ <Logo> TeamLog   看板  日报  设置        (搜索) <通知><头像>│  ← 顶部导航
├──────────┬─────────────────────────────────────────────┤
│ ≡ 菜单    │ 本周团队进度  [KPI 提交率][KPI 阻塞][KPI 风险] │
│ · 概览    │ ┌──────────────┐ ┌──────────────┐           │
│ · 项目    │ │ {周进度折线}   │ │ {成员完成度}   │           │  ← 内容区
│ · 成员    │ └──────────────┘ └──────────────┘           │
│ · 设置    │ ≡ 今日 AI 摘要（关键进展/阻塞/风险）[查看全部] │
└──────────┴─────────────────────────────────────────────┘
```

交互说明：
- 顶部导航固定，滚动时加 backdrop-blur
- KPI 卡片 hover 上浮，点击进入对应明细
- 无数据时图表区展示空状态插画 + "暂无日报数据"
- 关键状态：默认 / 加载（骨架屏）/ 空数据

---

## 5. AI 出图提示词（示例：P02 进度看板）

**适用模型**：gpt-image2 / Nano Banana；Midjourney 见末尾。**画面比例**：16:10

### 中文提示词
一张高保真 UI 设计图，现代浏览器窗口框。整体风格：modern、clean、professional、data-dense、柔和可信赖；配色主色 `#1F6FEB` 青蓝、强调色 `#FF8A3D` 暖橙、背景 `#F5F7FA`、卡片纯白、文字 `#1B2330`；Inter 字体，卡片 12px 圆角、按钮 8px 圆角，柔和带青蓝调的低饱和阴影，线性 1.5px 图标，干净自然光、像素级清晰、正视图。页面为团队日报工具「进度看板」，自上而下：顶部固定导航栏含 Logo"TeamLog"、主菜单（看板/日报/设置）、搜索框、通知与头像；下方左侧为可折叠侧边菜单（概览/项目/成员/设置，当前项"概览"以青蓝高亮）；右侧主内容区顶部为 3 个 KPI 卡片（"本周提交率 92%"、"阻塞项 3"、"风险 1"，强调色点缀），下方为两个并排图表卡片（左：周进度折线图，右：成员完成度条形图），再下方为"今日 AI 摘要"列表（关键进展/阻塞/风险三类标签）。留白充足、专业清爽、UI 设计稿质感。

### English Prompt
A high-fidelity UI design mockup inside a modern desktop browser window. Overall style: modern, clean, professional, data-dense, soft and trustworthy; primary color `#1F6FEB` teal-blue, accent `#FF8A3D` warm orange, background `#F5F7FA`, white cards, text `#1B2330`; Inter typeface, 12px card radius, 8px button radius, soft low-saturation shadows with a slight teal tint, 1.5px line icons, clean natural light, pixel-perfect, front view. The screen is a team daily-report tool "Progress Dashboard", top-to-bottom: a fixed top nav with logo "TeamLog", main menu (Board/Reports/Settings), search box, notifications and avatar; a collapsible left sidebar (Overview/Projects/Members/Settings, active "Overview" highlighted in teal-blue); the main area shows 3 KPI cards at top ("Weekly submission 92%", "Blockers 3", "Risks 1", accented in orange), then two side-by-side chart cards (left: weekly progress line chart, right: member completion bar chart), then a "Today's AI summary" list with three tag types (progress/blockers/risks). Generous whitespace, professional and crisp, UI design canvas quality.

### 关键状态变体
- **空状态**：将图表与摘要列表替换为扁平线性插画 + "暂无日报数据" + "去填写日报"按钮（暖橙强调色），其余风格不变。
- **加载态**：KPI 与图表替换为带青蓝调 shimmer 的骨架屏，其余风格不变。

### Midjourney 参数版
`A high-fidelity SaaS progress dashboard UI ... (same English description) --ar 16:10 --style raw --v 6`

### 负面提示（Negative）
避免：低分辨率、模糊、文字乱码、错位、水印、人物/手指、杂乱噪点、蓝紫渐变、卡通涂鸦风。

---

## 🔁 风格统一自检清单
- [x] 每个页面提示词均包含完全相同的「全局风格基准」段落
- [x] 所有页面使用同一套配色 HEX（`#1F6FEB` / `#FF8A3D` / `#F5F7FA` …）
- [x] 同一字体（Inter）/ 圆角（12px·8px）/ 阴影 / 线性图标
- [x] 统一正视图 + 浏览器窗口框 + 16:10 比例
- [x] 建议：先用 P02 出 1 张满意的"风格基准图"，再以它作参考图（垫图）出 P01/P03/P04，一致性最佳
