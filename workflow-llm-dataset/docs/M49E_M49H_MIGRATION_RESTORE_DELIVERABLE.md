# M49E–M49H — Migration Validation + Restore/Reconcile Flows: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `docs/M49E_M49H_MIGRATION_RESTORE_BEFORE_CODING.md` | New: before-coding doc (existing behavior, gaps, file plan, safety, reconcile principles, what we will not do). |
| `src/workflow_dataset/cli.py` | Added `migration_group`: validate, dry-run, restore, reconcile, verify. |
| `src/workflow_dataset/mission_control/state.py` | Added 6l: `migration_restore_state` from migration_restore_mission_control_slice. |
| `src/workflow_dataset/mission_control/report.py` | Added [Migration restore] section. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/migration_restore/__init__.py` | Package exports. |
| `src/workflow_dataset/migration_restore/models.py` | ContinuityBundleManifest, TargetEnvironmentProfile, RestoreCandidate, RestoreValidationReport, ReconcileAction, ConflictClass, StaleStateNote, RebuildRequiredComponent, RestoreConfidence, RestoreBlocker. |
| `src/workflow_dataset/migration_restore/bundle.py` | get_bundle_manifest (latest or saved), list_bundle_refs; manifest from state_durability boundaries. |
| `src/workflow_dataset/migration_restore/validation.py` | validate_bundle_for_target (version, runtime, trust, local-only, experimental); RestoreValidationReport. |
| `src/workflow_dataset/migration_restore/flows.py` | dry_run_restore, restore_with_review, partial_restore, conflict_aware_reconcile, post_restore_verify. |
| `src/workflow_dataset/migration_restore/mission_control.py` | migration_restore_mission_control_slice. |
| `tests/test_migration_restore.py` | Tests: manifest, validation, dry-run, restore, partial, reconcile, verify, models. |
| `docs/M49E_M49H_MIGRATION_RESTORE_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
workflow-dataset migration validate --bundle latest
workflow-dataset migration validate --bundle latest --repo-root /path/to/repo
workflow-dataset migration dry-run --bundle latest
workflow-dataset migration restore --bundle latest
workflow-dataset migration restore --bundle latest --approved
workflow-dataset migration reconcile --id restore_123
workflow-dataset migration verify --id restore_123
```

## 4. Sample restore validation report

```json
{
  "report_id": "rpt_xxx",
  "bundle_id": "bundle_xxx",
  "target_profile_id": "current",
  "passed": true,
  "version_compatible": true,
  "runtime_compatible": true,
  "trust_compatible": true,
  "blockers": [],
  "warnings": ["Local-only subsystems excluded from bundle: background_queue."],
  "local_only_excluded": ["background_queue"],
  "experimental_warnings": [],
  "restore_confidence": {
    "score": 0.9,
    "label": "high",
    "reasons": []
  },
  "generated_at_utc": "2025-03-16T12:00:00.000000+00:00"
}
```

## 5. Sample reconcile output

```json
{
  "restore_candidate_id": "latest",
  "reconcile_actions": [
    {
      "action_id": "act_xxx",
      "kind": "refresh_stale",
      "subsystem_id": "continuity_shutdown",
      "description": "Refresh stale state: continuity_shutdown",
      "safe_to_apply": true,
      "requires_review": false
    }
  ],
  "rebuild_required": [
    {
      "subsystem_id": "workday",
      "reason": "invalid_json",
      "suggested_command": "workflow-dataset state health"
    }
  ],
  "stale_notes": [],
  "conflict_classes": ["stale", "unsupported"],
  "generated_at_utc": "2025-03-16T12:00:00.000000+00:00"
}
```

## 6. Sample restore verification output

```json
{
  "restore_candidate_id": "restore_123",
  "verified": true,
  "ready": true,
  "degraded_but_usable": false,
  "summary_lines": ["All critical state is present and readable."],
  "resume_target": {
    "label": "Morning check",
    "command": "workflow-dataset continuity morning",
    "quality": "high",
    "rationale": [],
    "project_id": "",
    "day_id": ""
  },
  "generated_at_utc": "2025-03-16T12:00:00.000000+00:00"
}
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_migration_restore.py -v
```

Tests: test_bundle_manifest_latest, test_list_bundle_refs, test_validate_bundle_for_target, test_validation_blocked_unknown_bundle, test_dry_run_restore, test_restore_with_review_not_approved, test_partial_restore, test_conflict_aware_reconcile, test_post_restore_verify, test_restore_confidence_model, test_rebuild_required_component_model.

## 8. Exact remaining gaps for later refinement

- **Bundle payload persistence** — “Latest” builds manifest from current state but does not write a packable bundle to disk; saved bundles (data/local/migration_restore/bundles/<id>/) are not yet created by an export/pack step. Add bundle export that writes manifest + copies subsystem files.
- **Actual file copy on restore** — restore_with_review when approved and bundle is from a different source_repo_root does not yet copy files; implement copy from bundle dir to target paths with conflict checks.
- **Target environment profile from file** — TargetEnvironmentProfile is implied (current repo); support loading a profile from data/local/migration_restore/target_profiles/ for cross-machine restore.
- **Trust/governance compatibility** — Validation loads policy but does not yet enforce “bundle trust mode vs target trust mode” as a hard blocker; clarify and optionally add.
- **Restore candidate persistence** — Restore candidates are returned in memory; persist to data/local/migration_restore/restores.jsonl or similar for reconcile --id and verify --id by stored id.
- **Review gate for restore** — Integrate with review_domains or sensitive_gates so “restore with approval” can require a second role when target is production or high-trust.
