# M24D–M24G — Local Capability Activation Block

First-draft local activation subsystem: source registry hardening, activation request/preview/execution, capability health and lifecycle, mission control visibility, CLI and reports.

## Current repo state (summary)

- **Runtime mesh:** backends, model catalog, integration registry with `set_integration_enabled`.
- **External capability:** schema (with rollback_notes, machine_requirements, supported_value_pack_ids, LIFECYCLE_STATES), registry, policy, planner, plans, activation_models, activation_store, preview, executor.
- **Lifecycle:** `source_lifecycle_state(source_id)` → installed | configured | active | blocked | failed | unknown.
- **Health:** `build_capability_health()`, `format_health_report()` — lifecycle summary, prerequisite checks, failed activations, deactivation path, recommended next.
- **Mission control:** external_capabilities + activation_executor (pending, blocked, enabled, failed, rollback_count, **recommended_next_capability_action**).
- **CLI:** capabilities external list | recommend | plan | request | preview | execute | disable | history | **list-requests** | **health**.

## What exists (planning + execution)

- Unified source registry (integrations, backends, model catalog); override file; policy; planner; plan steps.
- Activation request model and store; preview; approval-gated execute; disable; history.
- Safe execution: enable/disable integration manifests; verify backend; instructions_only for ollama models.
- Capability health: lifecycle, prerequisite checks, failed diagnostics, deactivation path, recommended next.
- Mission control: pending, blocked, enabled, failed, rollback, recommended next capability action.

## What this block does NOT do

- Auto-download large models or run ollama pull.
- Auto-enable cloud/remote behavior.
- Bypass approval/trust policy.
- Rewrite runtime mesh.

---

## 1. Files modified

| File | Change |
|------|--------|
| `external_capability/schema.py` | LIFECYCLE_STATES; added rollback_notes, machine_requirements, supported_value_pack_ids to ExternalCapabilitySource and to_dict/from_dict. |
| `external_capability/registry.py` | rollback_notes and machine_requirements set in _integration_to_source, _backend_to_source, _model_to_source. |
| `external_capability/lifecycle.py` | (new) source_lifecycle_state(); use list_requests(status="failed") for failed. |
| `mission_control/state.py` | activation_executor: added recommended_next_capability_action. |
| `mission_control/report.py` | Print recommended_next_capability_action in [Activation executor]. |
| `cli.py` | capabilities external list-requests [--status], capabilities external health [--output]. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M24D_M24G_ACTIVATION_BLOCK_ANALYSIS.md` | Before-coding: current state, gaps, file plan, safety, out-of-scope. |
| `external_capability/lifecycle.py` | source_lifecycle_state(source_id, repo_root) → installed | configured | active | blocked | failed | unknown. |
| `external_capability/health.py` | build_capability_health(), format_health_report(); PrerequisiteCheck, CapabilityHealth. |
| `tests/test_capability_activation_block.py` | Schema lifecycle/rollback, source_lifecycle_state, build_capability_health, format_health_report, list_requests filter, mission_control recommended_next. |
| `docs/M24D_M24G_ACTIVATION_BLOCK.md` | This doc. |

## 3. Exact CLI usage

```bash
workflow-dataset capabilities external list
workflow-dataset capabilities external recommend [--domain D] [--task T]
workflow-dataset capabilities external plan --source <id>
workflow-dataset capabilities external request --source <id> [--action enable|disable|verify]
workflow-dataset capabilities external preview --id <activation_id>
workflow-dataset capabilities external execute --id <activation_id> [--approved]
workflow-dataset capabilities external disable --source <id>
workflow-dataset capabilities external history [--limit N]
workflow-dataset capabilities external list-requests [--status pending|blocked|executed|failed]
workflow-dataset capabilities external health [--output FILE]
```

## 4. Sample source registry entry

```json
{
  "source_id": "openclaw",
  "category": "openclaw",
  "local": true,
  "optional_remote": false,
  "security_notes": "Reference-only in this repo; no live import.",
  "supported_task_classes": ["desktop_assistant", "orchestration"],
  "supported_tiers": ["dev_full", "local_standard"],
  "activation_status": "optional",
  "enabled": false,
  "rollback_notes": "Set enabled=false in integration manifest or run: capabilities external disable --source openclaw"
}
```

## 5. Sample activation request

```json
{
  "activation_id": "act_openclaw_20250116143022",
  "source_id": "openclaw",
  "source_category": "openclaw",
  "requested_action": "enable",
  "approvals_required": ["optional_wrapper"],
  "expected_resource_cost": "medium",
  "reversible": true,
  "status": "pending",
  "created_at": "2025-01-16T14:30:22Z"
}
```

## 6. Sample activation preview

```
Activation preview: act_openclaw_20250116143022
---
  source_id: openclaw  action: enable
  approval_required: True  blocked: False  safe_to_proceed: True

What would change:
  - Set integration 'openclaw' enabled=true in integration manifest.
Files/configs affected:
  - data/local/runtime/integration_manifests.json
```

## 7. Sample execution / blocked output

- **Executed:** `Outcome: executed` / `Integration enabled.`
- **Blocked:** `Outcome: blocked` / `Operator approval required; run with --approved after review.`
- **Instructions only:** `Outcome: instructions_only` / `No auto-download. Follow instructions: ...`

## 8. Sample capability health report

```
=== Capability health report ===

[Lifecycle summary]
  active: 0  configured: 2  installed: 8  blocked: 0  failed: 0  unknown: 0
  total_sources: 12

[Prerequisite checks]
  backend_ollama  ollama_reachable: ok  Ollama responding
  openclaw  integration_enabled: ok  disabled

[Failed activations]
  (none)

[Deactivation path available]
  openclaw
  coding_agent
  ...

[Recommended next]
  Run: workflow-dataset capabilities external recommend (then request/preview/execute as needed)
```

## 9. Tests run

```bash
pytest tests/test_capability_activation_block.py tests/test_external_capability_executor.py tests/test_external_capability.py -v
```

Covers: schema lifecycle/rollback, source_lifecycle_state, build_capability_health, format_health_report, list_requests filter, mission_control recommended_next_capability_action, plus existing executor and external_capability tests.

## 10. Remaining gaps for a later refinement pass

- **Override file roundtrip:** When saving overrides (e.g. from executor or future UI), persist rollback_notes and supported_value_pack_ids so they survive registry reload.
- **Prerequisite checks:** Extend to more backends (e.g. repo_local path existence) and optional resource checks.
- **Health output format:** Optional JSON/structured output for `capabilities external health` for tooling.
- **list-requests output:** Optional table or JSON for scripting.
- **Recommended next:** Consider value-pack and domain context when choosing the next action (e.g. recommend request for value-pack–relevant source first).
