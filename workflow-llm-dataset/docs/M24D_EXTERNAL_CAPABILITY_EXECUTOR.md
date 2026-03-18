# M24D — External Capability Activation Executor

Safe local activation execution on top of the M24A planning layer. Supports activation requests, previews, approval-gated execution, enable/disable state, rollback (disable), and audit trail. No auto-download; no silent enablement.

## 1. Activation request model

- **activation_id** — Unique id (e.g. `act_openclaw_20250116143022`)
- **source_id** — From external capability registry (e.g. `openclaw`, `ollama_qwen2.5-coder`)
- **source_category** — openclaw, coding_agent, ollama_model, etc.
- **requested_action** — `install` | `enable` | `disable` | `remove` | `verify`
- **prerequisites** — From source install_prerequisites
- **approvals_required** — From source approval_notes
- **expected_resource_cost** — low | medium | high
- **reversible** — Whether the action can be undone (disable)
- **status** — `pending` | `approved` | `blocked` | `executed` | `failed` | `rolled_back`
- **notes**, **risks** — From source
- **created_at**, **updated_at** — Timestamps

## 2. Activation preview

Given an activation request, preview shows:

- **what_would_change** — e.g. “Set integration 'openclaw' enabled=true in integration manifest.”
- **files_or_configs_affected** — e.g. `data/local/runtime/integration_manifests.json`
- **approval_required** — True when source has approval_notes or request has approvals_required
- **blocked** — True when source not in registry or policy rejects
- **block_reason** — Rejection code or message
- **safe_to_proceed** — True when action is safe local (e.g. enable/disable integration, verify)
- **steps_summary** — From build_activation_plan (for ollama_model: instructions only)

## 3. Executor behavior

- **enable** for integration ids (`openclaw`, `coding_agent`, `ide_editor`, `notebook_rag`): writes `data/local/runtime/integration_manifests.json` with `enabled: true`. Requires `--approved` when preview shows approval_required.
- **disable**: same integrations → `enabled: false`; other sources → “no local toggle” recorded.
- **verify**: backend status check (read-only).
- **ollama_model** (enable/install): no auto-pull; outcome `instructions_only` with steps; no file change.

## 4. Deactivation / rollback

- **disable** via CLI or `disable_source(source_id)`.
- Config toggles reverted by writing integration manifest with `enabled: false`.
- History records outcome and `action: disable` for audit.

## 5. Audit / visibility

- **Requests:** `data/local/activations/requests/<activation_id>.json`
- **History:** `data/local/activations/history.json` (entries: activation_id, outcome, details, recorded_at)
- Mission control: `activation_executor` — pending_activation_requests, blocked_activation_requests, enabled_external_capabilities, failed_activations, rollback_history_count.

## 6. CLI

| Command | Description |
|--------|-------------|
| `capabilities external request --source <id> [--action enable\|disable\|verify]` | Create activation request |
| `capabilities external preview --id <activation_id>` | Show what would change and approval/block status |
| `capabilities external execute --id <activation_id> [--approved]` | Execute request (use --approved when required) |
| `capabilities external disable --source <id>` | Disable source (integration manifest or record) |
| `capabilities external history [--limit N]` | Show activation execution/rollback history |

### Exact CLI usage

```bash
workflow-dataset capabilities external request --source ollama_qwen2.5-coder --action enable
workflow-dataset capabilities external request --source openclaw --action enable --repo-root /path
workflow-dataset capabilities external preview --id act_openclaw_20250116143022
workflow-dataset capabilities external execute --id act_openclaw_20250116143022 --approved
workflow-dataset capabilities external disable --source openclaw
workflow-dataset capabilities external history --limit 20
```

## 7. Sample activation request

```json
{
  "activation_id": "act_openclaw_20250116143022",
  "source_id": "openclaw",
  "source_category": "openclaw",
  "requested_action": "enable",
  "prerequisites": [],
  "approvals_required": ["optional_wrapper"],
  "expected_resource_cost": "medium",
  "reversible": true,
  "status": "pending",
  "created_at": "2025-01-16T14:30:22Z",
  "updated_at": "2025-01-16T14:30:22Z"
}
```

## 8. Sample activation preview

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

## 9. Sample execution / blocked output

**Executed:**
```
Outcome: executed
Integration enabled.
```

**Blocked (approval required):**
```
Outcome: blocked
Operator approval required; run with --approved after review.
Run with --approved after review.
```

**Instructions only (ollama model):**
```
Outcome: instructions_only
No auto-download. Follow instructions: Ensure Ollama is installed and running...; Pull model 'qwen2.5-coder' via Ollama...
```

## 10. Sample history / rollback output

```
Activation history (recent)
---
  act_openclaw_20250116143022  outcome=executed  recorded=2025-01-16T14:31:00Z
  disable_openclaw  outcome=executed  recorded=2025-01-16T14:35:00Z
```

## 11. Tests

```bash
pytest tests/test_external_capability_executor.py tests/test_external_capability.py tests/test_runtime_mesh.py -v
```

Covers: activation request model, create_activation_request, save/load/list request, build_preview, execute (blocked when not found, enable/disable integration), disable_source, history, format_preview/format_history, set_integration_enabled.

## 12. What this phase does NOT do

- Auto-pull models or run `ollama pull`.
- Silently enable remote/cloud behavior.
- Bypass trust/approval policy.
- Rewrite runtime mesh (only additive `set_integration_enabled`).

## 13. Next step for the pane

- Optional: add `capabilities external list-requests [--status pending|blocked|executed]` to list saved requests by status.
- Optional: wire next_action in mission_control to suggest “run capabilities external execute --id X --approved” when there are pending requests and approval is in place.
