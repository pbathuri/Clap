# Open-source rejection criteria (M21)

If a candidate matches any of these, we **reject** for integration (or allow **reference-only** at most). No exceptions without explicit policy override and document.

---

## 1. Cloud/network as core requirement

- The repo **requires** internet or a remote service for its primary function.
- Our narrow release and pilot are **local-first**. We reject integration that makes local-only use impossible or degraded-by-default.
- **Exception:** Optional features that are clearly opt-in and documented (e.g. optional model download, optional proxy).

---

## 2. Violation of local-first or privacy-first

- Sends user-private data (work graph, suggestions, feedback, documents) to a third party **by default** or without explicit user consent.
- Requires cloud account or cloud state for core flows (setup, suggest, generate, apply).
- We reject; no integration. Reference-only for pattern study only.

---

## 3. Unsafe plugin or dependency model

- Allows arbitrary code execution from untrusted sources (e.g. “install any plugin from the internet” with no allow-list).
- Pulls in dependencies with known critical vulnerabilities or no clear maintenance.
- We reject for integration; optional wrapper only if sandboxed and allow-listed.

---

## 4. License incompatible or unclear

- GPL/AGPL if we cannot or do not intend to GPL this repo.
- “No commercial use” or “no distribution” that conflicts with our goals.
- No license file or unclear license → treat as reference-only until clarified.

---

## 5. Bypass of safety boundaries

- Would bypass **adoption flow** (e.g. direct write to user files without adoption candidate).
- Would bypass **apply flow** (e.g. no preview, no confirm).
- Would bypass **sandbox-only** (e.g. write outside generation/bundle dirs by default).
- We reject; no integration.

---

## 6. Unmaintained and security-sensitive

- No commits or maintainer response for >2 years **and** the component would handle sensitive data or network.
- Known unpatched CVEs in the dependency tree.
- Reject for integration; reference-only at most.

---

## 7. Model zoo or unbounded dependency

- Would turn this repo into a generic “model zoo” or launcher for arbitrary external models without curation.
- Adds heavy or recursive dependencies that we cannot audit.
- We reject for core path; optional wrapper with strict allow-list only.

---

## 8. Identity unresolved

- Candidate name (e.g. “OpenClaw”, “MiroFish”) does not map to a single canonical repo/URL.
- We do **not** guess. Mark as unresolved; adoption = **reference_only** until exact identity is recorded.

---

## Summary

| Criterion                    | Action        |
|-----------------------------|---------------|
| Cloud/network core          | Reject        |
| Privacy/local-first violation | Reject      |
| Unsafe plugin model         | Reject        |
| License incompatible        | Reject        |
| Bypass safety boundaries    | Reject        |
| Unmaintained + security     | Reject        |
| Model zoo / unbounded deps  | Reject        |
| Identity unresolved         | Reference-only |

All intake must pass policy (OPEN_SOURCE_ADOPTION_POLICY.md) and this rejection checklist before any code integration.
