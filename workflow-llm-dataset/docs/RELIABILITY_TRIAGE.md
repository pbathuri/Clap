# Reliability triage (M20)

Issues grouped by: **must-fix before pilot**, **acceptable for pilot with warning**, **post-pilot**. Based on M19 trial evidence (when available) and known failure modes from release/LLM flows.

---

## Must-fix before pilot

- **Missing graph with no clear message:** Release verify must identify "Graph missing" as blocking and tell user to run setup init + setup run. *(Hardened in release verify.)*
- **Adapter resolution failure with no fallback:** When no successful adapter exists, release run/demo must fall back to base model and print an explicit degraded-mode notice so the user knows they are not using a fine-tuned adapter. *(Hardened: fallback + notice.)*
- **Release verify exits 0 when critical path is broken:** Verify should report a non-OK status (e.g. exit 1 or clear "not ready") when graph is missing, so scripts and operators can detect failure. *(Hardened: explicit blocking check.)*

---

## Acceptable for pilot with warning

- **No adapter / baseline only:** Demo and run work with base model; operator sees "LLM adapter: missing (demo will use baseline)" and degraded notice when running. Document in pilot operator guide.
- **Retrieval unavailable or failing:** If corpus missing or retrieval fails, degrade to non-retrieval with notice; do not block demo/run.
- **Empty suggestions list:** When graph is sparse or style signals missing, suggestions may be empty; document as expected in boundary docs.
- **Generic or low-personalization outputs:** Model often generic; document "mild personalization" in NOT_YET_SUPPORTED and pilot scope.

---

## Post-pilot improvements

- **Latest-run detection edge cases:** If run_summary.json is corrupted or adapter dir is removed after write, detection may fail; improve robustness in a later pass.
- **Retrieval tuning:** So retrieval consistently helps (not hurts) on eval; keep optional for pilot.
- **Console UX:** Simplify further for non-technical pilot users; optional.
- **Bundle/adoption misclassification:** If we add more adapters, improve classification; out of scope for narrow pilot.
- **Noisy or low-quality outputs:** Improve via more SFT or data; post-pilot.

---

## Data source

Structured issues are also listed in `data/local/pilot/reliability_issues.json` for tooling and reporting. Update both this doc and the JSON when new issues are triaged.
