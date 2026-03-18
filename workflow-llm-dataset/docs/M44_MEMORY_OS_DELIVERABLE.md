# M44A–M44D Memory OS — Deliverable

First-draft memory OS layer: models, task-aware retrieval surfaces, explanation/traceability, CLI, mission-control visibility, tests.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/mission_control/state.py` | Added `memory_os_state` via `memory_os_slice(repo_root)` and `local_sources["memory_os"]`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Memory OS]` section: surfaces count, weak_warnings, substrate_units, next_review. |
| `src/workflow_dataset/memory_os/surfaces.py` | Import `RETRIEVAL_INTENT_RECALL_PATTERN`, `RETRIEVAL_INTENT_RECALL_REVIEW_HISTORY` for LEARNING surface. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M44_MEMORY_OS_READ_FIRST.md` | Pre-coding analysis: existing behavior, gaps, file plan, safety, principles, “what this block will NOT do”. |
| `src/workflow_dataset/memory_os/models.py` | MemoryNamespace, RetrievalSurface, RetrievalIntentOS, RetrievalScope, MemoryEvidenceBundle/Item, RetrievalExplanation, FreshnessMarkers, TrustedMemoryMarker, intent/trust constants. |
| `src/workflow_dataset/memory_os/surfaces.py` | Surface registry (project, session, episode, continuity, operator, learning, cursor), list_surfaces, get_surface, resolve_scope_entity, retrieve_via_surface. |
| `src/workflow_dataset/memory_os/retrieval.py` | retrieve(surface_id, scope, intent, repo_root) → (items, retrieval_id, RetrievalExplanation). |
| `src/workflow_dataset/memory_os/explain.py` | build_explanation(), format_explanation_text(). |
| `src/workflow_dataset/memory_os/mission_control.py` | memory_os_slice(), memory_os_status(). |
| `src/workflow_dataset/memory_os/__init__.py` | Public exports. |
| `src/workflow_dataset/cli.py` | New group `memory-os` with status, retrieve, explain, surfaces, weak. |
| `tests/test_memory_os.py` | Tests: list_surfaces, get_surface, retrieve (empty/learning), explain format, weak-memory handling, memory_os_status. |
| `docs/M44_MEMORY_OS_DELIVERABLE.md` | This file. |

---

## 3. Exact CLI usage

```bash
# Status: namespaces, surfaces count, weak warnings, substrate units, next review
workflow-dataset memory-os status
workflow-dataset memory-os status --repo /path/to/repo

# List retrieval surfaces (project, session, episode, continuity, operator, learning, cursor)
workflow-dataset memory-os surfaces
workflow-dataset memory-os surfaces --repo /path/to/repo

# Retrieve by intent and scope
workflow-dataset memory-os retrieve --intent recall_context --scope project --id founder_case_alpha
workflow-dataset memory-os retrieve --intent recall_context --scope session --session-id sess_1
workflow-dataset memory-os retrieve --intent recall_context --scope learning --query "eval run" --top-k 5

# Explain a retrieval (optional id, or sample retrieve)
workflow-dataset memory-os explain
workflow-dataset memory-os explain memret_abc123

# List weak memory links (needs review / low confidence)
workflow-dataset memory-os weak
workflow-dataset memory-os weak --repo /path/to/repo
```

---

## 4. Sample retrieval surface

One surface from `list_surfaces()` → `RetrievalSurface.to_dict()`:

```json
{
  "surface_id": "project",
  "label": "Project memory",
  "description": "Memory linked to a project (entity_type=project).",
  "entity_types": ["project"],
  "supports_intents": ["recall_context", "recall_similar_case", "recall_blocker", "recall_pattern", "recall_decision_rationale", "recall_review_history"]
}
```

---

## 5. Sample memory retrieval output

From `memory_os_retrieve("session", scope, intent, repo_root=root)`:

- **items**: list of dicts, e.g. `[{"memory_id": "mu_...", "text": "...", "confidence": 0.85, "tier": "trusted", "source": "substrate"}]`
- **retrieval_id**: e.g. `memret_a1b2c3d4e5f6`
- **explanation**: `RetrievalExplanation(reason="Retrieved 2 item(s) for surface=session, intent=recall_context.", evidence_bundle=..., confidence=0.82, weak_memory_warnings=[...])`

---

## 6. Sample explanation / trace output

**Structured** (from `build_explanation(retrieval_id, explanation, include_evidence=True, include_weak=True)`):

```json
{
  "retrieval_id": "memret_abc123",
  "reason": "Retrieved 2 item(s) for surface=session, intent=recall_context.",
  "confidence": 0.82,
  "no_match_reason": "",
  "evidence": { "total_count": 2, "items": [{ "memory_id": "...", "source": "substrate", "score": 0.85, "snippet": "..." }] },
  "near_match_ids": [],
  "weak_memory_warnings": []
}
```

**Text** (from `format_explanation_text(explanation)` or CLI `memory-os explain`):

```
Reason: Retrieved 2 item(s) for surface=session, intent=recall_context.
Confidence: 0.82
Evidence: 2 item(s)
```

---

## 7. Exact tests run

```bash
pytest tests/test_memory_os.py -v
```

- `test_list_surfaces` — Surfaces include project, session, episode, continuity, operator, learning, cursor.
- `test_get_surface` — get_surface returns correct surface or None.
- `test_retrieve_by_intent_scope_empty` — Empty scope yields empty items and explanation with no_match_reason.
- `test_retrieve_learning_surface` — Learning surface returns items or empty list with valid retrieval_id and explanation.
- `test_explain_format` — build_explanation and format_explanation_text produce valid structure/text.
- `test_weak_memory_handling` — Weak links produce retrieval result and explanation can include weak_warnings.
- `test_memory_os_status` — memory_os_status returns namespaces, surfaces_count, weak_memory_warnings.

---

## 8. Remaining gaps for later refinement

- **Top surfaces in use**: Currently placeholder (first 5 surface IDs); can be driven by real retrieval counters or logs.
- **Recent retrieval misses**: Count not yet populated; needs retrieval-path instrumentation or explicit “no match” logging.
- **Near-match alternatives**: Explanation has `near_match_ids` but retrieval does not yet fill it from similarity search.
- **Freshness/recency in evidence**: FreshnessMarkers exist in models but are not yet set per evidence item.
- **Cursor surface**: Wired to fusion/substrate; Cursor-specific filters or scopes can be refined.
- **Pagination / top-k consistency**: top_k is supported; pagination and cursor-style listing not yet defined.
- **Cloud retrieval**: Out of scope; all local-first.
