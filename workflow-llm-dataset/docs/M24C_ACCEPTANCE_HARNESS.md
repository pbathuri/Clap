# M24C — First Real-User Acceptance Harness

## Purpose

Validate whether the product is ready for a first real user in a controlled local environment by:

- **Acceptance scenarios** — Founder, analyst, developer, document-worker first-run scenarios with profile/machine/approval assumptions, starter kit, first-value steps, and expected outputs/blocked/trust expectations.
- **Golden journeys** — Reusable steps: install_readiness, bootstrap_profile, onboard_approvals, select_pack, run_first_simulate (existence check only), inspect_trust, inspect_inbox. Run in **report mode** (gather state only; no job/macro execution).
- **Acceptance runner** — Run a scenario, compare actual state to expectations, classify **pass** / **partial** / **blocked** / **fail**, produce reasons.
- **Acceptance reports** — Where the system succeeded, where it blocked correctly, where it failed unexpectedly, and **ready for real-user trial** (yes/no with evidence).

All local; no auto-run of unsafe real actions; no bypass of trust/approval.

---

## CLI usage

```bash
workflow-dataset acceptance list
workflow-dataset acceptance run --id founder_first_run [--repo-root PATH] [--output FILE]
workflow-dataset acceptance report [--latest] [--repo-root PATH] [--output FILE]
```

- **acceptance list** — List scenario IDs and names.
- **acceptance run --id &lt;id&gt;** — Run scenario in report mode; saves run to `data/local/acceptance/runs/`; optionally write report to file.
- **acceptance report** — Show report for latest run (default). Use `--output` to write to file.

---

## Sample acceptance scenario (founder_first_run)

- **scenario_id:** founder_first_run  
- **name:** New founder/operator first run  
- **profile_assumptions:** field=operations, job_family=founder  
- **approvals_needed:** path_workspace, apply_confirm  
- **starter_kit_id:** founder_ops_starter  
- **first_value_steps:** install_readiness, bootstrap_profile, onboard_approvals, select_pack, run_first_simulate, inspect_trust, inspect_inbox  
- **expected_outputs:** Install check passes or reports missing prereqs; bootstrap profile created or exists; onboarding status available; founder_ops_starter recommended or selectable; first simulate workflow can be run or reported; trust cockpit and inbox return state.  
- **expected_blocked:** Real mode blocked without approval registry; macro/job real run blocked until approvals.  
- **trust_readiness_expectations:** simulate_only_available true, trust_cockpit_available true.

---

## Sample acceptance run output

```
=== Acceptance report (M24C) ===

Scenario: New founder/operator first run
Outcome: partial

--- Reasons ---
  · Bootstrap profile not yet created (run profile bootstrap or first-run).

--- Where the system succeeded ---
  · install_readiness
  · onboard_approvals
  · select_pack
  · run_first_simulate
  · inspect_trust
  · inspect_inbox

--- Partial: some steps met, some blocked ---
  · Bootstrap profile not yet created (run profile bootstrap or first-run).

--- Ready for real-user trial? ---
  No. Address reasons above before a small real-user rollout.

(Acceptance harness is report-only; no automatic execution of real actions.)
```

---

## Sample acceptance report (pass)

When install passes, bootstrap exists, kit is found, and first simulate workflow exists:

```
Outcome: pass
--- Reasons ---
  · All critical steps met; product ready for controlled first-user rollout.

--- Ready for real-user trial? ---
  Yes. Evidence: all critical steps met; product ready for controlled first-user rollout.
```

---

## Outcome classification

| Outcome   | Meaning |
|----------|---------|
| **pass**   | All critical steps met; ready for controlled first-user trial. |
| **partial**| Some steps met; some blocked as expected (e.g. no bootstrap yet, or missing prereqs for kit). |
| **blocked**| Cannot proceed: install check failed, or starter kit not found, or first simulate workflow (job/routine) missing. |
| **fail**   | Unexpected error (e.g. scenario not found, or a gather step raised). |

---

## Safety

- **Report mode only** — Runner only gathers state via existing read-only APIs (install_check, onboarding, trust cockpit, job_packs, inbox, starter_kits). It does **not** execute jobs or macros; `run_first_simulate` only checks that the job or routine **exists**.
- **No bypass** — Trust and approval policy are not bypassed; no real actions are run.
- **Local-only** — Runs and reports under `data/local/acceptance/runs/`.

---

## Tests

```bash
pytest tests/test_acceptance.py -v
```

Covers: scenario definitions, get_scenario, classify_outcome (fail/blocked/partial), run_scenario structure, format_acceptance_report, save_run/load_latest_run/list_runs, run_journey_steps.

---

## Next step for the pane

- **Optional:** Add an explicit “run first simulate” step that **invokes** (with operator consent or a flag) `jobs run --id X --mode simulate` or `macro run --id X --mode simulate` in a subprocess, and then include that run’s success/failure in the acceptance result. Today the harness only checks that the job/routine **exists**; it does not execute it.
- **CI:** Run `workflow-dataset acceptance run --id founder_first_run` in CI (after install and optional bootstrap) to gate releases on “partial” or “pass” for at least one scenario.
