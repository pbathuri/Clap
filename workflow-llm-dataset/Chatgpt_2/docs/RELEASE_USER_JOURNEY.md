# Release user journey — Operations reporting assistant (v1)

Concrete, minimal steps for the first narrow release. The user should know what to do next at every step.

---

## 1. Onboarding / setup

- **Goal:** One-time setup so the system has local memory (graph, parsed artifacts, style signals).
- **Commands / UI:**
  - `workflow-dataset setup init --config configs/settings.yaml` (if not already done)
  - `workflow-dataset setup run` (or equivalent) to run scan and parsing
- **Outcome:** Session exists; parsed artifacts and style signals under setup dirs; graph has projects/nodes.
- **Check:** `workflow-dataset release verify` includes setup check.

---

## 2. Parse / build local memory

- **Goal:** Ensure graph and style profiles are up to date (often done as part of setup run).
- **Commands:** Setup run above; optionally `workflow-dataset assist suggest` to refresh suggestions and persist to graph.
- **Outcome:** Graph and style profiles reflect current projects and patterns.

---

## 3. Suggest / retrieve / explain

- **Goal:** Get style-aware suggestions and assistant explanations (workflow type, reporting summary, next steps).
- **Commands / UI:**
  - **Console:** Operator console → Suggestions (2) or Chat (8) or LLM status (L) then demo-suite from CLI.
  - **CLI:** `workflow-dataset assist suggest` (suggestions); `workflow-dataset llm demo-suite` (curated prompts); `workflow-dataset llm demo --prompt "Summarize this user's workflow style."` (single prompt).
- **Retrieval:** Use `--retrieval` with demo/demo-suite for corpus-grounded answers when desired.
- **Outcome:** User sees suggestions and/or text answers about their workflow and reporting.

---

## 4. Generate / review

- **Goal:** Produce a scaffold or artifact in the sandbox (e.g. status report structure, ops handoff).
- **Commands / UI:**
  - **Console:** Generation (9) → create generation plan (e.g. style pack + prompt pack).
  - **CLI:** `workflow-dataset assist generate ...` (generation type, project/session).
- **Outcome:** Generation workspace contains manifest and generated outputs; user can inspect via `assist generate-preview` or console.

---

## 5. Bundle / package

- **Goal:** Turn generated outputs into a named bundle (e.g. ops_handoff) in the bundle store.
- **Commands / UI:**
  - **CLI:** `workflow-dataset assist bundle-create ...` with adapter type (e.g. ops_handoff) and bundle id.
  - **Console:** Apply/bundle flow to create bundle from generation or workspace.
- **Outcome:** Bundle dir under `data/local/bundles/<bundle_id>` with manifest and generated paths.

---

## 6. Adoption candidate

- **Goal:** Mark selected bundle outputs as candidate for apply (no write yet).
- **Commands / UI:**
  - **Console:** Adopt bundle → creates adoption candidate under review.
  - **CLI:** Via console or internal API: create adoption candidate from bundle/generation workspace.
- **Outcome:** Adoption candidate stored; ready for apply preview.

---

## 7. Apply preview

- **Goal:** See what would be copied where (dry-run, diff).
- **Commands / UI:**
  - `workflow-dataset assist apply-preview` (or equivalent) with adoption id / workspace.
  - **Console:** Apply (6) → preview plan.
- **Outcome:** User sees target paths and diff; no writes.

---

## 8. Apply confirmation

- **Goal:** Execute apply only after explicit user confirmation.
- **Commands / UI:**
  - **Console:** Apply (6) → confirm after reviewing preview.
  - **CLI:** Apply command with confirmation flag when supported.
- **Outcome:** Files copied to target; backups/rollback available per config.
- **Safety:** No apply without explicit confirm; sandbox-first remains default.

---

## Narrow-release shortcut

For the **first narrow release**, the minimal path is:

1. **Release verify** — `workflow-dataset release verify`
2. **Release run** — `workflow-dataset release run` (runs ops-focused flow: suggest + trial + optional demo)
3. **Release demo** — `workflow-dataset release demo` (founder demo script: prompts + outputs to show)
4. **Release package** — `workflow-dataset release package` (generate + bundle for ops, then report readiness)

See **docs/FOUNDER_DEMO_FLOW.md** for exact demo steps.
