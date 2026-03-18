# M23Y — Field Starter Kits + Immediate-Value Packs

## Overview

Starter kits combine domain pack, job packs, routines/macros, runtime/model recommendation, and a **first-value flow** so the product feels useful immediately. They are explicit and inspectable; no auto-download or auto-enable.

## CLI usage

```bash
workflow-dataset kits list
workflow-dataset kits recommend [--repo-root PATH] [--output FILE]
workflow-dataset kits show --id founder_ops_starter
workflow-dataset kits show -i analyst_starter
workflow-dataset kits first-run --id analyst_starter
workflow-dataset kits first-run -i developer_starter [--repo-root PATH]
```

## Built-in kits

| Kit ID | Target | Domain pack | First simulate workflow |
|--------|--------|-------------|-------------------------|
| founder_ops_starter | Founder / operator | founder_ops | morning_ops (routine) |
| analyst_starter | Analyst / researcher | research_analyst | weekly_status_from_notes (job) |
| developer_starter | Developer / coding | coding_development | replay_cli_demo (job) |
| document_worker_starter | Document-heavy knowledge worker | document_knowledge_worker | weekly_status_from_notes (job) |

## Sample starter kit definition (founder_ops_starter)

- **kit_id:** founder_ops_starter  
- **name:** Founder / operator starter  
- **target_field:** operations  
- **target_job_family:** founder  
- **domain_pack_id:** founder_ops  
- **recommended_runtime_task_class:** desktop_copilot  
- **recommended_job_ids:** weekly_status_from_notes, weekly_status  
- **recommended_routine_ids:** morning_reporting, morning_ops, weekly_review  
- **first_simulate_only_workflow:** morning_ops  
- **first_value_flow:**  
  - Run: `workflow-dataset macro run --id morning_ops --mode simulate`  
  - Get back: Simulated morning routine steps and outputs (no writes)  
  - Why useful: Confirms pipeline before enabling real mode  
  - Next: Run inbox; add approvals then try --mode real  
- **approvals_likely_needed:** path_workspace, apply_confirm  

## Sample kit recommendation output

```
=== Starter kit recommendation ===

Recommended: Founder / operator starter (founder_ops_starter)
Score: 0.8
Reason: Profile (field='operations', job_family='founder') matches domain pack founder_ops -> kit founder_ops_starter.

[Missing prerequisites]
  - Routine not found: morning_ops (add data/local/copilot/routines/morning_ops.yaml)
  - Approval registry missing (data/local/capability_discovery/approvals.yaml); required for real mode.

[Alternatives]
  analyst_starter  (score=0.05)  Analyst / researcher starter
  document_worker_starter  (score=0.05)  Document-heavy knowledge worker starter
  developer_starter  (score=0.05)  Developer / coding-heavy starter

Show details: workflow-dataset kits show --id founder_ops_starter
First run: workflow-dataset kits first-run --id founder_ops_starter
```

## Sample first-value flow (analyst_starter)

```
=== First-value flow: analyst_starter ===

1. Run (simulate-first):
   workflow-dataset jobs run --id weekly_status_from_notes --mode simulate

2. What you get back:
   A simulate run of weekly status from notes: folder inspect and list (no writes).

3. Why useful:
   Validates job pack and adapters; safe way to see what the job would do.

4. What to do next:
   Run 'workflow-dataset copilot recommend' for more jobs; add routine for research_digest if desired.
```

## Recommendation logic

- If user profile exists at `data/local/onboarding/user_work_profile.yaml`, it is loaded and used (field, job_family, daily_task_style).
- Otherwise profile is empty and the default kit (founder_ops_starter) is returned.
- Domain pack recommendation (`recommend_domain_packs`) is used to pick the primary kit via `DOMAIN_PACK_TO_KIT`.
- **Missing prerequisites** are computed from the recommended kit: jobs/routines that are not present, and approval registry if real mode is likely.

## Safety

- No auto-download of models or datasets.
- No auto-enable of external integrations.
- First-value flow is a suggested command string; user runs it explicitly.
- Real mode still requires approval registry and `check_job_policy`.

## Tests

```bash
PYTHONPATH=src python3 -m pytest tests/test_starter_kits.py -v
```

## Files

- **Created:** `starter_kits/` (models, registry, recommend, report), `tests/test_starter_kits.py`, `docs/M23Y_STARTER_KITS_ANALYSIS.md`, `docs/M23Y_STARTER_KITS.md`
- **Modified:** `cli.py` (kits group and commands)
