# Multi-pack runtime model (M24)

How multiple capability packs coexist in one local-first runtime. Explicit and predictable; no silent ambiguity.

---

## Pack categories

| Category | Description | Resolution weight |
|----------|--------------|-------------------|
| **primary role pack** | One pack designated as the main role pack (e.g. ops_reporting_pack for role=ops). | Highest for role-scoped resolution. |
| **secondary workflow pack** | Additional packs that add workflows/tasks without replacing the primary. | Included when tags match; merge rules apply. |
| **temporary task/project pack** | Pack pinned for a session, project, or task. | Overrides primary for the pinned scope when set. |
| **support pack** | Optional add-on (e.g. retrieval profile, parser profile). | Merged with primary/secondary; no template takeover. |
| **experimental pack** | Not used in release/pilot; for tryout only. | Excluded from resolution unless explicitly pinned. |

---

## Resolution scope

Resolution can be driven by:

- **role scope** — e.g. `ops`, `founder`. Primary pack for that role wins template selection for release/trials.
- **workflow scope** — e.g. `reporting`, `scaffold_status`. Packs matching workflow contribute templates/adapters.
- **task scope** — e.g. `summarize`, `next_steps`. Task-specific pins can override.
- **project scope** — (future) project id; pinned pack for project.
- **session scope** — current session; pinned pack for session overrides default role pack for that session.

---

## Activation modes

| Mode | Meaning |
|------|--------|
| **installed** | Pack is in installed_state.json; available for resolution. |
| **enabled** | Not suspended; included when tags match. |
| **active** | Currently participating in resolution (primary or matching secondary). |
| **preferred** | Designated primary for a role (stored in activation state). |
| **pinned** | Forced active for a scope (session/project/task) regardless of role. |
| **suspended** | Excluded from resolution until resumed. |

---

## Selection modes

| Mode | Description |
|------|-------------|
| **automatic resolution** | Role/workflow/task filters + primary + pinned → active set. Merge/precedence rules produce final capabilities. |
| **user-selected role mode** | User set active role (e.g. via `runtime switch-role ops`); primary pack for that role is used. |
| **project/session-pinned mode** | A pack is pinned for session/project/task; it wins for that scope. |
| **conflict-blocked mode** | Incompatible or blocked conflicts detected; resolution reports conflicts and may degrade to primary-only or safe subset. |

---

## State files (local)

- **installed_state.json** — pack_id → { path, version, installed_utc }.
- **active_role.txt** — (M23) current role for “no --role” flows; kept for backward compatibility.
- **activation_state.json** (M24) — primary_pack_id, secondary_pack_ids[], pinned { scope: pack_id }, suspended_pack_ids[], current_role, current_workflow, current_task.

---

## Rule summary

1. At most one **primary role pack** per role; primary wins template selection for that role when no pin overrides.
2. **Pinned** pack for session/project/task overrides primary for that scope.
3. **Suspended** packs are never active.
4. **Conflicts** are detected and reported; precedence and merge rules are applied; blocked conflicts prevent ambiguous activation.
5. **Safety** constraints merge conservatively (stricter wins); network/proxy cannot be enabled by a pack when a stricter pack is active.
