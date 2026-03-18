# M44I–M44L — Retrieval-Grounded Operator Intelligence + Memory Actioning: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/continuity_engine/models.py` | Added optional `memory_context: dict` to `ResumeCard` and `NextSessionRecommendation`; included in `to_dict()`. |
| `src/workflow_dataset/continuity_engine/store.py` | `load_next_session_recommendation` now reads `memory_context` from JSON. |
| `src/workflow_dataset/continuity_engine/resume_flow.py` | `build_resume_flow` calls `get_resume_memory_context` and sets `ResumeCard.memory_context`. |
| `src/workflow_dataset/planner/sources.py` | `gather_planning_sources` accepts optional `project_id` and `session_id`; when provided, calls `enrich_planning_sources` to add `memory_context` and `memory_prior_cases`. |
| `src/workflow_dataset/cli.py` | New `memory-intelligence` Typer group with commands: `suggest`, `explain`, `prior-cases`, `planner-context`. |
| `src/workflow_dataset/mission_control/state.py` | New block `memory_intelligence_state`: recommendation count, weak caution count, top prior case, most influential recommendation id, next recommended memory review. |
| `src/workflow_dataset/mission_control/report.py` | New "[Memory intelligence]" section in mission control report. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M44I_M44L_MEMORY_INTELLIGENCE_BEFORE_CODING.md` | Before-coding doc: existing intelligence, gaps, file plan, safety, actioning principles, what we will not do. |
| `src/workflow_dataset/memory_intelligence/__init__.py` | Package exports. |
| `src/workflow_dataset/memory_intelligence/models.py` | RetrievalGroundedRecommendation, RetrievedPriorCase, DecisionRationaleRecall, MemoryBackedNextStepSuggestion, MemoryBackedOperatorFlowHint, WeakMemoryCaution, MemoryToActionLinkage. |
| `src/workflow_dataset/memory_intelligence/retrieval.py` | `retrieve_for_context(project_id, session_id, query, limit, repo_root)` using memory_substrate + fusion links. |
| `src/workflow_dataset/memory_intelligence/store.py` | `save_recommendation`, `load_recommendation`, `list_recent_recommendations` (JSON under `data/local/memory_intelligence/`). |
| `src/workflow_dataset/memory_intelligence/recommendations.py` | `build_memory_backed_recommendations(project_id, session_id, repo_root, limit, persist)`. |
| `src/workflow_dataset/memory_intelligence/planner_enrichment.py` | `enrich_planning_sources(sources_dict, project_id, session_id, repo_root)`. |
| `src/workflow_dataset/memory_intelligence/continuity_enrichment.py` | `get_resume_memory_context`, `get_next_session_memory_context`. |
| `src/workflow_dataset/memory_intelligence/assist_enrichment.py` | `memory_backed_suggestions_for_context(project_id, session_id, repo_root, max_suggestions)`. |
| `src/workflow_dataset/memory_intelligence/operator_context.py` | `get_memory_backed_operator_context(project_id, responsibility_id, repo_root)`. |
| `src/workflow_dataset/memory_intelligence/explanation.py` | `explain_recommendation(rec_id)`, `explain_prior_case_influence(rec_id)`, `list_weak_memory_cautions(limit, repo_root)`. |
| `tests/test_memory_intelligence.py` | Tests for models, retrieval, recommendations, explanation, planner/continuity/assist/operator wiring, store, no-memory behavior. |
| `docs/samples/M44_memory_backed_recommendation.json` | Sample memory-backed recommendation. |
| `docs/samples/M44_explain_output.json` | Sample explain output. |
| `docs/samples/M44_prior_case_influence_output.json` | Sample prior-case influence output. |

## 3. Exact CLI usage

```bash
# Build memory-backed recommendations for a project (persist for explain)
workflow-dataset memory-intelligence suggest --project founder_case_alpha
workflow-dataset memory-intelligence suggest --project founder_case_alpha --session sess_xyz --json

# Explain which memory influenced a recommendation
workflow-dataset memory-intelligence explain rec_123
workflow-dataset memory-intelligence explain rec_123 --json

# List prior cases retrieved for a project
workflow-dataset memory-intelligence prior-cases --project founder_case_alpha
workflow-dataset memory-intelligence prior-cases --project founder_case_alpha --limit 10 --json

# Show planner context enriched with memory
workflow-dataset memory-intelligence planner-context --project founder_case_alpha
workflow-dataset memory-intelligence planner-context --project founder_case_alpha --session sess_xyz --json
```

## 4. Sample memory-backed recommendation

See `docs/samples/M44_memory_backed_recommendation.json`. Example:

- `recommendation_id`: rec_abc123  
- `kind`: next_step  
- `title`: Memory-backed suggestion  
- `description`: Last session you were iterating on founder_case_alpha onboarding flow; next step was to run the demo script and capture outcomes.  
- `prior_cases`: one prior case with unit_id, snippet, confidence 0.92  
- `rationale_recall`: one rationale with source_unit_ids and influence_strength medium  
- `weak_cautions`: []  
- `created_at_utc`: ISO timestamp  

## 5. Sample explanation output

See `docs/samples/M44_explain_output.json`. Example:

- `found`: true  
- `memory_influence`: prior_cases, rationale_recall, weak_cautions  
- `action_linkages`: []  

## 6. Sample prior-case influence output

See `docs/samples/M44_prior_case_influence_output.json`. Example:

- `prior_cases`: list of prior cases with unit_id, snippet, confidence  
- `rationale_recall`: list of rationales  
- `influence_summary`: "1 prior case(s) and 1 rationale(s) influenced this recommendation."  

## 7. Exact tests run

```bash
python3 -m pytest tests/test_memory_intelligence.py -v
```

All 10 tests passed:

- test_models_to_dict  
- test_retrieve_for_context_empty  
- test_build_memory_backed_recommendations_no_memory  
- test_explain_recommendation_not_found  
- test_explain_prior_case_influence_not_found  
- test_list_weak_memory_cautions_structure  
- test_planner_enrichment_adds_keys  
- test_continuity_enrichment_returns_dict  
- test_store_save_load  
- test_no_relevant_memory_behavior  

## 8. Remaining gaps for later refinement

- **Planner compiler**: Planner compile step does not yet consume `memory_context` / `memory_prior_cases` in prompt or logic; only sources are enriched. A later step can pass these into the planner compiler or LLM context.  
- **Assist queue merge**: `memory_backed_suggestions_for_context` is available but not yet merged into the assist engine queue (e.g. as a separate “memory suggests” bucket or merged with `generate_assist_suggestions`).  
- **Operator mode UI**: `get_memory_backed_operator_context` is callable but not yet wired into operator-mode CLI or mission control display for a specific responsibility.  
- **Review studio / prior-decision recall**: No direct wiring yet to review studio or benchmark/learning-lab case selection; retrieval and models are in place for future use.  
- **Memory-to-action linkage**: `MemoryToActionLinkage` and `action_linkages` on recommendations are modeled but not yet populated when creating action cards or queue items.  
- **Next-session memory at shutdown**: `get_next_session_memory_context` exists but is not yet called from shutdown flow when building/saving `NextSessionRecommendation`; only resume flow is wired.  
- **Confidence tuning**: Confidence in retrieval is rank-based; could be refined with link confidence from memory_fusion or backend scores when available.  
