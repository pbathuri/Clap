# Role switch and capability resolution (M24)

How the runtime decides which pack(s) are active and how the user switches role/context.

---

## Resolution flow

1. **Load activation state** — primary_pack_id, secondary_pack_ids, pinned, suspended.
2. **Apply scope** — role (from CLI, active_role, or activation_state.current_role), optional workflow, task.
3. **Pinned override** — If a pack is pinned for current session/project/task, include it and give it precedence for that scope.
4. **Primary** — If role is set and primary_pack_id is set for that role (or primary_pack_id’s manifest has matching role_tags), include primary pack.
5. **Matching secondaries** — Include installed, non-suspended packs whose role/workflow/task tags match; exclude any that are blocked by conflict policy.
6. **Merge** — Apply merge/precedence rules: primary’s templates win for role scope; safety merge (stricter wins); retrieval_profile from primary unless pinned overrides; output_adapters merged with precedence.
7. **Output** — ActiveCapabilities + resolution explanation (why these packs, why these templates).

---

## Role switch

- **switch-role &lt;role_tag&gt;** — Set current role to role_tag. Primary pack for that role (if any) becomes the main driver for template selection. Stored in activation_state.current_role and active_role.txt (backward compat).
- **clear-context** — Clear current role/workflow/task and pins (or just role/workflow/task; pins are cleared via unpin). Resolution falls back to “all installed” or config default.

---

## Context switch

- **switch-context --workflow W --task T** — Set current_workflow and current_task in activation state. Resolution uses these as additional filters so only packs matching W/T (and role) participate.
- **pin &lt;pack_id&gt; --scope session|project|task** — Force pack_id to be active for the given scope; it wins over primary for template selection in that scope.
- **unpin &lt;pack_id&gt;** — Remove pin for that pack.

---

## Inspectability

- **runtime status** — Shows primary pack, secondary packs, pinned, suspended, current role/workflow/task, active capabilities.
- **packs explain &lt;task_or_scope&gt;** — Explains which packs are active and why (e.g. “primary ops_reporting_pack for role=ops”, “founder_ops_pack pinned for session”).
- **packs conflicts** — Lists detected conflicts and their resolution (harmless, mergeable, precedence-required, blocked).
