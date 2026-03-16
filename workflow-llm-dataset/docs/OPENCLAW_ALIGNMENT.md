# OpenClaw alignment (M21)

OpenClaw is adopted as the **top-level architectural reference** for the local agent runtime. We do not clone or vendor OpenClaw; we align our layer model and safety boundaries with its concepts where they support local-first, privacy-first operation.

---

## What we adopt from OpenClaw

- **Layer separation:** Channel/interface → agent runtime/planner → memory → tools → policy/approval → execution/sandbox. We map our existing components into this stack and fill gaps with explicit “to build” items.
- **Local-first agent runtime:** Agents can run locally with optional channel bindings. We keep all user-private state and execution local; channels (if any) are opt-in and do not send private data by default.
- **Multi-agent / routing concepts:** Deterministic routing of requests to the right “agent” or capability (e.g. by task type, role, workflow). We implement this as routing over our existing suggest/trial/release/pilot flows and future capability packs, not as untrusted third-party skills.
- **Session and state isolation:** Each logical agent or flow has its own session/state scope. We already have session/store concepts; we align naming and boundaries with this idea.
- **Workspace and config per scope:** SOUL.md/AGENTS.md-style configuration per agent/scope is a useful pattern. We can adopt “pack manifest + config per capability” without importing OpenClaw code.

---

## What we explicitly reject

- **Untrusted skill/marketplace:** We do not load or execute third-party skills from an open marketplace. Capability packs are curated and signed; installation is explicit and local.
- **Default cloud channel binding:** We do not bind user-private data to Feishu, WhatsApp, Telegram, Discord, or any external channel by default. Any channel integration is opt-in and documented.
- **Bypassing approval gates:** Our adoption flow, apply flow, and sandbox/confirm gates are non-negotiable. OpenClaw patterns that would auto-execute on user data without approval are not adopted.
- **Third-party code execution by default:** We do not run arbitrary code from external repos inside our runtime. We wrap or reimplement with clear boundaries.

---

## Current repo mapping to OpenClaw-inspired layers

| Layer | OpenClaw concept | Current repo implementation | Gap / next |
|-------|------------------|-----------------------------|------------|
| Channel / interface | Incoming requests, channel bindings | CLI, operator console, release/pilot entrypoints | Optional future: role-based “channels” (e.g. ops vs creative) as routing only |
| Agent runtime / planner | Multi-agent gateway, routing, LLM per agent | Single-path assist/suggest, trials, release run/demo; LLM verify/train/demo | Explicit planner/routing layer that selects capability pack or flow by role/task |
| Memory | Session store, state directory | Work graph, routines, style signals, feedback store, session store | Align naming; add “memory” as first-class doc concept for graph + retrieval |
| Tools | Agent tools, agentToAgent | Parsers, adapters, generation, bundle creation | Document as “tools”; no untrusted tool loading |
| Policy / approval | Safe merge, configurable safety | Sandbox-only, apply confirm, pilot boundaries, adoption flow | Keep and harden; add explicit policy layer doc |
| Execution / sandbox | Workspace, execution isolation | Generation workspace, bundle dirs, apply preview/confirm | Keep; document as execution/sandbox layer |
| Capability-pack layer | N/A in OpenClaw | Our capability packs (manifests, installer, role/industry tags) | Build local installer and pack registry foundation |

---

## Reference links

- OpenClaw main: https://github.com/openclaw/openclaw  
- OpenClaw multi-agent docs: https://clawdocs.org/guides/multi-agent/  
- We use these as **reference only**; no direct dependency or vendoring.

---

## Next steps

1. Implement **AGENT_RUNTIME_TARGET_ARCHITECTURE.md** with the same layer model and “to build” list.
2. Add a **routing/planner** concept that selects flow or pack by role/task (without executing untrusted code).
3. Keep **capability-pack** design aligned with local install and signed manifests; no open marketplace.
