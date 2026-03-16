# Capability packs (M21 foundation)

Future pack system for local and (optionally) cloud-distributed capability packs. This doc defines the **idea** and scope; full marketplace is out of scope for M21.

---

## What is a capability pack?

A **capability pack** is a curated, versioned bundle that extends the product with:

- **Recommended local model(s)** — e.g. adapter path, base model id, quantization
- **Prompts** — prompt templates or prompt-pack references
- **Retrieval config** — corpus filters, top_k, context formatting
- **Parser config** — document/tabular/creative adapter settings
- **Workflow templates** — trial scenarios or release task sets
- **Evaluation tasks** — tasks and criteria for pack quality
- **Safety policies** — sandbox-only, apply confirm, no network by default
- **Optional orchestration settings** — e.g. multi-step flow config (future)
- **Supported output adapters** — ops_handoff, document, etc.
- **Supported release/pilot modes** — baseline, adapter, retrieval, adapter_retrieval

Packs are **local-first**: they can be installed from a local path or (future) from a curated registry. They do **not** bypass safety boundaries (adoption flow, apply confirm, sandbox-only).

---

## What packs are NOT (yet)

- A public marketplace of arbitrary third-party packs.
- A way to run untrusted code inside the main process without sandbox.
- A replacement for the current narrow release/pilot scope — packs **extend** within that scope.

---

## Future distribution

- **Local install:** User points to a pack manifest (file or dir); we validate and register it.
- **Cloud-distributed packs:** Optional; curated registry only; no user-private state in registry. Pack **content** (manifests, prompts, config) may be fetched; **runtime state** stays local.
- **Role/requirement:** Packs may declare supported user role or workflow type (e.g. ops, creative) so we can filter or recommend.

---

## Relation to open-source intake

- External repos we classify as **candidate_for_pack** or **optional_wrapper** may later become the basis of a capability pack (e.g. wrap Ollama as an optional backend pack).
- All packs must satisfy OPEN_SOURCE_ADOPTION_POLICY and OPEN_SOURCE_REJECTION_CRITERIA if they bundle or depend on external code.
- See **CAPABILITY_PACK_MANIFEST.md** for the manifest schema.
