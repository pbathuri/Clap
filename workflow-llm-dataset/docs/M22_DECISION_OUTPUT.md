# M22 — Decision output: OpenClaw-aligned runtime refactor + capability-pack installer

## 1. Has the repo now become a real pack-installable runtime?

**Yes, for the local-first scope of M22.** The repo now has:

- A **concrete runtime layer model** (docs/RUNTIME_LAYER_MODEL.md, docs/CAPABILITY_RUNTIME_BOUNDARIES.md) mapping interface, planner, memory, tools, policy, and pack layers to current code.
- A **real local capability-pack installer**: install, uninstall, list, validate, resolve. Installed state is stored under `data/local/packs/`; manifests are validated (schema + safety policies + declarative recipes only).
- **Pack-aware resolution**: given role/industry/workflow/task (or none), the runtime resolves active packs and merged config (prompts, templates, output adapters, recommended models, retrieval profile, safety restrictions).
- **CLI**: `workflow-dataset packs list|show|install|uninstall|validate|resolve` and `workflow-dataset runtime status|show-active-capabilities|explain-resolution`.
- **Console**: Runtime screen (X) shows installed packs and active capabilities.

What is **not** yet done: cloud pack registry, signed manifest distribution, or automatic updates. Those are out of scope for M22 and remain future work.

---

## 2. Which approved external sources actually influence the runtime?

- **OpenClaw**: Influences **design only** — runtime layer model and docs. No imported code; reference metadata in `external_wrappers/openclaw_runtime_reference.py`.
- **World Monitor, CLIProxyAPI/Plus, MiroFish**: Reference-only; documented in `external_wrappers/` with approved patterns and rejected/unsafe items. No code imported.
- **Ollama** (optional_wrapper in M21): Not wired into the pack installer in M22; optional wrapper foundation is in place so a future pack can declare `optional_wrappers: ["ollama_ref"]` and we can gate usage in code. No arbitrary execution.

So **no external repo code is executed at runtime**; only our own runtime and pack logic runs. External influence is documentation and reference metadata.

---

## 3. What still remains reference-only?

All of: OpenClaw, World Monitor, CLIProxyAPI/Plus, MiroFish. They remain reference-only — no live integration, no imports from those repos. Only Ollama was approved as optional_wrapper in M21, and in M22 we do not yet invoke it from the pack layer; that would be a follow-up (e.g. “use Ollama for inference” gated by config).

---

## 4. Which pack type should be built first as a real installable pack?

**Ops reporting pack.** The current narrow release is an “ops reporting assistant”; the first real installable pack should be an **ops role pack** that:

- Declares `role_tags: ["ops"]`, `workflow_tags: ["reporting"]`, `task_tags: ["summarize", "scaffold", "next_steps"]`.
- Registers prompts/templates and output adapters (e.g. ops_handoff) already used by release/pilot.
- Ships a manifest + declarative recipe (create_config, register_templates) and no scripts.
- Can be installed via `packs install <path>` and resolved with `--role ops` for release/pilot flows.

Building this pack validates the installer and resolver end-to-end and keeps the product scope unchanged.

---

## 5. Biggest remaining gap before a true role-based install flow works end-to-end

**Planner/orchestration does not yet consume resolved capabilities.** We have:

- Installed packs and resolution (active packs, prompts, templates, adapters, models, retrieval, safety).
- CLI and console that **show** installed packs and active capabilities.

We do **not** yet have:

- Release run / pilot verify / trial run **reading** `resolve_active_capabilities(role=..., industry=...)` and **using** the returned prompts, templates, output adapters, and retrieval profile to drive the actual flow.

So the gap is: **wire the planner (release, pilot, trials) to the resolver output** so that “role=ops” not only shows the right capabilities but also runs the ops pack’s prompts, templates, and adapters. That is the logical next step after M22.

---

## 6. Exact next milestone after M22

**M23 — Planner integration with resolved capabilities**

- Inputs: role (and optionally industry/workflow/task) from CLI/console or release config.
- Flow: Call `resolve_active_capabilities(role=..., packs_dir=...)`; pass `ActiveCapabilities` (prompts, templates, output_adapters, recommended_models, retrieval_profile) into the existing release/pilot/trial execution paths.
- Outcome: Running release run or pilot verify with `--role ops` (or configured role) uses the resolved ops pack’s prompts, templates, and adapters instead of a single hard-coded path.
- Constraints: Same as M22 — no cloud APIs for private data, no arbitrary code execution, sandbox and apply gates unchanged.

After M23, the repo will have a true end-to-end role-based install flow: install ops pack → set role=ops → run release/pilot using that pack’s capabilities.

---

## Example pack manifest

See `docs/examples/ops_pack_manifest.example.json` for a full example. Minimal fields:

- `pack_id`, `name`, `version` (required)
- `role_tags`, `industry_tags`, `workflow_tags`, `task_tags` (for resolution)
- `recommended_models`, `output_adapters`, `templates`
- `safety_policies`: must have `sandbox_only`, `require_apply_confirm`, `no_network_default` not false
- `recipe_steps`: only allowed types e.g. `create_config`, `register_templates`, `register_prompts`

Install: `workflow-dataset packs install docs/examples/ops_pack_manifest.example.json`  
Resolve: `workflow-dataset packs resolve --role ops` or `workflow-dataset runtime show-active-capabilities --role ops`
