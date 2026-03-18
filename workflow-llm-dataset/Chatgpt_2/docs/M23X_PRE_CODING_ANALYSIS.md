# M23X — Pre-coding analysis (First-Run Operator Quickstart + Guided Product Tour)

## 1. What the current operator surface already includes

- **Dashboard** — `workflow-dataset dashboard` (workspace, package, cohort, apply-plan, action). Command center for workspaces, packages, cohort, apply.
- **Profile** — `profile bootstrap | show | operator-summary`. User work profile and bootstrap; operator summary (domain pack, models, specialization route).
- **Onboard** — `onboard`, `onboard status | bootstrap | approve`. First-run onboarding: status, bootstrap profile, approval bootstrap. Uses onboarding_flow, product_summary, approval_bootstrap.
- **Jobs** — `jobs list | show | run | report | diagnostics | specialization-show | seed`. Job packs and specialization (M23J/M23U).
- **Copilot** — `copilot recommend | plan | run | reminders | explain-recommendation | report`. Recommendations, plan, run, reminders (M23K/M23V).
- **Inbox** — `inbox` (default), `inbox explain | compare | snapshot`. Daily digest; macros via `macro list | preview | run`.
- **Trust** — `trust cockpit | release-gates | readiness-report`. Trust cockpit and release gates (M23V).
- **Runtime** — `runtime status | show-active-capabilities | explain-resolution | switch-role | switch-context | clear-context | backends | catalog | integrations | recommend | profile | compatibility`. Packs runtime (M22) and runtime mesh (M23T).
- **Mission-control** — `workflow-dataset mission-control`. Unified report: product, evaluation, development, incubator, coordination graph, desktop bridge, job packs, copilot, work context, corrections, runtime mesh, daily inbox, trust cockpit, package readiness, macros; recommended next action.
- **Console** — `workflow-dataset console`. TUI: Home, Setup summary, Projects, Suggestions, Drafts, Materialize, Apply, Rollback, Chat, LLM status, Trials, Release, Pilot, Runtime. No dedicated first-run or tour path.

Existing first-run–related pieces:
- **Onboarding flow** — `get_onboarding_status`, `format_onboarding_status`, `run_onboarding_flow`; recommended next steps.
- **First-run summary** — `build_first_run_summary`, `format_first_run_summary`: what_can_do_safely, trusted_benchmarked, simulate_only, ready_jobs/routines, recommended_first_workflow.
- **Next action** — `recommend_next_action(state)` in mission_control (build, benchmark, cohort_test, promote, hold, rollback, replay_task).

---

## 2. What a first-time operator would still find confusing

- **No single “start here” path** — Many commands (dashboard, profile, onboard, jobs, copilot, inbox, trust, runtime, mission-control) with no clear order or one-page map.
- **Mission-control is dense** — Sections 1–15 and next action; a new operator may not know how to interpret “Desktop bridge”, “Runtime mesh”, “Inbox”, “Trust cockpit” or what to do first.
- **No guided tour** — Nothing that explicitly says “what the system can do now”, “what is still simulate-only”, “what approvals matter”, “recommended first workflow”, “how to read trust/runtime/profile”.
- **No explicit first-value flow** — No single flow that walks: bootstrap profile → check runtime → onboard approvals → show recommended job → show inbox → run one safe simulate-only routine.
- **Quick reference missing** — Integration report recommends an “Operator quick reference”; it does not exist yet.
- **No product status card** — No one-place summary of “integrated modules available”, “missing optional pieces”, “trusted-real vs simulate-only”, “current recommended next action” in a card-style format.
- **No-data / partial-setup** — Commands may show errors or empty state without a clear “run X first” (e.g. run profile bootstrap, onboard bootstrap, jobs seed).

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/operator_quickstart/__init__.py` — Public API. |
| Create | `src/workflow_dataset/operator_quickstart/quick_reference.py` — Build quick reference (dashboard, profile, onboard, jobs, copilot, inbox, trust, runtime, mission-control): one-line purpose + key commands. Return structured dict and formatted text/md. |
| Create | `src/workflow_dataset/operator_quickstart/first_run_tour.py` — Build guided first-run tour: what system can do, what is simulate-only, what approvals matter, recommended first workflow, how to interpret trust/runtime/profile. Use existing first_run_summary, onboarding status, mission_control state (read-only). Return structured + formatted text. |
| Create | `src/workflow_dataset/operator_quickstart/first_value_flow.py` — Ordered first-value steps: (1) bootstrap profile, (2) check runtime mesh, (3) onboard approvals, (4) show recommended job pack, (5) show inbox, (6) run one safe simulate-only routine. No auto-run; emit steps with commands and optional run_read_only flags (e.g. run status checks only, suggest job run). |
| Create | `src/workflow_dataset/operator_quickstart/status_card.py` — Product status card: integrated modules (available/missing), trusted-real vs simulate-only coverage, recommended next action. Aggregate from mission_control state + first_run_summary + package_readiness. |
| Modify | `src/workflow_dataset/cli.py` — Add `quickstart_group` or top-level commands: `quickref` (print quick reference), `tour` (print first-run tour), `first-value` (print/run first-value flow steps), `status-card` (print product status card). |
| Create | `tests/test_operator_quickstart.py` — Quick reference generation, first-run tour content, first-value flow steps, status card, no-data/partial-setup behavior. |
| Create | `docs/M23X_OPERATOR_QUICKSTART.md` — Usage, sample quick-reference output, sample tour, sample first-value flow, sample status card, safety, what this phase will not do. |

---

## 4. Safety/risk note

- **Read-only and suggestive** — Quick reference, tour, first-value flow, and status card only read existing state and print text or suggest commands. No hidden permissions, no auto-run of workflows, no change to approval or trust logic.
- **No new automation** — First-value flow may “run” only status/read-only steps (e.g. profile show, onboard status, runtime backends, inbox); any “run job” or “run routine” is suggested as a command for the operator to run explicitly.
- **Local-only** — All data from existing local sources (mission_control, onboarding, product_summary, package_readiness). No cloud, no telemetry.
- **Preserve gates** — No bypass of check_job_policy, approval registry, or trust cockpit. Tour and status card only explain what is simulate-only and what approvals matter.

---

## 5. What this phase will NOT do

- **No hidden permissions** — No new approval or permission grants.
- **No auto-run of workflows** — No automatic execution of jobs, routines, or macros; only suggest commands.
- **No rewrite of dashboard or mission-control** — Reuse existing modules; add quickref/tour/status-card and a first-value flow that references them.
- **No broadening of runtime behavior** — No new runtime or cloud behavior; only explain and point to existing runtime/trust/profile.
- **No first-run wizard in console** — Optional: later add a “Tour” or “Quickstart” menu item in the TUI that calls the same tour/quickref; not required for M23X if we add CLI-only.
