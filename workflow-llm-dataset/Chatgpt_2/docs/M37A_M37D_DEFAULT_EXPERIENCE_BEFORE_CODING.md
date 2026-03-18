# M37A–M37D Default Experience Narrowing — Before Coding

## 1. What top-level operating surfaces already exist

- **Workday**: `day status`, `day start`, `day mode --set`, `day wrap-up`, `day shutdown`, `day resume`, `day preset list/show/set`. States: not_started, startup, focus_work, review_and_approvals, operator_mode, wrap_up, shutdown, resume_pending. Daily operating surface aggregates project, queue, approvals, trust, next transition.
- **Workspace**: `workspace home` (full: Where you are, Top priority, Approvals, Blocked, Recent, Trust/Health, Areas, Quick); `workspace open`, `workspace context`, `workspace next`. WORKSPACE_AREAS (13 areas including conversational_ask, timeline, intervention_inbox). Presets: founder_operator, analyst, developer, document_heavy (section order + quick actions).
- **Queue**: `queue list`, `queue view --mode`, `queue summary`, `queue quality`, `queue suppressions`, `queue resurfacing`, `queue focus-protection`, `queue profile`, `queue interruption-budget`. Unified work queue with modes focus/review/operator/wrap-up.
- **Mission control**: Long report (Product, Evaluation, Development, Incubator, Coordination graph, Desktop bridge, Observation, Live context, Assist, In-flow, Job packs, Copilot, Context, Action cards, Background runner, Automation inbox, Workflow episodes, Live workflow, Personal graph, Corrections, Teaching/skills, Runtime mesh, Daily inbox, Trust cockpit, Authority/Trust contracts, Operator mode, Package readiness, Workday, Environment, Starter kits, External capabilities, Activation executor, Value packs, Provisioning, …). `recommend_next_action()` returns build/benchmark/cohort_test/promote/hold/rollback/replay_task/observe_setup.
- **Default experience (existing)**: `default_experience/models.py` (SurfaceClassification, DefaultWorkdayModeSet, DefaultExperienceProfile, USER_MODE_*); `profiles.py` (first_user, calm_default, full); `surfaces.py` (DEFAULT_VISIBLE_SURFACES, ADVANCED_SURFACES, EXPERT_SURFACES); `modes.py` (SIMPLIFIED_MODE_SET, internal_state_to_user_mode); `calm_home.py` (format_calm_default_home); `store.py` (get/set active profile); `disclosure_paths.py` (progressive disclosure); `onboarding_defaults.py`. **Workspace CLI** calls `cmd_home(profile_id=…)` only when profile is passed — but **CLI does not expose --profile** on `workspace home`; it only has --preset.

## 2. Which parts are too exposed/noisy for a default daily user

- **Mission control report**: Dozens of sections in one go; overwhelming for “what do I do next.”
- **Workspace home (full)**: Areas list with 13 areas and command hints; Top priority + Approvals + Blocked + Recent + Trust + Areas + Quick in one view — high signal but dense.
- **Queue**: Many subcommands (list, view, summary, quality, suppressions, resurfacing, focus-protection, profile, interruption-budget); default user may only need summary + list.
- **Workday states**: Eight internal states (not_started, startup, focus_work, review_and_approvals, operator_mode, wrap_up, shutdown, resume_pending); user-facing simplification to six modes exists in default_experience/modes but not surfaced in a single `day modes` command.
- **No single “defaults” entry point**: Active profile is stored and read but there is no `workflow-dataset defaults show` or `defaults apply --profile first_user` or `defaults paths` in the main CLI.
- **Trust/Policy/Operator**: Expert-level; should stay accessible but not be the first thing a new user sees.

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|--------|
| Create | `docs/M37A_M37D_DEFAULT_EXPERIENCE_BEFORE_CODING.md` | This analysis. |
| Modify | `src/workflow_dataset/cli.py` | Add `defaults` group: `defaults show`, `defaults apply --profile`, `defaults paths`. Add `day modes` command. Add `--profile` to `workspace home` and pass to cmd_home. |
| Modify | `src/workflow_dataset/workspace/cli.py` | Ensure cmd_home uses profile_id when provided (already does). |
| Modify | `src/workflow_dataset/mission_control/state.py` | Add `default_experience_state`: active_profile_id, simplified_mode_mapping, advanced_surfaces_hidden_by_default, next_recommended_default_entry_action. |
| Modify | `src/workflow_dataset/mission_control/report.py` | Add [Default experience] section. |
| Modify | `src/workflow_dataset/default_experience/calm_home.py` | Optionally append “Show me more” footer from disclosure_paths (format_show_more_footer). |
| Create | `tests/test_default_experience.py` | Classification, mode mapping, profile, calm home, preserved advanced access. |
| Create | `docs/M37A_M37D_DEFAULT_EXPERIENCE_AND_NARROWING.md` | Files modified/created, CLI, sample profile, sample mode mapping, sample narrowed home, tests, gaps. |

## 4. Safety/risk note

- Narrowing is **advisory and additive**: we do not remove or gate critical trust/approval/policy surfaces; we classify them as advanced/expert and keep them reachable via explicit commands and “Show me more” paths.
- Active profile is **local-only** (data/local/default_experience/active_profile.txt). No cloud; no automatic locking of advanced features.
- First-user profile recommends calm home and avoids suggesting expert surfaces first; expert surfaces remain available to anyone who runs the command.

## 5. Simplification principles

- **Default-visible first**: Calm home, day status, queue summary, urgent approvals, carry-forward — one clear entry and next action.
- **Progressive disclosure**: Default → Advanced → Expert with explicit “show me more” steps and commands.
- **Six user-facing modes**: start, focus, review, operator, wrap_up, resume — map from internal workday states so the model is simpler to explain.
- **Single defaults entry point**: `defaults show` / `defaults apply` so the user can see and set the active experience profile.
- **Mission control**: Add a short default-experience block (active profile, next default entry action) without replacing the full report for those who want it.

## 6. What this block will NOT do

- Will not remove or disable trust cockpit, policy board, operator mode, or approval flows; they remain available as advanced/expert.
- Will not rebuild workspace or workday state machines; we extend and wire existing default_experience and calm home.
- Will not implement a new UI or visual redesign; CLI and text reports only.
- Will not hide advanced capability permanently; every surface remains reachable by command.
