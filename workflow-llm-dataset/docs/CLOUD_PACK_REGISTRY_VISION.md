# Cloud pack registry vision (M21)

Future vision for **distribution** of capability packs. The cloud layer distributes only **signed manifests and installer recipes**; it does **not** receive or store user-private data.

---

## What the cloud layer distributes

- **Signed capability pack manifests** — versioned, signed metadata (pack_id, name, version, role/industry/workflow tags, safety policies, dependencies).
- **Manifest metadata** — recommended model ids, prompts references, retrieval/parser config references, workflow template ids, eval task ids.
- **Recommended model stacks** — e.g. “use base model X + adapter Y”; no model weights in registry, only references.
- **Installer recipes** — how to fetch or build the pack locally (e.g. “clone repo X”, “run script Y”, “download from URL Z” with checksums). Recipes are signed and versioned.
- **Workflow templates** — task sets and scenario definitions that can be imported into the local workflow trial system.
- **Eval suites** — task definitions and criteria for pack quality; no user data.
- **Parser configs** — adapter or parser configuration snippets; no user data.

---

## What stays local / on-device

- **Parsed user data** — work graph, routines, style signals, feedback, session state.
- **User memory graph** — never synced to cloud.
- **User-specific personalization** — local adapters, local retrieval corpora, user preferences.
- **Local adapters/models** — trained or fine-tuned models stay on device.
- **Execution approval gates** — apply preview/confirm, sandbox; all enforced locally.
- **Sandbox/apply safety** — no cloud override of local policy.

---

## Principles

1. **Registry is metadata and recipes only.** No user data, no private state, no execution in the cloud.
2. **Packs are signed.** Installation verifies signature; we do not run unsigned or tampered packs.
3. **Install is explicit and local.** User chooses to install a pack; we fetch manifest + recipe and run installer locally.
4. **No mandatory cloud.** The product remains usable fully offline; cloud registry is optional for discovery and updates.
5. **Role/industry/workflow tags** in manifests enable “best packs for this role” without sending role data to cloud (filtering can be client-side from a cached manifest index).

---

## Not in scope (ever)

- Cloud execution of user workflows.
- Cloud storage of user graph, feedback, or private data.
- Public marketplace of arbitrary third-party untrusted packs.
- Bypassing local approval or sandbox via cloud.

---

## Relation to M21

We **define** this vision and the pack manifest schema; we do **not** build the cloud registry or signing infrastructure in M21. We build the **local** pack installer and **local** pack list/validate so that when the cloud registry exists, clients can install from it using the same manifest and safety checks.
