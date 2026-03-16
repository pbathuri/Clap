# M23M — Operator Correction Loop + Explicit Learning Updates — Final Output

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added **corrections** group: `corrections add`, `list`, `show`, `propose-updates`, `preview-update`, `apply-update`, `reject-update`, `revert-update`, `report`. |
| `src/workflow_dataset/mission_control/state.py` | Added block 10 **corrections**: recent_corrections_count, proposed_updates_count, applied_updates_count, reverted_updates_count, review_recommended, next_corrections_action. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Corrections]** section: recent, proposed, applied, reverted, review_recommended, next. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/corrections/__init__.py` | Package exports. |
| `src/workflow_dataset/corrections/config.py` | get_corrections_root, get_events_dir, get_updates_dir, get_proposed_dir (data/local/corrections). |
| `src/workflow_dataset/corrections/schema.py` | CorrectionEvent dataclass; SOURCE_TYPES, CORRECTION_CATEGORIES, OPERATOR_ACTIONS, SEVERITY_LEVELS; validate_category_for_source, is_eligible_for_memory_update. |
| `src/workflow_dataset/corrections/store.py` | save_correction, get_correction, list_corrections (events as JSON). |
| `src/workflow_dataset/corrections/capture.py` | add_correction(...) — validate, set eligible_for_memory_update, save. |
| `src/workflow_dataset/corrections/rules.py` | LEARNING_RULES (category → target_type), BLOCKED_TARGETS, get_targets_for_category. |
| `src/workflow_dataset/corrections/propose.py` | ProposedUpdate; propose_updates(repo_root) — scan eligible corrections, build proposed updates. |
| `src/workflow_dataset/corrections/updates.py` | UpdateRecord; save_proposed, load_proposed, save_update_record, load_update_record; preview_update, apply_update, revert_update; list_proposed_updates. |
| `src/workflow_dataset/corrections/history.py` | list_applied_updates, list_reverted_updates. |
| `src/workflow_dataset/corrections/report.py` | corrections_report, format_corrections_report. |
| `src/workflow_dataset/corrections/eval_bridge.py` | advisory_review_for_corrections — review_trust / review_benchmark / review_trigger_policy from repeated corrections. |
| `docs/M23M_READ_FIRST.md` | Pre-coding analysis. |
| `docs/M23M_CORRECTION_OPERATOR.md` | Operator guide. |
| `docs/M23M_FINAL_OUTPUT.md` | This file. |
| `tests/test_corrections.py` | Tests: schema, add/list, propose, preview/apply/revert, blocked targets, report, advisory, mission_control. |

## 3. Exact CLI usage

```bash
workflow-dataset corrections add --source recommendation|job|plan|routine|artifact|benchmark_result --id <ref_id> --category <category> [--action rejected|corrected|...] [--original ...] [--corrected ...] [--reason ...] [--severity low|medium|high] [--notes ...] [--repo-root PATH]
workflow-dataset corrections list [--limit N] [--source TYPE] [--category CAT] [--repo-root PATH]
workflow-dataset corrections show --id <correction_id> [--repo-root PATH]
workflow-dataset corrections propose-updates [--repo-root PATH]
workflow-dataset corrections preview-update --id <update_id> [--repo-root PATH]
workflow-dataset corrections apply-update --id <update_id> [--repo-root PATH]
workflow-dataset corrections reject-update --id <update_id> [--repo-root PATH]
workflow-dataset corrections revert-update --id <update_id> [--repo-root PATH]
workflow-dataset corrections report [--repo-root PATH]
```

## 4. Sample correction event

```json
{
  "correction_id": "corr_6d026f66e89c06c4",
  "timestamp": "2026-03-15T12:00:00.000Z",
  "source_type": "job_run",
  "source_reference_id": "weekly_status_from_notes",
  "operator_action": "corrected",
  "correction_category": "bad_job_parameter_default",
  "original_value": {"path": "/old/out"},
  "corrected_value": {"path": "/corrected/out"},
  "correction_reason": "Wrong default output path",
  "severity": "medium",
  "eligible_for_memory_update": true,
  "reversible": true,
  "notes": ""
}
```

## 5. Sample proposed update preview

```
Update preview
  target: specialization_params:weekly_status_from_notes
  before: {'path': '/old/out'}
  after:  {'path': '/corrected/out'}
  risk: low  reversible: True
```

## 6. Sample applied update history entry

```json
{
  "update_id": "upd_a2e7cd918d7db6ca",
  "correction_ids": ["corr_6d026f66e89c06c4"],
  "target_type": "specialization_params",
  "target_id": "weekly_status_from_notes",
  "before_value": {"path": "/old/out"},
  "after_value": {"path": "/corrected/out"},
  "applied_at": "2026-03-15T12:05:00.000Z",
  "reverted_at": "",
  "reversible": true
}
```

## 7. Sample revert output

```
Reverted: upd_a2e7cd918d7db6ca  target: specialization_params:weekly_status_from_notes
```

(Record then has reverted_at set; before_value restored in specialization.)

## 8. Sample correction impact/report output

```
=== Corrections report (M23M) ===

Recent corrections: 5
Proposed updates: 2
Applied updates: 1
Reverted updates: 0

Most corrected: weekly_status_from_notes, morning_reporting

Proposed (sample):
  upd_xxx  specialization_params:weekly_status_from_notes
  upd_yyy  routine_ordering:morning_reporting
```

## 9. Exact tests run

```bash
pytest tests/test_corrections.py -v
```

9 passed: test_correction_event_schema, test_validate_category, test_add_and_list_corrections, test_propose_updates, test_preview_apply_revert, test_blocked_targets, test_corrections_report, test_advisory_review, test_mission_control_includes_corrections.

## 10. What remains manual or non-learning by design

- **Recording corrections:** Operator runs `corrections add`. No automatic capture from UI or runs.
- **Applying updates:** Operator runs `corrections apply-update --id X`. No auto-apply from corrections.
- **Trust/approval:** No learning path can change trust_level or approval registry. Only trust_notes (advisory) and “review recommended” signals.
- **Reversion:** Operator runs `corrections revert-update`. No automatic rollback.

## 11. Exact recommended next phase after M23M

- **Optional:** Wire trigger evaluation to read `data/local/corrections/trigger_suppressions.json` so suppressed triggers are not fired for specified job/routine + trigger_type.
- **Optional:** “Corrections” panel in dashboard/mission control TUI showing recent corrections and proposed updates with one-shot apply from UI.
- **Optional:** Correction categories for artifact_output (e.g. artifact_content_correction) with a safe target such as “template hint” or “output_style” only.
- **Continue:** Use corrections add and propose-updates in daily workflow; keep all learning explicit, local, and reversible.
