# M37 Integration Pane Report — Pane 1 + 2 + 3

**Scope:** Integrate M37A–M37D (Default Experience), M37E–M37H (Signal Quality), M37I–M37L (State Durability) safely.

**Merge order:** Pane 1 → Pane 2 → Pane 3 (as specified).

---

## 1. Merge steps executed

- **No git merge was required.** The three blocks already coexist in the same codebase (branch `feat/ops-product-next-integration` or current working tree).
- **Integration validation performed:**
  - **Pane 1 (M37A–M37D + M37D.1):** Confirmed `default_experience` package (profiles, modes, surfaces, disclosure_paths, onboarding_defaults, calm_home, store); CLI under `defaults`; mission_control `default_experience_state`.
  - **Pane 2 (M37E–M37H + M37H.1):** Confirmed `signal_quality` package (attention, quieting, reports, scoring, profiles, budgets, explain); queue commands use quieting/resurfacing/focus-protection/profile/interruption-budget; mission_control `signal_quality` block.
  - **Pane 3 (M37I–M37L + M37L.1):** Confirmed `state_durability` package (boundaries, startup_health, resume_target, maintenance, compaction, profiles); CLI under `state`; mission_control `state_durability_state`.
- **Dependency order:** Default experience defines simplified mode and entry action; signal_quality consumes queue and optional workday mode; state_durability checks persistence boundaries and does not depend on default_experience or signal_quality. No circular dependency.

---

## 2. Files with conflicts

**None.** No merge conflicts. Integration is additive: separate CLI groups (`defaults`, `queue` with signal-quality commands, `state`) and separate mission_control state keys (`default_experience_state`, `signal_quality`, `state_durability_state`).

---

## 3. How each conflict was resolved

N/A — no conflicts. Design choices already present:

- **defaults vs day:** `defaults` group for default experience (apply profile, show, disclosure paths); `day` for workday state machine. Distinct.
- **queue:** Queue list/view/summary use signal_quality (quieting, quality report); suppressions, resurfacing, focus-protection, profile, interruption-budget are additive commands under `queue`.
- **state:** State health, snapshot, reconcile, startup-readiness, resume-target, maintenance-profiles, compaction-recommendations are under `state`; no name clash with other groups.
- **Report order:** [Signal quality], [State durability], [Default experience] appear in mission_control report; ordering is acceptable.

---

## 4. Tests run after each merge

Single validation slice (all three panes already in tree):

| Test target | Command | Result |
|-------------|---------|--------|
| Default experience | `pytest tests/test_default_experience.py -v` | **14 passed** |
| Signal quality | `pytest tests/test_signal_quality.py -v` | **22 passed** |
| State durability | `pytest tests/test_state_durability.py -v` | **15 passed** |
| Combined slice | `pytest tests/test_default_experience.py tests/test_signal_quality.py tests/test_state_durability.py -v` | **55 passed** |
| Mission control | `pytest tests/test_mission_control.py -v` | Run separately; may be slow (heavy aggregation). |

---

## 5. Final integrated command surface

**Pane 1 — Default experience (M37A–M37D + M37D.1)**  
- `workflow-dataset defaults show` — active profile, simplified mode, next default entry  
- `workflow-dataset defaults apply <profile>` — first_user | calm_default | full  
- `workflow-dataset defaults paths` — progressive disclosure paths  

**Pane 2 — Signal quality (M37E–M37H + M37H.1)**  
- Under **queue:** `queue list` (uses quieting/quality), `queue view`, `queue summary`, `queue quality`, `queue suppressions`, `queue resurfacing`, `queue focus-protection`, `queue profile`, `queue interruption-budget`  
- Mission control: `signal_quality` block (calmness, suppressed, resurfacing_candidates, focus_protected, top_high_signal)  

**Pane 3 — State durability (M37I–M37L + M37L.1)**  
- `workflow-dataset state health`  
- `workflow-dataset state snapshot [--save]`  
- `workflow-dataset state reconcile`  
- `workflow-dataset state startup-readiness`  
- `workflow-dataset state resume-target`  
- `workflow-dataset state maintenance-profiles [--profile <id>]`  
- `workflow-dataset state compaction-recommendations [--profile light|balanced|aggressive]`  
- Mission control: `state_durability_state` (ready, resume_target, warnings, recommended_recovery_action)  

**Mission control** aggregates all three: `default_experience_state`, `signal_quality`, `state_durability_state` in `get_mission_control_state()`; report prints [Signal quality], [State durability], [Default experience].

---

## 6. Remaining risks

- **Mission control latency:** Full state aggregation touches default_experience, signal_quality, state_durability, workday, continuity, and many other subsystems; first run can be slow.
- **Test env:** Use project venv (`.venv`) for pytest; system Python may lack dependencies.
- **Order of report sections:** Default experience appears after State durability in the report; operator may expect “defaults” earlier; optional reorder for UX.
- **Trust/review:** No change; local-first, inspectable, no hidden autonomy.

---

## 7. Exact recommendation for the next batch

1. **CI:** Add a job that runs the M37 integration slice:  
   `pytest tests/test_default_experience.py tests/test_signal_quality.py tests/test_state_durability.py -v`
2. **Optional:** In mission_control report, group [Default experience], [Signal quality], and [State durability] consecutively (e.g. after Workday/Continuity) so “simplified shell + queue calmness + durability” are read together.
3. **Next feature batch:** Wire default experience profile into state durability recommended first action (e.g. when profile is calm_default, recommend `defaults show` or calm_home entry); optionally persist active maintenance profile for compaction-recommendations default.
