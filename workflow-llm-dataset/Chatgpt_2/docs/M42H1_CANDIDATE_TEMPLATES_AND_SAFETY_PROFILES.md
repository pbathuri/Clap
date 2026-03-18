# M42H.1 — Candidate Templates + Distillation Safety Profiles

First-draft support for candidate templates (evaluator, vertical specialist, routing, calmness), distillation safety profiles, and clearer production-adjacent restrictions for local training paths.

---

## 1. Files modified

- **`src/workflow_dataset/candidate_model_studio/models.py`**
  - Added `ProductionAdjacentRestrictions` (require_council_before_supported, no_weight_changes_in_production_scope, max_slice_size, experimental_only_until_council, allowed_path_ids).
  - Added `CandidateTemplate` (template_id, label, description, default_training_path_id, default_boundary, suggested_provenance_sources, default_safety_profile_id).
  - Added `DistillationSafetyProfile` (profile_id, label, description, allowed_path_ids, production_restrictions).
  - Extended `TrainingDistillationPath` with `default_safety_profile_id` and `production_restrictions_summary`.
  - Extended `CandidateModel` with `template_id` and `safety_profile_id`.

- **`src/workflow_dataset/candidate_model_studio/training_paths.py`**
  - Each path now has `default_safety_profile_id` and `production_restrictions_summary` for production-adjacent use.

- **`src/workflow_dataset/candidate_model_studio/store.py`**
  - `load_candidate` now reads and sets `template_id` and `safety_profile_id`.

- **`src/workflow_dataset/candidate_model_studio/create.py`**
  - All create_* helpers accept `template_id` and `safety_profile_id`; when `template_id` is set, default path/boundary/safety come from template.
  - `create_candidate()` accepts `template_id` and `safety_profile_id` and passes them through.

- **`src/workflow_dataset/candidate_model_studio/report.py`**
  - `build_candidate_report` includes `template_id` and `safety_profile_id` in the report dict.

- **`src/workflow_dataset/candidate_model_studio/__init__.py`**
  - Exported `ProductionAdjacentRestrictions`, `CandidateTemplate`, `DistillationSafetyProfile`.

- **`src/workflow_dataset/cli.py`**
  - `model-studio create` has `--template` and `--safety-profile`.
  - New commands: `model-studio templates list|show --id ID`, `model-studio safety-profiles list|show --id ID`.

- **`tests/test_candidate_model_studio.py`**
  - Added tests for templates (evaluator, calmness, list), safety profiles (strict, production_restrictions, list), path production_restrictions_summary, and create with template.

---

## 2. Files created

- **`src/workflow_dataset/candidate_model_studio/templates.py`** — Registry of candidate templates: evaluator, vertical_specialist, routing, calmness. Each has default_training_path_id, default_boundary, suggested_provenance_sources, default_safety_profile_id.
- **`src/workflow_dataset/candidate_model_studio/safety_profiles.py`** — Registry of distillation safety profiles: strict_production_adjacent, experimental_only, council_gated, lab_research. Each has allowed_path_ids and production_restrictions (ProductionAdjacentRestrictions).
- **`docs/M42H1_CANDIDATE_TEMPLATES_AND_SAFETY_PROFILES.md`** — This file.

---

## 3. Sample candidate template

**Evaluator candidate** (`workflow-dataset model-studio templates show --id evaluator` or JSON):

```json
{
  "template_id": "evaluator",
  "label": "Evaluator candidate",
  "description": "Model or rule set used only to score/critique outputs; not primary response model. Suited to council or review pipeline.",
  "default_training_path_id": "critique_evaluator",
  "default_boundary": "experimental",
  "suggested_provenance_sources": ["council_disagreement", "accepted_adaptations", "production_safe"],
  "default_safety_profile_id": "strict_production_adjacent"
}
```

**Calmness candidate** (prompt/config only, reduce interruptiveness):

```json
{
  "template_id": "calmness",
  "label": "Calmness candidate",
  "description": "Prompt/config only: reduce interruptiveness or adjust tone (calmness, brevity). No weight changes.",
  "default_training_path_id": "prompt_config_only",
  "default_boundary": "experimental",
  "suggested_provenance_sources": ["corrections", "accepted_adaptations", "production_safe"],
  "default_safety_profile_id": "experimental_only"
}
```

---

## 4. Sample safety profile

**Strict production-adjacent** (`workflow-dataset model-studio safety-profiles show --id strict_production_adjacent` or JSON):

```json
{
  "profile_id": "strict_production_adjacent",
  "label": "Strict production-adjacent",
  "description": "Use when candidate may affect production-adjacent surfaces. Council required before supported; no weight changes in production scope.",
  "allowed_path_ids": ["prompt_config_only", "routing_only", "critique_evaluator", "vertical_specialist"],
  "production_restrictions": {
    "require_council_before_supported": true,
    "no_weight_changes_in_production_scope": true,
    "max_slice_size": 0,
    "experimental_only_until_council": true,
    "allowed_path_ids": []
  }
}
```

**Experimental only** (candidate stays experimental; max_slice_size 5000):

```json
{
  "profile_id": "experimental_only",
  "label": "Experimental only",
  "description": "Candidate stays in experimental surfaces only. No promotion to supported without switching profile.",
  "allowed_path_ids": ["prompt_config_only", "routing_only", "critique_evaluator", "vertical_specialist", "lightweight_distillation"],
  "production_restrictions": {
    "require_council_before_supported": true,
    "no_weight_changes_in_production_scope": true,
    "max_slice_size": 5000,
    "experimental_only_until_council": true,
    "allowed_path_ids": []
  }
}
```

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_candidate_model_studio.py -v
```

**15 tests**, including M42H.1:

- test_candidate_model_creation
- test_dataset_slice_curation
- test_lineage_provenance
- test_training_path_descriptor
- test_quarantined_candidate
- test_no_evidence_weak_dataset
- test_candidate_report_full
- **test_candidate_template_evaluator** — Evaluator template has critique_evaluator path and strict_production_adjacent safety.
- **test_candidate_template_calmness** — Calmness template has prompt_config_only and experimental_only.
- **test_list_templates** — List returns evaluator, vertical_specialist, routing, calmness.
- **test_safety_profile_strict_production_adjacent** — Strict profile has require_council and no_weight_changes.
- **test_safety_profile_production_restrictions** — get_production_restrictions returns restrictions (e.g. max_slice_size 5000).
- **test_list_safety_profiles** — List includes strict_production_adjacent, experimental_only, council_gated, lab_research.
- **test_training_path_has_production_restrictions_summary** — Path has default_safety_profile_id and production_restrictions_summary.
- **test_create_with_template_sets_template_and_safety** — Create from corrections with template_id sets template_id, safety_profile_id, and training_path_id on candidate.

---

## 6. Next recommended step for the pane

- **Wire council subject_type `candidate_model`** — When promoting or reviewing a candidate model, run council with subject_type `candidate_model` and enforce the candidate’s `safety_profile_id` (e.g. require_council_before_supported) so promotion to supported is gated by council and production-adjacent restrictions are applied consistently.
- **Enforce slice size from profile** — When building or validating a dataset slice for a candidate, apply `production_restrictions.max_slice_size` from the candidate’s safety profile (if set) and reject or warn when the slice exceeds it.
- **Mission control** — Surface “safety profile” and “template” in the candidate model studio state (e.g. top_candidate.template_id, top_candidate.safety_profile_id) and optionally show a short “production restrictions” summary for the top candidate.
