# M51D.1 — Demo Bundle Profiles + USB Launch Playbooks

Extends M51A–M51D without rebuilding bootstrap. Adds profiles, playbooks, safe-launch operator guidance.

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Merged duplicate `demo` Typer into one group: USB commands + `demo profiles`, `demo playbook`, `demo safe-launch-guide`; enhanced `demo launch` with suggested profile/playbook. |

## 2. Files created

| File | Purpose |
|------|---------|
| `configs/demo_usb_profiles.yaml` | Profiles (`full_demo`, `lightweight_demo`, `degraded_laptop_demo`) + playbooks (`usb_fresh_laptop`, `usb_lightweight`, `usb_degraded_honest`). |
| `src/workflow_dataset/demo_usb/profiles_playbooks.py` | Load YAML, suggest profile/playbook from readiness, format text. |
| `tests/test_demo_usb_profiles_m51d1.py` | Profile/playbook/suggestion tests. |
| `docs/M51D1_DEMO_PROFILES_PLAYBOOKS_DELIVERABLE.md` | This doc. |

## 3. Sample demo bundle profile (excerpt)

```yaml
full_demo:
  label: "Full demo"
  summary: "Best laptop: writable bundle copy, Python 3.10+, optional LLM config..."
  when_to_use: "Conference room machine or prepared Mac/Windows laptop..."
  capability_hint: "full"
  command_hints:
    - "demo bootstrap"
    - "demo onboarding start"
```

## 4. Sample USB launch playbook (excerpt)

**`usb_fresh_laptop`**

1. Copy bundle if USB is read-only  
2. Create isolated venv  
3. Install minimal CLI deps  
4. `workflow-dataset demo env-report`  
5. `demo bootstrap` → `demo readiness`  
6. Pick profile + `demo playbook --profile <id>`  
7. `demo onboarding start` → …

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_demo_usb.py tests/test_demo_usb_profiles_m51d1.py -v --tb=short
```

**Result:** 16 passed.

**Note:** `profiles_playbooks.py` embeds a minimal default when `configs/demo_usb_profiles.yaml` cannot be parsed (e.g. PyYAML missing); with PyYAML, the YAML file is authoritative.

## 6. Next recommended step for the pane

- Wire **one printed QR or one-pager PDF** for investors that points to `demo safe-launch-guide` + `demo playbook --id auto`.
- Optional: **`demo match`** command that prints single line: profile + playbook + next command from live `readiness`.

## CLI usage

```bash
workflow-dataset demo profiles              # list
workflow-dataset demo profiles --show full_demo
workflow-dataset demo playbook --list
workflow-dataset demo playbook --id usb_fresh_laptop
workflow-dataset demo playbook --id auto   # from readiness
workflow-dataset demo playbook --id usb_lightweight --profile lightweight_demo
workflow-dataset demo safe-launch-guide
workflow-dataset demo launch                 # includes suggested profile/playbook
```
