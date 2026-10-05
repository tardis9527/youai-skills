# TeamLog walkthrough: idea → PRD → prototype plan

[中文](./teamlog-walkthrough.md) · [Home](../README_en.md) · [Installation guide (Chinese)](../docs/usage-guide.md)

This tutorial provides copyable inputs, document handoffs, and review checkpoints. TeamLog is fictional. Existing samples are manually written excerpts, and this tutorial is not a recorded model run. Actual results and duration depend on your model, tools, and answers.

## Prepare

Choose one route:

- **Text-only chat:** Paste the full skill definition into a new conversation for each stage, then send the request. Paste the previous document in full for each handoff and save outputs manually.
- **AI IDE:** Install using the guide and open a fresh demo project. The prompts below use Codex's `$skill-name`; use `/skill-name` in Claude Code / Windsurf or the skill selection interface in Cursor.

Use a new conversation for each stage and pass documents between them. Skill definitions are currently Chinese; explicitly request English output. This does not constitute a full English translation of the skills.

This run produces documents, wireframes, and image prompts. No image API is required.

## Step 1: define the product and MVP

Full definition: [product-discovery (Chinese)](../skills/02_product-discovery.md). Omit the invocation line in a text-only chat.

```text
$product-discovery
I want to build TeamLog, a daily-report assistant for technical teams of 10–50 people.
Help a team lead see key progress, blockers, and risks. Use Express mode.

The following are fictional demo assumptions, not validated user research:
- V1 is web only: members submit reports and leads review summaries.
- Exclude automatic Git integration, a mobile app, and complex enterprise permissions.
- We plan to recruit initial interviewees from technical-lead communities; none are recruited yet.
- Users must still be able to read original reports if AI summarization fails.

Ask follow-up questions and let me confirm key scope decisions.
Mark uncertain assumptions as unverified. Respond in English.
For this demo, save the final brief to doc/TeamLog_Brief.md.
```

Review the target user, existing alternatives, MVP and exclusions, empty/failure/recovery flows, measurable success criteria, and validation plans. Answer based on your actual constraints; do not accept every recommendation automatically.

Handoff: `doc/TeamLog_Brief.md`, or the full confirmed brief in a text-only chat.

[Compare the existing brief (Chinese)](./example-product-discovery.md). Its targets are fictional product settings, not measured benefits.

## Step 2: write a reviewable PRD

Full definition: [prd-generation (Chinese)](../skills/04_prd-generation.md). Start a new conversation:

```text
$prd-generation
Read doc/TeamLog_Brief.md and generate TeamLog's PRD in Standard mode.
Check that the input includes background, users, features, and scope before proceeding.
Confirm key technical decisions and keep the agreed MVP.
Label new recommendations separately and ask me to confirm them.
Check role permissions, report submission/editing, and fallback when AI summarization fails.
Map each feature to acceptance criteria, data, APIs, pages, and key states.
Keep unresolved questions in the open-questions table and retain draft or review status.
Respond in English. Save the final document to doc/TeamLog_PRD.md for this demo.
```

In text-only chat, paste the full definition and confirmed brief, and replace the file-reading instruction with a reference to the pasted brief.

Review permissions, report-editing rules, failed summaries, incomplete submissions, duplicate submissions, scope changes, and whether acceptance criteria can actually be tested.

Handoff: `doc/TeamLog_PRD.md`, including unresolved questions.

[Compare the PRD excerpt (Chinese)](./example-prd-generation.md). It is not a complete deliverable under the current 14-chapter template and should not replace your full PRD.

## Step 3: design pages, states, and a shared style

Full definition: [prototype-design (Chinese)](../skills/07_prototype-design.md). Start a new conversation:

```text
$prototype-design
Read doc/TeamLog_PRD.md and design TeamLog's V1 web prototype plan.
Confirm context and page scope first, then the shared style, wireframes, and prompts.
Prioritize login, progress dashboard, report entry, and summary details.
Identify and confirm additional pages required by the PRD's core flows.
Cover relevant normal, empty, loading, failure, and interrupted-entry recovery states.
Include feature-to-page mapping, shared design tokens, wireframes and interaction notes,
and bilingual image prompts using the same Style Anchor.
Produce documents and prompts only; do not call image APIs or generate actual images.
Respond in English. Save the plan to doc/TeamLog_Prototype.md.
```

In text-only chat, paste the full definition and PRD, and replace the file-reading instruction with a reference to the pasted text.

Check that core features have page entry points, permissions match the PRD, exceptional states have clear feedback, and every page references the same Style Anchor ID / version and design tokens.

[Compare the prototype excerpt (Chinese)](./example-prototype-design.md). It contains prompts rather than generated images; images alone do not implement interactions or accessibility.

## Save and check

This demo uses fixed filenames for easier handoffs. Normal skill filenames also include dates and versions.

```text
doc/
├── TeamLog_Brief.md
├── TeamLog_PRD.md
└── TeamLog_Prototype.md
```

From the cloned repository root, run the following commands after replacing the paths with the actual demo files:

```powershell
pwsh ./scripts/validate-product-artifact.ps1 -Path 'D:\demo\doc\TeamLog_PRD.md' -Type PRD
pwsh ./scripts/validate-product-artifact.ps1 -Path 'D:\demo\doc\TeamLog_Prototype.md' -Type Prototype
```

The validator checks document structure and unexplained placeholders. Some required section markers are currently Chinese, so fully English outputs may report missing sections unless those markers are retained. Passing does not validate product decisions, data, or design. Run it on completed outputs; abbreviated repository samples may fail the full checks.

## Share an actual run

Record tool/model versions, the skill repository revision, inputs, key answers, full documents, human edits, and unresolved issues. If measuring duration, separate interaction time from model waiting time.

A short recording can show the initial request, a key follow-up, MVP scope, one acceptance criterion, and a wireframe with a failure state. Show only work actually completed, and sanitize sensitive information.

See [Contributing (Chinese)](../CONTRIBUTING.md) to share a reproducible run. If the workflow helps you, Star the repository to save it.
