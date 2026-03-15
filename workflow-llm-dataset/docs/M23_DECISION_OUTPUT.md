# M23 — Decision output: First real role pack implementation

## 1. Is the first real role pack installable and useful?

**Yes.** The **ops_reporting_pack** is a real, installable pack:

- **Manifest:** `packs/ops_reporting_pack/manifest.json` — valid against schema and safety policy; declares role=ops, templates (ops_summarize_reporting, ops_scaffold_status, ops_next_steps), retrieval_profile (top_k: 5), output_adapters (ops_handoff).
- **Install:** `workflow-dataset packs install packs/ops_reporting_pack/manifest.json` installs to `data/local/packs/` and updates installed state.
- **Activate:** `workflow-dataset packs activate ops_reporting_pack` sets active role so `release run` (without `--role`) uses the pack’s templates and retrieval.
- **Usefulness:** When the pack is active, release run runs the same three ops trials but driven by the pack’s templates and retrieval_top_k; pilot verify and latest-report show **Active pack(s): ops_reporting_pack**. The pack is a single, inspectable unit that materially affects which tasks run and which retrieval profile is used.

## 2. Which parts of the runtime are now genuinely pack-driven?

- **Trial/task selection:** Release run uses `resolve_active_capabilities(role=...)` when `--role` is passed or when an active role is set. Resolved `cap.templates` become the trial_ids for the run (replacing the fixed list from release config when a pack is active).
- **Retrieval:** `retrieval_top_k` passed to `run_trial` comes from `cap.retrieval_profile.get("top_k", 5)` when a pack is active.
- **Pilot reporting:** `pilot_status_dict` resolves by release scope (e.g. ops) and adds `active_pack_ids` to status; `write_pilot_readiness_report` includes **Active pack(s)** in the report.
- **Runtime status:** `workflow-dataset runtime status` shows active role and, when set, the capabilities resolved for that role (packs, templates, recommended_models).
- **Lifecycle:** Install, uninstall, activate, deactivate, report are CLI commands; pack state (installed, active role) is stored under `data/local/packs/`.

## 3. Is the pack ready for narrow pilot usage?

**Yes**, for the existing narrow pilot (ops/reporting, single device, local-first):

- Safety boundaries are unchanged (sandbox_only, require_apply_confirm, no_network_default).
- The pack does not execute arbitrary code; recipe steps are declarative only.
- Release run and pilot flows work with or without the pack; with the pack they report and use it explicitly.
- Demo and evaluation report paths are documented (`docs/packs/FIRST_ROLE_PACK_DEMO.md`, `packs report ops_reporting_pack`).

## 4. What is missing before multiple packs can coexist cleanly?

- **Conflict/priority:** When multiple packs match the same role (e.g. two packs with role_tags including "ops"), resolution merges all; there is no “preferred” or “primary” pack beyond activate (which sets role, not pack_id). Defining precedence (e.g. one active pack per role, or explicit ordering) would help.
- **Pack-specific prompts:** Today the pack declares template ids; prompts are still taken from the trial registry. Pack-level prompt overrides (e.g. pack-provided prompt files) are not wired.
- **Versioning and update:** Install overwrites; there is no “update pack” flow that preserves local overrides or migrates config.
- **Discovery:** There is no in-repo or external “registry” of available packs; the first pack is shipped in-tree. A second pack (e.g. founder_ops_pack) would need a clear place and naming.

## 5. What should the next milestone be?

Recommended: **Second role pack implementation** (e.g. founder_ops_pack or a small analyst pack), with the goal of:

- Validating multi-pack coexistence (two packs installed; resolution by role selects the right one).
- Introducing a simple “preferred pack per role” or “active pack” so that when both ops_reporting_pack and founder_ops_pack exist, the operator can choose which drives release for role=ops.

Alternatives for a later milestone:

- **Pack marketplace/registry expansion:** Curated list or cloud manifest distribution (no private data); install from URL.
- **Pack-driven UI/dashboard mode:** Console or dashboard surfaces that are driven by active pack (e.g. pack-specific home widgets).
- **Model/router specialization by pack:** Recommend or select model per pack (e.g. different adapter for founder vs ops).
- **Role-pack evaluation automation:** Automated comparison runs (with vs without pack, or baseline vs adapter) and report generation.

---

## Summary

M23 delivers one real installable role pack (ops_reporting_pack), pack-driven trial selection and retrieval in release run, pack-aware pilot status and report, activate/deactivate and report CLI commands, and a documented demo and evaluation path. The pack system is real enough to be a central product mechanism for the narrow ops/reporting scope. The next step is a second pack and clean coexistence rules.
