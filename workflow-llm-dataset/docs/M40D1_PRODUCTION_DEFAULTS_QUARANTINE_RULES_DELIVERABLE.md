# M40D.1 — Production Defaults + Experimental Quarantine Rules — Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/production_cut/models.py` | Added `ProductionDefaultProfile`, `ExperimentalQuarantineRule`, `ProductionSafeLabel` (M40D.1). |
| `src/workflow_dataset/production_cut/__init__.py` | Exported new models and functions: `get_production_default_profile`, `list_quarantine_rules`, `build_quarantine_rules_report`, `build_production_safe_label_report`, `build_operator_surface_explanations`. |
| `src/workflow_dataset/cli.py` | Added commands: `production-cut production-default`, `production-cut quarantine-rules`, `production-cut operator-explanations`, `production-cut labels`. |
| `tests/test_production_cut.py` | Added 5 tests for M40D.1: production default profile, quarantine rules report, production-safe label report, operator explanations. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/production_cut/production_defaults.py` | `get_production_default_profile(cut \| repo_root)` — production-default workspace/day/queue/experience from active cut. |
| `src/workflow_dataset/production_cut/quarantine_rules.py` | `list_quarantine_rules`, `build_quarantine_rules_report` — experimental quarantine rules with operator explanations. |
| `src/workflow_dataset/production_cut/labels.py` | `build_production_safe_label_report`, `build_operator_surface_explanations` — production-safe vs non-production-safe labeling; advanced-only vs experimental-only summaries. |
| `docs/M40D1_PRODUCTION_DEFAULTS_QUARANTINE_RULES_DELIVERABLE.md` | This file. |

---

## 3. Sample production default profile

After `workflow-dataset production-cut lock --id founder_operator_core` and `workflow-dataset production-cut production-default`:

**CLI output:**
```
Production default for Founder / Operator (core)
  vertical=founder_operator_core  workspace=founder_operator  workday=founder_operator
  experience=founder_calm  operator_mode=preferred
  workday=founder_operator  experience=founder_calm  operator_mode=preferred
  hint: Portfolio and approvals first; operator mode for delegated runs.
```

**JSON (`production-cut production-default --json`):**
```json
{
  "label": "Production default for Founder / Operator (core)",
  "vertical_id": "founder_operator_core",
  "workspace_preset_id": "founder_operator",
  "workday_preset_id": "founder_operator",
  "queue_section_order": ["approval_queue", "focus_ready", "review_ready", "operator_ready", "wrap_up"],
  "default_experience_profile_id": "founder_calm",
  "operator_mode_usage": "preferred",
  "role_operating_hint": "Portfolio and approvals first; operator mode for delegated runs.",
  "operator_summary": "workday=founder_operator  experience=founder_calm  operator_mode=preferred"
}
```

---

## 4. Sample quarantine rule report

**CLI (`workflow-dataset production-cut quarantine-rules`):**
```
Quarantine rules  vertical=founder_operator_core  count=1
  1 experimental surface(s) in quarantine; not production-safe. Available only per reveal rule (on_demand or after_first_milestone).
  automation_inbox  on_demand  Available on demand only; experimental, not part of production-default experience.
```

**JSON (`production-cut quarantine-rules --json`):**
```json
{
  "vertical_id": "founder_operator_core",
  "label": "Founder / Operator (core) (production cut)",
  "quarantine_rules": [
    {
      "surface_id": "automation_inbox",
      "label": "Automation inbox",
      "reveal_rule": "on_demand",
      "condition_summary": "On demand only",
      "operator_explanation": "Available on demand only; experimental, not part of production-default experience.",
      "production_safe": false
    }
  ],
  "count": 1,
  "operator_summary": "1 experimental surface(s) in quarantine; not production-safe. Available only per reveal rule (on_demand or after_first_milestone)."
}
```

---

## 5. Exact tests run

```bash
pytest tests/test_production_cut.py -v --tb=short
```

**Result:** 18 passed (0.84s).

New M40D.1 tests:
- `test_production_default_profile` — profile from active cut has label, workday, operator_summary
- `test_production_default_profile_no_cut` — no cut returns None
- `test_quarantine_rules_report` — report has quarantine_rules with production_safe=False and operator_explanation
- `test_production_safe_label_report` — production_safe only for included; reason_if_not_safe for others
- `test_operator_surface_explanations` — production_safe_summary, advanced_only_summary, experimental_only_summary present

---

## 6. Next recommended step for the pane

- **Wire production-default into shell/UI** — Have workspace/day/queue shell read `get_production_default_profile(repo_root)` and apply workspace_preset_id, workday_preset_id, queue_section_order when “production default” mode is selected, so the UI reflects the locked cut’s defaults without rebuilding the production-cut layer.
- **Optional: persist “production default applied”** — Store a flag or timestamp in `data/local/production_cut/` when the operator explicitly applies production default (e.g. “use production default profile”), and surface it in mission control for “current profile = production default”.
- **Optional: quarantine bypass audit** — When a quarantined surface is revealed (on_demand or after_first_milestone), log a lightweight audit entry so operators can see “experimental surface X was used at T”; keep it local-first and optional.
- **Docs** — Add a short “Production defaults and quarantine” section to the M40 operator-facing doc (or M39 verticals operator guide) describing production-default profile, quarantine rules, and production-safe vs non-production-safe labels.
