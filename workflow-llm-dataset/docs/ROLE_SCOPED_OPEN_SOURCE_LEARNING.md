# Role-scoped open-source learning (M21)

How we use open-source repo signals to improve the agent in a **role-scoped** way while keeping user data local and private.

---

## Goal

- Improve **capability packs**, **eval suites**, **workflow templates**, and **role/domain knowledge priors** using ranked open-source repos.
- Keep **user-private data** and **open-source domain priors** strictly separate.
- Filter and rank repos by **role**, **industry**, **workflow type**, and **pain points** so that only relevant, approved sources influence each scope.

---

## Role / industry / workflow scoping

- **Query model:** RepoTaskFitQuery (role, industry, workflow_type, task_type, pain_points, UI_need, parsing_need, orchestration_need, etc.).
- **Ranking:** We rank registered sources by fit (role_match, workflow_match, pain_point_match, safety, maintenance, license). Results are RepoTaskFitResult.
- **Use of rank:**
  - **Capability pack design:** Packs declare role/industry/workflow tags; we can recommend or build packs using top-ranked repos for that tag set.
  - **Eval suites:** Eval tasks can be derived from or inspired by top-ranked repos for the same role/workflow; we do not run external code.
  - **Workflow templates:** Trial scenarios and release task sets can align with patterns from ranked repos (documented, not vendored).
  - **Domain priors:** Curated text from high-ranking, approved repos can be used to build retrieval or SFT material **per role/workflow**; user data is never mixed in during ingestion.

---

## Separation: user data vs open-source priors

- **User data (local only):** Work graph, routines, style signals, feedback, session state, parsed user artifacts. Never sent to cloud or to an external repo. Not used to train third-party models without explicit consent.
- **Open-source priors:** Licensed, curated content from approved repos; used to build or extend:
  - retrieval corpora (e.g. role-specific docs),
  - SFT or reference data (e.g. task exemplars),
  - workflow/task templates,
  - parser/config examples.
- **Combination at runtime:** The local agent may use **both** (e.g. retrieval over user graph + role-specific prior corpus). Combination happens **on device**; prior data was ingested in a separate, auditable pipeline with no user data in it.

---

## Pipeline constraints

- **Ingestion:** Only sources with adoption_recommendation in (reference_only, borrow_patterns, optional_wrapper, candidate_for_pack) and with acceptable license can contribute to priors.
- **Provenance:** Every ingested document or template must reference a source_id (and ideally version); we can audit and remove if a source is later rejected.
- **Role scope:** Priors are tagged by role/industry/workflow; we only use priors that match the user’s selected or inferred scope (e.g. ops pack uses ops-scoped priors only).
- **No uncontrolled scrape:** We do not automatically crawl GitHub or the web; we only use explicitly registered and ranked sources.

---

## Relation to capability packs

- Packs declare **role_industry_workflow_tags**.
- When building or recommending a pack, we can rank repos by the same tags and use top candidates as **reference** for templates, eval tasks, and config.
- Pack installer and pack list are local; cloud (when it exists) distributes only manifests and recipes, not user data.

---

## Summary

- **Role-scoped learning:** Rank repos by role/industry/workflow/pain point; use results to improve packs, eval, templates, and priors.
- **User data separate:** Never mix user-private data with open-source ingestion; combine only at runtime on device.
- **Provenance and policy:** All sources in registry; OPEN_SOURCE_TRAINING_POLICY and rejection criteria apply; pipelines are auditable.
