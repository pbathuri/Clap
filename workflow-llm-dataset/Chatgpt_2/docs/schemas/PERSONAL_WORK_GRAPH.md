# Personal Work Graph Schema

## Purpose

The personal work graph is the device-local, private representation of the user’s work: profile, projects, recurring tasks, tools, collaborators, routines, workflow chains, time patterns, preferences, pain points, goals, and approval boundaries. It is built from observation and explicit teaching and is used by the agent to interpret context and propose actions.

## Entities (v1 scope)

| Entity | Description | v1 |
|--------|-------------|-----|
| **User profile / role** | Identity, self-described role(s), industry/occupation hints. | Yes |
| **Projects** | Named projects or work streams the user cares about. | Yes |
| **Recurring tasks** | Tasks that repeat (daily, weekly, or ad hoc). | Yes |
| **Files/documents touched** | References to paths or stable IDs; no content. | Yes |
| **Tools/apps used** | Applications and tools associated with the user’s work. | Yes |
| **Collaborators** | People or roles the user works with (names or labels only). | Yes |
| **Routines** | Time-based or trigger-based patterns (e.g. “morning review”). | Yes |
| **Workflow chains** | Ordered sequences of steps the user follows; can link to global workflow priors. | Yes |
| **Time/frequency patterns** | When and how often things happen; derived from observation. | Yes |
| **Priorities** | User-stated or inferred priorities. | Yes |
| **Preferences** | UI, notification, and execution preferences. | Yes |
| **Pain points** | Friction or bottlenecks the user has noted. | Yes |
| **Goals** | Short- or long-term goals. | Yes |
| **Approval boundaries** | What the agent may do without asking (e.g. read-only paths, allowed apps). | Yes |
| **Device-local memory references** | Pointers to local store (e.g. embeddings, audit log segments). | Yes |

## Fields (conceptual)

- **IDs**: Stable, device-local IDs (e.g. `user_*`, `project_*`, `routine_*`, `workflow_*`).
- **Timestamps**: Created/updated at; optional validity windows.
- **Source**: `observation` | `teaching` | `import`; links to observation event or teaching session when applicable.
- **Confidence**: Optional score for inferred nodes/edges.

Relationships are graph edges: e.g. user → projects, project → tasks, task → tools, routine → workflow_chain.

## Examples

- User profile: `role = "operations manager"`, `industry_hint = "logistics"`.
- Project: `name = "Q1 dispatch"`, `files = ["/docs/dispatch.xlsx"]`, `tools = ["Excel", "Slack"]`.
- Routine: `name = "morning review"`, `trigger = "time 09:00"`, `workflow_chain_id = "wf_abc"`.
- Approval boundary: `scope = "path"`, `path_prefix = "/Users/me/work/readonly"`, `allow = "read"`.

## Out of scope for v1

- Full graph DB with complex queries (v1 can be key-value or document per entity type).
- Cross-device graph merge (deferred).
- Cloud backup of graph (optional sync only; not required for v1).
