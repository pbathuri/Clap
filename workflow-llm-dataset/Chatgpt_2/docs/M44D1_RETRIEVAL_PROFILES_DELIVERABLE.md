# M44D.1 — Retrieval Profiles + Vertical Memory Views (Deliverable)

First-draft support for retrieval profiles, vertical-specific memory views, and clearer explanation of why one profile is preferred over another. Extends the existing Memory OS layer (M44A–M44D); no rebuild.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/memory_os/models.py` | Added `RetrievalProfile`, `VerticalMemoryView`, profile constants (`PROFILE_*`, `RETRIEVAL_PROFILE_IDS`). Extended `RetrievalExplanation` with `profile_used`, `profile_reason`. |
| `src/workflow_dataset/memory_os/retrieval.py` | `retrieve()` accepts optional `profile_id`; applies `apply_profile_filters()` (min_confidence, trusted_only, max_items); sets `explanation.profile_used` and `explanation.profile_reason`. |
| `src/workflow_dataset/memory_os/explain.py` | `build_explanation()` and `format_explanation_text()` include `profile_used` and `profile_reason` when set. |
| `src/workflow_dataset/memory_os/__init__.py` | Exported `RetrievalProfile`, `VerticalMemoryView`, profile constants, `list_profiles`, `get_profile`, `get_profile_reason`, `list_views`, `get_view`, `get_view_for_vertical`. |
| `src/workflow_dataset/cli.py` | `memory-os retrieve` has `--profile`; added `memory-os profiles` and `memory-os views`; explain command prints profile and profile_reason. |
| `tests/test_memory_os.py` | Added tests: `test_list_profiles`, `test_get_profile_and_reason`, `test_conservative_profile_filters_weak`, `test_list_views_and_get_view_for_vertical`, `test_explanation_includes_profile_reason`. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/memory_os/profiles.py` | Registry of retrieval profiles (conservative, continuity_heavy, operator_heavy, coding_heavy); `list_profiles()`, `get_profile()`, `get_profile_reason()`, `apply_profile_filters()`. |
| `src/workflow_dataset/memory_os/views.py` | Vertical memory views (project, session, learning, coding, continuity, operator); `list_views()`, `get_view()`, `get_view_for_vertical()`. |
| `docs/M44D1_RETRIEVAL_PROFILES_DELIVERABLE.md` | This deliverable. |

---

## 3. Sample retrieval profile

From `list_profiles()` → first profile `to_dict()` (conservative):

```json
{
  "profile_id": "conservative",
  "label": "Conservative",
  "description": "High-confidence only, fewer items, trusted memory only. Use when decisions must be low-risk.",
  "surface_weights": { "project": 0.5, "session": 0.5 },
  "intent_weights": { "recall_context": 1.0 },
  "min_confidence": 0.7,
  "max_items": 10,
  "trusted_only": true,
  "preference_reason": "Conservative profile prefers high-confidence, trusted-only memory and fewer items; reduces noise and weak links."
}
```

---

## 4. Sample vertical memory view

From `list_views()` → coding vertical `to_dict()`:

```json
{
  "view_id": "view_coding",
  "vertical_id": "coding",
  "label": "Coding / Cursor memory view",
  "description": "Memory for Cursor and coding workflows.",
  "surface_ids": [ "cursor", "learning", "session" ],
  "preferred_profile_id": "coding_heavy",
  "why_this_profile": "Coding vertical uses coding-heavy profile to prioritize patterns and Cursor context."
}
```

---

## 5. Exact tests run

```bash
pytest tests/test_memory_os.py -v
```

- **Existing (7):** test_list_surfaces, test_get_surface, test_retrieve_by_intent_scope_empty, test_retrieve_learning_surface, test_explain_format, test_weak_memory_handling, test_memory_os_status.
- **M44D.1 (5):** test_list_profiles, test_get_profile_and_reason, test_conservative_profile_filters_weak, test_list_views_and_get_view_for_vertical, test_explanation_includes_profile_reason.

**Total: 12 passed.**

---

## 6. Next recommended step for the pane

- **Auto-select profile from vertical:** When a caller has a vertical context (e.g. “coding”, “session”), use `get_view_for_vertical(vertical_id)` and pass `preferred_profile_id` into `memory_os_retrieve()` so retrieval and explanation automatically reflect “why this profile” for that vertical.
- **Multi-surface retrieval by view:** For a vertical, run retrieval across `view.surface_ids` (in order) and merge/dedupe with profile filters, so one “coding” or “session” call returns a single combined result with one explanation that includes the vertical’s preferred profile and reason.
- **Mission control:** Expose “current preferred profile” or “vertical → profile” in the Memory OS slice/report when a vertical is set (e.g. from workspace or mission_control context).
