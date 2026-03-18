# M42D.1 — Routing Policies + Vertical Runtime Profiles (Deliverable)

Extension to M42A–M42D model registry/runtime routing. Adds vertical-specific runtime profiles, routing policies (conservative, balanced, eval-heavy, production-safe), and stronger route explanation (preferred / allowed / degraded / blocked + reason_why).

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/runtime_mesh/routing.py` | Import `get_vertical_profile`, `get_routing_policy`. `route_for_task(..., vertical_id=, routing_policy_id=)`; filter candidates by vertical (allowed_backends, allowed_task_families); apply policy (prefer_production_safe_only, allow_degraded_fallback, block_when_no_production_safe). Added `_build_route_outcome()`; return `route_outcome`, `reason_why`, `vertical_id`, `routing_policy_id`. `explain_route(..., vertical_id=, routing_policy_id=)`. Constants `ROUTE_OUTCOME_PREFERRED/ALLOWED/DEGRADED/BLOCKED`. |
| `src/workflow_dataset/runtime_mesh/__init__.py` | Exported `list_vertical_profiles`, `list_routing_policies`, `get_vertical_profile`, `get_routing_policy`, `build_routing_policy_report`, `ROUTE_OUTCOME_*`. |
| `src/workflow_dataset/cli.py` | `models route`: added `--vertical`, `--policy`; print `outcome` and `reason`; extended explanation. New commands: `models runtime-profiles`, `models routing-policies`, `models policy-report` (--vertical, --policy). |
| `tests/test_model_registry_routing.py` | 4 new tests: vertical profiles and routing policies list/get, route returns route_outcome/reason_why, route with policy and vertical, routing policy report. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/runtime_mesh/profiles_and_policies.py` | `VerticalRuntimeProfile`, `RoutingPolicy`; built-in `VERTICAL_RUNTIME_PROFILES` (default, document_workflow, codebase, council_eval), `ROUTING_POLICIES` (conservative, balanced, eval_heavy, production_safe); `list_vertical_profiles`, `get_vertical_profile`, `list_routing_policies`, `get_routing_policy`, `build_routing_policy_report`. |
| `docs/M42D1_ROUTING_POLICIES_AND_PROFILES_DELIVERABLE.md` | This file. |

---

## 3. Sample runtime profile

**Vertical: council_eval**

```python
VerticalRuntimeProfile(
    vertical_id="council_eval",
    label="Council / evaluation",
    allowed_backends=["ollama", "repo_local"],
    allowed_task_families=["review", "evaluation", "council"],
    required_production_safe=True,
    notes="Council review and evaluation; production-safe only.",
)
```

**CLI:** `workflow-dataset models runtime-profiles`

```
Vertical runtime profiles  count=4
  default  Default  allowed_backends=all  allowed_task_families=all
  document_workflow  Document workflow  allowed_backends=['ollama', 'repo_local']  allowed_task_families=['summarization', 'vertical_workflow']
  codebase  Codebase  allowed_backends=['ollama', 'repo_local', 'llama_cpp']  allowed_task_families=['suggestion', 'vertical_workflow', 'adaptation_comparison']
  council_eval  Council / evaluation  allowed_backends=['ollama', 'repo_local']  allowed_task_families=['review', 'evaluation', 'council']
```

---

## 4. Sample routing policy report

**CLI:** `workflow-dataset models policy-report --policy conservative`

```
Routing policy report  vertical=default  policy=conservative
  Policy conservative: prefer_production_safe=True, allow_degraded=False, block_when_no_production_safe=True. 
```

**CLI:** `workflow-dataset models policy-report --vertical council_eval --policy production_safe --json`

```json
{
  "vertical_id": "council_eval",
  "vertical_profile": {
    "vertical_id": "council_eval",
    "label": "Council / evaluation",
    "allowed_backends": ["ollama", "repo_local"],
    "allowed_task_families": ["review", "evaluation", "council"],
    "required_production_safe": true,
    "notes": "Council review and evaluation; production-safe only."
  },
  "policy_id": "production_safe",
  "routing_policy": {
    "policy_id": "production_safe",
    "label": "Production-safe",
    "allow_experimental_models": false,
    "prefer_production_safe_only": true,
    "allow_degraded_fallback": true,
    "eval_task_families_priority": [],
    "block_when_no_production_safe": true,
    "notes": "Production-safe only; allow degraded fallback to next production-safe option."
  },
  "effect_summary": "Policy production_safe: prefer_production_safe=True, allow_degraded=True, block_when_no_production_safe=True. Vertical council_eval: allowed_backends=['ollama', 'repo_local'], allowed_task_families=['review', 'evaluation', 'council']."
}
```

---

## 5. Stronger route explanation (preferred / allowed / degraded / blocked)

**CLI:** `workflow-dataset models route --task planning --explain --policy balanced`

Example output:

```
Route   task_family=planning  policy=balanced
  primary_model=llama3.2  primary_backend=ollama  status=missing
  fallback_chain=[]  is_degraded=True
  outcome=degraded  reason=Primary backend is missing or unavailable; using degraded fallback or suggestion.
  task_family=planning -> task_class=plan_run_review -> capability=safety_guardrail; ... Outcome: degraded. Primary backend is missing or unavailable; using degraded fallback or suggestion.
```

Route result now includes:
- **route_outcome**: `preferred` | `allowed` | `degraded` | `blocked`
- **reason_why**: Short explanation (e.g. "Primary model and backend are available; route is preferred." or "Policy does not allow degraded fallback; primary backend is unavailable.")

---

## 6. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_model_registry_routing.py -v --tb=short
```

**Result:** 14 passed (10 existing + 4 for M42D.1).

New tests:
- `test_vertical_profiles_and_routing_policies` — list/get vertical profiles and routing policies
- `test_route_returns_outcome_and_reason_why` — route has route_outcome in {preferred, allowed, degraded, blocked} and reason_why string
- `test_route_with_policy_and_vertical` — route_for_task with vertical_id and routing_policy_id
- `test_routing_policy_report` — build_routing_policy_report returns vertical_profile, routing_policy, effect_summary

---

## 7. Next recommended step for the pane

- **Persist current policy/vertical:** Add a small state file (e.g. `data/local/runtime/current_routing_policy.txt` and `current_vertical.txt`) and `models policy-set`, `models vertical-set` so that downstream callers (e.g. council, learning lab) can read “current” policy/vertical without passing flags every time. Keep override-by-flag in `models route`.
- **Mission control visibility:** Add to `runtime_mesh` state (or a dedicated block) the current routing policy id, current vertical id, and a one-line “route outcome summary” (e.g. how many task families are preferred vs degraded vs blocked under current policy).
- **Wire to council/learning lab:** When running council review or learning-lab experiment comparison, optionally pass `vertical_id=council_eval` and `routing_policy_id=production_safe` into routing so the recommended model for that flow is policy- and vertical-aware.

These steps keep routing explicit and inspectable while making policy/vertical the default for the product pane.
