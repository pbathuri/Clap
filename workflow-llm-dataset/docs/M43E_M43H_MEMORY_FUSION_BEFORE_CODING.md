# M43E–M43H — Product Memory Fusion + Personal Graph Wiring: Before Coding

## 1. What product memory linkage already exists

- **Personal graph** (`personal/`): Nodes (projects, routines, file_ref, etc.) and edges in SQLite; graph_store, graph_builder, graph_models (ProvenanceMarker, REL_ASSOCIATED_SESSION). No explicit “memory” node type or memory–project/session link table.
- **Live context** (`live_context/`): ActiveWorkContext with inferred_project, inferred_task_family, session_hint, project_hint; fusion uses observation events + graph_projects + graph_routines + session_hint. No memory retrieval or memory contribution to context.
- **Continuity engine** (`continuity_engine/`): ResumeCard, NextSessionRecommendation, CarryForwardItem; resume_flow uses workday state, last shutdown, carry_forward; no memory-derived context for resume or next-session.
- **Workflow episodes** (`workflow_episodes/`): Episodes, stages, linked activity; store by episode; no memory–episode links.
- **Session**: Referenced as session_hint / project_hint in live context; agent_loop has AgentSession and session_store. No memory–session link store.
- **Observe**: Events in live_context fusion; no memory layer.
- **Memory substrate**: Not present in repo; Pane 1 is building it. No `memory_substrate` or `memory` package found.

## 2. What is missing

- **Memory-to-project and memory-to-session links**: A store that records which memory entry IDs are linked to which project_id, session_id (and optionally episode_id, routine_id), so retrieval can be scoped.
- **Memory-aware live-context retrieval**: When building or explaining live context, optionally retrieve memories for the current project/session and attach as a “memory_context” or source contribution.
- **Memory-assisted continuity**: When building next-session recommendation or resume card, optionally attach memory-derived context (e.g. “last time you worked on X you had Y open” or “memories linked to this project”).
- **Weak/uncertain memory review**: A way to list memories that are low-confidence or marked needs_review so the operator can review or correct.
- **Thin adapter to memory substrate**: An interface that the fusion layer calls (retrieve, link); when the substrate is absent, use a stub that returns empty results so the rest of the product still runs.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/memory_fusion/__init__.py` — Exports. |
| Create | `src/workflow_dataset/memory_fusion/substrate.py` — MemorySubstrate interface (retrieve, store, link) + get_memory_substrate() returning stub when no substrate, or real adapter when present. |
| Create | `src/workflow_dataset/memory_fusion/links.py` — Link store (data/local/memory_fusion/links.json): add_link(memory_id, entity_type, entity_id), get_links_for_entity(entity_type, entity_id), list_memory_links(limit). |
| Create | `src/workflow_dataset/memory_fusion/live_context_integration.py` — get_memory_context_for_live_context(project_id, session_id, repo_root) → list of snippets or summary; uses substrate.retrieve + links. |
| Create | `src/workflow_dataset/memory_fusion/continuity_integration.py` — get_memory_context_for_continuity(project_id, session_id, repo_root) → dict for resume/next-session; optional merge into NextSessionRecommendation.details or similar. |
| Create | `src/workflow_dataset/memory_fusion/review.py` — list_weak_memories(repo_root, confidence_below, needs_review_only) → list of memory refs for operator review. |
| Modify | `src/workflow_dataset/cli.py` — personal memory-links (under first personal group); continuity memory-context; live-context memory-explain (extend explain or new subcommand). |
| Create | `tests/test_memory_fusion.py` — Links add/get; stub retrieve; live_context_integration and continuity_integration return structure; review empty/weak. |
| Create | `docs/samples/M43_memory_linked_project_session.json`, `M43_memory_assisted_continuity.json`. |
| Create | `docs/M43E_M43H_MEMORY_FUSION_DELIVERABLE.md`. |

## 4. Safety/risk note

- Memory fusion is read-only from the product’s perspective for this block: we add retrieval and link storage; we do not write into the personal graph, live context, or continuity stores in a way that could overwrite user data. Optional “attach memory context” to continuity recommendation is additive (e.g. extra field or rationale line).
- Link store is local (data/local/memory_fusion/). No PII in links beyond entity IDs already present in graph/session. If the substrate later stores sensitive content, retrieval and display are the substrate’s responsibility; we only pass project_id/session_id as filters.
- Weak-memory review is operator-facing only; no automatic deletion or modification of memories.

## 5. What this block will NOT do

- Will not rebuild or replace the personal graph, observe, session, live context, or learning lab.
- Will not implement the memory substrate itself (Pane 1); we consume it via an adapter interface and stub when absent.
- Will not add new observation pipelines or event schemas; we only consume existing project_id/session_id from live context and continuity.
- Will not auto-merge memory into graph nodes; we only link memory entries to entity IDs and use that for retrieval scoping.
