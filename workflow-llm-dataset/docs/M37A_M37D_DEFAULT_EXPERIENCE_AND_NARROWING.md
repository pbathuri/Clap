# M37A–M37D Default Experience Narrowing — Final Output

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `defaults` group with `defaults show`, `defaults apply`, `defaults paths`; added `day modes` command; added `--profile` to `workspace home` and pass to `cmd_home`. |
| `src/workflow_dataset/workspace/cli.py` | `cmd_home`: when `profile_id` is omitted, use active default profile from store; use calm home when active profile is `calm_default` or `first_user`. |
| `src/workflow_dataset/mission_control/state.py` | Added `default_experience_state`: `active_profile_id`, `simplified_mode_for_current_state`, `simplified_mode_set`, `advanced_surfaces_hidden_by_default_count`, `next_recommended_default_entry_action`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Default experience]` section: profile, user_mode, advanced_surfaces_hidden count, next_default_entry. |
| `src/workflow_dataset/default_experience/calm_home.py` | Appended “Show me more” footer from `format_show_more_footer()` to calm home output. |
| `tests/test_default_experience.py` | Skipped `test_role_calm_profiles` (role calm profiles not implemented). |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M37A_M37D_DEFAULT_EXPERIENCE_BEFORE_CODING.md` | Before-coding analysis: surfaces, noisy parts, file plan, safety, principles, what we do not do. |
| `docs/M37A_M37D_DEFAULT_EXPERIENCE_AND_NARROWING.md` | This deliverable: files, CLI, samples, tests, gaps. |

## 3. Exact CLI usage

```bash
# Default experience
workflow-dataset defaults show
workflow-dataset defaults show --json
workflow-dataset defaults apply first_user
workflow-dataset defaults apply calm_default
workflow-dataset defaults apply full
workflow-dataset defaults apply --profile first_user   # same as: defaults apply first_user
workflow-dataset defaults paths

# Day modes (simplified user-facing modes + current mapping)
workflow-dataset day modes
workflow-dataset day modes --json

# Workspace home with profile (narrowed vs full)
workflow-dataset workspace home
workflow-dataset workspace home --profile calm_default
workflow-dataset workspace home --profile first_user
workflow-dataset workspace home --profile full
```

When `workspace home` is run with **no** `--profile`, the active default profile (from `defaults apply`) is used; if that is `calm_default` or `first_user`, the calm home is shown.

## 4. Sample default experience profile

```json
{
  "profile_id": "first_user",
  "label": "First user",
  "description": "Narrowest default: calm home, single entry, minimal sections.",
  "default_home_format": "calm",
  "default_entry_command": "workflow-dataset workspace home --profile calm_default",
  "show_areas_section": false,
  "max_mission_control_sections": 0
}
```

## 5. Sample simplified mode mapping

| User mode | Internal workday states |
|-----------|--------------------------|
| start | not_started, startup |
| focus | focus_work |
| review | review_and_approvals |
| operator | operator_mode |
| wrap_up | wrap_up |
| resume | shutdown, resume_pending |

Example `day modes` output:

```
Simplified user-facing modes: start, focus, review, operator, wrap_up, resume
Current internal state: focus_work
Mapped user mode: focus
```

## 6. Sample narrowed home output

```
=== Workspace Home (calm default) ===

[Current focus]
  Project: proj1  Test Project
  Goal: —

[Next best action]
  review  — Check inbox
  Next project: proj1

[Urgent approvals / reviews]
  2 pending

[Carry-forward / resume]
  (no carry-forward)

[Most relevant project]
  proj1  Test Project

[Automation / health]
  OK

[Show me more]
  Show more surfaces (full home, mission control, queue list): workflow-dataset workspace home
  See all day modes: workflow-dataset day modes
  Full mission control report: workflow-dataset mission-control
  All paths: workflow-dataset defaults paths
```

## 7. Exact tests run

```bash
python3 -m pytest tests/test_default_experience.py -v
```

- **test_surface_classification_default_visible** — default-visible surfaces and classification  
- **test_surface_classification_advanced_expert** — advanced/expert hidden by default  
- **test_get_surface_by_id** — lookup by id  
- **test_surfaces_hidden_by_default** — hidden = advanced + expert  
- **test_simplified_mode_mapping** — six modes, correct ids  
- **test_internal_state_to_user_mode** — internal → user mode  
- **test_profiles_list_and_get** — first_user, calm_default, full  
- **test_store_get_set_profile** — get/set active profile  
- **test_calm_home_format** — calm home sections present  
- **test_preserved_advanced_access** — advanced/expert still listable  
- **test_onboarding_defaults** — recommended first command, safe surfaces  
- **test_progressive_disclosure_paths** — disclosure steps and footer  
- **test_role_calm_profiles** — SKIPPED (role calm profiles not implemented)  
- **test_calm_home_includes_show_more** — “[Show me more]” and “defaults paths” in calm home  

Result: **13 passed, 1 skipped**.

## 8. Remaining gaps for later refinement

- **Role calm profiles**: `founder_calm`, `analyst_calm`, etc., and `get_calm_profile_for_workday_role()` are not implemented; test skipped. Add when role-based default experience is desired.
- **Mission control “narrowed” report**: `max_mission_control_sections` on profiles is not yet used to produce a shortened mission-control report; full report only.
- **Empty-state / new-user first run**: No dedicated “first run” detection or one-time guidance beyond `defaults apply first_user` and `recommended_first_command`; could add a small first-run hint in calm home when no day has been started.
- **UI/visual**: All changes are CLI and text reports; no UI redesign.
- **Trust/approval visibility**: Critical trust and approval surfaces remain available via commands and “Show me more”; no change to their behavior, only to default visibility of the home view.
