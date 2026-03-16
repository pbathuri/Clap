# M21 decision output — OpenClaw-anchored capability intake

Blunt, evidence-based answers. Do not overstate.

---

## 1. Should OpenClaw remain reference-only, or is there a narrow part we should wrap/integrate?

**Remain reference-only.** We adopt OpenClaw as the **architectural reference** (layer model, routing concepts, session/state isolation) as documented in OPENCLAW_ALIGNMENT.md and AGENT_RUNTIME_TARGET_ARCHITECTURE.md. We do **not** clone, vendor, or depend on OpenClaw code. Reasons:

- **Safety:** OpenClaw supports channel bindings (Feishu, Telegram, etc.) and multi-agent workflows that could pull in untrusted or network-dependent paths. We explicitly reject default cloud channels and untrusted skills.
- **Control:** Our planner, memory, tools, and policy layers must stay under our control; we reimplement patterns rather than wrap their runtime.
- **Narrow scope:** Our current product is narrow release/pilot + capability intake; a full OpenClaw integration would broaden scope and dependency surface.

**Narrow part we could later consider:** If we ever add an optional “local multi-agent” mode, we could design a **minimal** wrapper that only runs in a sandbox and uses only local channels—but that is not M22; it would require explicit design and safety review.

---

## 2. Should World Monitor be used as a UI/dashboard reference, optional component, or only inspiration?

**Reference and inspiration only for now.** World Monitor (https://github.com/koala73/worldmonitor) is registered as a dashboard/UI candidate. We have not verified its license, maintenance, or whether it is local-first. Until we:

- confirm license and local-first fit,
- and decide we need a dashboard component (our current UI is the operator console),

we use it only as **reference** for UI/dashboard/data architecture ideas. We do **not** integrate it as an optional component without that verification and a clear product need. If we later add a dashboard view, we can re-evaluate as optional component or borrow-patterns.

---

## 3. Should CLIProxyAPI / CLIProxyAPIPlus be adopted as an optional mediated network/proxy layer?

**Reference-only for now; optional wrapper only after explicit design.** Both repos (CLIProxyAPI, CLIProxyAPIPlus) are registered as network_proxy candidates. Reasons to be cautious:

- **Local-first risk:** Any proxy layer can become the path for sending user-private data over the network. We must not allow that by default.
- **Opt-in and boundaries:** If we ever add an optional proxy, it must be: (1) off by default, (2) documented as “for power users / API mediation only,” (3) never used for work graph, feedback, or adoption state unless the user explicitly opts in to a documented flow.

**Recommendation:** Do **not** adopt as an optional component in M22. Keep as reference_only; in a later milestone, if we have a concrete use case (e.g. “mediate API calls for a specific integration”), we can design a narrow, gated wrapper and then reclassify one or both as optional_wrapper.

---

## 4. Is MiroFish usable, unresolved, or reject-for-now?

**Unresolved.** The registry entry uses https://github.com/666ghj/MiroFish.git. We have not verified that the repo is accessible, its license, or its maintenance. The entry is marked with unresolved_reason: “License and accessibility not verified; may be private or renamed.” Until we can resolve:

- repo is public and accessible,
- license is compatible (e.g. MIT, Apache, BSD),
- and local-first / simulation use case is clear,

we treat MiroFish as **unresolved** and **reference_only**. If we confirm the above, we can move to borrow_patterns or candidate_for_pack for simulation/workflow patterns. If the repo is private or gone, we mark reject-for-now or remove from active consideration.

---

## 5. Which candidate is the highest-value near-term addition?

**OpenClaw (as reference)** is the highest-value near-term **conceptual** addition: it anchors our agent runtime target architecture and gives us a clear layer model (channel, planner, memory, tools, policy, execution, capability-pack). That is already done in M21 via docs and registry.

**Ollama** remains the highest-value **optional integration** candidate: known URL, MIT license, local runtime. Adding it as an optional backend (behind config) would broaden model support without replacing MLX. Value is incremental and safe if kept optional.

---

## 6. Which candidate is the highest-risk?

**CLIProxyAPI / CLIProxyAPIPlus** are the highest-risk **if** integrated without strict boundaries: they are built for network/API mediation. Misuse could route user data or internal state over the network. Risk is **architectural** (slippery slope). Hence reference_only and no optional wrapper until we have a gated design.

**MiroFish** carries **identity/access risk**: if we cannot access or verify the repo, we must not depend on it. Unresolved status is the correct holding state.

---

## 7. What should M22 focus on?

Recommend **M22** focus on:

1. **OpenClaw-aligned runtime refactor (planner layer)** — Implement a small planner that, given role/workflow/task, selects which capability pack or flow to run. No OpenClaw code; our implementation aligned with AGENT_RUNTIME_TARGET_ARCHITECTURE.md.
2. **Capability-pack installer** — Local install from manifest (path or dir); register pack; `packs list` shows installed packs. No cloud yet.
3. **GitHub repo parser expansion (optional, scoped)** — If we add live discovery, keep it optional and rate-limited; use it only to refresh metadata for already-registered URLs or to propose new candidates for human review. Do not auto-ingest into training or packs.

**Do not** prioritize in M22:

- Specialist model/router layer (unless we have a clear use case).
- Safe optional proxy/network mediation (defer until we have a concrete, gated design).

---

## Exact next milestone after M21

**M22 — OpenClaw-aligned planner + local capability-pack installer**

- Implement **planner** that selects pack/flow by role/workflow/task (see AGENT_RUNTIME_TARGET_ARCHITECTURE.md Layer 2).
- Implement **local pack installer** (install from manifest path/dir, validate, register); extend `packs list` to show installed packs.
- Optionally: **resolve MiroFish** (access + license); if resolved and fit, move to borrow_patterns.
- Optionally: **Ollama optional backend** behind config flag if it fits safety policy.
- Do **not**: integrate OpenClaw code; add default cloud channels; adopt CLIProxyAPI/Plus as optional layer; build cloud pack marketplace.
