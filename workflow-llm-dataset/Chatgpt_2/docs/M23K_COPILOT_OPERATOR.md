# M23K — Workday copilot operator guide

What the copilot is, what it is not, how recommendations are formed, how routines work, how approvals are enforced, and how to use reminders without enabling uncontrolled automation.

---

## 1. What the copilot is

The **workday copilot** is a local, operator-approved layer on top of job packs and specialization memory. It:

- **Recommends jobs** from local data (recent success, trusted-for-real, approval-blocked, simulate-only) with explicit reasons.
- **Routines** are ordered bundles of job packs (e.g. morning reporting) that you can plan and run in one go.
- **Plan preview** shows what would run (jobs, order, mode, approvals, blocked) before any execution.
- **Approved execution** runs a plan only when you run `copilot run --job X` or `copilot run --routine Y --mode simulate|real`; each run is recorded.
- **Reminders** are stored proposals (e.g. “run morning routine”); they do **not** auto-run. Use `copilot reminders due` to see what’s due and run manually.

Everything is **local** (data/local/copilot) and **inspectable**.

---

## 2. What the copilot is not

- **Not autonomous:** Nothing runs in the background. No hidden scheduling or auto-execution.
- **Not cloud-managed:** No cloud sync or remote orchestration.
- **Not full desktop autopilot:** Only job packs (and routines of job packs) that you define and run explicitly.
- **Not bypassing trust:** Real mode still requires approval registry and job-level policy; the copilot does not skip checks.

---

## 3. How recommendations are formed

Recommendations use **only local, inspectable data**:

- **recent_successful_run** — Job has a recent successful run in specialization memory.
- **trusted_for_real** — Job is in the trusted-for-real set (trust_level and real_mode_eligibility).
- **approval_blocked** — Job could run real but is blocked by missing approval registry or scope; reason is stored.
- **simulate_only_available** — Job is simulate-only and available.

Each recommendation includes: `job_pack_id`, `reason`, `trust_level`, `mode_allowed` (simulate_only | trusted_real_eligible), `blocking_issues`, `recommended_timing_context`. There is no opaque ranking; reasons are explicit.

---

## 4. How routines work

- A **routine** is a YAML file under `data/local/copilot/routines/<routine_id>.yaml` with: `routine_id`, `title`, `description`, `job_pack_ids`, optional `ordering`, `stop_on_first_blocked`, `required_approvals`, `simulate_only`, `expected_outputs`.
- **Ordering:** Jobs run in the order of `job_pack_ids` (or by `ordering` indices if set).
- **simulate_only:** If true, the routine can only be run with `--mode simulate`; real mode is refused.
- You can create routines by writing YAML or via code (e.g. seed_morning_routine). List with `copilot report` (or mission-control shows routine count).

---

## 5. How approvals are enforced

- **Plan preview** runs the same job-level policy as `jobs run`: check_job_policy(job, mode, params, repo_root). Blocked jobs appear in `plan.blocked` and `plan.blocked_reasons`.
- **Plan run** executes each job in order; if a job is blocked, it is recorded and (by default) execution stops (`stop_on_first_blocked`). No silent skip; the plan run record lists `executed` and `blocked`.
- Real mode still requires the approval registry and trusted action scopes; the copilot does not add new approval bypasses.

---

## 6. How to use reminders without uncontrolled automation

- **Reminders** are stored in `data/local/copilot/reminders.yaml`. They are **proposals only**.
- **No auto-run:** Nothing runs when a reminder is “due.” Use `copilot reminders due` to see what you might want to run, then run `copilot run --routine X` or `jobs run --id Y` manually.
- **Add reminders:** `copilot reminders add --routine morning_reporting --due-at "09:00" --title "Morning check-in"` (or `--job weekly_status_from_notes`). This only writes to the reminders file.
- There is **no background scheduler** in this phase. Optional future: an explicit opt-in local trigger (e.g. a script you run via cron) that you control and can stop.

---

## 7. CLI reference

| Command | Purpose |
|--------|--------|
| `copilot recommend` | List recommended jobs with reasons and blocking issues |
| `copilot plan --job <id>` or `--routine <id>` `--mode simulate\|real` | Preview plan (no execution) |
| `copilot run --job <id>` or `--routine <id>` `--mode simulate\|real` | Run plan and record plan run |
| `copilot reminders list` | List all reminders |
| `copilot reminders add --routine X` or `--job Y` `--due-at ...` `--title ...` | Add reminder (no auto-run) |
| `copilot reminders due` | List reminders (due/upcoming) |
| `copilot report` | Copilot report: recommendations, routines, plan runs, reminders |

Mission control report includes **[Copilot]** (recommended_jobs, blocked, routines, plan_runs, reminders, next action).
