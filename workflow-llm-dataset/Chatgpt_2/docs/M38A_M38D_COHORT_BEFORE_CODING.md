# M38A–M38D Cohort Profiles + Supported Surface Matrix — Before Coding

## 1. What release/readiness/scope concepts already exist

- **Release readiness** (`release_readiness/`): `ReleaseReadinessStatus` (ready | blocked | degraded), `ReleaseBlocker`, `ReleaseWarning`, `SupportedWorkflowScope` (workflow_ids), `KnownLimitation`, `SupportabilityStatus`, `build_release_readiness()`. Mission control reports `[Release readiness]` with status, blockers, warnings, supportability_confidence, guidance.
- **Launch profiles** (`release_readiness/models.py`): `LaunchProfile` (profile_id, label, description, required_gate_ids) — demo, internal pilot, careful first user, broader controlled pilot. Not yet wired to a “cohort profile” or surface matrix.
- **Reliability** (`reliability/`): GoldenPathScenario, ReliabilityRunResult, DegradedModeProfile, FallbackRule — path health, not per-cohort scope.
- **Triage** (`triage/`): `cohort_id` on evidence and issues; `SupportabilityImpact` (supported_surface_involved, experimental_surface_involved, recovery_exists). `build_cohort_health_summary(cohort_id)` — open issues, severity, recommended_mitigation, recommended_downgrade. No canonical “which surfaces are supported for this cohort.”
- **Trust** (`trust/`): Authority tiers (observe_only, suggest_only, draft_only, sandbox_write, queued_execute, bounded_trusted_real, commit_or_send_candidate), contracts, scope. No per-cohort “allowed tier set.”
- **Default experience** (`default_experience/`): Surface classification (default_visible, advanced, expert), profiles (first_user, calm_default, full, role calm), disclosure paths. Surfaces are UX visibility tiers, not supportability (supported vs experimental vs blocked).
- **Mission control**: Aggregates release_readiness, triage_state, default_experience_state, trust/authority. No “active cohort profile” or “supported-surface matrix for cohort.”

## 2. What is missing for a true cohort-profile and supported-surface layer

- **Explicit cohort profile**: A single type that defines “who this cohort is” and what they are allowed: internal_demo, careful_first_user, bounded_operator_pilot, document_heavy_pilot, developer_assist_pilot. LaunchProfile is gate-based; we need scope-based cohort profiles (surfaces, trust, workday, automation, readiness).
- **Supported vs experimental vs blocked**: A clear three-way classification per surface per cohort. Triage uses supported_surface_involved but there is no registry of “surface X is supported for cohort Y.” Default_experience uses default_visible/advanced/expert (UX), not supportability.
- **Matrix**: One place that can answer “for cohort C, is surface S supported | experimental | blocked” and “allowed trust tiers,” “allowed workday modes,” “allowed automation scope,” “required readiness level,” “support expectations.”
- **Binding to existing systems**: Cohort profile should bind to default workday preset, default trust preset (or allowed tier set), default experience profile, allowed automations (or “simulate_only” vs “trusted_real”), and required release readiness level (e.g. ready for careful_first_user).
- **Active cohort and persistence**: Which cohort profile is active for this install (e.g. data/local/cohort/active_profile.txt) and surface in mission control.
- **Explain command**: “Why is surface X supported/experimental/blocked for my cohort?” and “What cohort am I in?”

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|---------|
| Create | `src/workflow_dataset/cohort/__init__.py` | Exports |
| Create | `src/workflow_dataset/cohort/models.py` | CohortProfile, SurfaceSupportLevel (supported/experimental/blocked), allowed trust/workday/automation, required_readiness, support_expectations |
| Create | `src/workflow_dataset/cohort/surface_matrix.py` | Surface IDs from default_experience + extended list; per-cohort matrix: surface_id -> supported | experimental | blocked; get_matrix(cohort_id), get_support_level(cohort_id, surface_id) |
| Create | `src/workflow_dataset/cohort/profiles.py` | BUILTIN_COHORT_PROFILES (internal_demo, careful_first_user, bounded_operator_pilot, document_heavy_pilot, developer_assist_pilot); get_cohort_profile(id), list_cohort_profile_ids() |
| Create | `src/workflow_dataset/cohort/bindings.py` | Resolve default workday preset, default trust preset / allowed tiers, default experience profile, allowed automation scope, required readiness; apply_cohort_defaults(cohort_id) returns config dict |
| Create | `src/workflow_dataset/cohort/store.py` | get_active_cohort_id(), set_active_cohort_id(); data/local/cohort/active_profile.txt |
| Create | `src/workflow_dataset/cohort/explain.py` | explain_surface(surface_id, cohort_id), explain_cohort(cohort_id) — why supported/experimental/blocked, what’s allowed |
| Modify | `src/workflow_dataset/cli.py` | cohort_group: add cohort profiles, cohort show --id, cohort matrix --id, cohort apply --id, cohort explain --surface |
| Modify | `src/workflow_dataset/mission_control/state.py` | cohort_state: active_cohort_id, supported_count, experimental_count, blocked_surfaces, trust_posture, next_readiness_review |
| Modify | `src/workflow_dataset/mission_control/report.py` | [Cohort] section |
| Create | `tests/test_cohort.py` | Profile model, matrix, support level, apply, explain, invalid combo, no-profile default |
| Create | `docs/M38A_M38D_COHORT_PROFILES_AND_MATRIX.md` | Files, CLI, samples, tests, gaps |

## 4. Safety/risk note

- **No silent hiding of critical safety**: Blocked surfaces are explicit; operator mode and trust remain visible in mission control. “Blocked” means “not in scope for this cohort,” not “hidden from UI.”
- **Cohort is advisory for rollout**: Applying a cohort profile sets active cohort and can suggest defaults (workday preset, trust); it does not by itself disable trust or approvals. Enforcement of “blocked” in CLI/runtime can be a later step (e.g. warn when using a blocked surface).
- **Supported vs experimental**: Supported = in scope and we commit to support; experimental = in scope but best-effort / known limitations. Blocked = out of scope for this cohort. Triage’s supported_surface_involved should align with this matrix over time.

## 5. Supported-vs-experimental principles

- **Supported**: In scope for the cohort; issues on these surfaces count toward cohort health and supportability; we aim to fix or document.
- **Experimental**: In scope but best-effort; known limitations documented; we may expand to supported after validation.
- **Blocked**: Not in scope for this cohort; use is outside rollout boundaries; can be allowed in a different cohort profile (e.g. internal_demo).

## 6. What this block will NOT do

- Will not implement enterprise feature flags or cloud entitlements.
- Will not silently hide unstable features; blocked/experimental are explained via cohort explain.
- Will not rebuild release_readiness, reliability, or trust; only consume and bind.
- Will not enforce “blocked” at runtime (e.g. hard block commands); first draft is definition and visibility; enforcement can be a follow-up.
