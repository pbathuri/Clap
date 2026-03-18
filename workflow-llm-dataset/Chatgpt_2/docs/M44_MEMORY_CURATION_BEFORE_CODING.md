# M44E–M44H — Memory Curation + Summarization + Forgetting: Before-Coding

## 1. What memory maintenance already exists

- **memory_substrate**: `MemoryItem`, `CompressedMemoryUnit`, `MemoryRetentionState` (retention_tier: default | pinned | candidate_evict). `compress_item()`, `synthesize_units()` (merge by session + keywords). Store/retrieve via backends (SQLite, in-memory). No explicit ephemeral/durable or forgetting workflow.
- **observe/profiles**: `ObservationProfile` with `retention_global_default_days`, `retention_overrides_days`; `RetentionPolicy` (per-source days, per-source max events/day). Observation-scoped only.
- **state_durability**: `ArchivalTarget`, `CompactionRecommendation`, `CompactionPolicy`, `MaintenanceProfile`. Compaction gathers targets (background_run, automation_inbox, event_log, etc.); recommendations are operator-facing; **no archival without explicit operator action**. Read-only recommendations.
- **outcomes**: Outcome history (last 500 entries); session outcome summaries in history.
- **workflow_episodes / continuity**: WorkflowEpisode, InterruptedWorkChain, ResumeCard — no built-in summarization or retention policy.
- **session**: Session (open/closed/archived) — state only; no retention/forgetting.

So: **retention exists at observe and state_durability level; compression/synthesis exists in memory_substrate. Missing: unified curation layer, ephemeral vs durable classification, summarization rollups with provenance, forgetting candidates and review-required flow, protected memory classes, and archive-report.**

---

## 2. What is missing for true long-term memory curation

- **Ephemeral vs durable**: No explicit classification of memory as ephemeral (short-lived, can be summarized or dropped) vs durable (keep long-term, protect).
- **Summarized memory unit**: Rollup of many items/sessions with provenance; memory_substrate has CompressedMemoryUnit but no “summary of N units” with source refs.
- **Compression candidate**: Identified batch of items/units that are good to compress into one summary (repeated patterns, old session chunk).
- **Forgetting candidate**: Item/unit or batch proposed for forgetting, with reason and optional review-required flag.
- **Retention policy (curation-level)**: Short/medium/long-term and protected classes; not only observe/compaction but a single place for curation policies.
- **Review-required deletion**: Forgetting that must not happen until operator reviews (e.g. high-value or uncertain).
- **Archival state**: Archived-but-retrievable state (e.g. moved to archive store or marked archived with pointer).
- **CLI and mission control**: status, summarize, retention, forgetting-candidates, archive-report; mission control slice for growth pressure, top compression candidates, protected classes, forgetting awaiting review, next action.

---

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M44_MEMORY_CURATION_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/memory_curation/models.py` | EphemeralMemory, DurableMemory, SummarizedMemoryUnit, CompressionCandidate, ForgettingCandidate, RetentionPolicy (curation), ReviewRequiredDeletionCandidate, ArchivalState. |
| Summarization | `src/workflow_dataset/memory_curation/summarization.py` | Rollups: repeated events, session history, operator patterns, episode chains; provenance-preserving. |
| Policies | `src/workflow_dataset/memory_curation/retention.py` | Retention policy definitions (short/medium/long, protected); forgetting policy (review-required, safe-to-forget). |
| Forgetting | `src/workflow_dataset/memory_curation/forgetting.py` | Forgetting-candidate generation from retention state, age, size; review-required tagging. |
| Store | `src/workflow_dataset/memory_curation/store.py` | Persist summaries, compression/forgetting candidates, archival state under data/local/memory_curation/. |
| Report | `src/workflow_dataset/memory_curation/report.py` | status(), archive_report(), next_action. |
| CLI | `src/workflow_dataset/cli.py` | memory-curation status, summarize, retention, forgetting-candidates, archive-report. |
| Mission control | `src/workflow_dataset/mission_control/state.py` | memory_curation_state: growth pressure, top compression candidates, protected classes, forgetting awaiting review, next action. |
| Tests | `tests/test_memory_curation.py` | Summarization, retention, protected, forgetting candidate, archive, no-curation. |
| Doc | `docs/M44_MEMORY_CURATION_DELIVERABLE.md` | Files, samples, CLI, tests, gaps. |

---

## 4. Safety/risk note

- **No silent destructive deletion**: Forgetting is either policy-based (explicit short-lived class) or review-required; no hidden purge.
- **Provenance preserved**: Summaries and rollups keep source refs and unit_ids so retrieval and audit remain possible.
- **Protected classes**: Designate memory classes (e.g. corrections, approvals, trust) as protected; they are never auto-forgotten.
- **Archive ≠ delete**: Archival state is “archived but retrievable”; actual deletion only after explicit operator action on review-required candidates.

---

## 5. Curation/forgetting principles

- **Summarize before forget**: Prefer compressing repeated or old memory into durable summaries rather than deleting raw data when possible.
- **Explicit retention tiers**: Short-lived, medium-term working, long-term durable, and protected are explicit; policy drives candidate generation.
- **Review-required for uncertain or high-value**: When in doubt or when memory is high-value (e.g. linked to corrections/trust), require review before forgetting.
- **Sustainable growth**: Curation aims to keep memory useful long-term without unbounded accumulation; bloat and low-value clutter are reduced via summarization and permitted forgetting.

---

## 6. What this block will NOT do

- Rebuild memory substrate, personal graph, session/context, continuity engine, or trust/review boundaries.
- Implement hidden destructive deletion or unreviewable memory mutation.
- Replace observe retention or state_durability compaction; we add a curation layer that can use them.
- Build generic cloud retention tooling; local-first only.
- Delete protected memory without explicit override (documented and rare).
