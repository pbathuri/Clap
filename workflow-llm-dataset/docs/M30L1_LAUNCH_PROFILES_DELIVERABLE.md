# M30L.1 — First-User Launch Profiles + Controlled Rollout Gates (Deliverable)

## 1. Files modified

| File | Changes |
|------|--------|
| `src/workflow_dataset/release_readiness/models.py` | Added `RolloutGate`, `LaunchProfile` dataclasses (M30L.1). |
| `src/workflow_dataset/release_readiness/__init__.py` | Exported `LaunchProfile`, `RolloutGate`, `GATES`, `evaluate_gate`, `list_gates`, `PROFILES`, `build_launch_profiles_report`, `build_rollout_gate_report`, `format_launch_profiles_report`, `format_rollout_gate_report`, `is_profile_allowed`, `list_profiles`. |
| `src/workflow_dataset/cli.py` | Added `release launch-profiles` and `release rollout-gates [--profile PROFILE]` commands. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/release_readiness/gates.py` | Gate definitions (env_required_ok, acceptance_pass, first_user_ready, release_readiness_not_blocked, rollout_stage_ready_for_trial, trust_approval_ready) and `evaluate_gate()` using existing release/rollout/acceptance/env/trust builders. |
| `src/workflow_dataset/release_readiness/profiles.py` | Four launch profiles (demo, internal_pilot, careful_first_user, broader_controlled_pilot), `evaluate_all_gates()`, `is_profile_allowed()`, `build_launch_profiles_report()`, `build_rollout_gate_report()`, and text formatters. |
| `tests/test_launch_profiles.py` | Tests for gate/profile models, gate evaluation, profile-allowed logic, report structure, formatters. |
| `docs/M30L1_LAUNCH_PROFILES_DELIVERABLE.md` | This deliverable. |

## 3. Sample launch profile

**Profile: `demo`**

```json
{
  "profile_id": "demo",
  "label": "Demo",
  "description": "Controlled demo: rollout stage ready for trial and latest acceptance pass.",
  "required_gate_ids": [
    "rollout_stage_ready_for_trial",
    "acceptance_pass"
  ]
}
```

Other profiles:
- **internal_pilot**: demo + `env_required_ok`, `release_readiness_not_blocked`
- **careful_first_user** / **broader_controlled_pilot**: internal_pilot + `first_user_ready`, `trust_approval_ready`

## 4. Sample rollout-gate report

```json
{
  "gates": {
    "env_required_ok": { "passed": false, "detail": "required_ok=false or missing" },
    "acceptance_pass": { "passed": false, "detail": "no acceptance run" },
    "first_user_ready": { "passed": false, "detail": "One or more required machine checks failed.; ..." },
    "release_readiness_not_blocked": { "passed": false, "detail": "release_readiness=blocked" },
    "rollout_stage_ready_for_trial": { "passed": false, "detail": "current_stage=" },
    "trust_approval_ready": { "passed": false, "detail": "registry_exists=false or missing" }
  },
  "profiles_summary": [
    { "profile_id": "demo", "label": "Demo", "allowed": false },
    { "profile_id": "internal_pilot", "label": "Internal pilot", "allowed": false },
    { "profile_id": "careful_first_user", "label": "Careful first user", "allowed": false },
    { "profile_id": "broader_controlled_pilot", "label": "Broader controlled pilot", "allowed": false }
  ]
}
```

With `--profile demo`, the report also includes a `profile` block with `allowed`, `gates_passed`, `gates_failed`, and `gate_details` for that profile.

## 5. Exact tests run

```bash
python3 -m pytest tests/test_release_readiness.py tests/test_launch_profiles.py -v
```

**Result:** 33 passed (15 existing release_readiness + 18 launch_profiles).

Launch-profile tests: `test_rollout_gate_to_dict`, `test_launch_profile_to_dict`, `test_gates_registry_has_expected_ids`, `test_profiles_registry_has_four_profiles`, `test_demo_profile_requires_two_gates`, `test_evaluate_gate_returns_passed_and_detail`, `test_evaluate_all_gates_returns_dict_per_gate`, `test_is_profile_allowed_unknown_profile`, `test_is_profile_allowed_with_mock_gate_results`, `test_is_profile_allowed_fails_when_gate_fails`, `test_build_launch_profiles_report_structure`, `test_build_rollout_gate_report_structure`, `test_build_rollout_gate_report_with_profile`, `test_format_launch_profiles_report_contains_allowed`, `test_format_rollout_gate_report_contains_gates`, `test_list_gates_returns_dicts`, `test_list_profiles_returns_dicts`, `test_get_gate_get_profile`.

## 6. Next recommended step for the pane

- **Mission control / release pane:** Surface launch profiles and rollout gates in the UI (e.g. show “Launch: demo ✗, internal pilot ✗, careful first user ✗” and a “Rollout gates” subsection with pass/fail and details), and add a single “Rollout gate report” action that opens or exports the full report.
- **Optional:** Persist last rollout-gate report path in mission control state so “View last report” is one click.
- **Optional:** Add a gate “first_user_ready_from_rollout” that reuses `build_rollout_readiness_report()["first_user_ready"]` for consistency with the existing rollout readiness wording, and reference it from the careful_first_user profile if desired (currently first_user_ready is package-based).
