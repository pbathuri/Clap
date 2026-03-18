# M40A–M40D Production Cut — Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `production_cut_group` and commands: `show`, `lock`, `scope`, `explain`, `surfaces`. |
| `src/workflow_dataset/mission_control/state.py` | Added `production_cut_state` (active_cut_id, vertical_id, included/excluded/quarantined counts, primary_workflow_ids, top_scope_risk, next_freeze_review). |
| `src/workflow_dataset/mission_control/report.py` | Added report block for Production cut. |
| `src/workflow_dataset/vertical_selection/scope_lock.py` | `get_scope_report(vertical_id, repo_root=None)` — added optional `repo_root` for API compatibility with production_launch gates. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/production_cut/__init__.py` | Public API. |
| `src/workflow_dataset/production_cut/models.py` | ProductionCut, ChosenPrimaryVertical, IncludedSurface, ExcludedSurface, QuarantinedExperimentalSurface, SupportedWorkflowSet, RequiredTrustPosture, DefaultOperatingProfile, ProductionReadinessNote. |
| `src/workflow_dataset/production_cut/store.py` | get_active_cut, set_active_cut; `data/local/production_cut/active_cut.json`. |
| `src/workflow_dataset/production_cut/lock.py` | choose_primary_from_evidence, build_production_cut_for_vertical, lock_production_cut, explain_production_cut. |
| `src/workflow_dataset/production_cut/freeze.py` | build_production_freeze, get_default_visible_surfaces, get_hidden_experimental_surfaces, get_blocked_unsupported_surfaces. |
| `src/workflow_dataset/production_cut/scope_report.py` | build_frozen_scope_report, build_surfaces_classification. |
| `tests/test_production_cut.py` | 13 tests: model, lock, freeze, scope report, classification, explain, invalid/unknown vertical. |
| `docs/M40A_M40D_PRODUCTION_CUT_BEFORE_CODING.md` | Before-coding: what exists, what’s missing, file plan, safety, principles, what this block will NOT do. |
| `docs/M40A_M40D_PRODUCTION_CUT_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# Show active production cut
workflow-dataset production-cut show
workflow-dataset production-cut show --repo /path/to/repo
workflow-dataset production-cut show --json

# Lock production cut for a vertical (sets active cut, active vertical, active pack)
workflow-dataset production-cut lock --id founder_operator_core
workflow-dataset production-cut lock --id founder_operator_core --cut-id my_cut
workflow-dataset production-cut lock --id founder_operator_core --json

# Frozen-scope report (included / excluded / quarantined)
workflow-dataset production-cut scope
workflow-dataset production-cut scope --json

# Explain active cut (why chosen, what’s in/out, defaults)
workflow-dataset production-cut explain
workflow-dataset production-cut explain --json

# List included, excluded, quarantined surfaces
workflow-dataset production-cut surfaces
workflow-dataset production-cut surfaces --json
```

## 4. Sample production cut

After `workflow-dataset production-cut lock --id founder_operator_core`:

```json
{
  "cut_id": "founder_operator_core_primary",
  "vertical_id": "founder_operator_core",
  "label": "Founder / Operator (core) (production cut)",
  "frozen_at_utc": "2026-03-17T19:30:00Z",
  "chosen_vertical": {
    "vertical_id": "founder_operator_core",
    "label": "Founder / Operator (core)",
    "selection_reason": "Curated pack and scope; morning ops and weekly status.",
    "primary_workflow_ids": ["morning_ops", "weekly_status_from_notes", "weekly_status", "morning_reporting"],
    "allowed_roles": ["founder operator core"],
    "allowed_modes": ["preferred"],
    "non_core_surface_ids": [...],
    "excluded_surface_ids": [...]
  },
  "included_surface_ids": ["workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward", ...],
  "excluded_surface_ids": [...],
  "quarantined_surface_ids": ["automation_inbox", ...],
  "supported_workflows": { "workflow_ids": ["morning_ops", ...], "path_id": "founder_ops_core_workflow", "label": "Founder ops core workflow" },
  "required_trust": { "trust_preset_id": "supervised_operator", "review_gates_default": ["before_real"], "audit_posture": "before_real" },
  "default_profile": { "workday_preset_id": "founder_operator", "default_experience_profile_id": "founder_calm", "queue_section_order": [...], "operator_mode_usage": "preferred" },
  "production_readiness_note": { "summary": "Production cut for Founder / Operator (core); scope frozen.", "blockers": [], "warnings": [] }
}
```

## 5. Sample frozen-scope report

`workflow-dataset production-cut scope` (after lock):

```
Frozen scope  vertical=founder_operator_core  included=5  excluded=...  quarantined=...
  risk: N surfaces excluded from production scope

Included (default-visible): workspace_home, day_status, queue_summary, approvals_urgent, continuity_carry_forward, ...
Quarantined (experimental): automation_inbox, ...
```

`workflow-dataset production-cut scope --json` (excerpt):

```json
{
  "vertical_id": "founder_operator_core",
  "included": [{"surface_id": "workspace_home", "label": "Workspace home"}, ...],
  "excluded": [{"surface_id": "agent_loop", "label": "Agent loop"}, ...],
  "quarantined": [{"surface_id": "automation_inbox", "label": "Automation inbox"}, ...],
  "included_count": 5,
  "excluded_count": 25,
  "quarantined_count": 1,
  "top_scope_risk": "25 surfaces excluded from production scope"
}
```

## 6. Sample included/excluded/quarantined surface output

`workflow-dataset production-cut surfaces`:

```
Included (default-visible)
  workspace_home  Workspace home  level=recommended
  day_status  Day status  level=recommended
  queue_summary  Queue summary  level=recommended
  ...

Excluded
  agent_loop  Agent loop  reason=excluded
  timeline  Timeline  reason=excluded
  ...

Quarantined (experimental)
  automation_inbox  Automation inbox  reveal=on_demand
  ...
```

## 7. Exact tests run

```bash
pytest tests/test_production_cut.py -v --tb=short
```

**Result:** 13 passed (0.90s).

- test_production_cut_model  
- test_choose_primary_from_evidence  
- test_choose_primary_unknown_vertical  
- test_build_production_freeze  
- test_build_production_freeze_unknown  
- test_build_production_cut_for_vertical  
- test_build_production_cut_unknown  
- test_lock_production_cut_and_store  
- test_frozen_scope_report_from_cut  
- test_surfaces_classification  
- test_explain_production_cut  
- test_default_profile_generation  
- test_get_default_visible_and_blocked  

## 8. Exact remaining gaps for later refinement

- **Cohort intersection:** Production cut does not yet intersect with active cohort’s surface matrix (supported/experimental/blocked). Refinement: ensure included set is subset of cohort-supported; quarantined is subset of cohort-experimental.
- **Version/timestamp on cut:** No version field or cut history. Refinement: optional cut_version or list of prior cuts for audit.
- **Production gate wiring:** `production_launch` gate `supported_surface_freeze_complete` still only checks active vertical + scope report. Refinement: optionally require active production cut and validate surface set against it.
- **UI/Shell consumption:** No wiring from production cut to workspace/day/queue shell to hide excluded or gate quarantined. Refinement: shell reads active cut and applies default_visible_surfaces / blocked.
- **Weak cut validation:** No check that the chosen vertical has sufficient evidence or first-value progress before allowing lock. Refinement: optional gate “production cut only if first-value reached or explicit override”.
- **Doc:** Single operator doc linking vertical selection → packs → production cut → launch kit → rollout review (as in M39 integration report) not added in this block.
