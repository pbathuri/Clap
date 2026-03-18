# M45I–M45L — Supervisory Control Panel + Human Takeover Paths: Before Coding

## 1. What supervision/monitoring/control surfaces already exist

| Area | What exists | Limitation for supervisory control panel |
|------|-------------|------------------------------------------|
| **supervised_loop/** | AgentCycle, QueuedAction, ApprovalQueueItem, ExecutionHandoff, OperatorPolicy; current_cycle.json, approval_queue.json, handoffs.json; status proposing/awaiting_approval/executing/completed/blocked/idle. build_cycle_summary() for CLI/mission control. | Single cycle; no first-class “loop view” with pause/takeover/handback; no operator rationale or audit notes; no redirect/takeover state. |
| **operator_mode/** | DelegatedResponsibility, PauseState (emergency/safe/none), RevocationRecord, OperatorModeSummary; explain_work_impact (what will stop/continue/human takeover). pause_revocation: set_emergency_pause, set_safe_pause, clear_pause. | Global pause over responsibilities; not loop-scoped. No takeover/handback or “return to supervised” flow. |
| **mission_control/** | Aggregates supervised_loop (cycle_id, status, queue counts, next_proposed_action_*), operator_mode_state (pause_kind, suspended count, next_action). Read-only. | No “active supervised loops”, “paused loops”, “awaiting continuation”, “under takeover”, or “most urgent intervention candidate”. |
| **agent-loop CLI** | status, next, queue, approve, reject, defer, cycle-report. | No supervision pause, takeover, redirect, handback, or rationale. |
| **trust / approvals / audit** | Trust cockpit, approval registry, audit trails (not rebuilt here). | Not a control surface for loop intervention; remain downstream. |
| **queue / day / continuity** | Unified queue, day presets, continuity (not rebuilt here). | Can feed “what’s pending”; no direct loop control. |

So: **cycle + queue + operator pause exist; missing a unified supervisory control layer with loop-level pause, takeover, redirect, handback, rationale, and audit notes.**

---

## 2. What is missing for a real supervisory control panel

- **Supervised loop view** — First-class view of a loop (id, label, status, ref to cycle, pending/awaiting/taken_over), not just raw cycle summary.
- **Operator intervention** — Recorded intervention: pause, stop, takeover, redirect, approve_continuation, handback, with timestamp and optional rationale.
- **Pause state (loop-level)** — This loop is paused (reason, at_utc); distinct from operator_mode’s global pause.
- **Redirect state** — Next-step hint or redirect target for the loop; applied flag.
- **Takeover state** — Loop is under manual control; operator_note; return time when handback happens.
- **Handback state** — Loop returned to supervised mode; handback_note; safe_to_resume flag.
- **Operator rationale** — Text reason attached to an intervention or loop; stored and attachable to audit.
- **Loop-control audit note** — Immutable note (rationale, gate_status, audit) attached to loop or intervention.
- **CLI** — supervision loops | show | pause | stop | takeover | redirect | handback | approve-continuation (and optionally attach rationale).
- **Mission control slice** — active supervised loops, paused loops, awaiting continuation, under takeover, most urgent intervention candidate.

---

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M45I_M45L_SUPERVISORY_CONTROL_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/supervisory_control/models.py` | SupervisedLoopView, OperatorIntervention, PauseState, RedirectState, TakeoverState, HandbackState, OperatorRationale, LoopControlAuditNote. |
| Store | `src/workflow_dataset/supervisory_control/store.py` | Persist loops, interventions, pause/redirect/takeover/handback, rationales, audit notes under data/local/supervisory_control/. |
| Flows | `src/workflow_dataset/supervisory_control/flows.py` | pause_loop, stop_loop, take_over_loop, redirect_loop, approve_continuation, handback_loop; integrate with supervised_loop where appropriate. |
| Panel | `src/workflow_dataset/supervisory_control/panel.py` | inspect_loop, inspect_confidence_gates, attach_rationale; build loop view from supervised_loop + supervisory store. |
| CLI | `src/workflow_dataset/cli.py` | supervision group: loops, show, pause, stop, takeover, redirect, handback, approve-continuation, rationale. |
| Mission control | `src/workflow_dataset/mission_control/state.py` | supervisory_control_state: active/paused/awaiting/taken_over counts, most_urgent_intervention_candidate. |
| Tests | `tests/test_supervisory_control.py` | Model creation, pause/takeover/redirect/handback, rationale, invalid handback, no-loop/many-loop. |
| Deliverable | `docs/M45I_M45L_SUPERVISORY_CONTROL_DELIVERABLE.md` | Files, CLI, samples, tests, gaps. |

---

## 4. Safety/risk note

- **No hidden control transfer** — Takeover and handback are explicit; state is stored and visible.
- **No bypass of trust/review** — Supervisory layer does not replace trust or approval gates; it adds a human-supervision layer on top.
- **Handback only when safe** — Handback state includes safe_to_resume; UI/CLI can require explicit confirmation before returning to supervised mode.
- **Audit trail** — Operator rationale and loop-control audit notes are persisted; no silent overrides.

---

## 5. Takeover/handback principles

- **Explicit takeover** — Operator takes over a loop by explicit action; loop status becomes “taken_over”; no automatic takeover.
- **Clean handback** — Handback records when and why control was returned; optional safe_to_resume and note; loop can return to “active” or “awaiting_continuation” as appropriate.
- **Pause is reversible** — Pause state stores reason; resume clears pause and allows loop to continue (subject to approval gates).
- **Redirect is advisory** — Redirect stores next-step hint for the loop; execution layer (e.g. agent-loop next) may use it; no forced execution without approval.

---

## 6. What this block will NOT do

- Rebuild workspace shell, mission control, review studio, operator mode, trust/approvals/audit, queue/day/continuity.
- Replace or duplicate operator_mode’s global pause; we add loop-level pause and integrate where useful.
- Implement adaptive execution or shadow execution (Pane 1/2); we consume supervised_loop and optional cycle id as “the loop”.
- Auto-execute after redirect; redirect is a hint, not a bypass of approval.
- Hidden or automatic takeover/handback; all transitions are operator-initiated and recorded.
