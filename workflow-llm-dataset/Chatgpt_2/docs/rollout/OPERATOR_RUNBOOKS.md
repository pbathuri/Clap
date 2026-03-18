# Rollout operator runbooks (M24I.1)

First-draft runbooks for running demos, recovering from blocked states, interpreting support bundles, deciding go/no-go, and escalating or deferring when activation/provisioning/readiness fails. Local-first; no cloud dependency.

---

## 1. How to run demos

- **List demos**: `workflow-dataset rollout demos list` — shows founder_demo, analyst_demo, developer_demo, document_worker_demo.
- **Launch a guided demo (golden journey)**:
  1. From repo root: `workflow-dataset rollout launch --id founder_demo` (or analyst_demo, developer_demo, document_worker_demo).
  2. The launcher runs the acceptance scenario for that demo in report mode (no job/macro execution), saves the run, and updates rollout state.
  3. Read the printed **Outcome** (pass / partial / blocked / fail) and **Next step**.
- **If outcome is pass**: Proceed to first-user flow — e.g. `workflow-dataset inbox`, `workflow-dataset kits first-run --id founder_ops_starter`.
- **If outcome is partial or blocked**: See "How to recover from blocked rollout states" below.
- **Pre-demo check**: Run `workflow-dataset rollout readiness` to see demo-ready and first-user-ready status before presenting.

---

## 2. How to recover from blocked rollout states

When rollout status shows **blocked** or **current_stage** is not `ready_for_trial`:

1. **Inspect status**: `workflow-dataset rollout status` — note **Blocked** and **Next action**.
2. **Inspect readiness**: `workflow-dataset rollout readiness` — review **[Blocks]** and **[Operator actions]**.
3. **Common causes and actions**:
   - **Install check did not pass**: Run `workflow-dataset package readiness-report` and fix missing prerequisites (config, runtimes, etc.). Then `workflow-dataset local-deploy first-run` if applicable.
   - **Bootstrap profile missing**: Run onboarding/bootstrap so profile exists: `workflow-dataset onboarding status` and follow prompts or `workflow-dataset local-deploy first-run`.
   - **Starter kit not found or prerequisites missing**: Ensure the demo’s required pack is available: `workflow-dataset kits list` and fix any missing prereqs reported by acceptance.
   - **Acceptance outcome blocked/fail**: Re-run acceptance after fixing the above: `workflow-dataset acceptance run --id <scenario_id>` (e.g. founder_first_run). Then run `workflow-dataset rollout launch --id founder_demo` again to refresh rollout state.
4. **Re-check**: After fixes, run `workflow-dataset rollout launch --id <demo_id>` again; repeat until outcome is pass or you escalate (see escalation section).

See **Sample recovery path** below for a concrete step sequence.

---

## 3. How to interpret support bundles

- **Generate a bundle**: `workflow-dataset rollout support-bundle` (writes to `data/local/rollout/support_bundle_<timestamp>/`) or `--output /path/to/dir`.
- **What’s inside**:
  - **environment_health.json** — required/optional checks, Python version, incubator presence.
  - **runtime_mesh.json** — backends, recommended models, integrations.
  - **starter_kits.json** — kit count, recommended kit, score.
  - **latest_acceptance.json** — last acceptance run: scenario_id, outcome, ready_for_trial, reasons.
  - **trust_cockpit.json** — benchmark trust, approval registry, release gates.
  - **rollout_state.json** — target scenario, current_stage, blocked_items, next_required_action.
  - **issue_summary.txt** — human-readable issue template for handoff or triage.
- **Use**: Share the bundle directory (or its contents) with support or attach to an issue; use **issue_summary.txt** as the description body. All content is local and inspectable; no secrets should be added by the tool.

---

## 4. How to decide go/no-go

- **Readiness report**: `workflow-dataset rollout readiness` (optionally `--output data/local/rollout/readiness_report.txt`).
- **Interpret**:
  - **[Demo-ready] YES** — Safe to run a guided demo for an audience; rollout stage is ready_for_trial and latest acceptance pass.
  - **[First-user-ready] YES** — Package readiness and acceptance indicate ready for first real-user install/trial; still operate under local operator discipline (simulate-first, approvals where required).
  - **[Demo-ready] NO** or **[First-user-ready] NO** — Use **[Blocks]** and **[Operator actions]** to fix before demo or first user; or defer and escalate (see below).
- **Go**: If demo-ready and/or first-user-ready YES and no blocking items you cannot resolve locally, proceed with demo or pilot.
- **No-go**: If blocks cannot be cleared locally or critical checks fail, defer first-user rollout and follow escalation.

---

## 5. How to escalate or defer when activation/provisioning/readiness fails

When activation, provisioning, or readiness fails and cannot be resolved with the steps in "How to recover from blocked rollout states":

1. **Capture state**: Run `workflow-dataset rollout support-bundle` and `workflow-dataset rollout issues report --output <path>`. Attach the bundle directory and issue report to your escalation.
2. **Defer**: Do not run first-user or pilot sessions until blocks are resolved or escalation path returns a decision.
3. **Escalate**: Use the **Sample escalation decision tree** below to choose path (e.g. internal owner, engineering, or document-as-known-limitation and defer first-user).
4. **Document**: Note in rollout support notes (or local doc) what failed, what was tried, and who is responsible for next action. Optionally keep a short log in `data/local/rollout/` (e.g. escalation_log.txt) with date, summary, and next owner.

---

## Sample recovery path

**Scenario**: Rollout is blocked after `rollout launch --id founder_demo`; status shows "Install check did not pass" and "Bootstrap profile not yet created."

| Step | Action | Command or check |
|------|--------|-------------------|
| 1 | Check rollout status | `workflow-dataset rollout status` |
| 2 | Check readiness | `workflow-dataset rollout readiness` |
| 3 | Fix install / env | `workflow-dataset package readiness-report`; fix missing config/runtime; then `workflow-dataset local-deploy first-run` if needed |
| 4 | Ensure profile exists | `workflow-dataset onboarding status`; run bootstrap if missing |
| 5 | Re-run acceptance | `workflow-dataset acceptance run --id founder_first_run` |
| 6 | Refresh rollout state | `workflow-dataset rollout launch --id founder_demo` |
| 7 | Confirm | `workflow-dataset rollout status` → current_stage ready_for_trial; `rollout readiness` → Demo-ready YES (if applicable) |

---

## Sample escalation decision tree

```
Activation / provisioning / readiness failed?
  │
  ├─ Can you fix with package readiness-report + first-run + onboarding + re-run acceptance?
  │     YES → Follow "Sample recovery path"; no escalation.
  │     NO  → Continue.
  │
  ├─ Is the failure due to missing or broken local tooling (e.g. Python, config, repo state)?
  │     YES → Escalate to: owner of repo/environment. Handoff: support bundle + issue report.
  │     NO  → Continue.
  │
  ├─ Is the failure due to product/acceptance scenario design (e.g. scenario expects something not available)?
  │     YES → Escalate to: engineering/product. Handoff: support bundle + scenario_id + steps_results. Option: defer first-user until scenario or product is updated.
  │     NO  → Continue.
  │
  └─ Unknown or external (e.g. hardware, network, third-party)?
        → Document as known limitation; defer first-user rollout. Optional: escalate to internal owner with support bundle + issue report for tracking.
```

---

(Local-only. Operator-controlled. No automatic changes.)
