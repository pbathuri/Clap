# M23J — Job packs operator guide

What a job pack is, how it differs from a task demo, how specialization memory works, what is still simulate-only, how trust is earned, and how this stays local-first and approval-gated.

---

## 1. What is a job pack

A **job pack** is a reusable, named workflow that points at a **source** (a task demo or a desktop benchmark case) and adds:

- **Parameter schema** — which parameters the job accepts and their defaults
- **Trust policy** — simulate_only, trusted_for_real, approval_required_every_run, experimental, benchmark_only
- **Local specialization memory** — preferred params, last successful run, operator notes (updated only through explicit actions)

Job packs are stored under `data/local/job_packs/*.yaml`. They are inspectable and editable.

---

## 2. How it differs from a task demo

| | Task demo | Job pack |
|---|-----------|----------|
| **Purpose** | One-off captured sequence of adapter steps | Reusable “job” with params and policy |
| **Source** | Steps only (adapter_id, action_id, params) | References a task_demo **or** a benchmark_case |
| **Params** | Fixed in the task file | Parameter schema + specialization defaults + CLI override |
| **Trust** | Replay is simulate-only | Job declares trust_level; real mode gated by policy + approval registry |
| **Memory** | None | Specialization memory (preferred params, last run, notes) |

A job pack can **wrap** a task demo (source kind `task_demo`) or a benchmark case (source kind `benchmark_case`). Running the job runs that source with resolved parameters and policy checks.

---

## 3. How specialization memory works

- **Stored in:** `data/local/job_packs/<job_pack_id>/specialization.yaml`
- **Contains:** preferred_params, preferred_paths, preferred_apps, last_successful_run, recurring_failure_notes, operator_notes, confidence_notes, update_history
- **Updated only when:**
  - Operator runs **save-as-preferred** with explicit params
  - Operator runs job with **--update-specialization** and the run **succeeds** (outcome pass)
  - Explicit **update from successful run** or **operator override** in code/API

Specialization is **not** updated from failed runs or background inference. All updates are traceable in `update_history`.

---

## 4. What is still simulate-only

- **Task-demo-backed jobs:** Running a job whose source is a task_demo always uses replay_task_simulate; real mode is refused.
- **Jobs with trust_level=simulate_only** or **real_mode_eligibility=false:** Real mode is refused.
- **browser_open / app_launch:** Remain simulate-only at the adapter level; any job that uses them is effectively simulate-only for those steps.

---

## 5. How trust is earned for a real-action job

- Job must have **real_mode_eligibility=true** and a trust_level that allows real (e.g. trusted_for_real, approval_required_every_run, experimental).
- **Approval registry** must exist (`data/local/capability_discovery/approvals.yaml`) and, when it has non-empty approved_action_scopes, the job’s adapters/actions must be in the trusted set (see desktop-bench trusted-actions).
- Policy check runs before every real run; if the registry is missing or the job exceeds approved scope, the run is **refused** with a clear message.

Trust is **not** inferred from simulate success; real mode requires explicit eligibility and approvals.

---

## 6. Local-first and approval-gated

- All job pack and specialization data is under `data/local/job_packs`. No cloud sync.
- Real execution is gated by the same approval_registry and approval_check used by `adapters run` and desktop-bench.
- No hidden automation: job run is explicit (`jobs run --id ... --mode simulate|real`); preview shows resolved params and policy result before execution.

---

## 7. CLI reference

| Command | Purpose |
|--------|--------|
| `workflow-dataset jobs list` | List job pack ids |
| `workflow-dataset jobs show --id <id>` | Show job details, specialization summary, last run |
| `workflow-dataset jobs run --id <id> --mode simulate \| real [--param k=v]` | Run job (preview then execute) |
| `workflow-dataset jobs report` | Summary: total, simulate-only, trusted, approval-blocked, recent successful |
| `workflow-dataset jobs diagnostics --id <id>` | Per-job: trust level, policy simulate/real, specialization |
| `workflow-dataset jobs specialization-show --id <id>` | Show full specialization memory |
| `workflow-dataset jobs save-as-preferred --id <id> --param k=v` | Save params as preferred (explicit) |
| `workflow-dataset jobs seed` | Seed example job packs (requires desktop-bench cases) |

Mission control report includes a **[Job packs]** line (total, simulate_only, trusted_for_real, approval_blocked, recent_successful).
