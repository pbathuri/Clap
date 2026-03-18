# M24 — Decision output: Multi-pack coexistence + role switch / conflict resolution

## 1. Can multiple packs now coexist safely?

**Yes.** The runtime supports:

- **Multiple installed packs** — installed_state.json tracks all; list shows them with optional activation state (primary, pinned, suspended).
- **Primary pack** — One pack can be set as primary (activation_state.json); it wins template selection and retrieval profile for role scope.
- **Pinned pack** — A pack can be pinned for session/project/task; it wins over primary for that scope.
- **Suspended packs** — Excluded from resolution until resumed.
- **Role/workflow/task filters** — Resolution only includes packs whose tags match the current role (and optional workflow/task). So with ops_reporting_pack (role=ops) and founder_ops_pack (role=founder), `--role ops` returns only the ops pack; no silent merge of unrelated templates.
- **Conflict detection** — Conflicts are detected (templates overlap, different default adapters, retrieval top_k, optional_wrappers vs strict local) and reported via `packs conflicts` and conflict_report.md. Blocked conflicts exclude the less-strict pack when a strict local pack is primary.
- **Merge/precedence rules** — Documented in PACK_CONFLICT_RESOLUTION_POLICY.md; primary wins for role scope; safety merges conservatively; no silent overwrites.

## 2. Is role/context switching understandable and inspectable?

**Yes.**

- **switch-role &lt;role_tag&gt;** — Sets current_role (and active_role.txt for backward compat). Resolution uses this to filter packs; primary is only included if it matches the role.
- **switch-context --workflow W --task T** — Sets current_workflow and current_task; resolution filters by these as well.
- **clear-context** — Clears role, workflow, task, and all pins (primary pack unchanged).
- **runtime status** — Shows primary pack, pinned, suspended, current role, and active capabilities.
- **packs explain** — Prints resolution summary (primary, pinned, secondary, excluded, conflicts) and active packs/templates.
- **packs list --all** — Shows each pack with [primary], [pinned(scope)], [suspended] when applicable.

## 3. What kinds of conflicts are still hardest?

- **Default output adapter** — When two packs list different first adapters, we classify as precedence_required and primary wins; but we do not yet have task-level “for task X use adapter Y” so fine-grained overrides require future schema.
- **Model recommendations** — We merge recommended_models as a list; incompatible required_models (e.g. one pack requires GPU, another CPU-only) are not yet detected as incompatible; we only surface optional_wrappers vs strict local as blocked.
- **Parser profiles** — Merge is union; if two packs register incompatible parser configs for the same artifact type, that is not yet detected.
- **Multi-role overlap** — A pack with role_tags ["ops", "founder"] would match both roles; resolution would include it for both. We do not yet restrict “one primary per role” when a pack declares multiple roles.

## 4. Is the runtime now ready for a second real pack, pilot users with adjacent workflows, and future marketplace behavior?

- **Second real pack:** Yes. founder_ops_pack is added as a fixture; install both ops_reporting_pack and founder_ops_pack, set primary to one, switch-role to the other — resolution and release run behave correctly. A second real pack (e.g. analyst or creative support) can follow the same pattern.
- **Pilot users with adjacent workflows:** Yes. User can install multiple packs, set primary for their main role, pin a pack for a session when switching context, and use switch-role/switch-context to change filters. Narrow release (scope=ops) remains clear; pilot report shows active_pack_ids.
- **Future capability-pack marketplace:** The model is ready in the sense that: multiple packs install locally; conflict detection and reporting exist; precedence rules are documented. What is not yet there: signed manifests, distribution from a registry, or update/versioning flows.

## 5. Exact next milestone after M24

**M25 — Pack registry and distribution (optional)**

- Curated list of available packs (in-repo or external URL); install from URL or registry index.
- Signed manifest verification (checksum/signature in manifest); reject unsigned or tampered installs when verification is enabled.
- Pack update flow: check for newer version, install update with user confirm; preserve activation state where possible.

Alternatively, if the next priority is product depth rather than distribution:

**M25 — Pack-driven prompts and task-level overrides**

- Pack-provided prompt overrides (e.g. prompt files in pack dir) used when pack is active.
- Task-level default adapter (e.g. “for task X use adapter Y” in manifest) and precedence when multiple packs match the same task.

---

## Summary

M24 delivers multi-pack coexistence with primary, pinned, and suspended state; role and context switching (switch-role, switch-context, clear-context); conflict detection and reporting; merge/precedence rules; and a second pack fixture (founder_ops_pack). Release and pilot remain clear under multiple packs; the system is ready for a second real pack and for pilot users with adjacent workflows.
