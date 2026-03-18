# M49A–M49D Continuity Bundle Deliverable

First-draft portable continuity layer: portable state model, continuity bundle build/inspect/validate, portability boundaries, CLI, mission control slice, tests, and docs.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `continuity-bundle` Typer group and commands: `create`, `inspect`, `validate`, `components`, `explain`. |
| `src/workflow_dataset/mission_control/state.py` | Added `continuity_bundle_state` from `continuity_bundle_slice(repo_root)` (try/except). |
| `src/workflow_dataset/mission_control/report.py` | Added "[Continuity bundle]" section: latest_bundle_id, safe_to_transfer_count, transfer_sensitive_components, excluded_local_only, next_portability_review. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/continuity_bundle/__init__.py` | Package exports (models, create_bundle, inspect_bundle, validate_bundle, list_components, get_portability_boundaries, explain_component, continuity_bundle_slice). |
| `src/workflow_dataset/continuity_bundle/models.py` | TransferClass enum; PortableStateClass, NonPortableStateClass, BundleComponent, BundleProvenance, ContinuityBundle. |
| `src/workflow_dataset/continuity_bundle/components.py` | Component registry from SUBSYSTEM_BOUNDARIES + EXTRA_COMPONENTS; get_component_registry(), get_component(), list_components(). |
| `src/workflow_dataset/continuity_bundle/build.py` | create_bundle(), inspect_bundle(), validate_bundle(); writes `data/local/continuity_bundle/bundles/<bundle_id>/manifest.json`. |
| `src/workflow_dataset/continuity_bundle/portability.py` | get_portability_boundaries(), explain_component(). |
| `src/workflow_dataset/continuity_bundle/mission_control.py` | continuity_bundle_slice(). |
| `tests/test_continuity_bundle.py` | Tests: create, inspect, validate, list_components, include/exclude, sensitive, explain, portability boundaries, mission control slice, no-portable-state edge case. |
| `docs/M49A_M49D_BEFORE_CODING_ANALYSIS.md` | Pre-implementation analysis (existing state, portable vs non-portable, gaps, file plan, safety, principles, what we do not do). |
| `docs/M49A_M49D_CONTINUITY_BUNDLE_DELIVERABLE.md` | This file. |

---

## 3. Exact CLI usage

```bash
# Create bundle (default: all portable components)
workflow-dataset continuity-bundle create
workflow-dataset continuity-bundle create --repo-root /path/to/repo
workflow-dataset continuity-bundle create --include workday,continuity_shutdown,operator_mode_config
workflow-dataset continuity-bundle create --exclude production_cut,trust_contracts
workflow-dataset continuity-bundle create --json

# Inspect bundle
workflow-dataset continuity-bundle inspect
workflow-dataset continuity-bundle inspect --bundle cb_abc123
workflow-dataset continuity-bundle inspect --bundle latest --repo-root /path --json

# Validate bundle
workflow-dataset continuity-bundle validate
workflow-dataset continuity-bundle validate --bundle cb_abc123 --repo-root /path --json

# List components (transfer class, sensitive, review)
workflow-dataset continuity-bundle components
workflow-dataset continuity-bundle components --include-local
workflow-dataset continuity-bundle components --class safe_to_transfer
workflow-dataset continuity-bundle components --json

# Explain one component
workflow-dataset continuity-bundle explain --component operator_mode_state
workflow-dataset continuity-bundle explain --component production_cut --repo-root /path --json
```

Note: `--component` is required for `explain`. For `components`, the filter option is `--class` or `-c` (e.g. `safe_to_transfer`, `transfer_with_review`, `local_only`).

---

## 4. Sample continuity bundle (manifest snippet)

Location: `data/local/continuity_bundle/bundles/<bundle_id>/manifest.json`

```json
{
  "bundle_id": "cb_a1b2c3d4e5f6g7",
  "created_at_utc": "2025-03-16T12:00:00.000000+00:00",
  "product_version": "0.1.0",
  "source_repo_root": "/path/to/repo",
  "manifest_ref": "cb_a1b2c3d4e5f6g7",
  "excluded_component_ids": ["background_queue"],
  "components": [
    {
      "component_id": "workday",
      "path": "data/local/workday/state.json",
      "path_pattern": "data/local/workday/state.json",
      "transfer_class": "safe_to_transfer",
      "sensitive": false,
      "review_required": false,
      "optional": false,
      "label": "Workday",
      "description": "Subsystem: workday",
      "provenance": {
        "product_version": "0.1.0",
        "created_at_utc": "2025-03-16T12:00:00.000000+00:00",
        "source_repo_root": "/path/to/repo",
        "bundle_id": "cb_a1b2c3d4e5f6g7",
        "component_version_hint": "data/local/workday/state.json"
      }
    },
    {
      "component_id": "production_cut",
      "path": "data/local/production_cut/active_cut.json",
      "transfer_class": "transfer_with_review",
      "sensitive": true,
      "review_required": true,
      "optional": true,
      "label": "Production cut",
      "description": "Locked production cut; review before transfer.",
      "provenance": { ... }
    }
  ]
}
```

---

## 5. Sample component classification report

From `get_portability_boundaries(repo_root)` (or `workflow-dataset continuity-bundle components` with human-readable boundaries):

```python
{
  "safe_to_transfer": ["workday", "continuity_shutdown", "continuity_carry_forward", "continuity_next_session", "project_current", "workday_preset", "governance_preset", "vertical_packs_progress", "vertical_packs_active", "operator_mode_config"],
  "transfer_with_review": ["production_cut", "trust_contracts"],
  "local_only": ["background_queue"],
  "rebuild_on_restore": [],
  "experimental_transfer": ["memory_curation_index"],
  "summary": "safe=10 review=2 local_only=1 rebuild=0 experimental=1"
}
```

---

## 6. Sample portability explanation

From `explain_component("operator_mode_config", repo_root)` or `workflow-dataset continuity-bundle explain --component operator_mode_config`:

```python
{
  "component_id": "operator_mode_config",
  "found": True,
  "path": "data/local/operator_mode",
  "transfer_class": "safe_to_transfer",
  "sensitive": False,
  "review_required": False,
  "optional": True,
  "label": "Operator mode config",
  "description": "Operator mode configuration dir.",
  "rationale": "Safe to copy to another machine; no sensitive or machine-specific data.",
  "on_restore": "Restore overwrites or merges target path; continuity preserved."
}
```

For a sensitive component:

```bash
workflow-dataset continuity-bundle explain --component production_cut
```

Output (conceptually): `transfer_class=transfer_with_review`, `sensitive=True`, `review_required=True`, rationale "Contains sensitive or scope-specific state; human review before restore.", on_restore "Restore after approval; may conflict with target state."

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_continuity_bundle.py -v
```

**Tests included:**

- `test_create_bundle` — Bundle creation writes manifest and returns ContinuityBundle.
- `test_inspect_bundle_latest` — Inspect latest loads the most recent bundle.
- `test_inspect_bundle_nonexistent` — Nonexistent bundle returns None.
- `test_validate_bundle_valid` — Valid bundle returns valid=True.
- `test_validate_bundle_invalid` — Nonexistent bundle returns valid=False and errors.
- `test_list_components_classification` — List components; default excludes local_only (e.g. background_queue).
- `test_selective_include_exclude` — create_bundle with include/exclude filters components.
- `test_sensitive_components_in_registry` — production_cut/trust_contracts marked sensitive/review.
- `test_explain_component` — explain returns transfer_class, rationale, on_restore for known component.
- `test_explain_component_unknown` — Unknown component returns found=False.
- `test_portability_boundaries` — get_portability_boundaries returns all transfer classes and summary.
- `test_mission_control_slice` — continuity_bundle_slice returns latest_bundle_id, transfer_sensitive, excluded_local_only, next_portability_review.
- `test_no_portable_state_edge_case` — Exclude everything: bundle has zero components, validate still valid.
- `test_get_component` — get_component by id returns component or None.

All 14 tests should pass.

---

## 8. Remaining gaps for later refinement

- **Restore integration:** This deliverable builds and inspects continuity bundles only. Restoring from a continuity bundle (copying payloads, reconciling conflicts) remains in `migration_restore` flows; no new restore path was added. Future work: optionally drive restore from continuity_bundle manifest (e.g. map component ids to migration_restore subsystems or add a dedicated restore path).
- **Payload copy:** Current bundle stores only `manifest.json` (component list + provenance). No copying of actual file/dir payloads into the bundle directory. Restore today relies on source paths on the same machine or external copy. Future: optional `payload/` inside bundle with snapshots of included paths.
- **Version mismatch handling:** validate_bundle warns on product_version mismatch but does not block; no strict version gate or compatibility matrix. Refinement: optional strict version policy and compatibility rules.
- **Conflict detection:** No pre-restore conflict scan (e.g. diff target state vs bundle). migration_restore has conflict/reconcile logic; continuity bundle could call into it or expose a “would overwrite” report.
- **Transfer-class filter in create:** CLI and create_bundle support `--include`/`--exclude` by component id; `include_transfer_classes` is implemented in build but not exposed in CLI. Easy add: `--transfer-class safe_to_transfer,transfer_with_review`.
- **Mission control report detail:** Report section shows latest_bundle_id, counts, and truncated lists. Optional: link to last bundle path or add “inspect” hint.
- **Documentation:** In-code docstrings and this deliverable; no separate user-facing “Portable continuity” guide. Later: short runbook for “create bundle before machine swap” and “inspect/validate before restore”.

---

## Summary

- **Portable state model:** Explicit TransferClass, BundleComponent, ContinuityBundle, provenance (Phase A).
- **Bundle building:** create_bundle (with optional include/exclude), inspect_bundle, validate_bundle; manifest under `data/local/continuity_bundle/bundles/<id>/manifest.json` (Phase B).
- **Portability boundaries:** get_portability_boundaries and explain_component (Phase C).
- **CLI and mission control:** `continuity-bundle create|inspect|validate|components|explain`; mission control state + “[Continuity bundle]” report section (Phase D).
- **Tests and docs:** 14 tests in test_continuity_bundle.py; before-coding analysis and this deliverable doc (Phase E).

No cloud sync, no replacement of existing persistence; local-first, inspectable, migration-safe continuity bundle layer.
