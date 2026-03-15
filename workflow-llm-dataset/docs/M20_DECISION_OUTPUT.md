# M20 decision output (narrow private pilot expansion + reliability hardening)

Evidence-based answers to the five decision questions. Update after pilot sessions and feedback.

---

## 1. Is the product ready for a narrow private pilot?

**Yes, with the M20 hardening.** The narrow release (Operations reporting assistant) now has:

- **Pilot scope** defined (docs/PILOT_SCOPE.md): ops/reporting only; 2–5 users; exact task set and exclusions.
- **Reliability triage** (docs/RELIABILITY_TRIAGE.md, data/local/pilot/reliability_issues.json): must-fix items addressed (release verify blocks when graph/setup missing; fallback to base model with degraded notice).
- **Pilot health commands:** `pilot verify` (exit 1 if blocking), `pilot status`, `pilot latest-report`.
- **Recovery/degraded behavior:** No adapter → base model with explicit notice; retrieval failure does not block run/demo.
- **Pilot operator guide** and **pilot readiness report** for inspectable readiness.

**Caveat:** Run `workflow-dataset pilot verify` before each pilot session. If it exits 1, fix blocking issues (graph, setup) before adding users.

---

## 2. What exact user profile should be included first?

- **Role:** One person who does recurring reporting or status work (ops/office lead).
- **Context:** Single device; local-first; willing to run one-time setup (scan, parse, graph) and then use suggestions and generated scaffolds.
- **Expectation:** Narrow, suggest-only tool; no production SLA or full automation.
- **Not:** Multi-user, stakeholder demo requiring polish, or users with no ops/reporting context.

See **docs/PILOT_SCOPE.md** for the full profile.

---

## 3. What exact task boundaries should be enforced?

**In scope:**

- ops_summarize_reporting
- ops_scaffold_status
- ops_next_steps
- release_demo (3 prompts)

**Excluded:** Spreadsheet-heavy workflows, creative/design, finance automation, founder handoff as primary, multi-user, cloud, automated execution. Per **docs/NOT_YET_SUPPORTED.md** and **docs/PILOT_SCOPE.md**.

**Enforcement:** Operator guide and pilot scope doc; do not add out-of-scope tasks to the pilot task set or demo.

---

## 4. What failures still block pilot expansion?

From **docs/RELIABILITY_TRIAGE.md** and **data/local/pilot/reliability_issues.json**:

- **Addressed in M20:** Missing graph with no clear message (verify now blocks and lists it); adapter resolution with no fallback (fallback to base + notice); release verify exiting 0 when critical path broken (now exit 1).
- **Acceptable with warning:** No adapter (degraded mode); retrieval unavailable; empty suggestions; generic outputs. Documented; do not block pilot.
- **Post-pilot:** Latest-run edge cases, retrieval tuning, bundle/adoption classification. Do not block narrow pilot.

**Ongoing:** If a pilot user repeatedly hits a new blocker (e.g. config load failure on their machine), add to triage and fix before adding more users.

---

## 5. What should the next milestone after M20 be?

**M21 — Pilot execution and iteration**

- **Execute** the narrow private pilot with 2–5 users per PILOT_SCOPE.
- **Collect** structured feedback via existing trial commands and aggregate reports.
- **Iterate** on reliability and UX from pilot feedback (no scope creep).
- **Decide** after pilot: continue pilot with more users, refine and re-pilot, or prepare for a slightly broader (still private) pilot — all within ops reporting scope.

Do not broaden product scope in M21; focus on pilot execution and evidence-based iteration.
