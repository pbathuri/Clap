# M44A–M44D Memory OS — READ FIRST

## 1. What memory and retrieval behavior already exists

- **Memory substrate (M43A–D):** `MemoryItem`, `CompressedMemoryUnit`, `RetrievalIntent` (query, top_k, session_id, source, semantic), SQLite/in-memory backends, `ingest()`, `retrieve_units()`, `list_sessions()`, `get_status()`. Hybrid retrieval: keyword + structured filter; no “intent” taxonomy or “scope” abstraction.
- **Memory fusion (M43E–H):** Links (memory_id ↔ project | session | episode | routine), `add_link`, `get_memory_ids_for_entity`, `get_memory_context_for_live_context`, `get_memory_context_for_continuity`, `list_weak_memories` (confidence_below, needs_review). Live context returns snippets only when links exist for that project/session; then calls substrate.retrieve. No unified “surface” or “intent” vocabulary.
- **Learning / evaluation (M43I–L):** `list_memory_slices`, `get_memory_slice_refs` (mem_exp_*, mem_cand_*, mem_corrections_recent), cursor_bridge report. Slices are logical aggregations over experiments/candidate_studio/corrections; not a retrieval surface API.
- **Workflow episodes:** Episode store, stage detection, bridge, explain. Episode is a first-class entity; memory_fusion links support entity_type=episode. No “episode memory” retrieval surface that other layers call by name.
- **Mission control:** `get_mission_control_state()` aggregates product_state, evaluation_state, development_state, incubator_state, candidate_studio, benchmark_board, vertical_packs, etc. `memory_curation.report.mission_control_slice()` provides growth pressure, compression candidates, forgetting review. No “memory OS” slice (active namespaces, retrieval surfaces in use, weak-memory warnings, recent misses, next review).
- **Trust / approvals:** Exist; not yet wired to “trusted vs weak memory” in a single OS layer.

So: **storage, links, and a few ad-hoc retrieval paths exist; there is no single memory operating layer with named surfaces, intents, scopes, explanations, or mission-control visibility.**

---

## 2. What is missing for a real memory OS layer

- **Namespace:** No explicit “memory namespace” (e.g. personal, product, learning, cursor) that other subsystems use to ask for memory in a consistent way.
- **Retrieval surfaces:** No registry of named surfaces (project, session, episode, continuity, operator, learning, cursor) that map to substrate + fusion + episodes/slices in a single API.
- **Retrieval intents:** Substrate has query/top_k/session_id/source but no intent taxonomy (recall_context, recall_similar_case, recall_blocker, recall_pattern, recall_decision_rationale, recall_review_history). Callers cannot express “why” they are asking.
- **Retrieval scope:** No explicit scope (e.g. project_id, session_id, episode_id, time_window) passed through a single retrieval API.
- **Evidence bundle / explanation:** No structured “why this memory was retrieved” (match reason, provenance, confidence, alternative near-matches, weak-memory warnings). Live context has a short explanation string only.
- **Freshness / recency / confidence markers:** Links have confidence and needs_review; units have timestamp. No unified freshness/recency/confidence on the *retrieval result* for the OS to expose.
- **Trusted vs weak memory:** Weak memories are in fusion (list_weak_memories); not elevated to a first-class distinction in a single retrieval/explain API.
- **CLI and reports:** No `memory-os` command group (status, retrieve, explain, surfaces). No mission-control section for memory OS (active namespaces, top surfaces, weak-memory count, recent misses, next recommended review).
- **Inspectability:** Retrieval is not fully traceable (retrieval_id, evidence, alternatives) in one place.

---

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|---------|
| New | `memory_os/models.py` | MemoryNamespace, RetrievalSurface, RetrievalIntentOS, RetrievalScope, MemoryEvidenceBundle, RetrievalExplanation, FreshnessMarkers, TrustedMemory / WeakMemory markers |
| New | `memory_os/surfaces.py` | Surface registry; resolve (surface, scope, intent) → substrate/fusion/episodes/slices; list_surfaces() |
| New | `memory_os/retrieval.py` | retrieve(surface, scope, intent, …) → (items, retrieval_id, explanation); delegate to surfaces + substrate/fusion |
| New | `memory_os/explain.py` | build_explanation(retrieval_id, items, evidence, confidence, near_matches, weak_warnings); format for CLI/reports |
| New | `memory_os/mission_control.py` | memory_os_slice(repo_root) for mission_control: active_namespaces, top_surfaces, weak_memory_warnings_count, recent_misses_count, next_recommended_review |
| New | `memory_os/__init__.py` | Export public API |
| Modify | `mission_control/state.py` | Add memory_os_state from memory_os.mission_control.memory_os_slice() |
| Modify | `mission_control/report.py` | Append memory OS section when memory_os_state present |
| Modify | `cli.py` | Add memory_os_group: status, retrieve, explain, surfaces |
| New | `tests/test_memory_os.py` | Surfaces list, retrieve by intent/scope, explain output, weak-memory handling, no-match/multi-match |
| New | `docs/M44_MEMORY_OS_DELIVERABLE.md` | Final deliverable (files, CLI, samples, tests, gaps) |

---

## 4. Safety/risk note

- **Local-only:** Memory OS uses existing substrate/fusion; no new network or cloud. All data from data/local/memory_substrate and data/local/memory_fusion.
- **Additive:** No replacement of session/personal/context/continuity; OS sits on top and exposes a unified retrieval/explain API. Trust/review boundaries unchanged; weak memory remains explicit (list_weak_memories, needs_review).
- **Risk:** Mission control state grows one more slice; ensure memory_os_slice() is read-only and does not pull heavy deps. Keep retrieval explanation bounded (no unbounded logging of alternatives).

---

## 5. Retrieval-surface principles

- **Surfaces are named and stable:** project, session, episode, continuity, operator, learning, cursor. Other layers call by surface name + scope + intent.
- **Intent clarifies “why”:** recall_context, recall_similar_case, recall_blocker, recall_pattern, recall_decision_rationale, recall_review_history. Enables better explanation and future routing.
- **Scope is explicit:** project_id, session_id, episode_id, time_window so retrieval is scoped and explainable.
- **Explanation is first-class:** Every retrieval returns or can be followed by an explanation (why these items, evidence, confidence, near-matches, weak-memory warnings).
- **Strong vs weak is visible:** Trusted vs weak memory is part of the model and reports; do not hide low-confidence or needs_review.

---

## 6. What this block will NOT do

- Will not rebuild memory substrate or fusion from scratch.
- Will not add cloud retrieval or external vector APIs.
- Will not blur strong vs weak memory; weak remains flagged and reviewable.
- Will not replace session/personal/context/continuity; will sit on top and delegate.
- Will not implement full semantic/vector search in this block (substrate intent.semantic remains optional for later).
- Will not optimize for polish; first-draft coherence and coverage of surfaces/intents/explain/mission-control.
