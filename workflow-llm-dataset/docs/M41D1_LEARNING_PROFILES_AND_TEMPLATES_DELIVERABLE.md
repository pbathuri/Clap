# M41D.1 — Learning Profiles + Safe Experiment Templates (Deliverable)

Extension to the existing learning lab (M41A–M41D). No rebuild; adds first-draft support for learning profiles, experiment templates, and safety boundaries for production-adjacent environments.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/learning_lab/models.py` | Added `LearningProfile`, `ExperimentTemplate`; constants `PROFILE_*`, `TEMPLATE_*`, `ENV_LOCAL_ONLY`, `ENV_PRODUCTION_ADJACENT`; `ImprovementExperiment.profile_id`, `template_id`. |
| `src/workflow_dataset/learning_lab/store.py` | Added `CURRENT_PROFILE_FILE`, `set_current_profile_id`, `get_current_profile_id`; `_dict_to_experiment` / serialization for `profile_id`, `template_id`. |
| `src/workflow_dataset/learning_lab/experiments.py` | Added `_apply_profile_and_template`; `create_experiment_from_*` accept optional `profile_id`, `template_id` and set them on new experiments. |
| `src/workflow_dataset/learning_lab/__init__.py` | Exported profiles/templates API, profile/template constants, `set_current_profile_id`, `get_current_profile_id`. |
| `src/workflow_dataset/learning_lab/report.py` | `build_experiment_report` now includes `profile_id` and `template_id`. |
| `src/workflow_dataset/cli.py` | Added `learning-lab profiles`, `learning-lab templates` (--profile, --production-adjacent), `learning-lab profile-set <id>`; `learning-lab create` accepts `--profile`, `--template`. |
| `src/workflow_dataset/mission_control/state.py` | `learning_lab_state` extended with `current_profile_id`, `safe_templates_local_count`, `safe_templates_production_adjacent_count`. |
| `tests/test_learning_lab.py` | Added 9 tests for profiles, templates, allowed-for-profile, safety boundaries, current profile get/set, experiment with profile/template, report includes profile/template. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/learning_lab/profiles_and_templates.py` | Built-in `LEARNING_PROFILES`, `EXPERIMENT_TEMPLATES`; `get_profiles()`, `get_templates()`, `get_profile()`, `get_template()`, `get_templates_allowed_for_profile()`, `is_experiment_allowed_in_environment()`. |
| `docs/M41D1_LEARNING_PROFILES_AND_TEMPLATES_DELIVERABLE.md` | This file. |

---

## 3. Sample learning profile

**ID:** `conservative`

```python
LearningProfile(
    profile_id="conservative",
    label="Conservative",
    description="Minimal local learning: few pending experiments, only approved templates; production-adjacent restricted to trust-threshold and read-only prompt tweaks.",
    max_pending_experiments=3,
    allow_production_adjacent=True,
    allowed_template_ids=["prompt_tuning", "trust_threshold_tuning"],
    production_adjacent_template_ids=["trust_threshold_tuning"],
    safety_notes="In production-adjacent: only trust_threshold_tuning with narrow bounds. No routing or queue changes.",
)
```

**CLI:** `workflow-dataset learning-lab profiles`

```
Learning profiles  current=balanced
    conservative  Conservative  max_pending=3
  * balanced  Balanced  max_pending=10
    research_heavy  Research-heavy  max_pending=25
```

---

## 4. Sample safe experiment template

**ID:** `trust_threshold_tuning`

```python
ExperimentTemplate(
    template_id="trust_threshold_tuning",
    label="Trust threshold tuning",
    description="Adjust confidence or trust thresholds for escalation/auto-apply; validate on local evidence.",
    experiment_type="trust_threshold_tuning",
    allowed_subsystems=["safe_adaptation", "assist_engine", "corrections"],
    production_adjacent_allowed=True,
    safety_notes="In production-adjacent: narrow bounds; require comparison report before promote.",
)
```

**CLI:** `workflow-dataset learning-lab templates --profile conservative --production-adjacent`

```
Experiment templates  profile=conservative  production_adjacent
  - prompt_tuning  Prompt tuning  prod_adjacent=True
  - routing_changes  Routing changes  prod_adjacent=False
  - queue_tuning  Queue tuning  prod_adjacent=False
  * trust_threshold_tuning  Trust threshold tuning  prod_adjacent=True
```

(`*` = allowed for the selected profile in the selected environment.)

---

## 5. Safety boundaries (production-adjacent)

| Profile | Local-only templates | Production-adjacent templates |
|---------|----------------------|-------------------------------|
| **conservative** | prompt_tuning, trust_threshold_tuning | trust_threshold_tuning only |
| **balanced** | prompt_tuning, routing_changes, queue_tuning, trust_threshold_tuning | prompt_tuning, trust_threshold_tuning |
| **research_heavy** | (same as balanced) | prompt_tuning, trust_threshold_tuning |

- **Routing changes** and **queue tuning** are never allowed in production-adjacent in this first draft.
- Use `get_templates_allowed_for_profile(profile_id, production_adjacent=True/False)` or `is_experiment_allowed_in_environment(profile_id, template_id, production_adjacent)` to enforce or display boundaries.

---

## 6. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_learning_lab.py -v --tb=short
```

**Result:** 23 passed (14 existing + 9 new for M41D.1).

New tests:

- `test_get_profiles` — 3 profiles, conservative/balanced/research_heavy
- `test_get_templates` — 4 templates (prompt_tuning, routing_changes, queue_tuning, trust_threshold_tuning)
- `test_get_profile_get_template` — get by id or None
- `test_templates_allowed_for_profile_local` — conservative local: prompt_tuning, trust_threshold_tuning allowed; routing_changes not
- `test_templates_allowed_for_profile_production_adjacent` — conservative prod-adjacent: only trust_threshold_tuning
- `test_safety_boundary_is_experiment_allowed` — is_experiment_allowed_in_environment for conservative/balanced
- `test_current_profile_get_set` — set/get current profile; default balanced when file missing
- `test_experiment_with_profile_and_template` — save/load experiment with profile_id and template_id
- `test_build_experiment_report_includes_profile_template` — report includes profile_id and template_id

---

## 7. Next recommended step for the pane

- **Option A (enforcement):** Before running an experiment in a production-adjacent environment, call `is_experiment_allowed_in_environment(get_current_profile_id(), template_id, production_adjacent=True)` and block or warn if `False`. Wire `production_adjacent` from mission control or from an explicit env flag.
- **Option B (UI):** In the learning lab pane, show current profile and “Safe templates (local)” / “Safe templates (production-adjacent)” from `learning_lab_state` (`current_profile_id`, `safe_templates_local_count`, `safe_templates_production_adjacent_count`), and when creating an experiment, filter template dropdown by profile and environment.
- **Option C (templates as first-class):** Require `--template` on `learning-lab create` when in production-adjacent mode and validate against `get_templates_allowed_for_profile` before creating.

Recommendation: do **Option B** next so the pane reflects profiles and safe templates; then add **Option A** when the runner knows whether it is in a production-adjacent environment.
