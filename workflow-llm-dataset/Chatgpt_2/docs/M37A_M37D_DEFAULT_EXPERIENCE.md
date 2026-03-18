# M37A–M37D Default Experience Narrowing + Mode Simplification

## Summary

First-draft default-experience hardening: explicit default/advanced/expert surface classification, simplified user-facing workday modes (six), calm default home, profiles (first_user, calm_default, full), CLI (`defaults show` / `defaults apply`, `day modes`, `workspace home --profile calm_default`), and mission-control visibility for current profile and next default entry.

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/workspace/cli.py` | `cmd_home` accepts `profile_id`; when `calm_default` or `first_user`, uses `format_calm_default_home`. |
| `src/workflow_dataset/cli.py` | Added `defaults` group with `defaults show`, `defaults apply`; `workspace home --profile`; `day modes`. |
| `src/workflow_dataset/mission_control/state.py` | Added `default_experience_state`: active_profile_id, simplified_mode_mapping, advanced_surfaces_hidden_by_default_count, next_default_entry_action. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Default experience]` section: profile, advanced_surfaces_hidden, next_entry, command hints. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/default_experience/__init__.py` | Package exports. |
| `src/workflow_dataset/default_experience/models.py` | SurfaceClassification, DefaultWorkdayModeSet, DefaultExperienceProfile; SURFACE_* and USER_MODE_* constants. |
| `src/workflow_dataset/default_experience/surfaces.py` | DEFAULT_VISIBLE_SURFACES, ADVANCED_SURFACES, EXPERT_SURFACES; get_all_surfaces, get_surface_by_id, surfaces_hidden_by_default. |
| `src/workflow_dataset/default_experience/modes.py` | SIMPLIFIED_MODE_SET, internal_state_to_user_mode, get_simplified_mode_mapping. |
| `src/workflow_dataset/default_experience/profiles.py` | FIRST_USER_PROFILE, CALM_DEFAULT_PROFILE, FULL_PROFILE; get_profile, list_profile_ids. |
| `src/workflow_dataset/default_experience/calm_home.py` | format_calm_default_home(snapshot, repo_root). |
| `src/workflow_dataset/default_experience/store.py` | get_active_default_profile_id, set_active_default_profile_id; data/local/default_experience/active_profile.txt. |
| `tests/test_default_experience.py` | Tests for classification, mode mapping, profiles, calm home, store, preserved advanced access. |
| `docs/M37A_M37D_DEFAULT_EXPERIENCE.md` | This document. |

## 3. Exact CLI usage

```bash
# Default experience
workflow-dataset defaults show
workflow-dataset defaults show --repo-root /path/to/repo
workflow-dataset defaults apply first_user
workflow-dataset defaults apply calm_default
workflow-dataset defaults apply full --repo-root /path

# Workspace home (narrowed vs full)
workflow-dataset workspace home
workflow-dataset workspace home --profile calm_default
workflow-dataset workspace home --profile first_user
workflow-dataset workspace home --preset founder-operator

# Day modes (simplified user-facing)
workflow-dataset day modes
```

## 4. Sample default experience profile

```json
{
  "profile_id": "calm_default",
  "label": "Calm default",
  "description": "Daily default: calm home, six modes, advanced surfaces hidden by default.",
  "default_home_format": "calm",
  "default_entry_command": "workflow-dataset workspace home --profile calm_default",
  "show_areas_section": false,
  "max_mission_control_sections": 0
}
```

## 5. Sample simplified mode mapping

| mode_id   | label    | internal_states                                      |
|-----------|----------|------------------------------------------------------|
| start     | Start    | not_started, startup                                 |
| focus     | Focus    | focus_work                                           |
| review    | Review   | review_and_approvals                                 |
| operator  | Operator | operator_mode                                        |
| wrap_up   | Wrap up  | wrap_up                                              |
| resume    | Resume   | shutdown, resume_pending                              |

## 6. Sample narrowed home output

```
=== Workspace Home (calm default) ===

[Current focus]
  Project: proj_1  My Project
  Goal: —

[Next best action]
  review  — Check inbox
  Next project: —

[Urgent approvals / reviews]
  2 pending

[Carry-forward / resume]
  Day not started. Run: workflow-dataset day start

[Most relevant project]
  proj_1  My Project

[Automation / health]
  OK

More: workflow-dataset workspace home  |  workflow-dataset day status  |  workflow-dataset mission-control
```

## 7. Exact tests run

```bash
pytest workflow-llm-dataset/tests/test_default_experience.py -v
```

Tests cover: default-visible surface classification, advanced/expert hidden by default, get_surface_by_id, simplified mode mapping (six modes), internal_state_to_user_mode, profile list/get, store get/set active profile, calm home format (sections present), preserved advanced access (surfaces listable).

## 8. Remaining gaps for later refinement

- **First-run auto profile**: No automatic application of `first_user` on first run; profile is set explicitly via `defaults apply`.
- **Mission control “default view”**: Report still full; no truncated “default view” variant by section count (max_mission_control_sections not yet used).
- **Workspace home default from profile**: `workspace home` without `--profile` always shows full home; optional “use active profile’s default_home_format” is not implemented.
- **Empty-state / new-user copy**: Calm home text is generic; no dedicated empty-state or onboarding copy.
- **UI/frontend**: No UI changes; CLI and text reports only.
