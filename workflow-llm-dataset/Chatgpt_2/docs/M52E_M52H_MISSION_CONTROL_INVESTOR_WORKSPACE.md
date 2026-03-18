# M52E–M52H — Mission-Control Workspace + Role/Memory Demo Surfaces

## BEFORE CODING (summary)

### 1. Product states represented
- **Readiness** — `demo_usb` capability (full / degraded / blocked).
- **Role** — demo onboarding session + role preset (label, vertical pack, one-liner).
- **Memory bootstrap** — bounded scan counts, themes/context/priorities as plain bullets.
- **Ready-to-assist** — completion gate from demo onboarding.
- **First value** — humanized from `recommended_first_value_action` (not benchmark next-action).
- **Trust** — simulate-first / demo conservative copy from preset.
- **Timeline** — env → role → memory → assist (synthetic from real flags).
- **Side panel** — inbox count summary only (no dump).

### 2. Investor-friendly vs internal
| Friendly (surfaced) | De-emphasized / not hero |
|----------------------|---------------------------|
| Role label, pack display name | Raw preset IDs in body copy |
| “Sample workspace understood” | Memory substrate / graph internals |
| First-value headline + why | `mission-control` eval runs, regressions |
| Trust “you stay in control” | Benchmark trust status strings |

### 3. File plan
`investor_mission_control/{models,surfaces,build,render}.py`, CLI `demo mission-control-home`, `edge_desktop` snapshot key, tests, this doc.

### 4. Safety
Read-only aggregation; no new execution paths; inbox capped; honest when bootstrap incomplete.

### 5. Principles
Scan in &lt;10s, premium tone, bounded/honest memory, no fake capabilities.

### 6. NOT done
Live adapter layer, new roles/verticals, replacement for full `workflow-dataset mission-control`.

---

## FINAL OUTPUT

### 1. Files modified
- `src/workflow_dataset/cli.py` — `demo mission-control-home`
- `src/workflow_dataset/edge_desktop/snapshot.py` — `investor_mission_control_home`

### 2. Files created
- `src/workflow_dataset/investor_mission_control/__init__.py`
- `models.py`, `surfaces.py`, `build.py`, `render.py`
- `tests/test_investor_mission_control.py`
- `docs/M52E_M52H_MISSION_CONTROL_INVESTOR_WORKSPACE.md`

### 3. Mission-control surface structure
| Block | Model | Source |
|-------|-------|--------|
| Device | `ReadinessStateSnapshot` | `demo_usb` readiness |
| Role | `RoleStateSurface` | session + `RolePreset` |
| Memory | `MemoryBootstrapSurface` | bootstrap summary + RTA bullets |
| Assist | `ReadyToAssistSurface` | `build_completion_state` + RTA |
| First value | `FirstValueSurface` | humanized CLI command |
| Trust | `TrustPostureSurface` | preset trust |
| Timeline | `ActivityTimelineState` | derived steps |
| Side | `MissionControlSidePanelState` | inbox count |

### 4. Cards / regions
- **Role card** — label, vertical pack display, description line.
- **Memory card** — headline, up to 4 “what we noticed” bullets, bounded note.
- **First-value card** — headline, why, command, what happens next.
- **Trust strip** — headline + body.

### 5. How current outputs map
- `ReadyToAssistState` → assist + memory bullets + first command.
- `build_readiness_report` → device strip only.
- `build_inbox` → side panel count line.
- **Not** using `recommend_next_action` / evaluation state for hero.

### 6. Live data wiring still needed
- Richer **activity timeline** (real timestamps from session file mtimes).
- **User preset** display when `demo_user_preset_id` set.
- Desktop shell **multi-panel** binding from `to_dict()` JSON.

### 7. Next step for adapter integration
Subscribe Edge Operator Desktop shell to `build_edge_desktop_snapshot()["investor_mission_control_home"]` and map keys to docked panels; wire primary CTA to `first_value.command` execution when adapter allows.

---

## CLI

```bash
workflow-dataset demo mission-control-home
workflow-dataset demo mission-control-home --json
workflow-dataset demo mission-control-home --compact
```

## Tests

```bash
python3 -m pytest tests/test_investor_mission_control.py -v --tb=short
```
