# M28L.1 — Policy Presets + Trust Modes

First-draft presets and trust-mode explanations extending the M28I–M28L human policy engine. Do not rebuild the engine; presets are named templates that produce a full `HumanPolicyConfig`.

---

## Presets (trust modes)

| Preset id | Description |
|-----------|-------------|
| `strict_manual` | All actions require explicit approval; no batch, no delegation, no worker lanes. |
| `supervised_daily_operator` | Batch low-risk simulate/plan; trusted real and resume still manual; no delegation. |
| `bounded_delegation` | Delegation and worker lanes allowed with approval; batch medium-risk; trusted real manual. |
| `demo_mode` | Relaxed for demos: simulate/plan auto; delegation allowed; trusted real requires approval. |
| `rollout_safe_mode` | Rollout-safe: batch low only; no delegation; keep projects simulate-only until explicitly allowed. |

---

## 1. Sample preset definition (internal)

Each preset is built in code as a `HumanPolicyConfig`. Conceptually, `strict_manual` is equivalent to:

```json
{
  "active_preset": "strict_manual",
  "approval_defaults": {
    "scope": "global",
    "always_manual": true,
    "may_batch_for_risk": ""
  },
  "delegation_default": { "scope": "global", "may_delegate": false },
  "action_class_policies": [
    { "action_class": "execute_simulate", "allow_auto": false, "require_approval": true, "allow_batch": true },
    { "action_class": "execute_trusted_real", "allow_auto": false, "require_approval": true, "allow_batch": false },
    { "action_class": "delegate_goal", "allow_auto": false, "require_approval": true, "allow_batch": false },
    { "action_class": "use_worker_lane", "allow_auto": false, "require_approval": true, "allow_batch": false }
  ],
  "project_simulate_only": {},
  "pack_may_override_defaults": {}
}
```

Applying a preset overwrites `data/local/human_policy/policy_config.json` with that preset’s full config and sets `active_preset` to the preset id.

---

## 2. Sample trust-mode explanation output

**Command:** `workflow-dataset policy trust-mode --preset strict_manual`

```
Trust mode explanation

  Trust mode: strict_manual

  Approval defaults:
    always_manual: True
    may_batch_for_risk: (none)

  Delegation:
    may_delegate: False

  Simulate vs trusted-real posture:
    execute_simulate: require_approval=True allow_auto=False allow_batch=True
    execute_trusted_real: require_approval=True allow_auto=False allow_batch=False

  Pack / worker-lane restrictions:
    pack_may_override_defaults: (none)
    delegate_goal: require_approval=True allow_batch=False
    use_worker_lane: require_approval=True allow_batch=False

  Project simulate_only (project_id -> must stay simulate):
    (none)
```

**Command (current config):** `workflow-dataset policy trust-mode`  
Output is the same structure, with `Trust mode: <active_preset>` or `Trust mode: custom` when no preset is set.

---

## CLI

- `workflow-dataset policy presets` — list presets and descriptions  
- `workflow-dataset policy apply-preset --name <id>` — apply a preset (overwrites config)  
- `workflow-dataset policy trust-mode [--preset <id>]` — explain trust mode (current or named preset)

---

## Tests

```bash
python3 -m pytest tests/test_human_policy.py -v
```

Preset/trust-mode tests: `test_list_presets`, `test_get_preset_config`, `test_apply_preset`, `test_trust_mode_explanation_preset`, `test_trust_mode_explanation_current`.
