# M45D.1 — Execution Profiles + Loop Templates (Deliverable)

First-draft execution profiles (conservative, balanced, operator-heavy, review-heavy), loop templates for common bounded workflows, and operator-facing explanation of why a loop template is safe or blocked. Extends M45A–M45D; no rebuild.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/adaptive_execution/models.py` | Added `ExecutionProfile`, `LoopTemplate`; added `profile_id` and `template_id` to `BoundedExecutionLoop`. |
| `src/workflow_dataset/adaptive_execution/generator.py` | `create_bounded_loop()` accepts `profile_id`, `template_id`; applies profile max_steps_cap and review_every_n_steps / require_review_before_first_step; sets loop.profile_id and loop.template_id. `generate_loop_from_goal()` accepts `profile_id`, `template_id`; uses template goal_hint and default_profile when template given. |
| `src/workflow_dataset/adaptive_execution/store.py` | `load_loop()` restores `profile_id` and `template_id` on `BoundedExecutionLoop`. |
| `src/workflow_dataset/adaptive_execution/__init__.py` | Exported profiles, templates, explain_safety APIs and constants. |
| `src/workflow_dataset/cli.py` | `adaptive-execution plans` has `--profile` and `--template`; added `adaptive-execution profiles` and `adaptive-execution templates`; `adaptive-execution explain` includes safety section (why safe/blocked) when profile or template set, with `--safety/--no-safety`. |
| `tests/test_adaptive_execution.py` | Added tests: test_list_profiles, test_get_profile_why_safe, test_list_templates, test_get_template_and_explain_safety, test_loop_with_profile_and_template. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/adaptive_execution/profiles.py` | Registry of execution profiles; `list_profiles()`, `get_profile()`, `get_profile_why_safe()`, `get_profile_when_blocked()`. |
| `src/workflow_dataset/adaptive_execution/templates.py` | Registry of loop templates; `list_templates()`, `get_template()`, `explain_template_safety(template_id, is_blocked, blocked_reason)`. |
| `src/workflow_dataset/adaptive_execution/explain_safety.py` | `explain_loop_safety(loop, is_blocked, blocked_reason)` and `format_safety_explanation()` for operator-facing text. |
| `docs/M45D1_EXECUTION_PROFILES_TEMPLATES_DELIVERABLE.md` | This deliverable. |

---

## 3. Sample execution profile

From `list_profiles()` → conservative `to_dict()`:

```json
{
  "profile_id": "conservative",
  "label": "Conservative",
  "description": "Low max steps, review before first step, simulate-first. Safest for unknown or high-stakes workflows.",
  "max_steps_cap": 5,
  "review_every_n_steps": 1,
  "require_review_before_first_step": true,
  "trust_mode": "simulate_first",
  "why_safe": "Conservative profile caps steps at 5 and requires review before the first step and after every step; all execution is simulate-first unless explicitly approved.",
  "when_blocked": "Not blocked by profile; use when you want maximum control and minimal autonomous progression."
}
```

---

## 4. Sample loop template

From `list_templates()` → weekly_summary `to_dict()`:

```json
{
  "template_id": "weekly_summary",
  "label": "Weekly summary",
  "description": "Bounded loop for generating or publishing a weekly summary.",
  "goal_hint": "Weekly summary",
  "default_profile_id": "balanced",
  "required_approval_scopes": ["checkpoint_before_real"],
  "max_steps_default": 10,
  "why_safe": "This template is safe because it uses a bounded step count and requires a checkpoint before any real (non-simulate) execution; the default profile adds plan checkpoints.",
  "why_blocked": "Blocked if approval registry or checkpoint policy is missing, or if the plan compiles to steps that require higher trust than the current tier."
}
```

---

## 5. Exact tests run

```bash
pytest tests/test_adaptive_execution.py -v
```

- **Existing (8):** test_adaptive_plan_creation, test_bounded_loop_enforcement, test_branch_fallback_behavior, test_stop_escalation_logic, test_no_loop_invalid_loop_behavior, test_blocked_step_handling, test_list_active_loops, test_mission_control_slice.
- **M45D.1 (5):** test_list_profiles, test_get_profile_why_safe, test_list_templates, test_get_template_and_explain_safety, test_loop_with_profile_and_template.

**Total: 13 passed.**

---

## 6. Next recommended step for the pane

- **Enforce required_approval_scopes:** When a loop is created from a template, check that the current trust/approval configuration satisfies the template’s `required_approval_scopes`; if not, set a “blocked” or “downgraded” state and surface `why_blocked` in explain and mission control.
- **Template-driven goal only:** Add a dedicated CLI path such as `adaptive-execution plans --template weekly_summary` (no `--goal`) that creates a loop from the template’s goal_hint and default profile only, and document that as the preferred way to start a templated workflow.
- **Mission control:** Include in the adaptive execution slice whether the active loop is using a profile/template and a one-line safety summary (e.g. “Template weekly_summary: safe when checkpoints and approval are in place”) so operators see why the loop is considered safe or blocked at a glance.
