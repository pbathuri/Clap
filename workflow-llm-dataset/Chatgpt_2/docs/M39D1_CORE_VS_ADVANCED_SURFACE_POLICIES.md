# M39D.1 — Core vs Advanced Surface Policies

Extends M39A–M39D with: vertical-specific core surfaces (mapped to recommended/allowed/discouraged/blocked), advanced surface reveal rules, explicit experimental labels, and a stronger surface policy report.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/vertical_selection/models.py` | Added SURFACE_POLICY_* (recommended, allowed, discouraged, blocked), REVEAL_* constants, SurfacePolicyEntry dataclass. |
| `src/workflow_dataset/vertical_selection/__init__.py` | Exported surface policy types and surface_policies helpers. |
| `src/workflow_dataset/cli.py` | Added **`verticals surface-policy [--id]`**: report recommended/allowed/discouraged/blocked counts and lists, experimental labels, reveal_rules summary. |
| `tests/test_vertical_selection.py` | Added test_surface_policy_level, test_is_surface_experimental, test_surface_policy_report, test_advanced_reveal_rule. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/vertical_selection/surface_policies.py` | get_surface_policy_level(), get_surface_policy_entry(), get_surface_policy_report(), is_surface_experimental(), get_advanced_reveal_rule(); EXPERIMENTAL_SURFACE_IDS. |
| `docs/M39D1_CORE_VS_ADVANCED_SURFACE_POLICIES.md` | This document. |

---

## 3. Sample core-surface policy

**founder_operator_core** (derived from curated pack):

| Policy level   | Meaning        | Example surface IDs |
|----------------|----------------|----------------------|
| **recommended** | Core for vertical; show first | workspace_home, day_status, queue_summary, approvals_urgent, continuity_carry_forward |
| **allowed**     | Advanced but available       | mission_control, review_studio, automation_inbox, trust_cockpit |
| **discouraged** | Not in core or optional      | (all others not in required/optional/hidden) |
| **blocked**     | Explicitly excluded          | (from pack hidden_for_vertical; currently empty for built-in packs) |

**Reveal rules:**
- **recommended** → `always`
- **allowed** → `on_demand`
- **blocked** → `never`
- **discouraged** → `on_demand`

**Experimental labels** (best-effort, known limitations): automation_run, background_run, copilot_plan, agent_loop, timeline, automation_inbox.

---

## 4. Sample surface policy report

**verticals surface-policy --id analyst_core** (text):

```
Surface policy  vertical=analyst_core
  recommended: 4  workspace_home, day_status, queue_summary, continuity_carry_forward
  allowed: 3  review_studio, mission_control, trust_cockpit
  discouraged: 9
  blocked: 0
  experimental: automation_run, background_run, copilot_plan, agent_loop, timeline, automation_inbox
  reveal_rules: always=4  on_demand=12  never=0
```

**With --json** (excerpt):

```json
{
  "vertical_id": "analyst_core",
  "recommended_surfaces": ["workspace_home", "day_status", "queue_summary", "continuity_carry_forward"],
  "allowed_surfaces": ["review_studio", "mission_control", "trust_cockpit"],
  "discouraged_surfaces": [...],
  "blocked_surfaces": [],
  "recommended_count": 4,
  "allowed_count": 3,
  "discouraged_count": 9,
  "blocked_count": 0,
  "experimental_labels": { "automation_run": true, "timeline": true, ... },
  "reveal_rules_summary": { "always": 4, "on_demand": 12, "after_first_milestone": 0, "never": 0 }
}
```

---

## 5. Exact tests run

```bash
python3 -m pytest tests/test_vertical_selection.py -v
```

**Result:** 15 passed, including M39D.1:
- test_surface_policy_level
- test_is_surface_experimental
- test_surface_policy_report
- test_advanced_reveal_rule

---

## 6. Next recommended step for the pane

- **Reveal rule “after_first_milestone”**: Wire REVEAL_AFTER_FIRST_MILESTONE to vertical_packs progress (e.g. reveal advanced surfaces only after first-value milestone is reached). Today all allowed/discouraged use `on_demand`; optional surfaces could move to `after_first_milestone` and be gated by progress.
- **Mission control**: Add a line to the existing [Vertical selection] block for surface policy summary (e.g. recommended/allowed/discouraged/blocked counts) when an active vertical is set, so operators see policy at a glance.
- **Cohort alignment**: When cohort is careful_first_user, optionally tighten policy (e.g. treat some “allowed” as “discouraged”) or show a note that cohort may further restrict use of advanced surfaces.
