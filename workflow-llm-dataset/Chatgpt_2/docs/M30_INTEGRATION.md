# M30 Integration — Install/Upgrade + Reliability + Release Readiness

## 1. Merge steps executed

| Step | Description |
|------|-------------|
| **Merge 1 (Pane 1)** | Confirmed M30A–M30D (+ M30D.1) install/upgrade as base. Install bundle, current-version, upgrade-plan, upgrade-apply, rollback, migration-report, compatibility-matrix, channels are in place. Mission control already has `install_upgrade` block. Ran `tests/test_install_upgrade_m30.py` + `tests/test_mission_control.py`. **28 passed.** |
| **Merge 2 (Pane 2)** | Confirmed M30E–M30H (+ M30H.1) reliability harness and recovery. `reliability` group (list, run, report, degraded-profile, fallback-matrix) and `recovery` group (suggest, guide) are registered. Mission control already has `reliability` block (golden_path_health, release_confidence, top_recovery_case). Ran `tests/test_reliability.py`. **24 passed.** |
| **Merge 3 (Pane 3)** | Confirmed M30I–M30L (+ M30L.1) user release readiness and supportability. `release readiness`, `release pack`, `release supportability`, `release triage`, `release handoff-pack`, `release launch-profiles`, `release rollout-gates` are registered. Mission control already has `release_readiness` block. Ran `tests/test_release_readiness.py`. **15 passed.** |

All three panes were already present in the same tree; integration was **additive**. No git merge or branch switch was required. Validation confirmed no regressions and consistent CLI and mission_control surface.

---

## 2. Files with conflicts

**None.** No merge conflicts. No existing commands or behaviors were removed or replaced. Two separate “handoff pack” concepts coexist by design:

- **release_readiness.handoff_pack** — Operator handoff (artifacts list, summary); used by `release handoff-pack` and mission_control `release_readiness.handoff_pack_freshness`.
- **distribution.handoff_pack** — Pack-based handoff (build_handoff_pack by pack_id, write_handoff_pack); used by deploy/handoff flows elsewhere. No overlap in CLI surface.

---

## 3. How each conflict was resolved

N/A — no conflicts. Coexisting surfaces:

- **Release group**: Contains both install/upgrade (Pane 1) and release-readiness/supportability (Pane 3) commands; no name clashes.
- **Recovery group**: Standalone `recovery` (Pane 2); distinct from `progress recovery` (stalled-project recovery).
- **Mission control**: Three blocks — `install_upgrade`, `release_readiness`, `reliability` — all populated; report prints all three.

---

## 4. Tests run after each merge

| After | Command | Result |
|-------|---------|--------|
| Merge 1 | `pytest tests/test_install_upgrade_m30.py tests/test_mission_control.py -v` | 28 passed |
| Merge 2 | `pytest tests/test_reliability.py -v` | 24 passed |
| Merge 3 | `pytest tests/test_release_readiness.py -v` | 15 passed |
| Full slice | `pytest tests/test_install_upgrade_m30.py tests/test_mission_control.py tests/test_reliability.py tests/test_release_readiness.py -v` | **67 passed** |

---

## 5. Final integrated command surface

### Pane 1 — Install / upgrade (release)

- `workflow-dataset release install-bundle` [ `--bundle-id` ]
- `workflow-dataset release current-version` [ `--json` ]
- `workflow-dataset release upgrade-plan` [ `--target` ] [ `--current-channel` ] [ `--target-channel` ]
- `workflow-dataset release upgrade-apply` [ `--target` ]
- `workflow-dataset release rollback` [ `--checkpoint` ]
- `workflow-dataset release migration-report` [ `--json` ]
- `workflow-dataset release compatibility-matrix` [ `--json` ]
- `workflow-dataset release channels` [ `--json` ]

### Pane 2 — Reliability + recovery

- `workflow-dataset reliability list`
- `workflow-dataset reliability run --id <path_id>` [ `--no-save` ] [ `--output` ]
- `workflow-dataset reliability report` [ `--latest/--all` ] [ `--output` ]
- `workflow-dataset reliability degraded-profile` [ `--current` ] [ `--id <profile_id>` ]
- `workflow-dataset reliability fallback-matrix` [ `--subsystem` ]
- `workflow-dataset recovery suggest` [ `--case <id>` ] [ `--subsystem <subsystem>` ]
- `workflow-dataset recovery guide --case <case_id>`  

### Pane 3 — Release readiness / supportability (release)

- `workflow-dataset release readiness` [ `--output` ]
- `workflow-dataset release pack` [ `--output` ]
- `workflow-dataset release supportability` [ `--output` ]
- `workflow-dataset release triage` [ `--latest/--full` ] [ `--json` ]
- `workflow-dataset release handoff-pack` [ `--output-dir` ]
- `workflow-dataset release launch-profiles` [ `--json` ] [ `--output` ]
- `workflow-dataset release rollout-gates` [ `--profile` ] [ `--json` ] [ `--output` ]

### Mission control

- `workflow-dataset mission-control` — Report includes **[Install / upgrade]**, **[Release readiness]**, **[Reliability]** with version, upgrade/rollback, readiness status, handoff freshness, golden_path_health, top_recovery_case, and command hints.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Two handoff-pack concepts** | Documented: release_readiness handoff-pack = operator artifact summary; distribution handoff_pack = pack-based deploy handoff. Different CLIs and call sites. |
| **Recovery vs progress recovery** | `recovery suggest/guide` = reliability playbooks; `progress recovery` = stalled-project recovery. Both kept; names distinguish scope. |
| **Mission control state load** | All three blocks (install_upgrade, release_readiness, reliability) can raise; state catches and sets `error` key. Report shows error line. |
| **Trust/approval** | Unchanged: no auto-upgrade, no auto-apply from reliability or release readiness. Operator-driven. |

---

## 7. Exact recommendation for post-M30 next phase

1. **Single “release health” view**  
   Add a single command or mission_control section that summarizes in one place: install version + upgrade available, release readiness status, and last golden-path result (e.g. `workflow-dataset release health` or a dedicated report section).

2. **Wire reliability into upgrade flow**  
   Optionally run a golden-path check (e.g. `reliability run --id recovery_blocked_upgrade`) as a non-blocking step in upgrade-plan or post upgrade-apply, and surface result in migration-report or mission_control.

3. **Handoff-pack and install bundle**  
   Document or link release_readiness handoff-pack with install_upgrade (e.g. “after upgrade, run release handoff-pack to refresh operator handoff”). Optionally add a hint in migration-report or mission_control when upgrade was recently applied.

4. **CI integration**  
   Add a CI job that runs the full M30 slice:  
   `pytest tests/test_install_upgrade_m30.py tests/test_mission_control.py tests/test_reliability.py tests/test_release_readiness.py -v`  
   so changes to any pane are validated together.

5. **Next feature phase**  
   Proceed with the next product phase (e.g. M31 or later) using this integrated surface as the baseline; avoid adding duplicate “release” or “handoff” entry points without documenting the distinction.
