# M50A–M50D — v1 Contract Freeze + Surface Finalization: Deliverable

First-draft v1 freeze layer: stable v1 contract model, surface classification (v1 core / v1 advanced / quarantined / excluded), workflow contract, support commitment, freeze report, CLI, and mission control.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/mission_control/state.py` | Added `v1_contract_state` from `v1_contract_slice(repo_root)` (try/except). |
| `src/workflow_dataset/mission_control/report.py` | Added "[V1 contract]" section: vertical, has_cut, core/advanced/quarantined/excluded counts, next_freeze_action. |
| `src/workflow_dataset/cli.py` | Added `v1-contract` Typer group and commands: `show`, `surfaces`, `workflows`, `explain --surface`, `freeze-report`. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/v1_contract/__init__.py` | Package exports. |
| `src/workflow_dataset/v1_contract/models.py` | StableV1Contract, V1CoreSurface, V1SupportedAdvancedSurface, QuarantinedExperimentalSurface, ExcludedSurface, StableWorkflowContract, SupportedOperatingPosture, SupportCommitmentNote. |
| `src/workflow_dataset/v1_contract/contract.py` | build_stable_v1_contract(repo_root) from production_cut store + freeze; classifies core vs advanced from vertical scope_lock. |
| `src/workflow_dataset/v1_contract/surfaces.py` | get_v1_surfaces_classification(), list_v1_core(), list_v1_advanced(), list_quarantined(), list_excluded(). |
| `src/workflow_dataset/v1_contract/explain.py` | explain_surface(surface_id, contract) → classification, rationale, may_rely_on. |
| `src/workflow_dataset/v1_contract/report.py` | build_freeze_report(), format_freeze_report_text(). |
| `src/workflow_dataset/v1_contract/mission_control.py` | v1_contract_slice(repo_root). |
| `tests/test_v1_contract.py` | 9 tests: contract build, to_dict, classification, explain, freeze report, slice, list helpers. |
| `docs/M50A_M50D_V1_CONTRACT_FREEZE_BEFORE_CODING.md` | Pre-implementation analysis. |
| `docs/M50A_M50D_V1_CONTRACT_FREEZE_DELIVERABLE.md` | This file. |

---

## 3. Exact CLI usage

```bash
workflow-dataset v1-contract show
workflow-dataset v1-contract show --repo-root /path --json

workflow-dataset v1-contract surfaces
workflow-dataset v1-contract surfaces --json

workflow-dataset v1-contract workflows
workflow-dataset v1-contract workflows --json

workflow-dataset v1-contract explain --surface operator_mode
workflow-dataset v1-contract explain --surface workspace_home --repo-root /path --json

workflow-dataset v1-contract freeze-report
workflow-dataset v1-contract freeze-report --json
```

---

## 4. Sample v1 contract

From `build_stable_v1_contract(repo_root).to_dict()` (with active cut and vertical founder_operator):

```json
{
  "contract_id": "stable_v1_contract",
  "vertical_id": "founder_operator",
  "vertical_label": "Founder / Operator",
  "frozen_at_utc": "2025-03-16T12:00:00Z",
  "has_active_cut": true,
  "v1_core_surfaces": [
    {"surface_id": "workspace_home", "label": "Workspace home", "rationale": "Core surface for chosen vertical."},
    {"surface_id": "queue_summary", "label": "Queue summary", "rationale": "Core surface for chosen vertical."}
  ],
  "v1_advanced_surfaces": [
    {"surface_id": "mission_control", "label": "Mission control", "rationale": "Supported advanced or optional surface."}
  ],
  "quarantined_surfaces": [
    {"surface_id": "experimental_feature", "label": "Experimental feature", "reveal_rule": "on_demand", "rationale": "Experimental; not in v1 supported set."}
  ],
  "excluded_surfaces": [
    {"surface_id": "out_of_scope_surface", "label": "Out of scope", "reason": "out_of_scope"}
  ],
  "stable_workflow_contract": {
    "workflow_ids": ["morning_ops", "weekly_status"],
    "path_id": "founder_operator_primary",
    "label": "Stable workflows for founder_operator",
    "description": "Primary supported workflows for stable v1.",
    "excluded_workflow_ids": []
  },
  "supported_operating_posture": {
    "trust_preset_id": "default",
    "review_gates_default": [],
    "audit_posture": "",
    "operator_mode_usage": "preferred",
    "description": "Required trust and review posture for v1."
  },
  "support_commitment_note": {
    "summary": "Stable v1: core and advanced surfaces supported; quarantined experimental; excluded out of scope.",
    "in_scope": ["Core and advanced surfaces", "Supported workflows", "Migration continuity bundle and restore"],
    "out_of_scope": ["Quarantined experimental surfaces", "Excluded surfaces", "Unsupported workflows"],
    "last_updated_utc": "2025-03-16T12:00:00Z"
  },
  "migration_support_expectation": "Continuity bundle and migration restore supported for v1."
}
```

---

## 5. Sample surface finalization report

From `get_v1_surfaces_classification(contract)` or `workflow-dataset v1-contract surfaces --json`:

```json
{
  "v1_core": [{"surface_id": "workspace_home", "label": "Workspace home", "rationale": "Core surface for chosen vertical."}],
  "v1_core_count": 1,
  "v1_advanced": [{"surface_id": "mission_control", "label": "Mission control", "rationale": "Supported advanced or optional surface."}],
  "v1_advanced_count": 1,
  "quarantined": [{"surface_id": "experimental_feature", "label": "Experimental feature", "reveal_rule": "on_demand", "rationale": "Experimental; not in v1 supported set."}],
  "quarantined_count": 1,
  "excluded": [{"surface_id": "other_vertical_surface", "label": "Other", "reason": "out_of_scope"}],
  "excluded_count": 1,
  "vertical_id": "founder_operator",
  "has_active_cut": true
}
```

---

## 6. Sample explanation output

From `workflow-dataset v1-contract explain --surface operator_mode` or `explain_surface("operator_mode", contract)`:

**When surface is v1_core:**
```json
{
  "surface_id": "operator_mode",
  "label": "Operator mode",
  "classification": "v1_core",
  "rationale": "Core surface for chosen vertical.",
  "may_rely_on": true,
  "support_note": "In scope for v1 support."
}
```

**When surface is excluded:**
```json
{
  "surface_id": "other_surface",
  "label": "Other surface",
  "classification": "excluded",
  "rationale": "Excluded from v1: out_of_scope.",
  "may_rely_on": false,
  "support_note": "Out of v1 scope.",
  "reason": "out_of_scope"
}
```

**When surface is unknown:**
```json
{
  "surface_id": "nonexistent_xyz",
  "label": "Nonexistent Xyz",
  "classification": "unknown",
  "rationale": "Surface not found in v1 contract; may be unmapped or from another vertical.",
  "may_rely_on": false,
  "support_note": "Not in current v1 contract."
}
```

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_v1_contract.py -v
```

**Result:** 9 passed.

- `test_build_stable_v1_contract_no_cut` — Contract built from default vertical when no active cut.
- `test_contract_to_dict` — Contract serializes to dict.
- `test_get_v1_surfaces_classification` — Classification has v1_core, v1_advanced, quarantined, excluded and counts.
- `test_explain_surface_core_or_unknown` — Explain returns classification and may_rely_on; unknown surface handled.
- `test_explain_surface_excluded` — Excluded surface returns classification excluded, may_rely_on False.
- `test_build_freeze_report` — Freeze report has in_v1, quarantined, excluded, may_rely_on_summary, next_freeze_action.
- `test_format_freeze_report_text` — Formatted text contains Vertical, In v1, Quarantined, Excluded, Next.
- `test_v1_contract_slice` — Mission control slice has vertical_id, has_active_cut, counts, next_freeze_action.
- `test_list_v1_core_advanced_quarantined_excluded` — List helpers return lists; no overlap between in_v1 and excluded.

---

## 8. Exact remaining gaps for later refinement

- **Production cut required for full contract:** Without an active production cut, contract is derived from default vertical (founder_operator) freeze; workflow_ids and posture may be empty. Locking a cut (production-cut lock) fills these. Optional: default cut seed or clearer “no cut” messaging.
- **Stable workflow contract source:** Workflows are taken from chosen_vertical.primary_workflow_ids or supported_workflows on cut; no separate “stable workflow contract” file. Later: optional data/local/v1_contract/stable_workflows.json for override.
- **Support commitment note content:** Support note is generic or from production_readiness_note; no structured “support commitment” template. Later: template or config for in_scope/out_of_scope and support summary.
- **Explain for workflows:** explain_surface only; no explain_workflow(workflow_id) for “in v1 / excluded” and rationale.
- **Ambiguity detection:** top_v1_ambiguity is set when no cut or no frozen_at_utc; could be extended (e.g. gate warnings, missing posture).
- **Integration with stable_v1_gate:** v1_contract does not call evaluate_stable_v1_gate; gate and contract are separate. Later: optional “v1-contract validate” that runs gate and reports blockers.
