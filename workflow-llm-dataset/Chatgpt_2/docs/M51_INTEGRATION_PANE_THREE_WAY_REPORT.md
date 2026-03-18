# M51 Integration Pane — USB Bootstrap + Demo Onboarding + Investor Narrative

Report date: integration verified on current `workflow-llm-dataset` tree (feat/ops-product-next-integration).  
This documents **logical merge order** and **resolution principles**; the tree already reflects an additive integration (no pending three-way git merge in this snapshot).

---

## 1. Merge steps executed (logical order)

| Step | Pane | Integration action |
|------|------|-------------------|
| **1** | M51A–M51D | Landed `demo_usb` + `workflow-dataset demo` commands: `bootstrap`, `readiness`, `env-report`, `launch`, `degraded-report`, `profiles`, `playbook`, `safe-launch-guide`. Config: `configs/demo_usb.yaml`, `demo_usb_profiles.yaml`. |
| **2** | M51E–M51H | Nested **`demo onboarding`** under the same `demo` group: `start`, `role`, `bootstrap-memory`, `ready-state`, `sequence`, `user-preset`, workspace pack helpers. Package: `demo_onboarding/`. |
| **3** | M51I–M51L (+ M51L.1) | Added **separate** top-level group **`investor-demo`** (avoids Typer name collision with `demo`): `presenter-mode`, `script`, `cue`, `session`, `first-value`, `supervised-action`, `mission-control`, `sequence`. Package: `investor_demo/`. |

**Rationale:** Pane 1 owns portable launch; Pane 2 extends that group with bounded onboarding; Pane 3 is narrative on **installed repo state** and stays distinct from USB bundle paths.

---

## 2. Files with conflicts (hotspots)

| Hotspot | Nature |
|---------|--------|
| **`cli.py`** | **Name collision risk:** both Pane 1 and Pane 3 wanted `demo`. **Resolved** by keeping USB + onboarding under `demo` and placing investor walkthrough under `investor-demo`. |
| **Mission control / investor panel** | Investor demo **reads** MC state only; no overwrite of `mission_control/state.py` for demo-only behavior. |
| **Onboarding** | `onboard` (general first-run) vs `demo onboarding` (bounded demo). **Preserved both** — different entry points. |
| **Trust / action cards** | Investor supervised path uses **simulate-only / prefill** previews; no weakening of approval gates. |

No unresolved merge markers were present in the integrated tree at verification time.

---

## 3. How each conflict was resolved

| Issue | Resolution |
|-------|------------|
| **Two “demo” stories** | **Additive CLI:** `demo` = USB + demo onboarding; `investor-demo` = presenter narrative + 5-min script + session. |
| **Broadening vertical** | Investor flow narrows to chosen vertical / first-value signals from existing layers; no new broad browsing. |
| **Presentation vs trust** | No auto-execute; degraded mode explicitly surfaced in presenter bridge and script beats. |
| **Degraded USB vs degraded repo** | USB: `demo readiness` / `demo degraded-report`. Repo narrative: `investor-demo cue` + collect_degraded_warnings on product repo. |

---

## 4. Tests run after each merge (representative slice)

After integration verification, the following **single slice** was run (covers all three panes):

```bash
cd workflow-llm-dataset && python3 -m pytest \
  tests/test_demo_usb.py \
  tests/test_demo_usb_profiles_m51d1.py \
  tests/test_demo_onboarding.py \
  tests/test_demo_onboarding_m51h1.py \
  tests/test_investor_demo.py \
  tests/test_investor_demo_presenter_m51l1.py \
  -v
```

**Result: 46 passed.**

Suggested **per-pane** regression (if splitting CI stages):

- After Pane 1: `pytest tests/test_demo_usb.py tests/test_demo_usb_profiles_m51d1.py`
- After Pane 2: `pytest tests/test_demo_onboarding.py tests/test_demo_onboarding_m51h1.py`
- After Pane 3: `pytest tests/test_investor_demo.py tests/test_investor_demo_presenter_m51l1.py`

---

## 5. Final integrated demo command surface

### A. USB / environment (spare laptop, bundle root)

```text
workflow-dataset demo bootstrap
workflow-dataset demo readiness
workflow-dataset demo env-report
workflow-dataset demo launch
workflow-dataset demo degraded-report
workflow-dataset demo profiles --list
workflow-dataset demo playbook --list
workflow-dataset demo safe-launch-guide
```

### B. Bounded demo onboarding (after bootstrap path)

```text
workflow-dataset demo onboarding start
workflow-dataset demo onboarding role --id <preset>
workflow-dataset demo onboarding bootstrap-memory
workflow-dataset demo onboarding ready-state
workflow-dataset demo onboarding sequence
workflow-dataset demo onboarding user-preset --id <id>
```

### C. Investor narrative (product repo / post–package first-run)

```text
workflow-dataset investor-demo presenter-mode --on
workflow-dataset investor-demo session start --presenter
workflow-dataset investor-demo script
workflow-dataset investor-demo cue
workflow-dataset investor-demo session stage
workflow-dataset investor-demo first-value
workflow-dataset investor-demo supervised-action
workflow-dataset investor-demo mission-control
workflow-dataset investor-demo sequence
```

**Handoff:** After USB path + `package first-run` + `onboard bootstrap` (per `demo launch`), run **investor-demo** from the **bundle/repo root** used for the meeting.

---

## 6. Remaining risks before live investor demo

1. **Wrong working directory** — Investor commands need the real `pyproject.toml` repo root; USB bundle alone may not expose full vertical_excellence signals.
2. **Cold continuity** — MC “memory” lines thin without prior local use; script beats already say to narrate honestly.
3. **Env degraded** — USB `readiness` blocked vs repo `required_ok` false; disclose once, continue (script + presenter bridge).
4. **Vertical not locked** — Weaker first-value story; lock or narrate “imagine locked vertical.”
5. **Time drift** — 5-minute script is timing guidance only; rehearse once on target hardware.

---

## 7. Exact recommendation for demo rehearsal on the spare laptop

1. Copy USB bundle; set `WORKFLOW_DEMO_BUNDLE_ROOT` or `cd` to bundle; run **`workflow-dataset demo bootstrap`** then **`workflow-dataset demo readiness`** (expect full or degraded, not blocked).
2. Follow **`workflow-dataset demo launch`** printed steps (`package first-run`, `onboard bootstrap`, optional quickstart).
3. Run **`workflow-dataset demo onboarding sequence`** once to validate role + memory bootstrap path.
4. **`workflow-dataset investor-demo sequence`** — rehearse full 5 minutes: presenter-mode on → session start --presenter → script (read once) → loop cue / stage / run lines → first-value → supervised-action → mission-control.
5. If anything is yellow: read **`investor-demo script`** “IF DEGRADED” line for that beat once, then continue—do not improvise trust posture.
