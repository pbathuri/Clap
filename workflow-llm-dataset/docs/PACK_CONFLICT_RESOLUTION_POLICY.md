# Pack conflict resolution policy (M24)

How conflicts between packs are classified and resolved. No silent overwrites; conflicts are reported and resolved by explicit rules.

---

## Conflict classes

| Class | Meaning | Resolution |
|-------|---------|------------|
| **harmless_overlap** | Two packs declare the same template or adapter; both can be active; merge (dedupe). | Merge lists; first/primary wins for single-value. |
| **mergeable** | Different values but semantically mergeable (e.g. retrieval top_k: 5 vs 10 → use primary or max). | Precedence rule: primary wins; or merge (e.g. union for adapters). |
| **precedence_required** | Two packs want different defaults for the same scope (e.g. default output adapter for task X). | Primary wins; or pinned pack wins for its scope. Document in explanation. |
| **incompatible** | Conflicting requirements (e.g. one pack requires network, another strict local-only). | Stricter wins; or one pack is excluded when the other is active. Report as conflict. |
| **blocked** | Activation would violate safety or policy (e.g. proxy pack when local-only pack is primary). | Block the less strict pack; report. |

---

## Per-capability rules

### Templates / trial ids

- **Overlap:** Same template in multiple packs → harmless_overlap; include once.
- **Precedence:** Primary pack’s template list defines the default set for role scope. Pinned pack can add or override for its scope.
- **Conflict:** If two packs require mutually exclusive trial sets for the same scope → precedence_required; primary wins.

### Output adapters

- **Overlap:** Same adapter in multiple packs → merge (list).
- **Precedence:** Default adapter for a task: primary pack’s first listed adapter; pinned can override for its scope.
- **Incompatible:** One pack disallows an adapter another requires → blocked; report.

### Retrieval profile

- **Mergeable:** top_k, corpus_filter: primary wins; or merge (e.g. max top_k) if documented.
- **Precedence:** Different top_k → primary wins unless pinned overrides.

### Safety constraints

- **Merge:** Always merge conservatively. Stricter wins (e.g. no_network + allow_network → no_network).
- **Incompatible:** If one pack weakens safety (e.g. sandbox_only: false), validation already rejects at install. At resolution, if somehow both present, stricter wins.

### Optional wrappers / network

- **Blocked:** A pack that enables proxy/network cannot be active when the primary or another active pack is strict local-only. Report as blocked.

---

## Reporting

- **conflict_report.md** — List all detected conflicts, class, and how they were resolved (or that they are blocked).
- **packs conflicts** CLI — Same information in terminal.
- **packs explain** — Include conflict summary when explaining resolution.
