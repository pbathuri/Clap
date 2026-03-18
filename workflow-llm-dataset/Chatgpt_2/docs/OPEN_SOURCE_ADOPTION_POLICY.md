# Open-source adoption policy (M21)

First-class policy for when and how we adopt external repos. All intake must comply.

---

## 1. When a repo can be **reference only**

- Exact canonical URL or identity is **not confirmed**.
- We document the candidate and its possible role but do **not** clone, vendor, or depend on it.
- No code import; no submodule; no copy-paste. Study and notes only.
- **Examples:** OpenClaw, MiroFish, TheWorld, proxy candidate until exact repo is identified.

---

## 2. When code can be **studied but not imported**

- License is incompatible with our use (e.g. strict copyleft in a way we cannot satisfy), or
- Repo is high-risk (see OPEN_SOURCE_REJECTION_CRITERIA.md) but we want to learn from patterns.
- We may describe patterns, algorithms, or UX ideas in docs or tickets. We do **not** copy code into this repo without explicit decision and license clearance.
- Any “borrow patterns” must be reimplemented and attributed; no direct source dependency.

---

## 3. When **wrapping** is acceptable

- The external component can run as a **separate process or optional backend**.
- It does **not** receive user-private runtime state (work graph, suggestions, feedback) unless the user explicitly opts in and the component is local-only.
- Integration is behind a config flag or optional dependency; default path remains local-first and within this repo’s safety boundaries.
- **Examples:** Optional Ollama backend for inference; optional proxy for power users with explicit opt-in.

---

## 4. When a repo is **too risky to integrate**

- See **OPEN_SOURCE_REJECTION_CRITERIA.md**. Summary:
  - Assumes or requires cloud/network for core flow.
  - Violates local-first or privacy-first (e.g. sends private data without consent).
  - Unsafe plugin/ecosystem (arbitrary code execution, unchecked dependencies).
  - License incompatible or unclear.
  - Unmaintained and security-sensitive.
  - Would bypass adoption flow, apply flow, or sandbox-only guarantees.

---

## 5. Licenses

- **Preferred:** MIT, Apache-2.0, BSD-2/3. We may wrap or depend with clear attribution.
- **Case-by-case:** LGPL (dynamic link only; no static link of our core with LGPL without legal review).
- **Reject for integration:** GPL/AGPL (unless we explicitly decide to GPL this repo), proprietary, “no commercial use” that conflicts with our goals.
- **Unknown:** Treated as reference-only until clarified.

---

## 6. Maintenance risk

- **Active maintainer:** Prefer. We may optional-wrapper or candidate-for-pack.
- **Stale (no commits >1 year, no response to issues):** Acceptable for reference-only or borrow-patterns; avoid as hard dependency.
- **Abandoned + security-sensitive:** Reject for integration; reference-only at most.

---

## 7. Unsafe plugin ecosystems

- We do **not** allow arbitrary third-party plugins to run inside this repo’s process with user data unless:
  - The plugin is from a curated allow-list, and
  - It runs in a sandbox or with explicit user confirmation for sensitive actions.
- “Capability packs” we distribute must follow the same safety policy (no uncontrolled writes, apply with confirm, local-first).

---

## 8. Network/cloud dependence

- Repos that **assume** or **require** network/cloud for core functionality are **reject** or **reference-only** for our core path.
- Optional network (e.g. model download, optional API proxy with user opt-in) is acceptable if:
  - Default path works offline/local, and
  - No user-private state is sent without explicit consent.

---

## 9. Local-first / privacy-first

- We **reject** any integration that would:
  - Send work graph, suggestions, feedback, or adoption state to a third-party server by default.
  - Require cloud login or cloud state for core release/pilot flow.
  - Weaken sandbox-only or apply-with-confirm guarantees.
- Optional telemetry or cloud sync must be opt-in, documented, and out of scope for narrow release/pilot.

---

## 10. Adoption decision flow

1. **Identify** — Exact canonical URL and license.
2. **Classify** — Role, risk, local/cloud fit (source_risk, source_fit, repo_classifier).
3. **Policy check** — Does it violate rejection criteria? If yes → reject or reference-only.
4. **Decide** — reference_only | borrow_patterns | optional_wrapper | candidate_for_pack | core_candidate | reject.
5. **Record** — Update source_registry.json and docs (capability map, decision output).

All adoption decisions are explicit and reviewable in the registry and docs.
