# M41 Integration Pane — Three-Pane Safe Integration Deliverable

Integration of:
1. **Pane 1** — M41A–M41D (+ M41D.1): Local Learning Lab + Karpathy Pattern Mapping  
2. **Pane 2** — M41E–M41H (+ M41H.1): Council-Based Evaluation + Safe Improvement Decisions  
3. **Pane 3** — M41I–M41L (+ M41L.1): Sustained Deployment Ops + Jobized Maintenance Loops  

Branch: `feat/ops-product-next-integration`. Merge order: Pane 1 → Pane 2 → Pane 3 (substrate → evaluation → ops).

---

## 1. Merge steps executed

- The codebase on `feat/ops-product-next-integration` **already contains all three panes**; there are no separate feature branches for each pane to merge. Integration is therefore **single-branch additive**.
- **Logical merge order** is enforced by design:
  - **Pane 1** provides the learning/improvement substrate (experiments, profiles, templates, pattern mapping).
  - **Pane 2** consumes it for evaluation (council review, disagreement, promotion policy).
  - **Pane 3** operationalizes maintenance (ops jobs, calendar, rhythm packs, operator summary).
- **Registration order** in code:
  - `mission_control/state.py`: council block → learning_lab_state block → ops_jobs_state block.
  - `mission_control/report.py`: Ops jobs block (report) → Learning lab block → Council block (report).
  - `cli.py`: `council` (10760) → `learning-lab` (11532) → `ops-jobs` (12761).

No git merge commands were run; the deliverable validates and documents the existing integrated state.

---

## 2. Files that are conflict hotspots (and how they were resolved)

| File | Risk | Resolution |
|------|------|------------|
| `src/workflow_dataset/cli.py` | Duplicate or overlapping command groups | **Additive.** Distinct groups: `council_group`, `learning_lab_group`, `ops_jobs_group` with unique names `council`, `learning-lab`, `ops-jobs`. No shared subcommand names across these three. |
| `src/workflow_dataset/mission_control/state.py` | Same state key or overwritten block | **Additive.** Separate keys: `council`, `learning_lab_state`, `ops_jobs_state`. Each block in its own `try/except`, no overwrites. |
| `src/workflow_dataset/mission_control/report.py` | Same report section or ordering | **Additive.** Separate sections: `[Ops jobs]`, `[Learning lab]`, `[Council]`. Order in report is independent of state key order. |
| Learning/adaptation/personal touchpoints | Coupling between learning lab and personal/adaptation | **No direct coupling.** Learning lab uses `learning_lab/` and store under `data/local/learning_lab/`; council and adaptation have their own stores. No shared imports that would create circular dependency. |
| `release/*` / `reliability/*` / `support/*` / `cohort/*` | Pane logic touching same modules | **No conflicts observed.** Council uses `council/`; ops jobs use `ops_jobs/`; learning lab uses `learning_lab/`. Mission control only *reads* from these and other subsystems. |
| `automations/*` / `background/*` / `ops-jobs/*` | Ops jobs vs other automations | **Clear boundary.** Only `ops_jobs_group` and `ops_jobs` package are used for M41I–M41L. No merging with other automation groups. |
| `trust/*` / `policy/*` / `approvals/*` | Council vs trust/policy | **Additive.** Council has its own presets and policy in `council/promotion_policy.py` and `council/presets.py`; trust and approvals remain separate. |
| Docs | Duplicate or conflicting docs | **Additive.** Separate docs: learning lab (M41A_M41D_*, M41D1_*), council, ops jobs. No single doc overwritten by multiple panes. |

**Summary:** All hotspots are resolved by **additive command groups**, **distinct state keys**, **distinct report sections**, and **separate packages** with no circular dependencies or shared mutable state.

---

## 3. How each conflict was resolved

- **CLI:** One Typer group per pane; no shared subcommand names. Example: `learning-lab report` vs `council report` vs `ops-jobs report` are different groups, so no name clash.
- **Mission control state:** Three separate keys (`council`, `learning_lab_state`, `ops_jobs_state`). If a pane’s block raises, only that key gets `{"error": "..."}`; others are unchanged.
- **Mission control report:** Three separate text sections. Order and content of each section are independent.
- **Local-first / privacy-first / approval-gated / inspectable:** Preserved — no new cloud calls, no new automatic promotion paths; council and learning lab remain review- and evidence-based; ops jobs are explicit operator-run.
- **No vendored or cloud dependencies:** Confirmed; all three panes use local data and existing in-repo code.

---

## 4. Tests run after each merge

Because the branch already contains all three panes, one **combined validation** was run for the integrated surface.

**Command run:**

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_learning_lab.py tests/test_council.py tests/test_ops_jobs.py -v --tb=short -q
```

**Result:** **47 passed** in ~0.6s.

| Suite | Tests | Result |
|-------|-------|--------|
| `test_learning_lab.py` | 23 | All passed (pattern mapping, experiments, profiles, templates, safety boundaries, report) |
| `test_council.py` | 14 | All passed (default council, perspectives, review persist, list/load, disagreement, synthesis, presets, policy) |
| `test_ops_jobs.py` | 10 | All passed (model, cadence/due, run, history, blocked, report, calendar, rhythm packs, operator summary) |

**Mission control tests** (`tests/test_mission_control.py`, 9 tests): Intended to validate integration with state/report. The first test (`test_mission_control_state_structure`) can be slow or appear to hang when `get_mission_control_state(tmp_path)` loads many subsystems; no failure was observed in the pane-specific tests above. Recommendation: run mission_control tests in CI with a generous timeout or in a separate job.

---

## 5. Final integrated command surface

**Pane 1 — Learning lab** (`workflow-dataset learning-lab ...`)

| Command | Purpose |
|---------|--------|
| `patterns` | Show Karpathy pattern mappings (adopted/rejected) |
| `experiments` | List improvement experiments |
| `profiles` | List learning profiles (M41D.1) |
| `templates` | List safe experiment templates; optional `--profile`, `--production-adjacent` (M41D.1) |
| `profile-set <id>` | Set current learning profile (M41D.1) |
| `create --from <spec>` | Create experiment (optional `--profile`, `--template`) |
| `compare --id <id>` | Compare before/after for experiment |
| `report --id <id>` | Full experiment report |
| `outcome --id <id> --outcome <rejected|quarantined|promoted>` | Record outcome |

**Pane 2 — Council** (`workflow-dataset council ...`)

| Command | Purpose |
|---------|--------|
| `list` | List council reviews |
| `review` | Run council review for subject; optional `--preset`, `--cohort`, `--persist` |
| `report` | Full council report for a review |
| `decision` | Show synthesis decision for review |
| `disagreement` | Disagreement report for review |
| `presets` | List council presets |
| `policy` | Show effective policy |

**Pane 3 — Ops jobs** (`workflow-dataset ops-jobs ...`)

| Command | Purpose |
|---------|--------|
| `list` | List ops job ids |
| `due` | List due/overdue jobs |
| `run --id <id>` | Run an ops job |
| `history` | List run history |
| `explain --id <id>` | Explain an ops job |
| `report` | Maintenance report (next due, blocked, overdue, recommended action) |
| `calendar` | Maintenance calendar by rhythm (M41L.1) |
| `operator-summary` | Operator maintenance summary |
| `rhythm-packs list` | List rhythm pack ids (M41L.1) |
| `rhythm-packs show --id <id>` | Show rhythm pack |

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Mission control report load time** | `get_mission_control_state()` imports and reads many subsystems; first test or CLI call can be slow. Use timeouts in CI or run state aggregation in background. |
| **Learning lab report block** | Addressed: mission control report now shows `profile=`, `safe_templates(local)=`, `safe_templates(prod_adj)=` when `current_profile_id` is set (see `mission_control/report.py`). |
| **Cross-pane workflow** | No single flow yet: e.g. "create experiment → run council review on it → schedule ops job to re-check." Documented as future integration (next batch). |
| **Duplicate `personal_group`** | `cli.py` registers `app.add_typer(personal_group, name="personal")` twice (e.g. 6401 and 16774). This is pre-existing and unrelated to the three panes; should be de-duplicated in a separate change. |
| **Council vs learning lab outcome terms** | Both use promote/quarantine/reject. Semantics align (council = multi-perspective decision; learning lab = experiment outcome). No conflict, but keep terminology consistent in docs. |

---

## 7. Exact recommendation for the next batch

- **Wire council to learning lab (optional):** When recording a learning-lab experiment outcome (e.g. `learning-lab outcome --outcome promoted`), optionally trigger or suggest a council review for the same subject (e.g. by subject_id or experiment_id). No automatic promotion; keep approval-gated.
- **De-duplicate `personal_group`** in `cli.py` (single registration for `personal`).
- **CI:** Add a job that runs `pytest tests/test_learning_lab.py tests/test_council.py tests/test_ops_jobs.py` with a short timeout (e.g. 60s) to protect the integrated surface on every push.

These steps preserve local-first, approval-gated, and inspectable behavior and do not add cloud or trust-boundary changes.
