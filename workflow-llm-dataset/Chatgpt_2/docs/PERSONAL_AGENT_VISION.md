# Personal Agent Vision

## Product direction

We are building a **plug-and-play personal work agent** that runs on a physical edge device (initial target: Raspberry Pi 5 + AI module; later stronger edge hardware). It connects to one user’s work environment, learns privately from that user’s laptop/tools/data/workflows, builds a structured understanding of how they work, and acts as a **Jarvis-like desktop/work operator**.

## Non-goals (explicit)

- This is **not** a generic cloud SaaS assistant.
- This is **not** an always-online product that sends user data to remote inference by default.
- The agent does **not** change the user’s actual local system unless the user explicitly approves.

## Core requirements

| Requirement | Meaning |
|-------------|---------|
| **Local-first** | Primary compute and storage on the user’s device or dedicated edge device. |
| **Private-first** | Raw user learning stays on-device; no telemetry or training on user data unless explicitly authorized. |
| **Continuous passive learning** | The system can observe (within configured tiers) files, apps, browser, terminal, calendar, etc. |
| **Explicit teaching** | The user can demonstrate, correct, and instruct the agent; this is first-class input. |
| **Personal work memory** | A structured graph of the user’s projects, routines, tools, workflows, and preferences. |
| **Task/workflow execution graph** | A model of how the user executes tasks and workflows, used for suggestion and later automation. |
| **Safe execution by default** | Default mode is **simulate**: proposals and dry-runs only; no writes to the real system without approval. |
| **Approval-gated local actions** | When the user opts into **assist** or **automate**, actions on the real machine are bounded by user-defined approval rules. |
| **Optional model/workflow packs** | The device can download additional models or workflow packs from an online library **without leaking user data**. |

## Primary verticals (v1 focus)

- Logistics
- Operations
- Founder workflows
- Office admin

Other domains are in scope as extensions after the foundation is stable.

## Relation to the current repo

The existing **workflow-llm-dataset** pipeline is the **global prior layer**. It produces occupational data (tasks, tools, workflows, labor market, industry–occupation mapping) that the device uses to interpret the user’s role and work. It is **not** the end product; it is the prior knowledge base that makes the personal agent’s interpretations and suggestions grounded and domain-aware.
