# M37D.1 — Onboarding Defaults + Progressive Disclosure Paths

## Summary

Extension of M37A–M37D: safer first-user defaults, progressive disclosure (default → advanced → expert), clearer “show me more” paths, and role-specific calm profiles.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/default_experience/profiles.py` | Added role calm profiles: `PROFILE_FOUNDER_CALM`, `PROFILE_ANALYST_CALM`, `PROFILE_DEVELOPER_CALM`, `PROFILE_DOCUMENT_CALM`, `PROFILE_SUPERVISION_CALM`; `ROLE_CALM_PROFILE_IDS`, `WORKDAY_PRESET_TO_CALM_PROFILE`; `list_role_calm_profile_ids()`, `get_calm_profile_for_workday_role()`. |
| `src/workflow_dataset/workspace/cli.py` | Calm home used for any profile with `default_home_format == "calm"` (includes role calm profiles). |
| `src/workflow_dataset/default_experience/disclosure_paths.py` | Clearer step labels; added `TIER_ORDER`, `get_disclosure_path_by_tier()`; footer uses numbered steps (1. … 2. …). |
| `src/workflow_dataset/default_experience/onboarding_defaults.py` | Added `RECOMMENDED_NEXT_AFTER_HOME`, `recommended_next_after_home()`, `is_safe_for_first_user(surface_id)`. |
| `tests/test_default_experience.py` | Un-skipped `test_role_calm_profiles` (full assertions); added `test_disclosure_path_by_tier`, `test_onboarding_safe_surface_and_next_after_home`. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M37D1_ONBOARDING_AND_DISCLOSURE.md` | This document: samples, tests, next step. |

---

## 3. Sample progressive disclosure path

Tiers: **default** → **advanced** → **expert**.

**From default (calm home):**
- 1. Full workspace home (all areas): `workflow-dataset workspace home`
- 2. See all day modes: `workflow-dataset day modes`
- 3. Mission control report: `workflow-dataset mission-control`
- 4. Queue list (all modes): `workflow-dataset queue list`  
- All paths: `workflow-dataset defaults paths`

**From advanced → expert:**
- Trust cockpit: `workflow-dataset trust cockpit`
- Policy board: `workflow-dataset policy board`
- Operator mode: `workflow-dataset day mode --set operator_mode`

Structured view (from `get_disclosure_path_by_tier()`):

```python
{
  "default": [
    {"from_tier": "default", "to_tier": "advanced", "label": "Full workspace home (all areas)", "command": "workflow-dataset workspace home"},
    {"from_tier": "default", "to_tier": "advanced", "label": "See all day modes", "command": "workflow-dataset day modes"},
    ...
  ],
  "advanced": [
    {"from_tier": "advanced", "to_tier": "expert", "label": "Trust cockpit", "command": "workflow-dataset trust cockpit"},
    ...
  ],
  "expert": []
}
```

---

## 4. Sample role-specific default profile

**Founder / Operator (calm)**

| Field | Value |
|-------|--------|
| `profile_id` | `founder_calm` |
| `label` | Founder / Operator (calm) |
| `description` | Calm default for founder/operator: portfolio and approvals first; operator mode when needed. |
| `default_home_format` | calm |
| `default_entry_command` | workflow-dataset workspace home --profile calm_default |
| `show_areas_section` | false |
| `max_mission_control_sections` | 0 |

**Mapping from workday preset:** `founder_operator` → `founder_calm`.  
Other role calm profiles: `analyst` → `analyst_calm`, `developer` → `developer_calm`, `document_heavy` → `document_heavy_calm`, `supervision_heavy` → `supervision_heavy_calm`.

**Usage:**
```bash
workflow-dataset defaults apply founder_calm
workflow-dataset workspace home   # uses active profile → calm home
workflow-dataset workspace home --profile analyst_calm
```

---

## 5. Exact tests run

```bash
python3 -m pytest tests/test_default_experience.py -v
```

**New/updated tests:**
- `test_role_calm_profiles` — list_role_calm_profile_ids, get_calm_profile_for_workday_role, founder/analyst, unknown→None, profile calm.
- `test_disclosure_path_by_tier` — get_disclosure_path_by_tier returns default/advanced/expert, steps have label/command.
- `test_onboarding_safe_surface_and_next_after_home` — recommended_next_after_home contains "day status"; is_safe_for_first_user(workspace_home or day_status) True; trust_cockpit and nonexistent False.

**Result:** 16 passed.

---

## 6. Next recommended step for the pane

- **Option A — CLI for role calm:** Add `workflow-dataset defaults apply --from-role founder_operator` that sets active profile to `founder_calm` (using `get_calm_profile_for_workday_role`), so day preset and default experience stay in sync.
- **Option B — First-run hint:** When active profile is `first_user` and workday has never been started, show a one-line hint in calm home: “Start your day: workflow-dataset day start.”
- **Option C — Mission control:** Include active role calm profile (if any) and “next recommended after home” in the mission control default experience block.

Implementing **Option A** is the smallest, highest-impact next step: one new CLI path that ties workday preset and default experience profile together.
