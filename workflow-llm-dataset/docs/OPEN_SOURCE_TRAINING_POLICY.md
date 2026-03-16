# Open-source training policy (M21)

Policy for using open-source repo content to train or improve the local agent. We do **not** implement uncontrolled repo-to-training ingestion; we define what is allowed and how.

---

## What repo content can be used as

### 1. Architecture references

- **Allowed:** Study design docs, layer diagrams, API shapes, routing patterns. No code import; reimplement or document only.
- **Example:** OpenClaw multi-agent layout → our AGENT_RUNTIME_TARGET_ARCHITECTURE.md.
- **Provenance:** Document source repo and license in docs; no runtime dependency.

### 2. Parser / tooling references

- **Allowed:** Document format specs, parser patterns, adapter interfaces. Reimplement in our codebase with attribution.
- **Not allowed:** Vendoring entire parser repos without license and safety review; loading untrusted parsers at runtime.
- **Provenance:** License must allow use; we record source in capability intake registry.

### 3. Eval / task templates

- **Allowed:** Task definitions, scenario descriptions, evaluation criteria that are role/workflow generic. We can add them to our trial or eval suite with attribution.
- **Not allowed:** Including user-private or proprietary data; using eval tasks that assume cloud or third-party APIs we do not support.
- **Provenance:** Task source and license in manifest or registry.

### 4. Training / reference material

- **Allowed:** Public-domain or permissively licensed text (e.g. docs, README, synthetic examples) that we explicitly curate for SFT or retrieval corpus. User-private data stays separate.
- **Not allowed:** Scraping arbitrary repos into training without license and curation; mixing user-private data with scraped content in the same ungoverned pipeline.
- **Provenance:** Each source must be in intake registry with license and adoption decision; training pipeline must log source ids.

---

## What cannot be used directly

- **Code execution:** We do not run code from external repos inside our runtime unless it is a reviewed, optional wrapper (e.g. optional backend).
- **Unlicensed or unclear license:** No use in training or distribution without clear permission.
- **User-private data in open-source:** We do not train on or mix user graph, feedback, or private docs with open-source content in a way that leaks or re-identifies users.
- **Uncurated scrape:** No “ingest all of GitHub” into training or retrieval; only explicitly registered and approved sources.

---

## Role / job / industry filtering

- **Intended use:** Rank and select open-source sources by role, industry, workflow type, pain point (RepoTaskFitQuery). Only approved sources (reference_only, borrow_patterns, optional_wrapper, candidate_for_pack) can contribute to:
  - capability pack content (manifests, templates, configs),
  - eval suites,
  - workflow templates,
  - role/domain knowledge priors (e.g. curated text for retrieval or SFT).
- **User-private data:** Stays local. Open-source repo signals improve **pack design** and **eval/templates**, not the raw storage of user data. User data is never sent to a repo or used to train a third-party model without explicit consent.

---

## How open-source signals improve the product

- **Capability packs:** Pack manifests can reference workflow templates, eval tasks, and parser configs inspired by or derived from ranked repos (with provenance).
- **Eval suites:** We add tasks/scenarios from approved repos to our trial/eval suite; we do not run external eval code untrusted.
- **Workflow templates:** We define templates (e.g. ops reporting, simulation) that may be informed by repo patterns; templates are first-class in our schema.
- **Role/domain priors:** Curated text from approved sources can be used to build or extend retrieval corpora or SFT data; pipeline must be auditable and source-linked.

---

## Summary

- **Use:** Architecture refs, parser/tooling refs (reimplement), eval/task templates (with attribution), curated training/reference material (licensed, registered).
- **Do not use:** Direct code execution from unvetted repos; unlicensed content; mixing user-private data with open-source without governance; uncontrolled scrape.
- **Provenance:** All sources in capability intake registry; adoption decision and license recorded; training/eval pipelines log source ids.
