<div align="center">

# Clap

**Workflow-LLM dataset + OpenClaw gateway - the data-and-infrastructure layer beneath OpsPilot.**

<br/>

<img src="https://img.shields.io/badge/Language-Python-0D1117?style=for-the-badge&logo=python&logoColor=FFA657&labelColor=161B22" />
<img src="https://img.shields.io/badge/Type-data%20%2B%20gateway-0D1117?style=for-the-badge&labelColor=161B22&color=58A6FF" />
<img src="https://img.shields.io/badge/Status-active-0D1117?style=for-the-badge&labelColor=161B22&color=FFA657" />

</div>

---

## TL;DR

Clap is the workspace that feeds **OpsPilot** - a privacy-first workflow-automation agent. It holds the training dataset, the gateway layer that brokers local ↔ cloud inference, and the program dashboard for tracking what's being built.

The consolidated, actively-maintained workspace is **[Clap_OpsPilot](https://github.com/pbathuri/Clap_OpsPilot)**. This repo is the dataset + gateway slice.

---

## Layout

| Path | Purpose |
|------|---------|
| `workflow-llm-dataset/` | Python dataset + scaffolding for the local workflow-capture agent |
| `openclaw/` | OpenClaw gateway - nested service for routing inference |
| `clap_program_dashboard.xlsx` | Program-level tracking spreadsheet |

---

## Context

OpsPilot is a **two-agent system** - a local capture agent (privacy-preserving) and a cloud reasoning agent (QLoRA-fine-tuned on workflow traces). Clap supplies the dataset + transport glue. See [`Clap_OpsPilot`](https://github.com/pbathuri/Clap_OpsPilot) for the full architecture and build-status reference.

---

<div align="center">
<sub>Consolidated workspace → <a href="https://github.com/pbathuri/Clap_OpsPilot">Clap_OpsPilot</a> · Part of <a href="https://github.com/pbathuri">@pbathuri</a>'s <a href="https://github.com/pbathuri/Map_Projects_MAC">project portfolio</a>.</sub>
</div>
