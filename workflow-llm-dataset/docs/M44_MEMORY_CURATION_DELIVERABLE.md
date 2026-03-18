# M44E–M44H — Memory Curation Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `memory_curation_group` and commands: `status`, `summarize`, `retention`, `forgetting-candidates`, `archive-report`. |
| `src/workflow_dataset/mission_control/state.py` | Added `memory_curation_state` (and `local_sources["memory_curation_dir"]`) from `mission_control_slice()`. |
| `src/workflow_dataset/memory_curation/summarization.py` | Minor: removed unused `get_stats` import. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/memory_curation/__init__.py` | Package exports (models). |
| `src/workflow_dataset/memory_curation/models.py` | EphemeralMemory, DurableMemory, SummarizedMemoryUnit, CompressionCandidate, ForgettingCandidate, RetentionPolicyCuration, ReviewRequiredDeletionCandidate, ArchivalState; RETENTION_* constants. |
| `src/workflow_dataset/memory_curation/summarization.py` | summarize_repeated_events, summarize_session_history, summarize_operator_pattern, summarize_episode_chain; build_compression_candidates_from_sessions. |
| `src/workflow_dataset/memory_curation/retention.py` | Default policies, get_policy_by_id, get_protected_policies, retention_tier_requires_review. |
| `src/workflow_dataset/memory_curation/forgetting.py` | generate_forgetting_candidates (and ReviewRequiredDeletionCandidate list). |
| `src/workflow_dataset/memory_curation/store.py` | load/save summaries, compression candidates, forgetting candidates, review-required, archival state under `data/local/memory_curation/`. |
| `src/workflow_dataset/memory_curation/report.py` | status(), archive_report(), next_action(), mission_control_slice(). |
| `tests/test_memory_curation.py` | Focused tests for summarization, retention, protected, forgetting, store round-trip, report, mission control. |
| `docs/M44_MEMORY_CURATION_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# Status
workflow-dataset memory-curation status
workflow-dataset memory-curation status --json
workflow-dataset memory-curation status --repo /path/to/repo

# Summarization (build compression candidates; --no-dry-run to apply)
workflow-dataset memory-curation summarize
workflow-dataset memory-curation summarize --no-dry-run
workflow-dataset memory-curation summarize --json

# Retention policies
workflow-dataset memory-curation retention
workflow-dataset memory-curation retention --json

# Forgetting candidates (list; --generate to rebuild from outcome history)
workflow-dataset memory-curation forgetting-candidates
workflow-dataset memory-curation forgetting-candidates --generate
workflow-dataset memory-curation forgetting-candidates --json

# Archive report
workflow-dataset memory-curation archive-report
workflow-dataset memory-curation archive-report --json
```

## 4. Sample summary/compression output

**`workflow-dataset memory-curation summarize --json`** (after running with outcome history):

```json
{
  "candidates_found": 2,
  "new_candidates": 2,
  "dry_run": true
}
```

**SummarizedMemoryUnit** (from summarization APIs) example:

```json
{
  "summary_id": "sum_abc123",
  "summary_text": "Session rollup: 5 items from sessions ['s1']",
  "source_unit_ids": ["u1", "u2", "u3", "u4", "u5"],
  "source_session_ids": ["s1"],
  "source_kind": "session_history",
  "created_at_utc": "2025-03-16T12:00:00+00:00",
  "keyword_tags": []
}
```

## 5. Sample forgetting candidate report

**`workflow-dataset memory-curation forgetting-candidates --generate --json`** (excerpt):

```json
{
  "forgetting_candidates": [
    {
      "candidate_id": "forget_xyz",
      "unit_ids": ["s1_2024-01-01T12:00:00Z"],
      "reason": "expired_short_lived",
      "created_at_utc": "2025-03-16T12:00:00+00:00",
      "review_required": false,
      "applied": false
    },
    {
      "candidate_id": "forget_abc",
      "unit_ids": ["s2_2024-02-01T00:00:00Z"],
      "reason": "policy_medium_term",
      "created_at_utc": "2025-03-16T12:00:00+00:00",
      "review_required": true,
      "applied": false
    }
  ],
  "review_required": [
    {
      "candidate_id": "review_abc",
      "forgetting_candidate_id": "forget_abc",
      "unit_ids": ["s2_2024-02-01T00:00:00Z"],
      "reason": "policy_medium_term",
      "high_value_hint": false,
      "reviewed": false,
      "approved_for_forget": false
    }
  ]
}
```

## 6. Sample retention policy output

**`workflow-dataset memory-curation retention --json`**:

```json
[
  {
    "policy_id": "short_lived",
    "label": "Short-lived memory",
    "retention_tier": "short_lived",
    "max_age_days": 7,
    "max_units_per_source": 0,
    "protected": false,
    "description": "Ephemeral; eligible for summarization or permitted forgetting after 7 days."
  },
  {
    "policy_id": "medium_term",
    "label": "Medium-term working memory",
    "retention_tier": "medium_term",
    "max_age_days": 30,
    "max_units_per_source": 500,
    "protected": false,
    "description": "Working memory; can be summarized or forgotten after 30 days or when over 500 units per source."
  },
  {
    "policy_id": "long_term",
    "label": "Long-term durable memory",
    "retention_tier": "long_term",
    "max_age_days": 0,
    "max_units_per_source": 0,
    "protected": false,
    "description": "Durable; keep unless explicitly archived or reviewed for forgetting."
  },
  {
    "policy_id": "protected",
    "label": "Protected memory",
    "retention_tier": "protected",
    "max_age_days": 0,
    "max_units_per_source": 0,
    "protected": true,
    "description": "Never auto-forget (corrections, trust, approvals); review-required for any deletion."
  }
]
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_memory_curation.py -v
```

Tests cover:

- **Summarization**: summarize_repeated_events, summarize_session_history, summarize_episode_chain; build_compression_candidates_from_sessions (empty and with outcome history).
- **Retention**: get_default_policies, get_policy_by_id, get_protected_policies, retention_tier_requires_review.
- **Forgetting**: generate_forgetting_candidates for short_lived (expired), protected (not candidate), medium_term (policy + review).
- **Store**: round-trip for summaries, append_summary; forgetting and review_required; archival state.
- **Report**: status (empty), archive_report (empty), next_action (none and review_required), mission_control_slice.

## 8. Remaining gaps for later refinement

- **Apply forgetting**: CLI/API to mark forgetting candidates as applied (and optionally remove from substrate) is not implemented; only candidate generation and persistence.
- **Apply compression**: `summarize` with `--no-dry-run` appends a simple rollup summary and does not mark compression candidates as applied or evict source units from the memory substrate.
- **Memory substrate integration**: Forgetting/compression candidates are generated from outcome history as a proxy; no direct read from memory_substrate units by retention_tier yet.
- **Protected source tagging**: No automatic tagging of units as protected from trust/corrections; policies are applied by tier passed into generate_forgetting_candidates.
- **Archive write**: Archival state is stored in curation store; no actual move-to-archive (e.g. state_durability compaction) or restore-from-archive flow.
- **LLM summarization**: Rollup text is synthetic (e.g. "Session rollup: N items"); no LLM-generated summary text for compression.
- **Mission control UX**: Slice is in state dict only; no dedicated dashboard panel or alerts for growth pressure / next action.
