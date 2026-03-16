# C4 — Dashboard action runner stubs + operator macros

Lightweight operator macros/shortcuts from the dashboard for common safe actions. Command shortcuts and console triggers only; no hidden automation.

---

## 1. Files modified

| Path | Change |
|------|--------|
| `src/workflow_dataset/release/dashboard_data.py` | Added `action_macros` list: each entry has `id`, `label`, `command`. Macros: inspect-workspace (review show-workspace &lt;ref&gt;), open-package (dashboard package), open-cohort-report (cat &lt;path&gt;), staging-board (review staging-board), benchmark-board (eval board). open-package / open-cohort-report only added when data exists. |
| `src/workflow_dataset/ui/dashboard_view.py` | Rendered "Action shortcuts" panel from `action_macros`. Console: "1-5: Run shortcut" — pressing 1–5 runs the corresponding macro via subprocess and shows output. |
| `src/workflow_dataset/cli.py` | Added `dashboard action &lt;macro_id&gt;` command: runs the macro’s command and exits with its return code. |
| `tests/test_review_queue.py` | `test_dashboard_data_structure` asserts `action_macros`. Added `test_dashboard_action_macros`, `test_dashboard_action_cli`. |
| **New** `docs/C4_DASHBOARD_ACTION_MACROS.md` | This delivery memo. |

---

## 2. Exact macro/shortcut usage

**CLI (run the underlying command):**
```bash
workflow-dataset dashboard action inspect-workspace
workflow-dataset dashboard action open-package
workflow-dataset dashboard action open-cohort-report
workflow-dataset dashboard action staging-board
workflow-dataset dashboard action benchmark-board
```

**Dashboard view:** The main dashboard prints an "Action shortcuts" panel with numbered items and the exact command for each. Copy-paste the command or use the CLI above.

**Console:** From the dashboard (D), press **1**–**5** to run the 1st–5th shortcut. Output is shown; Enter returns to the dashboard.

---

## 3. Macro IDs and commands

| ID | Label | Command (typical) |
|----|--------|-------------------|
| inspect-workspace | Inspect latest workspace | workflow-dataset review show-workspace &lt;workflow/run_id&gt; |
| open-package | Open latest package | workflow-dataset dashboard package |
| open-cohort-report | Open latest cohort report | cat &lt;path/to/cohort_*_report.md&gt; |
| staging-board | Show staging board | workflow-dataset review staging-board |
| benchmark-board | Show benchmark board | workflow-dataset eval board |

inspect-workspace and open-package / open-cohort-report appear only when there is at least one workspace or package/cohort report.

---

## 4. Sample dashboard action output

**Panel on main dashboard:**
```
——— Action shortcuts ———
╭──── Action shortcuts (run via: workflow-dataset dashboard action <id>) ────╮
│  1. Inspect latest workspace                                               │
│     workflow-dataset review show-workspace weekly_status/2026-03-16_0258__be6ab9e │
│  2. Open latest package                                                    │
│     workflow-dataset dashboard package                                     │
│  3. Open latest cohort report                                              │
│     cat /path/to/repo/data/local/pilot/cohort_broader_ops_q1_report.md     │
│  4. Show staging board                                                     │
│     workflow-dataset review staging-board                                  │
│  5. Show benchmark board                                                   │
│     workflow-dataset eval board                                            │
╰────────────────────────────────────────────────────────────────────────────╯
```

**CLI run:**
```bash
$ workflow-dataset dashboard action staging-board
Running: workflow-dataset review staging-board

Staging board: 0 item(s)
...
```

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_review_queue.py -v --tb=short -k "dashboard"
```

Includes: `test_dashboard_data_structure` (action_macros), `test_dashboard_action_macros`, `test_dashboard_action_cli`.
