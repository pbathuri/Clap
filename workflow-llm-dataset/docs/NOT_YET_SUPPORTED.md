# Not yet supported (v1 narrow release)

Truthful boundary for the first narrow release. Do not demo or claim these as production-ready.

---

## Out of scope for v1

- **Spreadsheet-heavy workflows:** Structured workbook creation, population from live data, reconciliation automation. (Adapters exist for spreadsheet output; they are not the primary release focus.)
- **Founder handoff as primary:** Multi-project handoff packages and startup cadence are in trials but not the chosen first scope; ops reporting is.
- **Creative/design workflows:** Creative brief, storyboard, revision plan bundles. Deferred.
- **Multi-user or sync:** Single user, one device; no cloud sync, no shared state.
- **Automated execution:** Agent suggests only; no execution without explicit user confirmation. Apply is always confirm-first.
- **Production SLA:** No uptime, latency, or support guarantees; internal/friendly-user use only.
- **Deep personalization:** Model often generic; “user’s style” is mild. We do not claim “remembers everything about you.”

---

## Still internal / dev flows

- **Full LLM training pipeline:** Corpus build, SFT build, full-train, compare-runs — for internal iteration, not end-user.
- **Workflow trials framework:** Trials list/run/compare/report — for evaluation; release run/demo are the user-facing entrypoints.
- **Raw observation/event ingestion:** File observer, event log — config exists but not part of narrow release UX.
- **Multiple backends:** Document/image demos, mock backends — config-gated; release focuses on ops + adapter.

---

## Future roadmap (not v1)

- Richer retrieval tuning so retrieval consistently helps (not hurts) full adapter on eval.
- More SFT from setup/graph for stronger personalization.
- Spreadsheet-first or creative-first narrow release after ops release is validated.
- Optional merge of adapter into base for faster inference.
- Pilot with multiple friendly users and feedback loop.

---

## Do not demo as production-ready

- Do not claim “full personal assistant” or “remembers your workflow.”
- Do not promise retrieval always improves answers (evidence shows mixed impact).
- Do not show apply without emphasizing “you must confirm; we never write without approval.”
- Do not suggest v1 is suitable for broad or paying users without explicit “first narrow release” framing.
