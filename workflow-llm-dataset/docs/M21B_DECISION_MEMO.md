# M21B — Pilot batch execution & evidence-based decision memo

This memo answers: how many real pilot sessions and feedback entries exist, what the evidence shows, and the recommended decision (continue / refine and re-pilot / pause) with the smallest next step.

**Filled after running pilot batches.** Until evidence exists, the answers below reflect "no sessions yet" and the recommendation is to execute the runbook to generate evidence.

---

# Evidence-based decision memo (filled from current pilot data)

**Source:** `data/local/pilot/` (sessions, feedback, aggregate_report.json, aggregate_report.md, pilot_readiness_report.md). **Scope:** docs/PILOT_SCOPE.md — narrow ops/reporting assistant.

| # | Question | Evidence |
|---|----------|----------|
| 1 | **Session count** | **3** (pilot_readiness_report.md; 3 session JSONs in `sessions/`) |
| 2 | **Feedback count** | **3** (3 `*_feedback.json` in `feedback/`; one per session) |
| 3 | **Tasks attempted** | Narrow ops/reporting demo (operator_notes: "Completed narrow ops/reporting demo", "Completed second/third narrow pilot session"). Session `task_type` and `commands_run` not populated; scope per PILOT_SCOPE: ops_summarize_reporting, ops_scaffold_status, ops_next_steps, release_demo. |
| 4 | **Recurring blockers** | **None** (aggregate_report: recurring_blockers [], blocker_counts {}) |
| 5 | **Degraded-mode frequency** | **0%** (0 of 3 sessions; degraded_count 0, degraded_pct 0.0; all sessions adapter_mode, no degraded_mode) |
| 6 | **Avg usefulness / trust / adoption** | Usefulness **3.67** (3, 4, 4); trust **3.33** (3, 3, 4); adoption **3.67** (3, 4, 4). All ≥ 3. |
| 7 | **Operator friction patterns** | No `operator_friction_notes` in feedback. Freeform notes: "Helpful, but user wanted more specific next steps."; "Output was useful; user wanted clearer report location."; "Reporting flow was understandable and useful." So patterns: **report location unclear**, **next steps could be more specific**. |
| 8 | **User quote excerpts** | **None** (all feedback `user_quote` fields empty) |
| 9 | **Recommendation** | **Continue pilot** — No recurring blockers; no critical blockers; disposition continue for all 3; usefulness/trust/adoption ≥ 3; no safety issues. Per PILOT_SCOPE success criteria: met. |
| 10 | **Exact smallest engineering fix justified by evidence** | **Docs/clarity only:** Add a short operator-facing note (runbook or operator guide) on **where to find the report** (e.g. `data/local/pilot/pilot_readiness_report.md`, `data/local/trials/latest_feedback_report.md`, release report path) and **how to give “more specific next steps”** (e.g. point to ops_next_steps / status report / next action in console). No code/feature change; improves operator ability to answer user questions. |
| 11 | **Exact next milestone justified by evidence** | **Add 1–2 pilot users** (PILOT_SCOPE: 2–5 users; currently 3 sessions). Re-run aggregate after new sessions; optionally capture `user_quote` and `operator_friction_notes` in feedback to enrich next memo. If report-location/next-step docs are added, do that before or in parallel with the next batch. No broader milestone (no orchestration, connectors, or scope expansion). |

---

## 1. How many real pilot sessions were completed?

**Answer:** See `data/local/pilot/pilot_readiness_report.md` → **M21 pilot evidence** → "Pilot sessions completed".

- **0** — No M21 sessions have been run. Use docs/PILOT_RUNBOOK.md to run 2–3 sessions.
- **1+** — Count of session JSON files under `data/local/pilot/sessions/`.

---

## 2. How many feedback entries exist?

**Answer:** See readiness report → "Structured feedback entries".

- **0** — Run `pilot capture-feedback` after each session (before or after `pilot end-session`).
- **1+** — Count of `*_feedback.json` under `data/local/pilot/feedback/`.

---

## 3. What tasks were attempted?

**Answer:** Inspect session JSONs: `task_type`, `commands_run`, `operator_notes`. Inspect aggregate report: `session_summaries`, `feedback_by_session`.

---

## 4. What blockers recurred?

**Answer:** See `data/local/pilot/aggregate_report.md` (or `.json`) → **Recurring blockers** and **blocker_counts**.

- None listed — No recurring blockers in the aggregated sessions.
- Listed with counts — Address these before the next batch or document as known limitations.

---

## 5. Was degraded mode frequent?

**Answer:** See aggregate report → **Degraded mode:** N sessions (P%).

- **0%** — Adapter was available for all sessions.
- **> 50%** with 2+ sessions — Consider training adapter or documenting baseline-only as expected (per M21 criteria).

---

## 6. Are usefulness / trust / adoption signals strong enough?

**Answer:** See aggregate report → **avg_usefulness**, and feedback JSONs for trust_score, adoption_likelihood, user_quote.

- **avg_usefulness ≥ 3** and no critical blockers — Supports continuing pilot (per M21).
- **< 3** or repeated blocker_encountered — Refine and re-pilot or pause until fixed.

---

## 7. Recommendation

| Condition | Recommendation |
|-----------|----------------|
| No sessions yet | **Refine and re-pilot** — Execute the runbook to generate evidence first; then re-fill this memo. |
| Recurring blockers | **Refine and re-pilot** — Fix causes (graph, setup, adapter, docs); run another batch; re-aggregate. |
| Degraded frequent (e.g. &gt;50%), 2+ sessions | **Refine and re-pilot** — Train adapter or document baseline; re-pilot. |
| disposition = pause in any session | **Refine and re-pilot** or **Pause** — Review notes; fix before continuing. |
| Verify repeatedly fails; inference fails with no fallback; uncontrolled write/data loss reported | **Pause** — Stop adding users until resolved. |
| No recurring blockers; usefulness/trust/adoption support it; no critical safety issue | **Continue pilot** — Add another pilot user (2–5 total) per PILOT_SCOPE. |

---

## 8. Exact smallest next step

- **If 0 sessions:** Run one full batch (verify → start-session → release demo → capture-feedback → end-session → aggregate). Confirm session and feedback files and aggregate_report.md are written. Then run a second session and re-run aggregate; fill this memo with real counts and recommendation.
- **If 1+ sessions and recommendation = continue:** Schedule next pilot user; use same runbook; after 2–3 total sessions re-aggregate and update this memo.
- **If 1+ sessions and recommendation = refine:** Address recurring blockers or degraded-mode cause; run one more session; re-aggregate; update memo.
- **If recommendation = pause:** Do not add users; fix blocking issues; re-run pilot verify; then consider one internal session before resuming.

---

## References

- Runbook: docs/PILOT_RUNBOOK.md  
- M21 execution: docs/M21_PILOT_EXECUTION.md  
- Criteria: docs/M21_PILOT_EXECUTION.md § Criteria: continue / refine / pause  
- Operator guide: docs/PILOT_OPERATOR_GUIDE.md  
