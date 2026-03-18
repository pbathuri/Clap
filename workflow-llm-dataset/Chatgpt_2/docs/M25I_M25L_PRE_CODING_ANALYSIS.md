# M25I–M25L — Pack Authoring SDK + Certification Harness — Pre-coding analysis

## 1. What pack structure/runtime/validation already exists

- **packs/scaffold.py** — `scaffold_pack(pack_id)`: creates pack dir with manifest.json skeleton, prompts/, tasks/, demos/, docs/README.md, tests/. No prompt/task asset file skeletons yet.
- **packs/pack_models.py** — `PackManifest` (pydantic), `validate_pack_manifest`: required pack_id/name/version, safety_policies (sandbox_only, require_apply_confirm, no_network_default must not be false).
- **packs/pack_validator.py** — `validate_pack_manifest_and_recipes`: manifest + recipe_steps validation.
- **packs/pack_recipes.py** — `validate_recipe_steps`: only declarative step types (create_config, register_templates, etc.); no run_shell/execute_script.
- **packs/authoring_validation.py** — `validate_pack_structure`: manifest + recipes, then prompts/docs presence (warnings), role_tags/workflow_tags recommended, safety_policies explicit. `conflict_risk_indicators`, `validate_pack_full`.
- **packs/certification.py** — `run_certification`: structural (validate_pack_full), installability (manifest+recipes), first_value_readiness (templates/workflow_templates), conflict_simulation with installed packs. Status: draft | valid | certifiable | blocked | needs_revision.
- **packs/scorecard.py** — `build_pack_scorecard`, `format_pack_scorecard`: roles_supported, tasks_workflows_supported, runtime_requirements, conflict_risk, first_value_strength, acceptance_readiness, certification_status, recommended_fixes.
- **packs/pack_registry.py**, **pack_state.py**, **pack_conflicts.py** — Installed state, conflict detection (harmless_overlap, mergeable, precedence_required, incompatible, blocked).
- **value_packs/** — Registry, recommend, first_run_flow; separate from capability packs.
- **starter_kits/** — Models, registry, recommend.
- **CLI** — `packs scaffold --id`, `packs validate` / `validate-manifest`, `packs certify --id`, `packs scorecard --id`, `packs gallery`, `packs showcase`.
- **mission_control** — Section 26 "Pack authoring": draft_packs, uncertified_packs, blocked_certification, certifiable_packs. Report prints draft/uncertified/blocked/certifiable counts.
- **Docs** — CAPABILITY_PACK_MANIFEST.md, PACK_CONFLICT_RESOLUTION_POLICY.md, MULTI_PACK_RUNTIME_MODEL.md.

## 2. What is missing for real authoring/certification

- **Richer scaffold** — Prompt asset skeletons (e.g. prompts/system_guidance.md, prompts/task_prompt.md), task/workflow defaults skeleton (tasks/ or manifest behavior.task_defaults), demo asset README, test file placeholder (e.g. tests/test_<pack_id>_smoke.py).
- **Stronger validation** — Trust/safety metadata presence (safety_constraints or trust_readiness_hint); optional strict mode where missing docs/README or tests/ surface as errors; behavior field shape check (prompt_assets, task_defaults).
- **Certification harness extensions** — Explicit acceptance_scenario_compatibility check (templates/workflow_templates + optional acceptance scenario list); trust_readiness_signals check (safety_policies and safety_constraints present). Human-readable certification report formatter.
- **Scorecard/report** — Already complete; add certification report formatter for file output and consistency with scorecard.
- **Mission control** — Already has draft/uncertified/blocked/certifiable; optional: "highest-value certifiable" (e.g. certifiable packs with most templates) for prioritization.
- **Tests and docs** — Focused tests for scaffold output, validation (valid/invalid/manifest-only), certification statuses, scorecard; one doc with sample scaffold, validation output, certification report, scorecard, and remaining gaps.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Modify | `packs/scaffold.py` — Add prompt skeletons (prompts/system_guidance.md, prompts/task_prompt.md), tasks/workflow_defaults.json.skel, demos/README.md, tests/test_<pack_id>_smoke.py.skel. |
| Modify | `packs/authoring_validation.py` — Add trust/safety metadata check; optional strict mode (missing docs/tests as errors). |
| Modify | `packs/certification.py` — Add acceptance_scenario_compatibility and trust_readiness_signals checks; add format_certification_report(). |
| Modify | `mission_control/state.py` — Add certifiable_pack_ids_sample or highest_value_certifiable (certifiable with most templates) for visibility. |
| Create | `docs/M25I_M25L_PACK_AUTHORING.md` — Sample scaffold layout, validation output, certification report, scorecard, CLI usage, tests run, remaining gaps. |
| Create/modify | Tests: `tests/test_pack_authoring.py` or extend existing — scaffold output, validate (valid/invalid), certify (draft/certifiable/blocked), scorecard, blocked/invalid cases. |

## 4. Safety/risk note

- No arbitrary code execution: scaffold and recipes remain declarative; validation and certification do not run pack code.
- Safety policies (sandbox_only, require_apply_confirm, no_network_default) cannot be set to false by manifest validation.
- Certification conflict simulation uses existing detect_conflicts; blocked/incompatible status blocks certifiable.
- Trust/readiness signals are advisory; they do not bypass approval or trust cockpit.

## 5. What this block will NOT do

- No public marketplace portal or automatic publishing to cloud.
- No arbitrary code plugin loading or execution from packs.
- No bypass of trust/safety validation or acceptance gates.
- No rewrite of pack runtime, mission control, value packs, or starter kits.
- Pack expansion factory stays local and inspectable; certification status is advisory for operators.
