# M38A–M38D Cohort Profiles + Supported Surface Matrix

First-draft cohort-readiness definition layer: cohort profiles, supported/experimental/blocked surface matrix, bindings to workday/experience/trust, CLI, mission control visibility, tests and docs.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Under `cohort_group`: `cohort profiles`, `cohort show --id`, `cohort matrix --id`, `cohort apply --id`, `cohort explain --surface` / `--id`, `cohort health`. |
| `src/workflow_dataset/mission_control/state.py` | Added `cohort_state`: active_cohort_id, cohort_label, supported_count, experimental_count, blocked_count, blocked_surfaces_sample, trust_posture, required_readiness, next_readiness_review. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Cohort]` section: active cohort, label, supported/experimental/blocked counts, blocked_sample, trust_posture, next command. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/cohort/__init__.py` | Package exports. |
| `src/workflow_dataset/cohort/models.py` | CohortProfile; SUPPORT_SUPPORTED/EXPERIMENTAL/BLOCKED; READINESS_*; support_expectations. |
| `src/workflow_dataset/cohort/surface_matrix.py` | get_all_surface_ids(), get_matrix(cohort_id), get_support_level(), get_supported_surfaces(), get_experimental_surfaces(), get_blocked_surfaces(). |
| `src/workflow_dataset/cohort/profiles.py` | BUILTIN_COHORT_PROFILES: internal_demo, careful_first_user, bounded_operator_pilot, document_heavy_pilot, developer_assist_pilot; get_cohort_profile(), list_cohort_profile_ids(). |
| `src/workflow_dataset/cohort/bindings.py` | apply_cohort_defaults(), get_recommended_workday_preset_id(), get_recommended_experience_profile_id(). |
| `src/workflow_dataset/cohort/store.py` | get_active_cohort_id(), set_active_cohort_id(); data/local/cohort/active_profile.txt. |
| `src/workflow_dataset/cohort/explain.py` | explain_surface(surface_id, cohort_id), explain_cohort(cohort_id). |
| `tests/test_cohort.py` | Profile list/get, matrix, support level, bindings, store, explain, unknown cohort, no-profile default. |
| `docs/M38A_M38D_COHORT_BEFORE_CODING.md` | Before-coding analysis. |
| `docs/M38A_M38D_COHORT_PROFILES_AND_MATRIX.md` | This document. |

## 3. Exact CLI usage

```bash
# List cohort profiles
workflow-dataset cohort profiles

# Show one cohort profile
workflow-dataset cohort show --id careful_first_user

# Supported-surface matrix for a cohort
workflow-dataset cohort matrix --id careful_first_user
workflow-dataset cohort matrix --id bounded_operator_pilot --json

# Set active cohort (does not auto-apply workday/experience)
workflow-dataset cohort apply --id careful_first_user
workflow-dataset cohort apply --id developer_assist_pilot --repo /path

# Explain surface for (active or specified) cohort
workflow-dataset cohort explain --surface operator_mode
workflow-dataset cohort explain --surface mission_control --id careful_first_user --json

# Explain cohort scope
workflow-dataset cohort explain --id careful_first_user
workflow-dataset cohort explain --id bounded_operator_pilot --json

# Existing cohort health (unchanged)
workflow-dataset cohort health --cohort my_cohort
```

## 4. Sample cohort profile

**careful_first_user** (abbreviated):

```json
{
  "cohort_id": "careful_first_user",
  "label": "Careful first user",
  "description": "Narrow scope for first real users; calm home, supported core only; operator and trust expert surfaces blocked.",
  "surface_support": {
    "workspace_home": "supported",
    "day_status": "supported",
    "queue_summary": "supported",
    "operator_mode": "blocked",
    "trust_cockpit": "blocked",
    "mission_control": "experimental"
  },
  "allowed_trust_tier_ids": ["observe_only", "suggest_only", "draft_only", "sandbox_write"],
  "allowed_workday_modes": ["start", "focus", "review", "wrap_up", "resume"],
  "allowed_automation_scope": "simulate_only",
  "required_readiness": "ready_or_degraded",
  "default_workday_preset_id": "analyst",
  "default_experience_profile_id": "calm_default",
  "support_expectations": "Supported surfaces are in scope; experimental best-effort; blocked surfaces out of scope."
}
```

## 5. Sample supported-surface matrix

For **careful_first_user** (excerpt):

| surface_id           | level        |
|----------------------|-------------|
| workspace_home       | supported   |
| day_status           | supported   |
| queue_summary        | supported   |
| approvals_urgent     | supported   |
| mission_control      | experimental|
| operator_mode        | blocked     |
| trust_cockpit        | blocked     |
| policy_board         | blocked     |
| approvals_policy     | blocked     |

CLI: `workflow-dataset cohort matrix --id careful_first_user`

## 6. Sample cohort explanation output

**Explain surface (operator_mode for careful_first_user):**

```
operator_mode  cohort=careful_first_user  level=blocked
  Out of scope for this cohort; use a different cohort profile to allow.
  command: day mode --set operator_mode
```

**Explain cohort (careful_first_user):**

```
careful_first_user  Careful first user
  supported=9  experimental=7  blocked=4
  allowed_automation_scope=simulate_only  required_readiness=ready_or_degraded
```

With `--json`: full structure including supported_surfaces, blocked_surfaces, allowed_trust_tiers, support_expectations.

## 7. Exact tests run

```bash
python3 -m pytest workflow-llm-dataset/tests/test_cohort.py -v
```

**Result:** 11 passed (list_cohort_profiles, get_cohort_profile, matrix_support_levels, get_support_level, supported_experimental_blocked_lists, apply_cohort_defaults, store_get_set_cohort, explain_surface, explain_cohort, unknown_cohort_matrix_defaults_blocked, no_profile_default_behavior).

## 8. Exact remaining gaps for later refinement

- **Runtime enforcement**: Blocked surfaces are defined and visible; no CLI or runtime enforcement yet (e.g. warn or block when invoking a blocked surface for active cohort).
- **Readiness gating**: required_readiness is stored but not checked when applying cohort or when mission control runs; could gate “apply” or show a warning if release readiness status is below required.
- **Triage alignment**: Triage’s supported_surface_involved and experimental_surface_involved are not yet derived from this matrix; could align classification with cohort matrix.
- **LaunchProfile linkage**: release_readiness.models LaunchProfile (demo, internal pilot, careful first user) is not wired to cohort profile id; could map LaunchProfile to CohortProfile for handoff/reporting.
- **Per-cohort release readiness**: Release readiness is global; optional future: per-cohort readiness view or filter.
