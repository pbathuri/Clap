# M17 — Product decision guide

After running workflow trials (`trials run-suite`, `trials compare`, `trials report`), use the trial report and this guide to answer product questions.

## 1. What should the first narrow release focus on?

- Use **Strongest trials (avg task_completion)** in `latest_trial_report.md`.
- Focus the first release on the **domain** (ops | spreadsheet | founder | creative) that has the highest average scores and the most “completed” statuses.
- Prefer domains where **adapter** and **adapter_retrieval** both perform well, or where at least adapter is strong.

## 2. Which workflow category is strongest right now?

- From the report’s **By trial and mode** section, identify trials with:
  - `task_completion` and `style_match` consistently > 0.5
  - `completion_status: completed`
- The **domain** that appears most often in those trials is the strongest category.

## 3. Which workflow category should be deferred?

- Trials with low `task_completion`, frequent `partial`/`failed`, or where **retrieval** clearly lowers scores (see **Retrieval impact**).
- Defer those until SFT, retrieval, or prompt tuning is improved.

## 4. Is the project good enough for a first-draft internal pilot?

- **Yes** if:
  - At least one domain has multiple trials with `task_completion` ≥ 0.6 and `completion_status: completed`.
  - At least one mode (adapter or adapter_retrieval) is usable for that domain.
  - No safety regressions (safety_score remains high).
- **No** if:
  - Most results are baseline-only or failed.
  - No clear “strongest” domain.
  - Adoption-ready count is 0 and outputs are not usable as scaffolds.

## 5. Single most important next milestone after M17

- If **retrieval hurt** full adapter in trials: **M18 — Retrieval tuning** (prompt format, context length, or retrieval target).
- If **personalization is weak**: **M18 — SFT for deferred categories** (more setup/graph-derived examples).
- If **strongest category is clear**: **M18 — Narrow pilot** (scope product to that category and run internal pilot).

---

*Fill in the “Product decision” section at the bottom of `data/local/trials/latest_trial_report.md` after each trial run, using the evidence from the report.*
