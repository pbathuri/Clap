# M47L.1 — Guidance Presets + Recovery Guidance Packs: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/quality_guidance/models.py` | Added `GuidancePresetKind`, `GuidancePreset`, `RecoveryGuidancePack`, `OperatorFacingSummary` with `to_dict()`. |
| `src/workflow_dataset/quality_guidance/__init__.py` | Exported `GuidanceKind`, `GuidancePreset`, `GuidancePresetKind`, `RecoveryGuidancePack`, `OperatorFacingSummary`, and presets/recovery_packs/operator_summary functions. |
| `src/workflow_dataset/cli.py` | Added `guidance preset show | set`, `guidance recovery-pack list | show`, `guidance operator-summary` commands. |
| `tests/test_quality_guidance.py` | Added tests: test_guidance_preset_defaults, test_preset_load_save, test_apply_preset_to_guidance, test_recovery_pack_defaults, test_operator_summary_structure, test_operator_summary_with_failure_pattern. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/quality_guidance/presets.py` | Default presets (concise, operator_first, review_heavy); `load_active_preset()`, `save_active_preset()`, `apply_preset_to_guidance(item, preset)`; persistence in `data/local/quality_guidance/preset.json`. |
| `src/workflow_dataset/quality_guidance/recovery_packs.py` | Default recovery packs: executor_blocked, vertical_onboarding_stalled, project_stalled, founder_operator_blocked; `get_recovery_pack_for_failure_pattern()`, `get_recovery_pack_for_vertical()`, `load_custom_recovery_packs()`. |
| `src/workflow_dataset/quality_guidance/operator_summary.py` | `build_operator_summary(repo_root, failure_pattern, vertical_id)` → OperatorFacingSummary (what_system_knows, what_it_recommends, what_it_needs_from_user); uses active preset and recovery pack when matched. |
| `docs/M47L1_GUIDANCE_PRESETS_RECOVERY_PACKS_DELIVERABLE.md` | This file. |

## 3. Sample guidance preset

**Operator-first (default):**
```json
{
  "preset_id": "operator_first",
  "kind": "operator_first",
  "label": "Operator-first",
  "max_rationale_chars": 0,
  "emphasize_commands": true,
  "emphasize_review": false,
  "lead_with_recommendation": true,
  "description": "Clear next step and command first; then context."
}
```

**Concise:**
```json
{
  "preset_id": "concise",
  "kind": "concise",
  "label": "Concise",
  "max_rationale_chars": 120,
  "emphasize_commands": true,
  "emphasize_review": false,
  "lead_with_recommendation": true,
  "description": "Short rationale; lead with recommendation; emphasize commands."
}
```

**Review-heavy:**
```json
{
  "preset_id": "review_heavy",
  "kind": "review_heavy",
  "label": "Review-heavy",
  "max_rationale_chars": 0,
  "emphasize_commands": true,
  "emphasize_review": true,
  "lead_with_recommendation": false,
  "description": "Emphasize review backlog and what needs operator attention."
}
```

Active preset stored in `data/local/quality_guidance/preset.json`: `{"preset_id": "operator_first"}`.

## 4. Sample recovery guidance pack

**Executor blocked:**
```json
{
  "pack_id": "executor_blocked",
  "vertical_id": "",
  "label": "Executor run blocked",
  "failure_patterns": ["executor_blocked", "run_blocked"],
  "what_we_know": "A run is blocked at a checkpoint; recovery options are retry, skip, or substitute.",
  "what_we_recommend": "Resume from blocked: choose retry (same step again), skip (move to next step), or substitute (run a different bundle/action).",
  "what_we_need_from_user": "Your decision: retry | skip | substitute. For substitute, provide --substitute-bundle ID and optionally --note.",
  "commands": [
    "workflow-dataset executor resume-from-blocked --run <run_id> --decision retry",
    "workflow-dataset executor resume-from-blocked --run <run_id> --decision skip",
    "workflow-dataset executor resume-from-blocked --run <run_id> --decision substitute --substitute-bundle <id>"
  ],
  "escalation_ref": "workflow-dataset executor hub get-recovery-options --run <run_id>"
}
```

**Vertical onboarding stalled:**
```json
{
  "pack_id": "vertical_onboarding_stalled",
  "label": "Vertical onboarding stalled",
  "failure_patterns": ["onboarding_stalled", "first_value_blocked", "vertical_stalled"],
  "what_we_know": "First-value or onboarding path is blocked at a step; playbook has remediation for this step.",
  "what_we_recommend": "Follow the playbook remediation for the blocked step; run vertical-packs progress and use the suggested command.",
  "what_we_need_from_user": "Complete the suggested step (e.g. fix env, approve, or run simulate); then re-run first-value or progress.",
  "commands": [
    "workflow-dataset vertical-packs progress",
    "workflow-dataset vertical-packs first-value --id <curated_pack_id>"
  ]
}
```

## 5. Exact tests run

```bash
python3 -m pytest tests/test_quality_guidance.py -v
```

**New M47L.1 tests (6):** test_guidance_preset_defaults, test_preset_load_save, test_apply_preset_to_guidance, test_recovery_pack_defaults, test_operator_summary_structure, test_operator_summary_with_failure_pattern.

(Full test run includes all existing quality_guidance tests; tests that call `build_operator_summary` or guidance with repo root may take longer where mission_control state is loaded.)

## 6. Next recommended step for the pane

- **Wire preset into next-action output**: When emitting `guidance next-action`, apply the active preset to the returned GuidanceItem’s summary/rationale so the CLI and any consumer see preset-formatted text (e.g. concise truncation, or review-heavy prefix).
- **Recovery pack selection from context**: In `build_operator_summary` or support_recovery_guidance, detect current failure context (e.g. executor run blocked, or vertical progress blocked) and auto-select the matching recovery pack so operator-summary shows “what we know / recommend / need” without requiring `--failure-pattern` or `--vertical`.
- **Custom recovery packs in repo**: Document or add a schema for `data/local/quality_guidance/recovery_packs.json` so operators can add vertical-specific packs; `load_custom_recovery_packs()` already exists and can be merged with defaults when resolving by pattern/vertical.
- **Mission control slice**: Add a short “operator summary” or “active preset + recovery pack” line to the mission_control quality_guidance slice (e.g. one-line “knows / recommends / needs” or preset_id + recovery_pack_id when in recovery context).
