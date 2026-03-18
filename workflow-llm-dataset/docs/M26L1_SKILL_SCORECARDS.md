# M26L.1 — Skill Scorecards + Pack/Goal Skill Coverage

Extension to the teaching studio: operator-readable scorecards and pack/goal coverage reports.

---

## 1. Files modified

- `src/workflow_dataset/teaching/__init__.py` — Exported `build_skill_scorecard`, `format_skill_scorecard`, `build_pack_goal_coverage_report`, `format_pack_goal_coverage_report`.
- `src/workflow_dataset/cli.py` — Added `skills scorecard` and `skills coverage` commands.

## 2. Files created

- `src/workflow_dataset/teaching/scorecard.py` — `build_skill_scorecard`, `format_skill_scorecard`, `build_pack_goal_coverage_report`, `format_pack_goal_coverage_report`.
- `docs/M26L1_SKILL_SCORECARDS.md` — This doc.

---

## 3. Sample skill scorecard

Output of `workflow-dataset skills scorecard`:

```
=== Skill scorecard ===

  [Summary] draft=2  accepted=5  rejected=1  trusted_real=2

  [Pack coverage] strong=2  weak=1
    strong: founder_ops_plus, analyst_research_plus
    weak: experimental_pack

  [Goal families under-taught] 3
    (unspecified), onboarding, compliance

  [More demonstrations needed]
    goal_families (none yet): (unspecified), onboarding, compliance
    packs (none linked yet): —
```

---

## 4. Sample pack/goal coverage report

Output of `workflow-dataset skills coverage`:

```
=== Pack / Goal skill coverage ===

  Summary: draft=2  accepted=5  trusted_real=2

  [By pack]
    analyst_research_plus  draft=0  accepted=2  trusted_real=1  coverage=strong
    founder_ops_plus  draft=1  accepted=3  trusted_real=1  coverage=strong
    experimental_pack  draft=1  accepted=0  trusted_real=0  coverage=weak

  [By goal family]
    (unspecified)  draft=1  accepted=0  trusted_real=0 under_taught
    compliance  draft=0  accepted=0  trusted_real=0 under_taught
    reporting  draft=1  accepted=4  trusted_real=2
```

---

## 5. Exact tests run

```bash
python3 -m pytest tests/test_teaching_skills.py -v
```

New tests: `test_skill_scorecard`, `test_pack_goal_coverage_report` (included in full `test_teaching_skills.py` run).

---

## 6. Next recommended step for the pane

- **Wire scorecard into mission control** — Add a one-line teaching/skills scorecard summary to the mission-control state and report (e.g. “strong_packs / weak_packs / under_taught_goals” counts), so operators see coverage at a glance without running `skills scorecard` separately.
- **Optional: known-packs gap** — Integrate with value_packs or job_packs to list “packs with no skills linked yet” (packs that exist but have zero skills in `pack_associations`), so “more demonstrations needed” can name specific packs to target.
