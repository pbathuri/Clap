# Narrow private pilot scope (M20)

Operational definition of who may use the pilot, what is supported, and what is excluded. This is narrower than the broad product vision.

---

## Target pilot user profile

- **Role:** One person who does recurring reporting or status work (ops/office lead).
- **Context:** Single device; local-first; willing to run one-time setup (scan, parse, graph) and then use suggestions and generated scaffolds.
- **Expectation:** Narrow, suggest-only tool; no promise of full automation or production SLA.
- **Not:** Multi-user, stakeholder demo requiring polish, or users with no ops/reporting context.

---

## Supported workflow category

**Operations / office admin — reporting and status only.**

- Recurring reporting workflow summarization.
- Weekly status / report package scaffolding.
- Next-step recommendations from project and routine context.
- Workflow explanation from observed patterns (e.g. .csv/.xlsx usage).

---

## Supported task set

| Task ID | Description |
|---------|-------------|
| ops_summarize_reporting | Summarize user's recurring reporting workflow and suggest weekly status structure |
| ops_scaffold_status | Propose weekly status report package structure in user's style |
| ops_next_steps | Recommend next steps based on projects and routines |
| release_demo | Founder demo: 3 prompts (workflow style, recurring patterns, reporting structure) |

**Excluded from pilot:** ops_handoff_bundle as primary flow, founder handoff, creative/spreadsheet/finance workflows, multi-user, cloud, automated execution.

---

## Supported operating mode

- **Primary:** Adapter (full-trained adapter when available).
- **Fallback:** Base model when no successful adapter exists; operator is notified (degraded mode).
- **Optional:** Retrieval-grounded prompts (`--retrieval`); if retrieval fails, degrade to non-retrieval with notice.
- **Not in pilot:** Multiple backends, mock backends, or non-ops adapters as primary.

---

## Supported output types

- Text: suggestions, workflow summary, next steps, explanations (CLI and console).
- Sandbox artifacts: generation workspace, bundle dir under `data/local/bundles`; adoption candidate for apply preview/confirm.
- **No** direct writes to user's real project paths without explicit apply confirmation.

---

## Safety boundaries

- **No uncontrolled writes:** All generated output in sandbox; apply only after preview + confirm.
- **Local-only:** No cloud APIs; no telemetry; no external calls except optional model download.
- **Simulate-first:** Suggest and explain only; no execution without approval.

---

## Expected pilot frequency / intensity

- **Frequency:** 2–5 pilot users; 1–3 sessions per user initially.
- **Intensity:** Short sessions (verify → run or demo → record feedback); not all-day or production-critical use.
- **Data:** Sandbox or non-critical data only; no production systems.

---

## What counts as pilot success

- Pilot user completes release verify and at least one of: release run, release demo, or console suggestions without founder handholding for every step.
- At least one of: usefulness ≥ 3, trust ≥ 3, or freeform indicates adoptable output.
- No critical blocker (e.g. repeated crash, data loss, or uncontrolled write).
- Operator can diagnose common failures via pilot status/verify and operator guide.

---

## What counts as pilot failure / pause

- Repeated failure of release verify (missing graph or unrecoverable config).
- Repeated inference failure with no clear fallback (adapter broken, base model not loadable).
- User reports uncontrolled write or data loss.
- Operator cannot resolve blocking issue using pilot docs and status commands.

See **docs/RELIABILITY_TRIAGE.md** and **docs/PILOT_OPERATOR_GUIDE.md** for triage and recovery.
