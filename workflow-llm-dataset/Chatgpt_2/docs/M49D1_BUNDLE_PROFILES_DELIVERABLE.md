# M49D.1 — Bundle Profiles + Sensitivity Policies — Deliverable

First-draft extension to the portable continuity layer: bundle profiles, sensitivity policies for transfer, and clearer operator-facing reports (portable / review-required / excluded / rebuild-only).

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/continuity_bundle/models.py` | Added optional `profile_id` to `ContinuityBundle` and `to_dict()`. |
| `src/workflow_dataset/continuity_bundle/build.py` | `create_bundle(..., profile_id=None)`; when `profile_id` is set and include/exclude not passed, resolve include/exclude/transfer_classes from profile; persist `profile_id` in manifest. `inspect_bundle` loads `profile_id` from manifest. |
| `src/workflow_dataset/continuity_bundle/mission_control.py` | Slice now includes `bundle_profile_id`, `portability_report_summary`, `portable_count`, `review_required_count`, `excluded_count`, `rebuild_only_count`; `next_portability_review` set to `continuity-bundle report`. |
| `src/workflow_dataset/continuity_bundle/__init__.py` | Exported profiles, sensitivity policies, and report APIs. |
| `src/workflow_dataset/mission_control/report.py` | "[Continuity bundle]" section shows profile, portable/review_required/excluded/rebuild_only counts, and summary. |
| `src/workflow_dataset/cli.py` | `create` accepts `--profile`; added `profiles`, `sensitivity-policies`, `report` commands. `inspect` shows `profile` when present. |
| `tests/test_continuity_bundle.py` | Added 11 tests for profiles, sensitivity policies, report, create-with-profile, mission control slice. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/continuity_bundle/profiles.py` | `BundleProfile`; built-in profiles `personal_core`, `production_cut`, `maintenance_safe`; `get_profile()`, `list_profiles()`, `resolve_profile_components()`. |
| `src/workflow_dataset/continuity_bundle/sensitivity_policies.py` | `SensitivityPolicy`; built-in policies `transfer_with_review`, `exclude_sensitive`, `strict_safe_only`; `get_sensitivity_policy()`, `list_sensitivity_policies()`, `apply_policy_to_boundaries()`. |
| `src/workflow_dataset/continuity_bundle/reports.py` | `get_portability_report(repo_root, profile_id=..., sensitivity_policy_id=...)`; `format_portability_report_text()` for operator-facing text. |
| `docs/M49D1_BUNDLE_PROFILES_DELIVERABLE.md` | This file. |

---

## 3. Sample bundle profile

**personal_core** (exclude production cut, trust contracts, memory curation, background_queue):

```json
{
  "profile_id": "personal_core",
  "label": "Personal core",
  "description": "Workday, continuity, project/session, operator mode, governance preset. Excludes production cut and trust contracts unless explicitly added.",
  "include_component_ids": null,
  "exclude_component_ids": ["production_cut", "trust_contracts", "memory_curation_index", "background_queue"],
  "include_transfer_classes": null
}
```

**maintenance_safe** (safe-to-transfer only):

```json
{
  "profile_id": "maintenance_safe",
  "label": "Maintenance safe",
  "description": "Safe-to-transfer only; no sensitive or review-required components. For low-risk backup or audit.",
  "include_component_ids": null,
  "exclude_component_ids": [],
  "include_transfer_classes": ["safe_to_transfer"]
}
```

**production_cut** (include transfer_with_review):

```json
{
  "profile_id": "production_cut",
  "label": "Production cut",
  "description": "Full portable set including production cut and trust contracts; all transfer-with-review and safe components.",
  "include_component_ids": null,
  "exclude_component_ids": ["background_queue"],
  "include_transfer_classes": ["safe_to_transfer", "transfer_with_review"]
}
```

---

## 4. Sample sensitivity policy report

From `get_portability_report(repo_root, sensitivity_policy_id="exclude_sensitive")` or `workflow-dataset continuity-bundle report --sensitivity-policy exclude_sensitive`:

```python
{
  "portable": ["workday", "continuity_shutdown", "continuity_carry_forward", "continuity_next_session", "project_current", "workday_preset", "governance_preset", "vertical_packs_progress", "vertical_packs_active", "operator_mode_config"],
  "portable_count": 10,
  "review_required": [],
  "review_required_count": 0,
  "excluded": ["production_cut", "trust_contracts", "memory_curation_index", "background_queue"],
  "excluded_count": 4,
  "rebuild_only": [],
  "rebuild_only_count": 0,
  "summary": "portable=10 review_required=0 excluded=4 rebuild_only=0",
  "sensitivity_policy_id": "exclude_sensitive",
  "sensitivity_policy_label": "Exclude sensitive",
  "portable_detail": [{"component_id": "workday", "label": "Workday", "sensitive": false, "review_required": false}, ...],
  "review_required_detail": [],
  "excluded_detail": [...],
  "rebuild_only_detail": []
}
```

With **transfer_with_review** (default), `review_required` includes `production_cut`, `trust_contracts`, `memory_curation_index` and they are not in `excluded`.

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_continuity_bundle.py -v
```

**Result:** 25 passed (14 existing + 11 M49D.1).

**M49D.1 tests added:**

- `test_list_profiles` — list_profiles returns personal_core, production_cut, maintenance_safe
- `test_get_profile_personal_core` — personal_core excludes production_cut, trust_contracts
- `test_resolve_profile_components_maintenance_safe` — maintenance_safe restricts to safe_to_transfer only
- `test_create_bundle_with_profile` — create_bundle(profile_id=personal_core) sets profile_id, excludes production_cut/trust_contracts, manifest has profile_id
- `test_inspect_bundle_includes_profile_id` — inspect_bundle returns profile_id from manifest
- `test_list_sensitivity_policies` — list returns transfer_with_review, exclude_sensitive, strict_safe_only
- `test_apply_policy_exclude_sensitive` — exclude_sensitive puts transfer_with_review into excluded, review_required_count 0
- `test_get_portability_report` — report has portable, review_required, excluded, rebuild_only, counts, summary
- `test_get_portability_report_strict_safe` — strict_safe_only gives review_required_count 0
- `test_format_portability_report_text` — text contains Portable, Review required, Excluded, Rebuild only
- `test_mission_control_slice_includes_portability_report` — slice has portability_report_summary and counts

---

## 6. Next recommended step for the pane

1. **Optional profile/policy in report CLI** — Allow `continuity-bundle report --profile personal_core` to show how that profile would affect the report (today profile is only context/label in the output).
2. **User-defined profiles** — Support loading profiles from `data/local/continuity_bundle/profiles/*.json` so operators can add custom profiles without code changes.
3. **Sensitivity policy at bundle create** — Optionally tag the bundle with the sensitivity policy used (e.g. `sensitivity_policy_id` in manifest) for restore-time checks.
4. **Mission control report truncation** — If summary is long, consider truncating in the report section or linking to `continuity-bundle report` for full detail.
5. **Docs** — Short runbook: when to use each profile (personal_core vs production_cut vs maintenance_safe) and when to use each sensitivity policy for reporting.
