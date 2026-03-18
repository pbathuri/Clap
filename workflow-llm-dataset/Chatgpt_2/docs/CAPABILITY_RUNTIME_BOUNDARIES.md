# Capability runtime boundaries (M22)

Hard boundaries for the pack-installable runtime. No exception without explicit policy change and documentation.

---

## 1. Local-first / privacy-first

- **User data** (work graph, routines, feedback, session, parsed artifacts) never leaves the device unless the user explicitly opts in to a documented flow.
- **Pack install** and **pack resolution** use only local state and local manifest/config. No cloud API calls for private runtime data.
- **Future cloud** distributes only signed manifests and installer recipes; cloud does not receive or store user data.

---

## 2. No arbitrary code execution

- **Pack install** must not run arbitrary scripts or binaries from the pack unless the recipe is a declared, allow-listed step type (e.g. "create_config", "register_templates") executed by our code.
- **Recipe steps** are declarative: create local config, register templates/prompts, declare model recommendation, add local references. We do **not** support "run_shell" or "execute_script" in recipes in M22.
- **Optional wrappers** around external frameworks (e.g. Ollama) are explicit code paths in our repo, not dynamically loaded from a pack.

---

## 3. Sandbox and apply gates

- **Generation and bundles** go only to sandbox dirs (generation workspace, bundle root). No write to user's real project paths except via **apply** with preview and explicit confirm.
- **Packs** cannot override sandbox_only or require_apply_confirm to false. Validation rejects such manifests.
- **Adoption flow** (candidate -> preview -> confirm) is unchanged; packs only register adapters/templates, they do not bypass the flow.

---

## 4. Release and pilot scope

- **Current narrow release** (ops reporting assistant) and **pilot** (verify, status, latest-report) behavior is preserved. Pack installation extends capabilities within the same safety boundaries; it does not replace or bypass release/pilot.
- **Role/workflow/task** selection (e.g. --role ops) selects which pack(s) and flow are active; it does not enable out-of-scope features (e.g. cloud channels, untrusted skills) that are already rejected.

---

## 5. Pack provenance and approval

- **Only approved sources** (from capability intake registry) can be referenced in pack manifests (e.g. source_repo, optional_wrappers). Adoption decision must be reference_only, borrow_patterns, optional_wrapper, or candidate_for_pack—not reject.
- **Provenance** (pack_id, version, source_repo, license) is stored with every installed pack and is inspectable via packs show and runtime status.

---

## 6. Optional wrappers

- **Optional wrappers** (e.g. Ollama backend) are off by default and behind config. They do not receive user-private data unless the user has explicitly opted in to a documented use (e.g. "use Ollama for inference" with model running locally).
- **Proxy/network** wrappers (CLIProxyAPI, etc.) remain reference-only per M21; no optional proxy layer in M22 runtime unless explicitly added later with gated design.

---

## Summary

- Local-first and privacy-first are non-negotiable.
- No arbitrary code execution in pack install; recipes are declarative.
- Sandbox and apply gates cannot be disabled by packs.
- Release/pilot behavior is preserved; packs extend within boundaries.
- Pack provenance and approval are required; optional wrappers are gated and off by default.
