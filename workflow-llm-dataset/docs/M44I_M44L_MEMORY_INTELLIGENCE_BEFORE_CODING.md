# M44I–M44L — Retrieval-Grounded Operator Intelligence + Memory Actioning: Before Coding

## 1. What memory-aware intelligence already exists

- **Memory substrate** (`memory_substrate/`): CompressedMemoryUnit, RetrievalIntent, retrieve_units(intent), store (SQLite/in-memory), search_keyword, search_structured. Session-scoped storage and retrieval; no project_id in intent (session_id only).
- **Memory fusion** (M43): memory_fusion links (memory ↔ project/session); get_memory_context_for_live_context, get_memory_context_for_continuity; explain_live_context_memory; list_weak_memories. Stub substrate adapter when memory_substrate not wired; continuity and live-context get “snippets” and rationale.
- **Planner** (`planner/sources.py`): gather_planning_sources pulls session, work_state, job_recommendations, routines, macros, task_demos, pack_summary. No memory or retrieval.
- **Assist engine** (`assist_engine/generation.py`): generate_assist_suggestions from progress board, goal/plan, digest, routines, skills, packs. No memory retrieval; suggestions are deterministic from current state.
- **Continuity** (`continuity_engine/resume_flow.py`): detect_interrupted_work, build_resume_flow; NextSessionRecommendation from store. M43 added continuity memory-context CLI and get_memory_context_for_continuity but it is not yet merged into resume card or next-session rationale.
- **Operator mode** (`operator_mode/`): DelegatedResponsibility, OperatorModeSummary; no memory-backed context for responsibilities.
- **Learning lab / council / benchmark board**: Use memory slices or substrate in places; no unified “retrieval-grounded recommendation” or “prior case” model.

## 2. What is missing for true retrieval-grounded operator intelligence

- **Explicit models**: Retrieval-grounded recommendation (with prior cases, rationale, weak-memory caution); retrieved prior case; decision-rationale recall; memory-backed next-step suggestion; memory-backed operator flow hint; memory-to-action linkage.
- **Product wiring**: Planner context enrichment with retrieved memory; continuity/resume recommendations that include memory-derived rationale and prior cases; assist suggestions that can be memory-backed (or a parallel “memory-backed suggestions” stream); operator-mode context enriched with memory for delegated responsibility; review studio / prior-decision recall.
- **Actioning**: Turning retrieved memory into explicit recommendations or hints (not hidden injection); linking memory to action cards, queue items, or project recommendations so the operator sees “why” this was suggested.
- **Explanation**: Which memory changed the recommendation; prior similar case influence; when memory was ignored due to low confidence; link memory to action.
- **Mission control visibility**: Memory-backed recommendation count, weak-memory caution count, top retrieved prior case, most influential memory-backed suggestion, next recommended memory review.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/memory_intelligence/__init__.py` — Exports. |
| Create | `src/workflow_dataset/memory_intelligence/models.py` — RetrievalGroundedRecommendation, RetrievedPriorCase, DecisionRationaleRecall, MemoryBackedNextStepSuggestion, MemoryBackedOperatorFlowHint, WeakMemoryCaution, MemoryToActionLinkage. |
| Create | `src/workflow_dataset/memory_intelligence/retrieval.py` — retrieve_for_context(project_id, session_id, query, limit, repo_root) using memory_substrate.retrieve_units + memory_fusion links; return list of units/snippets with confidence. |
| Create | `src/workflow_dataset/memory_intelligence/recommendations.py` — build_memory_backed_recommendations(project_id, session_id, repo_root) → list[RetrievalGroundedRecommendation]; persist for explain by id. |
| Create | `src/workflow_dataset/memory_intelligence/planner_enrichment.py` — enrich_planning_sources(sources_dict, project_id, repo_root) → add memory_context and optional prior_cases. |
| Create | `src/workflow_dataset/memory_intelligence/continuity_enrichment.py` — enrich_resume_with_memory(chain_or_card, repo_root), enrich_next_session_with_memory(rec, repo_root); additive rationale and prior_cases. |
| Create | `src/workflow_dataset/memory_intelligence/assist_enrichment.py` — memory_backed_suggestions_for_context(project_id, session_id, repo_root) → list[MemoryBackedNextStepSuggestion]; can be merged with assist queue or shown separately. |
| Create | `src/workflow_dataset/memory_intelligence/operator_context.py` — get_memory_backed_operator_context(project_id, responsibility_id, repo_root) → MemoryBackedOperatorFlowHint. |
| Create | `src/workflow_dataset/memory_intelligence/explanation.py` — explain_recommendation(rec_id), explain_prior_case_influence(rec_id), list_weak_memory_cautions(repo_root). |
| Create | `src/workflow_dataset/memory_intelligence/store.py` — save recommendation, load by id, list recent (for explain and mission control). |
| Modify | `src/workflow_dataset/planner/sources.py` — Optional call to enrich_planning_sources (or caller calls it); do not replace gather_planning_sources. |
| Modify | `src/workflow_dataset/continuity_engine/resume_flow.py` or build_resume_flow — Optionally merge memory context into ResumeCard / next-session rationale. |
| Modify | `src/workflow_dataset/cli.py` — memory-intelligence suggest, explain, prior-cases, planner-context. |
| Modify | `src/workflow_dataset/mission_control/state.py` and `report.py` — Add memory_intelligence_state block. |
| Create | `tests/test_memory_intelligence.py` — Models, retrieval, recommendations (stub), explanation, no-memory behavior. |
| Create | `docs/samples/M44_*.json` and `docs/M44I_M44L_MEMORY_INTELLIGENCE_DELIVERABLE.md`. |

## 4. Safety/risk note

- All memory influence is explicit: recommendations carry prior_cases and rationale; explanation by id is supported; weak-memory cautions are surfaced, not hidden.
- No autonomous reasoning loops: retrieval and recommendation generation are triggered by existing flows (planner gather, continuity resume, assist queue, CLI) or explicit CLI; no background memory-injection daemon.
- Trust/review boundaries unchanged: operator mode, action cards, and approval flows are not bypassed; memory-backed suggestions are additive and can be shown as “memory suggests” without auto-executing.
- Over-injection of weak memory: we will not promote low-confidence memories into high-impact recommendations; weak_memory_caution is attached and list_weak_memory_cautions is available for review.

## 5. Actioning principles

- **Grounded**: Every recommendation or hint that uses memory must reference specific retrieved units or prior cases (no “the system recalls” without traceability).
- **Explainable**: explain_recommendation(rec_id) and explain_prior_case_influence(rec_id) must return structured data showing which memory influenced what.
- **Bounded**: Limit number of prior cases and snippets per recommendation; cap retrieval top_k so product stays responsive.
- **Explicit**: If memory changed the outcome, say so in the recommendation reason or rationale; do not silently replace non-memory logic.
- **Safe under empty retrieval**: When no relevant memory is found, product behavior must remain correct (no hallucinated recall).

## 6. What this block will NOT do

- Will not rebuild planner, executor, operator mode, queue/day shell, assist engine, action cards, live workflows, learning lab, council, benchmark board, or trust/policy/approvals.
- Will not add hidden autonomous reasoning loops or silent memory injection.
- Will not replace core planner/executor logic; only enrich context and add optional memory-backed recommendations.
- Will not implement curation/forgetting policies (Pane 2); only consume retrieval and link to actions.
