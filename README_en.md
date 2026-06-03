# 🍊 YouAI Skills

**AI Skills for Builders** — A structured set of AI prompts covering the full product development lifecycle, from ideation to PRD and investor BP materials. Compatible with mainstream AI IDEs.

[中文](./README.md) | English

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![Windsurf](https://img.shields.io/badge/Windsurf-Compatible-00C4B4)](./platforms/windsurf/)
[![Cursor](https://img.shields.io/badge/Cursor-Compatible-7C3AED)](./platforms/cursor/)

---

## ✨ Why This Project?

Most AI coding prompts focus on "how to write code", but **deciding what to build matters far more than how to code it**.

This Skill Pack covers the **critical decision-making stages before coding** — helping you use AI to go from a vague idea to a production-ready PRD and investor-facing BP materials. **Get the direction right before writing the first line of code.**

---

## 🔗 Workflow Overview

Six Skills form a complete product development pipeline. Each Skill's output serves as input for the next:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           YouAI Skills                                  │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 01 Project│  │ 02 Product│  │ 03 Market │  │ 04 PRD   │  │ 05 UI/UX │  │
│  │ Analysis  │  │ Discovery │─▶│ Research  │─▶│Generation│  │ Redesign │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│       │              │             │              │            │         │
│       │ Existing     │ New product │ Pre-funding  │ Product    │ Brand    │
│       └──────────────┴─────────────┴──────────────┴────────────┘         │
│                              ▼                                           │
│                       ┌──────────┐                                       │
│                       │ 06       │                                       │
│                       │ Investor │                                       │
│                       │ BP       │                                       │
│                       └──────────┘                                       │
│                                                                          │
│  Path A: New product from scratch  ──▶ 02 → 03 → 04                     │
│  Path B: Existing project          ──▶ 01 → 04                           │
│  Path C: Validate direction        ──▶ 02 → 03 → Decision                │
│  Path D: UI/UX design optimization ──▶ 01 → 05 (or 02 → 05)              │
│  Path E: Investor BP preparation   ──▶ 02/03/04 → 06                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Skill Catalog

| # | Skill | Use Case | Input | Output |
|---|-------|----------|-------|--------|
| 01 | [Project Analysis](./skills/01_project-analysis.md) | Onboarding, code review, tech due diligence | Existing codebase | Structured project report |
| 02 | [Product Discovery](./skills/02_product-discovery.md) | 0-to-1 product ideation, MVP definition | Vague product idea | Product Brief |
| 03 | [Market Research](./skills/03_market-research.md) | Market validation, competitor analysis | Product direction | Research report |
| 04 | [PRD Generation](./skills/04_prd-generation.md) | Implementation plan → PRD | Implementation doc | Complete PRD |
| 05 | [UI/UX Redesign](./skills/05_uiux-redesign.md) | UI style optimization, brand upgrade, design system | Existing project + product context | UI/UX redesign plan |
| 06 | [Investor BP Generation](./skills/06_investor-bp-generation.md) | Fundraising, investor meetings, pitch materials | Product Brief + PRD/market/competitor docs | Markdown BP or HTML pitch deck + oral pitch |

> Note: Skill content is currently in Chinese. English translations are on the roadmap.

---

## 🚀 Quick Start

### Option 1: Direct Use (Any AI Tool)

1. Open the corresponding Skill file in [`skills/`](./skills/)
2. Copy the full content into your AI conversation (ChatGPT / Claude / any AI)
3. Follow the guided interaction in the prompt

### Option 2: Windsurf

```bash
cp -r platforms/windsurf/workflows/ your-project/.windsurf/workflows/
```

Use `/` commands: `/project-analysis`, `/product-discovery`, `/market-research`, `/prd-generation`, `/uiux-redesign`, `/investor-bp-generation`

### Option 3: Cursor (Recommended)

```bash
mkdir -p your-project/.cursor/skills/
cp -r platforms/cursor/skills/* your-project/.cursor/skills/
```

Invoke Skills in Cursor Agent via **@Skill** (e.g. `@project-analysis`). Full skill definitions are fetched from GitHub remotely — no need to copy the entire `skills/` source files.

---

## 📋 Key Features

- **🔗 Chainable** — 6 Skills form a pipeline, outputs feed into next stage
- **📐 Structured Output** — Every Skill defines clear output format and quality standards
- **🛡️ Behavioral Constraints** — Built-in role definitions, forbidden actions, self-check lists
- **🔄 Interactive Guidance** — Stage-by-stage progression with confirmation checkpoints
- **🏗️ Flexible Tech Stack** — PRD Skill includes preferred tech stack with alternatives
- **📱 Multi-platform** — Supports Web + Mobile (React Native) product design

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md).

## 📄 License

[MIT License](./LICENSE)
