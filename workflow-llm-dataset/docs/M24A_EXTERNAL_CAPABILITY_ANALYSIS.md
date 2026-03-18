# M24A — External Capability Activation Planner (before coding)

## 1. What runtime/integration/catalog capability already exists

- **runtime_mesh.backend_registry**: BackendProfile (repo_local, ollama, llama_cpp) with status (available/configured/missing/unsupported), install_prerequisites, risk_trust_notes, local/optional_remote. `list_backend_profiles`, `get_backend_profile`, `get_backend_status`.
- **runtime_mesh.model_catalog**: ModelEntry (model_id, backend_family, capability_classes, recommended_usage). `load_model_catalog`, `list_models_by_capability`, `get_model_info`.
- **runtime_mesh.integration_registry**: IntegrationManifest (integration_id, local, supported_job_categories, required_runtime_classes, required_model_classes, required_approvals, security_notes, install_status, enabled). Built-in: openclaw, coding_agent, ide_editor, notebook_rag. `list_integrations`, `get_integration`.
- **runtime_mesh.policy**: TASK_CLASS_POLICY, `recommend_for_task_class`, `recommend_backend_for_task`, `compatibility_for_model` — task class → backend/model recommendation and missing list.
- **domain_packs**: DomainPack (domain_id, suggested_model_classes, suggested_integration_classes, expected_approvals, trust_notes). Built-in founder_ops, office_admin, coding_development, etc.
- **starter_kits**: StarterKit (domain_pack_id, recommended_runtime_task_class, recommended_model_class, recommended_job_ids, recommended_routine_ids). `_missing_prerequisites(kit, repo_root)` for jobs/routines/approval.
- **capability_intake**: ExternalSourceCandidate (source_id, adoption_recommendation, safety_risk_level, local_runtime_fit, license, etc.). source_registry.json load/save; list_sources, get_source. Adoption = reject | reference_only | optional_wrapper | candidate_for_pack | core_candidate.
- **local_deployment**: build_local_deployment_profile (edge_profile, readiness, trust_summary, product_surfaces). Reproducible machine snapshot.
- **edge**: build_edge_profile, tiers (dev_full, local_standard, constrained_edge, minimal_eval), TIER_REQUIRED_PATHS, TIER_LLM_REQUIREMENT.
- **trust**: build_trust_cockpit, safe_to_expand, failed_gates, release_gate_checks.
- **incubator**: list_candidates (workflow candidates by stage), add_candidate, get_candidate.
- **Docs**: OPEN_SOURCE_ADOPTION_POLICY.md, OPEN_SOURCE_REJECTION_CRITERIA.md, OPEN_SOURCE_CAPABILITY_MAP.md — when to reject, reference-only, wrap; license/cloud/privacy/safety.

## 2. What is missing for true activation planning

- **Unified external capability source registry**: One place that represents Ollama models, OpenClaw, coding-agent, IDE, automation, optional model/dataset sources with: source_id, category, local vs optional_remote, install/activation prerequisites, licensing/usage policy metadata, security/approval/trust notes, supported task classes, supported verticals/domain packs, supported hardware tiers, **activation status**. Today: integrations (no domain/tier/activation_status); capability_intake (adoption but no activation status or task/domain/tier); backends and model catalog are separate.
- **Activation planner**: Given machine profile + user/domain pack/starter kit + trust/approval posture, produce: recommended activations, blocked activations, “not worth it on this machine”, “unsafe/rejected by policy”, prerequisite steps, estimated resource cost. We have recommend_for_task_class and starter kit missing_prerequisites but no single planner that applies rejection policy and machine/profile filtering to a unified source list.
- **Explicit pull/install/enable plans**: First-class “activation plan” (e.g. “activate Ollama model X”, “enable OpenClaw”) as plans only, no execution. Not represented as a dedicated type or report.
- **Centralized policy/rejection layer in code**: Rejection criteria (unsupported license, too-large resource, not useful for profile, unsafe for trust posture, incompatible machine, remote-only when local-first) exist in docs; no single function that takes (source, machine_profile, trust_posture) and returns allowed/blocked + reason.
- **CLI**: No `capabilities external list | recommend | plan | blocked | explain`.
- **Mission control**: No additive visibility for recommended external capabilities, blocked/rejected, missing prerequisites, activation plans pending review.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/external_capability/__init__.py` |
| Create | `src/workflow_dataset/external_capability/schema.py` — ExternalCapabilitySource dataclass (source_id, category, local, optional_remote, install_prerequisites, license_policy, security_notes, trust_notes, supported_task_classes, supported_domain_pack_ids, supported_tiers, activation_status, ...). |
| Create | `src/workflow_dataset/external_capability/registry.py` — load_external_sources(), list_external_sources(), get_external_source(). Build from integrations + backends + model catalog + optional capability_intake; write to data/local/runtime/external_capability_sources.json or derive in-memory. |
| Create | `src/workflow_dataset/external_capability/policy.py` — apply_rejection_policy(source, machine_profile, trust_posture) -> (allowed: bool, reason: str). Rules: unsupported_license, resource_too_high, not_useful_for_profile, unsafe_trust_posture, incompatible_machine, remote_only_local_first. |
| Create | `src/workflow_dataset/external_capability/planner.py` — ActivationPlanner: recommend(machine_profile, user_profile, domain_pack_id, trust_posture) -> recommended[], blocked[], not_worth_it[], rejected_by_policy[], prerequisite_steps[], resource_estimate. |
| Create | `src/workflow_dataset/external_capability/plans.py` — build_activation_plan(source_id, repo_root) -> list of plan steps (human-readable); no execution. |
| Create | `src/workflow_dataset/external_capability/report.py` — format_external_list, format_recommend, format_blocked, format_plan, format_explain. |
| Modify | `src/workflow_dataset/cli.py` — Add capabilities external list | recommend | plan | blocked | explain (under capabilities_group). |
| Modify | `src/workflow_dataset/mission_control/state.py` — Add external_capabilities: recommended[], blocked[], missing_prerequisites[], plans_pending_review[] (additive). |
| Create | `tests/test_external_capability.py` — registry load, planner recommend/blocked, policy rejection, plan build, report format. |
| Create | `docs/M24A_EXTERNAL_CAPABILITY_ACTIVATION.md` — CLI, schema, planner, policy, plans, samples, tests. |

## 4. Safety/risk note

- **No auto-download**: Planner and plans are advisory; no code in this phase downloads models or assets.
- **No silent enablement**: Activation status and “recommended” are visible; actual enable is explicit operator action (existing approval/trust gates unchanged).
- **Rejection layer**: Policy module explicitly marks sources as blocked/rejected (unsafe, license, local-first violation); product remains local-first and approval-aware.
- **Inspectable**: Registry and plans are file-based or derived from existing registries; operator can audit what is recommended vs blocked.

## 5. What this phase will NOT do

- Implement actual install/pull/enable execution (no running installers or model downloads).
- Add new backends or integrations from scratch (reuse runtime_mesh + capability_intake).
- Change trust or approval logic (read-only use of trust_cockpit and approval registry).
- Cloud/remote activation (local-first only).
- Auto-download models or datasets.
