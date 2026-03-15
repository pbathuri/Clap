# Agent runtime target architecture (M21)

OpenClaw-inspired layer model for the local-first personal agent platform. This is the **target** we evolve toward; current repo already implements subsets of each layer.

---

## Layer 1: Channel / interface

- **Purpose:** Ingress for user or system requests; no private data leaves the device by default.
- **Current:** CLI (`workflow-dataset`), operator console (home, release, pilot, trial, assist), release/pilot verify/run/demo.
- **OpenClaw idea:** Channel bindings (e.g. Feishu, Telegram). We **reject** default cloud channels; we **adopt** the idea of multiple entrypoints (CLI, console, future role-based “channels” as routing labels only).
- **To build:** Optional role/channel labels (e.g. `--role ops`) that route to the right capability pack or flow; no network channel unless explicitly opt-in.

---

## Layer 2: Agent runtime / planner

- **Purpose:** Route requests to the right capability (suggest, trial, generation, pack) and invoke LLM/model in a scoped way.
- **Current:** Single-path assist suggest, trials run, release run/demo; LLM via MLX adapter/base.
- **OpenClaw idea:** Multi-agent gateway, one LLM per agent, routing by channel/account/peer. We **adopt** routing by task/role; we **reject** loading arbitrary agents from the network.
- **To build:** Explicit **planner** that, given role/industry/workflow/task, selects: (1) which capability pack (if any), (2) which flow (suggest, trial, generate), (3) which model/config. All options are local and curated.

---

## Layer 3: Memory

- **Purpose:** Persistent state for the user: projects, routines, style, feedback, session.
- **Current:** Work graph, routines, style signals, style profiles, feedback store, trial session store, parsed artifacts.
- **OpenClaw idea:** Session store, state directory per agent. We **adopt** session/state isolation; we already have it.
- **To build:** Document “memory” as the union of graph + retrieval corpus + feedback; keep all memory local; no sync of private memory to cloud.

---

## Layer 4: Tools

- **Purpose:** Parsers, adapters, generation, bundle creation, apply preview/confirm. No untrusted tool loading.
- **Current:** Parse adapters, output adapters (ops_handoff, etc.), generation workspace, bundle creation, adoption candidate, apply preview/confirm.
- **OpenClaw idea:** Agent tools, agentToAgent. We **adopt** the concept of “tools” as fixed, curated capabilities; we **reject** dynamic loading of third-party tools from a marketplace.
- **To build:** Register tools in pack manifests (parser config, output adapters); no runtime fetch of tool code.

---

## Layer 5: Policy / approval

- **Purpose:** Enforce sandbox-only, apply confirm, adoption flow, pilot boundaries.
- **Current:** Sandbox-only, require_apply_confirm, adoption flow, pilot scope, reliability triage.
- **OpenClaw idea:** Safe merge, configurable safety. We **adopt** explicit policy; we keep our gates.
- **To build:** Formalize policy as a documented layer (e.g. policy config in pack manifest); reject any flow that bypasses approval.

---

## Layer 6: Execution / sandbox

- **Purpose:** Run generation and writes only in sandbox; apply only after preview and confirm.
- **Current:** Generation workspace, bundle dirs, apply preview, apply confirm, rollback.
- **OpenClaw idea:** Workspace per agent. We **adopt** workspace isolation; we already have it.
- **To build:** Ensure all pack-driven execution respects sandbox and apply gates; no “run anywhere” by default.

---

## Layer 7: Capability-pack layer

- **Purpose:** Role/industry/workflow-specific packs (manifests, models, prompts, templates, eval) installed locally; future cloud distributes only signed manifests and recipes.
- **Current:** Pack manifest schema, validate-manifest, source registry, intake/ranking foundation.
- **OpenClaw idea:** N/A. This is our extension.
- **To build:** Local pack installer (install from manifest/path), packs list, integrate pack selection into planner; later: cloud registry for manifest/distribution only, no private data in cloud.

---

## Summary

| Layer | Status | Next |
|-------|--------|------|
| Channel / interface | Exists (CLI, console) | Role/channel labels for routing |
| Agent runtime / planner | Partial (single-path) | Planner that selects pack/flow by role/task |
| Memory | Exists (graph, retrieval, feedback) | Document as “memory”; keep local |
| Tools | Exists (parsers, adapters, generation) | Register in packs; no untrusted load |
| Policy / approval | Exists (sandbox, apply, pilot) | Formalize in docs and pack policy |
| Execution / sandbox | Exists (workspace, apply) | Keep; enforce in pack execution |
| Capability-pack | Foundation only | Local installer, packs list, planner integration |

All layers retain **local-first** and **privacy-first**; no cloud APIs for private runtime state.
