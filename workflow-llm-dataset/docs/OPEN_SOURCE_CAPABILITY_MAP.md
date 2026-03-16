# Open-source capability map (M21)

Maps each registered candidate to current product layers. Use for adoption decisions.

---

## Product layers (current repo)

- **Local observation layer** — file observer, event log, setup scan
- **Personal work graph layer** — work graph, routines, projects, style signals
- **Retrieval layer** — corpus, retrieval context for prompts
- **LLM/model layer** — training, adapter, inference (MLX today)
- **Workflow trial layer** — trials, scenarios, comparison, trial report
- **Release/pilot layer** — release verify/run/demo, pilot verify/status, narrow scope
- **Generation/review layer** — generation workspace, draft structures, style packs
- **Bundle/adoption/apply layer** — bundles, adoption candidates, apply preview/confirm
- **UI/console/dashboard layer** — operator console, home, pilot, release, trial views
- **Optional cloud capability-pack distribution layer** — future; not implemented

---

## OpenClaw (candidate)

- **Layers touched:** Agent orchestrator concept; release/pilot layer (if we add orchestration).
- **Overlap with repo:** Repo has no multi-agent orchestrator today; assist/suggest and trials are single-path.
- **Replace / augment / inform:** Inform only until exact repo and license verified. Could later augment with optional local orchestration patterns.
- **Strongest reason to adopt:** Local multi-agent/routing inspiration aligns with future “capability pack” orchestration.
- **Strongest reason NOT to adopt:** Unresolved identity; risk of pulling in unsafe or cloud-dependent patterns if repo is wrong.

---

## MiroFish (candidate)

- **Layers touched:** Workflow trial layer; simulation (not yet a product layer).
- **Overlap with repo:** Repo has workflow trials (M17) and scenarios; no swarm/simulation engine.
- **Replace / augment / inform:** Inform only until exact repo verified. Could inform trial scenarios or future simulation-style evaluation.
- **Strongest reason to adopt:** Simulation/swarm examples could enrich workflow trial or evaluation harness ideas.
- **Strongest reason NOT to adopt:** Unresolved identity; simulation may be out of scope for narrow ops release.

---

## CLI / intermediary proxy (candidate)

- **Layers touched:** Optional proxy layer (not in repo today).
- **Overlap with repo:** None; repo is local-first with no proxy.
- **Replace / augment / inform:** Optional wrapper only, with strict boundaries; must not become default path for user-private data.
- **Strongest reason to adopt:** Optional mediation for power users (e.g. API routing) without touching core flow.
- **Strongest reason NOT to adopt:** Network-dependent patterns weaken local-first; exact repo unknown; easy to misuse.

---

## TheWorld (candidate)

- **Layers touched:** UI/console/dashboard layer; parser.
- **Overlap with repo:** Repo has Rich-based console and views; no “TheWorld” UI.
- **Replace / augment / inform:** Inform only until exact repo verified. Could inform dashboard/parsing UX.
- **Strongest reason to adopt:** UI/UX or parsing patterns could improve operator experience.
- **Strongest reason NOT to adopt:** Unresolved identity; risk of pulling in heavy or incompatible UI stack.

---

## Ollama (reference)

- **Layers touched:** LLM/model layer.
- **Overlap with repo:** Repo uses MLX for training/inference; Ollama is alternative local runtime.
- **Replace / augment / inform:** Reference; optional future backend. Do not replace MLX by default.
- **Strongest reason to adopt:** Popular local runtime; optional wrapper could broaden model support.
- **Strongest reason NOT to adopt:** Current stack is MLX; adding Ollama is optional and must remain optional.

---

## Summary

| Candidate        | Layer(s)              | Overlap        | Recommendation   |
|-----------------|------------------------|----------------|-------------------|
| OpenClaw        | Orchestrator, pilot    | None           | Inform / reference only |
| MiroFish        | Trial, simulation      | Partial (trials) | Inform / reference only |
| Proxy candidate | Optional proxy         | None           | Reference only; optional wrapper later |
| TheWorld        | UI, parser             | Partial (console) | Inform / reference only |
| Ollama          | LLM                    | Alternative runtime | Optional wrapper; do not replace MLX |
