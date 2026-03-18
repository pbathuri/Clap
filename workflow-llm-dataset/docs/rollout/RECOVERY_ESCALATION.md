# Rollout recovery and escalation (M24I.1)

Quick reference: recovery path and escalation decision tree. Full runbook: **OPERATOR_RUNBOOKS.md**.

---

## Recovery path (blocked rollout → ready)

1. `workflow-dataset rollout status` → note Blocked and Next action.
2. `workflow-dataset rollout readiness` → review Blocks and Operator actions.
3. Fix install/env: `workflow-dataset package readiness-report`; fix missing items; `workflow-dataset local-deploy first-run` if needed.
4. Ensure profile: `workflow-dataset onboarding status`; run bootstrap if missing.
5. Re-run acceptance: `workflow-dataset acceptance run --id <scenario_id>`.
6. Refresh rollout: `workflow-dataset rollout launch --id <demo_id>`.
7. Confirm: `rollout status` and `rollout readiness`.

---

## Escalation decision tree

```
Activation / provisioning / readiness failed?
  │
  ├─ Fixable with readiness-report + first-run + onboarding + re-run acceptance?
  │     YES → Use recovery path above. NO → continue.
  │
  ├─ Missing or broken local tooling (Python, config, repo)?
  │     YES → Escalate to: environment/repo owner. Handoff: support bundle + issue report.
  │
  ├─ Product/acceptance scenario design (scenario expects unavailable capability)?
  │     YES → Escalate to: engineering/product. Handoff: bundle + scenario_id. Defer first-user until fixed.
  │
  └─ Unknown or external → Document limitation; defer first-user. Optional: escalate with bundle + issue report.
```

---

To generate a support bundle: `workflow-dataset rollout support-bundle`.  
To generate an issue report: `workflow-dataset rollout issues report --output <path>`.
