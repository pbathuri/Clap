# M45I–M45L — Supervisory Control Panel + Human Takeover Paths (Deliverable)

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `supervision_group` and commands: loops, show, pause, resume, stop, takeover, redirect, handback, approve-continuation, rationale. |
| `src/workflow_dataset/mission_control/state.py` | Added `supervisory_control_state` (active/paused/awaiting/taken_over counts, most_urgent_loop_id, most_urgent_reason) and `local_sources["supervisory_control"]`. |
| `src/workflow_dataset/supervisory_control/store.py` | save_pause_state and save_takeover_state accept optional `loop_id` when clearing state. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M45I_M45L_SUPERVISORY_CONTROL_BEFORE_CODING.md` | Before-coding: existing surfaces, gaps, file plan, safety, takeover/handback principles. |
| `src/workflow_dataset/supervisory_control/__init__.py` | Package exports. |
| `src/workflow_dataset/supervisory_control/models.py` | SupervisedLoopView, OperatorIntervention, PauseState, RedirectState, TakeoverState, HandbackState, OperatorRationale, LoopControlAuditNote; status and intervention constants. |
| `src/workflow_dataset/supervisory_control/store.py` | Persist loops, interventions, pause/redirect/takeover/handback, rationales, audit notes under data/local/supervisory_control/. |
| `src/workflow_dataset/supervisory_control/flows.py` | pause_loop, resume_loop, stop_loop, take_over_loop, redirect_loop, approve_continuation, handback_loop. |
| `src/workflow_dataset/supervisory_control/panel.py` | sync_loop_views_from_supervised, list_loops, get_loop, inspect_loop, inspect_confidence_gates, attach_rationale, attach_audit_note, mission_control_slice. |
| `tests/test_supervisory_control.py` | 14 tests: model, pause, resume, takeover/handback, handback without takeover, redirect, stop, rationale, audit note, inspect, mission slice, list_loops sync, approve_continuation. |
| `docs/M45I_M45L_SUPERVISORY_CONTROL_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# List supervised loops (synced from agent-loop cycle)
workflow-dataset supervision loops
workflow-dataset supervision loops --json

# Inspect one loop
workflow-dataset supervision show --id <loop_id>
workflow-dataset supervision show --id default --json

# Pause / resume
workflow-dataset supervision pause --id <loop_id> [--reason "reason"]
workflow-dataset supervision resume --id <loop_id>

# Stop loop (clear pause/takeover, mark stopped)
workflow-dataset supervision stop --id <loop_id> [--reason "reason"]

# Take over / handback
workflow-dataset supervision takeover --id <loop_id> [--note "note"]
workflow-dataset supervision handback --id <loop_id> [--note "note"] [--safe | --unsafe]

# Redirect next step (advisory)
workflow-dataset supervision redirect --id <loop_id> --hint "next step text"

# Approve bounded continuation (when paused)
workflow-dataset supervision approve-continuation --id <loop_id>

# Attach operator rationale
workflow-dataset supervision rationale --id <loop_id> --text "reason" [--intervention int_id]
```

## 4. Sample supervision loop view

```json
{
  "loop_id": "cy_abc123",
  "label": "founder_case_alpha",
  "status": "active",
  "project_slug": "founder_case_alpha",
  "goal_text": "Ship weekly stakeholder update",
  "cycle_id": "cy_abc123",
  "pending_count": 1,
  "last_activity_utc": "2025-03-16T14:00:00+00:00",
  "created_at_utc": "2025-03-16T12:00:00+00:00",
  "updated_at_utc": "2025-03-16T14:00:00+00:00"
}
```

## 5. Sample takeover / redirect output

**Takeover:**
```
Takeover loop cy_abc123: Manual control for review
```

**Redirect:**
```
Redirect loop cy_abc123: Run job weekly_status_from_notes
```

**Handback:**
```
Handback loop cy_abc123  safe_to_resume=True
```

## 6. Sample handback output

CLI:
```
Handback loop L1  safe_to_resume=True
```

Stored HandbackState:
```json
{
  "loop_id": "L1",
  "handback_at_utc": "2025-03-16T14:05:00+00:00",
  "handback_note": "Review complete",
  "safe_to_resume": true
}
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_supervisory_control.py -v
```

**Result:** 14 passed.

- test_supervised_loop_view_model
- test_pause_loop
- test_resume_loop
- test_takeover_handback
- test_handback_without_takeover_returns_none
- test_redirect_loop
- test_stop_loop
- test_attach_rationale
- test_attach_audit_note
- test_inspect_loop_empty
- test_mission_control_slice_no_loops
- test_mission_control_slice_with_paused
- test_list_loops_syncs_from_supervised
- test_approve_continuation_requires_pause

## 8. Exact remaining gaps for later refinement

- **Wire to executor/agent-loop** — Pause/takeover/redirect are stored and visible; agent-loop next/approve does not yet read redirect hint or respect supervisory pause (e.g. skip proposing when loop is paused). Integration point: supervised_loop next_action or executor gate.
- **Inspect influential memory/prior cases** — Panel has inspect_loop and inspect_confidence_gates; no explicit “influential memory” or “prior cases” slice yet; can be added in panel or via memory_curation / learning_lab.
- **Multiple concurrent loops** — Currently one primary loop (cycle) from supervised_loop; loop_id can be cycle_id or default. Full multi-loop dashboard would persist multiple loop views and allow switching.
- **Unsafe handback** — Handback with safe_to_resume=False is stored but no downstream gate (e.g. “require re-approval before next real run”) is enforced yet.
- **Operator_mode integration** — Supervisory pause is loop-level; operator_mode global pause is separate. Optional: when supervisory “stop” is used, optionally signal or record in operator_mode for consistency.
- **Review studio / audit UI** — Rationale and audit notes are stored and CLI-attachable; no dedicated review-studio surface for “all interventions for this loop” or “audit trail for last 24h”.
