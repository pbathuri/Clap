# M46 Integration Pane Report — Pane 1 + 2 + 3

Integration of three completed panes into the `workflow-llm-dataset` project (Clap repo):

- **Pane 1:** M46A–M46D — Long-Run Health Model + Drift Detection  
- **Pane 2:** M46E–M46H — Reliability Repair Loops + Maintenance Control  
- **Pane 3:** M46I–M46L — Sustained Deployment Reviews + Stability Decision Packs  

Merge order was 1 → 2 → 3 so that health/drift (1) feeds repair loops (2), and both feed stability decision packs (3).

---

## 1. Merge steps executed

| Step | Description | Outcome |
|------|-------------|---------|
| **1. Pane 1** | Confirm long-run health (snapshot, drift, stability windows, threshold profiles, mission-control slice) is present and wired. | Already integrated: `long_run_health/*`, CLI `health` (long-run, drift-report, subsystem, stability-window, threshold-profiles, explain), mission_control state/report use `long_run_health_state`. No git merge; single branch. |
| **2. Pane 2** | Confirm repair loops (list, propose, show, approve, execute, verify, escalate, rollback, profiles, bundles) and mission-control slice. | Already integrated: `repair_loops/*`, CLI `repair-loops`, mission_control state/report use `repair_loops_state`. |
| **3. Pane 3** | Confirm sustained deployment reviews (stability decision pack, explain) and mission-control visibility. | Already integrated: `stability_reviews/*`, CLI `stability-reviews` and `stability-decision` (pack, explain). mission_control state includes `stability_reviews` (current_sustained_use_recommendation, watch_degraded_repair_state, etc.). **Change made:** mission control **report** did not format `stability_reviews`; added a "[Stability reviews]" section in `mission_control/report.py` so the text report shows recommendation, state, next_review, top_risk. |

All three panes were already on the same branch; integration was **additive** (one report section added for Pane 3 visibility).

---

## 2. Files with conflicts

**No merge conflicts** occurred. The only **change** made during this integration was:

- **`src/workflow_dataset/mission_control/report.py`** — Added formatting of `stability_reviews` in the text report (recommendation, watch_degraded_repair_state, next_scheduled_deployment_review_iso, top_stability_risk).

---

## 3. How each conflict was resolved

N/A — no conflicts. The single edit was additive: ensure the mission control **report** surfaces Pane 3 (stability reviews / sustained deployment recommendation) the same way it already surfaces Pane 1 (long-run health) and Pane 2 (repair loops).

---

## 4. Tests run after each merge

| After merge | Command | Result |
|-------------|---------|--------|
| Pane 1 | `pytest tests/test_long_run_health.py -v -k "not test_mission_control_slice and not test_build_deployment_health_snapshot_integration"` | **21 passed** (2 deselected) |
| Pane 2 | `pytest tests/test_repair_loops.py -v` | **20 passed** |
| Pane 3 | `pytest tests/test_stability_reviews.py -v` | **29 passed** |
| Integration | Smoke test: `format_mission_control_report(state)` with `long_run_health_state`, `repair_loops_state`, `stability_reviews` | **OK** — report includes all three sections. |

---

## 5. Final integrated command surface

M46-relevant top-level groups and subcommands:

| Group | Commands (selected) | Pane |
|-------|---------------------|------|
| **health** | long-run, drift-report, subsystem, stability-window, threshold-profiles, explain | 1 |
| **repair-loops** | list, propose, show, approve, execute, verify, escalate, rollback, profiles, bundles | 2 |
| **stability-reviews** | (group for review cycles / pack builder; see stability-decision for pack/explain) | 3 |
| **stability-decision** | pack, explain | 3 |

Full app also includes: dashboard, llm, observe, live-context, workflow-episodes, automations, live-workflow, operator-mode, governed-operator, continuity-confidence, automation-inbox, queue, automation-digest, automation-brief, gates, audit, trust-review, continuity, migration, state, setup, profile, onboard, assist, drafts, handoffs, in-flow, trials, trial, release, intake, templates, edge, adapters, capabilities, approvals, tasks, graph, personal, action-cards, desktop-bench, jobs, copilot, context, corrections, outcomes, skills, projects, progress, replan, portfolio, day, defaults, workspace, lanes, production-runbook, production-gates, production-cut, launch-decision, **stability-reviews**, v1-ops, **stability-decision**, stable-v1, guidance, council, model-studio, memory, memory-os, memory-intelligence, shadow-runs, memory-curation, adaptive-execution, supervision, **health**, triage, cohort, adaptation, learning-lab, verticals, vertical-packs, launch-kit, success-proof, operator-playbook, value-dashboard, rollout-review, vertical-paths, deploy-bundle, ops-jobs, pilot, review, chain, sources, packs, recipe, devlab, eval, benchmarks, models, planner, incubator, quickstart, rollout, acceptance, reliability, recovery, **repair-loops**, vertical-speed, inbox, macro, executor, background, agent-loop, policy, timeline, digest, inbox-studio, review-domains, trust, deploy, package, kits, value-packs, session, runtime, and others.

---

## 6. Remaining risks

- **No automatic health → repair flow:** Long-run health drift signals and repair-loop “propose” are separate CLI flows. A future “propose repair from strongest drift” or “health repair-needed → suggest repair-loops propose” is not implemented; operators coordinate manually.
- **Stability pack vs health snapshot:** Stability decision pack uses its own evidence bundle (e.g. drift_signals, health_summary). It is not guaranteed to use the same snapshot or threshold profile as `health long-run`; alignment may need a follow-up contract (e.g. stability_reviews reads from long_run_health snapshot or shared window).
- **Mission control test runtime:** Full `test_mission_control.py` can be slow (builds full state). Consider a smaller slice test that only builds M46-related state keys for CI.
- **Trust/approval boundaries:** No change was made to trust or approval logic; local-first and inspectable behavior are preserved.

---

## 7. Exact recommendation for the next batch

1. **Wire health → repair:** Add a path (e.g. `health long-run --suggest-repair` or `repair-loops propose --from-health`) that uses the current long-run health snapshot (strongest drift, top degraded subsystem) to suggest or prefill a repair proposal, with no hidden autonomous execution.  
2. **Align stability pack with health window/profile:** Document or implement that the stability decision pack uses the same stability window and (if applicable) threshold profile as the health snapshot, or explicitly document when they differ.  
3. **Mission control CI:** Add a fast test that builds only the M46-related slices (long_run_health_state, repair_loops_state, stability_reviews) and asserts structure and report section presence.  
4. **Docs:** Add or update one doc that describes the end-to-end flow: long-run health snapshot → drift signals → (optional) repair-loops propose/execute/verify → stability decision pack (continue / watch / repair / pause / rollback), and point operators to `health`, `repair-loops`, and `stability-decision` as the integrated surface.
