# Runtime layer model (M22)

Concrete layer model for the local personal-agent runtime. Aligned with OpenClaw-inspired architecture; all layers are local-first and privacy-first.

---

## 1. Interface / channel layer

- **Purpose:** Ingress for user or system requests. No private data leaves the device by default.
- **Components:** CLI (`workflow-dataset`), operator console (home, release, pilot, trial, assist, sources, packs), release/pilot verify/run/demo entrypoints.
- **Current repo:** `cli.py`, `ui/` (home_view, release_view, pilot_view, trial_friendly_view, etc.).
- **Routing:** Role/industry/workflow/task can be passed as options (e.g. `--role ops`); planner uses them to select active pack and flow. No network channel binding unless explicitly opt-in.

---

## 2. Runtime / planner layer

- **Purpose:** Agent orchestration, routing, role-capability selection, trial/release/pilot execution modes.
- **Components:** Planner (selects capability pack and flow from role/industry/workflow/task), release run/demo, trials run, assist suggest, pilot verify/status.
- **Current repo:** Release and pilot commands; trial runner; assist suggest. Planner is implemented in M22 as pack-aware resolution (which packs are active, which flow to run).
- **Resolution:** Given role, industry, workflow type, task type, and installed packs, the runtime resolves: active packs, active prompts/templates, active output adapters, recommended models, retrieval profile, safety restrictions. See `packs.pack_resolver` and `runtime status` / `runtime show-active-capabilities`.

---

## 3. Memory / retrieval layer

- **Purpose:** Personal graph, parsed artifacts, retrieval corpora, role/domain priors, capability-pack retrieval config.
- **Current repo:** Work graph (`personal/`, `graph_store`), parsed artifacts (setup, parse), style signals, feedback store, trial session store. LLM corpus and retrieval in `llm/`.
- **Pack integration:** Packs can declare `retrieval_profile` (e.g. top_k, corpus_filter); resolution merges pack config with base config. User data and priors stay local.

---

## 4. Tool / workflow layer

- **Purpose:** Parsers, generators, bundle adapters, adoption/apply flows; optional mediated proxy tools (gated).
- **Current repo:** Parse adapters, output adapters (ops_handoff, etc.), generation workspace, bundle creation, adoption candidate, apply preview/confirm, rollback.
- **Pack integration:** Packs declare `output_adapters`, `parser_profiles`; resolution enables only declared adapters. No untrusted tool loading; optional proxy remains reference-only per M21.

---

## 5. Policy / safety layer

- **Purpose:** Local-first/privacy-first, approval gating, sandbox/apply boundaries, role pack restrictions.
- **Current repo:** Sandbox-only, require_apply_confirm, adoption flow, pilot scope, reliability triage, OPEN_SOURCE_ADOPTION_POLICY, OPEN_SOURCE_REJECTION_CRITERIA.
- **Pack integration:** Every pack manifest must satisfy safety_policies (sandbox_only, require_apply_confirm, no_network_default true). Policy layer rejects any flow that bypasses approval; pack install does not execute arbitrary code.

---

## 6. Pack layer

- **Purpose:** Installed packs, manifests, pack dependencies, model recommendations, installer recipes.
- **Current repo:** Pack manifest schema in `capability_intake.pack_models`; validate-manifest CLI; M22 adds `packs/` package: pack_registry, pack_installer, pack_resolver, pack_validator, pack_state, pack_recipes.
- **State:** Installed packs stored under `data/local/packs/` (or configurable path); registry of pack_id -> manifest + install metadata. Resolver returns active packs and derived config for a given role/industry/workflow/task.

---

## Mapping summary

| Layer | Repo modules / entrypoints |
|-------|----------------------------|
| Interface | cli.py, ui/*.py, release/pilot/trial CLI |
| Runtime/planner | release run/demo, trials run, assist suggest, packs resolve, runtime status |
| Memory | personal/*, graph_store, setup, parse, llm/corpus, retrieval_context, feedback |
| Tools | parse/adapters, output adapters, generation, bundle, adoption, apply |
| Policy | Sandbox/apply gates, pilot scope, adoption policy, rejection criteria |
| Pack | packs/*, capability_intake.pack_models, data/local/packs |

All layers preserve local-first and privacy-first; no cloud APIs for private runtime state.
