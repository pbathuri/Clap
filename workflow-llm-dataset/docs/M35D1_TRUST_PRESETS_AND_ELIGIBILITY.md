# M35D.1 — Trust Presets + Routine Eligibility Matrix

First-draft extension to the M35A–M35D trust layer: trust presets, routine eligibility matrix, and invalid/unsafe trust configuration reporting.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/trust/__init__.py` | Exported presets, eligibility, and validation_report APIs. |
| `src/workflow_dataset/cli.py` | Added `trust presets list`, `trust presets show --id`, `trust eligibility-matrix [--preset]`, `trust validate-config [--preset]`. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/trust/presets.py` | TrustPreset, BUILTIN_PRESETS (cautious, supervised_operator, bounded_trusted_routine, release_safe), get_preset, list_presets, preset_allows_tier. |
| `src/workflow_dataset/trust/eligibility.py` | ROUTINE_TYPES, routine_type_for, ELIGIBILITY_MATRIX, max_tier_for_routine_under_preset, is_eligible, eligibility_matrix_report. |
| `src/workflow_dataset/trust/validation_report.py` | TrustValidationReport, TrustConfigIssue, validate_trust_config, format_validation_report, get_active_preset_id (from data/local/trust/active_preset.txt). |
| `tests/test_trust_presets_eligibility.py` | Tests for presets, eligibility matrix, validation reporting. |
| `docs/M35D1_TRUST_PRESETS_AND_ELIGIBILITY.md` | This document. |

---

## 3. Sample trust preset

**Preset: `supervised_operator`**

```json
{
  "preset_id": "supervised_operator",
  "name": "Supervised operator",
  "description": "Human-in-the-loop; queued execution and sandbox/simulate. No direct real run without approval.",
  "max_authority_tier_id": "queued_execute",
  "require_approval_for_real": true,
  "allow_commit_send": false,
  "allow_bounded_trusted_real": false,
  "valid_scope_hint": "project/pack scoped",
  "order": 1
}
```

---

## 4. Sample routine eligibility matrix

Which routine type may run at which **max tier** under each preset:

| Preset                  | digest              | followup             | background_run   | worker_lane           | macro                | ad_hoc    |
|-------------------------|---------------------|----------------------|------------------|------------------------|----------------------|-----------|
| cautious                | suggest_only        | suggest_only         | observe_only     | observe_only           | suggest_only         | suggest_only |
| supervised_operator     | sandbox_write       | queued_execute       | sandbox_write    | queued_execute         | queued_execute       | draft_only   |
| bounded_trusted_routine | bounded_trusted_real| bounded_trusted_real | queued_execute   | bounded_trusted_real   | bounded_trusted_real | sandbox_write |
| release_safe            | bounded_trusted_real| queued_execute       | sandbox_write    | bounded_trusted_real   | queued_execute       | sandbox_write |

CLI: `workflow-dataset trust eligibility-matrix` (all presets) or `workflow-dataset trust eligibility-matrix --preset cautious`.

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_trust_presets_eligibility.py -v
```

Test names:

- `test_builtin_presets_present`
- `test_get_preset`
- `test_preset_allows_tier`
- `test_routine_type_for`
- `test_eligibility_matrix_has_all_presets`
- `test_max_tier_for_routine_under_preset`
- `test_is_eligible_cautious_digest_suggest`
- `test_is_eligible_cautious_digest_sandbox_not_eligible`
- `test_validate_trust_config_no_preset_valid_contracts`
- `test_validate_trust_config_invalid_contract`
- `test_validate_trust_config_unsafe_exceeds_preset`
- `test_format_validation_report`
- `test_get_active_preset_id_missing`
- `test_get_active_preset_id_present`

---

## 6. Next recommended step for the pane

- **Wire presets into execution gates**: Have planner/executor/background runner (or a single “trust gate” used by all) call `get_active_preset_id()`, then for each routine/contract check `is_eligible(preset_id, routine_id, contract.authority_tier_id)` before allowing execution. Block or downgrade when ineligible or unsafe.
- **Persist active preset**: Add a CLI to set/clear active preset (e.g. `workflow-dataset trust presets set-active --id cautious`) that writes `data/local/trust/active_preset.txt`, and optionally surface active preset in mission control.
- **Expand routine type mapping**: Add more routine_id → routine_type mappings (e.g. from automations or recurring workflow definitions) so eligibility matrix applies to all defined routines.
- **Human policy alignment**: Document or automate alignment between human_policy presets (e.g. strict_manual, supervised_daily_operator) and trust presets so operator mode and trust presets stay consistent.
