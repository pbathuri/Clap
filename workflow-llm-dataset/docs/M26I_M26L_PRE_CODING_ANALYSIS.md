# M26I–M26L — Agent Teaching Studio + Skill Capture — Pre-coding analysis

## 1. What teaching/demos/corrections/memory surfaces already exist

- **task_demos (M23E-F1)** — TaskDefinition (task_id, steps [TaskStep: adapter_id, action_id, params, notes]), store: list_tasks, get_task, save_task under data/local/task_demonstrations. Replay for simulate. No “skill” abstraction; demos are raw task sequences.
- **corrections (M23M)** — CorrectionEvent (correction_id, source_type, source_reference_id, operator_action, correction_category, original/corrected_value, eligible_for_memory_update). Store: save_correction, get_correction, list_corrections under data/local/corrections/events. No conversion to reusable skill.
- **specialization** — SpecializationRecipe (recipe_id, mode, data_sources, licensing); recipe runs storage. Focus is retrieval/embedding/adapters, not “taught skills” from demos/corrections.
- **session (M24J–M24M)** — Session (session_id, value_pack_id, active_tasks, active_job_ids, …). Session board and artifacts. No explicit “skills learned from session.”
- **outcomes (M24N–M24Q)** — SessionOutcome, TaskOutcome, UsefulnessConfirmation, BlockedCause; store under data/local/outcomes. Success/blocked patterns exist but are not normalized into skill definitions.
- **job_packs / value_packs / packs** — Jobs, routines, macros, value packs, pack certification. No “skill” entity attached to packs/jobs.
- **planner (M26A)** — GoalRequest, ProvenanceSource (job, macro, routine, task_demo, pack). Plans can reference task_demo; no skill library as planning input.
- **acceptance/trust** — Readiness and trust gates; no per-skill trust/readiness today.

**Gaps:** No explicit skill model; no conversion from task_demo/correction/session pattern to “skill”; no review/accept/reject flow for candidate skills; no skill library (draft/accepted/rejected) or pack/job attachment; no teaching-studio CLI or mission-control visibility for candidate/accepted skills or skills needing review.

---

## 2. What is missing for a real skill-capture system

- **Skill model** — Explicit record: skill_id, source (demo/correction/session/manual), goal_family, task_family, required_capabilities, required_approvals, pack/job associations, expected_inputs/outputs, trust/readiness status, operator/certification notes, status (draft/accepted/rejected).
- **Demo-to-skill normalization** — Convert task_demo, correction, or repeated session pattern into a skill definition (draft) for review.
- **Teaching studio / review surface** — List candidates, review normalized steps, accept/reject/edit draft, attach to goal family/pack/job, mark simulate-only vs trusted-real candidate.
- **Skill library persistence** — Store draft/accepted/rejected skills; report by status, pack association, “needs review,” “top reusable,” “weak/unclear.”
- **CLI** — skills list, skills draft-from-demo --id, skills review --id, skills attach --id --pack, skills report.
- **Mission control** — Additive: candidate_skills, recently_accepted_skills, pack_linked_skills, skills_needing_review.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/teaching/__init__.py` — Public API. |
| Create | `src/workflow_dataset/teaching/skill_models.py` — Skill dataclass (skill_id, source_type, source_ref, goal_family, task_family, required_capabilities, required_approvals, pack_associations, job_associations, expected_inputs, expected_outputs, trust_readiness_status, operator_notes, certification_notes, status, simulate_only_or_trusted_real). |
| Create | `src/workflow_dataset/teaching/skill_store.py` — get_skills_dir, save_skill, load_skill, list_skills(status filter), delete_skill. Persist under data/local/teaching/skills/. |
| Create | `src/workflow_dataset/teaching/normalize.py` — demo_to_skill_draft(task_id), correction_to_skill_draft(correction_id), manual_skill_draft(skill_id, ...). Return Skill with status=draft. |
| Create | `src/workflow_dataset/teaching/review.py` — list_candidate_skills(), accept_skill(skill_id), reject_skill(skill_id), attach_skill_to_pack(skill_id, pack_id). |
| Create | `src/workflow_dataset/teaching/report.py` — build_skill_report(), format_skill_report(): draft/accepted/rejected counts, pack-associated, needing review, top reusable, weak/unclear. |
| Modify | `src/workflow_dataset/cli.py` — Add skills_group: skills list, skills draft-from-demo --id, skills review --id, skills attach --id --pack, skills report. |
| Modify | `src/workflow_dataset/mission_control/state.py` — Add teaching/skills section: candidate_skills, recently_accepted_skills, pack_linked_skills, skills_needing_review. |
| Modify | `src/workflow_dataset/mission_control/report.py` — Add [Teaching / skills] section. |
| Create | `tests/test_teaching_skills.py` — Skill model, store, demo-to-skill, review accept/reject, report, blocked/unclear cases. |
| Create | `docs/M26I_M26L_TEACHING_SKILLS.md` — Usage, sample skill, demo-to-skill output, review flow, report, gaps. |

---

## 4. Safety/risk note

- **Explicit only** — Skills are created from explicit demo/correction/manual input and operator review; no hidden continual learning.
- **No auto-promotion** — Raw demos become draft skills; accepted only after review/accept.
- **No bypass** — Trust/approval semantics unchanged; skills can be marked simulate-only or trusted-real candidate; no auto-execution.
- **Local and inspectable** — All skills under data/local/teaching/skills/; operator can review and delete.

---

## 5. What this block will NOT do

- No hidden continual learning or automatic model updates from every action.
- No direct opaque model fine-tuning from user actions.
- No automatic unsafe execution; skills inform planning/recommendations only.
- No rewrite of task_demos/corrections/specialization from scratch.
- No bypass of trust/approval semantics; first-draft teaching surface only.
