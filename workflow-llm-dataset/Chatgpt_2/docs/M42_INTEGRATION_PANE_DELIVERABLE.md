# M42 Integration Pane — Three-Pane Safe Integration Deliverable

Integration of:
1. **Pane 1** — M42A–M42D (+ M42D.1): Local Model Registry + Task-Aware Runtime Routing  
2. **Pane 2** — M42E–M42H (+ M42H.1): Candidate Model Studio + Local Training / Distillation Paths  
3. **Pane 3** — M42I–M42L (+ M42L.1): Benchmark Board + Promotion / Rollback Pipeline  

Branch: `feat/ops-product-next-integration`. Merge order: Pane 1 → Pane 2 → Pane 3 (runtime substrate → candidate improvements → promote/quarantine/rollback).

---

## 1. Merge steps executed

- The codebase on `feat/ops-product-next-integration` **already contains all three M42 panes**; there are no separate feature branches for each pane to merge. Integration is **single-branch additive**.
- **Logical merge order** is reflected in dependencies and CLI layout:
  - **Pane 1** (runtime_mesh + models registry/routing): Defines the local runtime/model substrate (backends, model catalog, task routing, vertical profiles, routing policies).
  - **Pane 2** (candidate_model_studio + model-studio CLI): Creates bounded candidate improvements from evidence (issue cluster, adaptation, correction set), training paths, safety profiles, lineage.
  - **Pane 3** (benchmark_board + benchmarks + models promote/rollback): Evaluates candidates, builds scorecards, and decides promote / rollback / quarantine / reject.
- **Registration order** in `cli.py`:
  - `model-studio` (10963) → `eval` (15368) → `benchmarks` (15697) → `models` (15843). The `models` group hosts both **registry/routing** (list, show, route, availability, fallback-report, runtime-profiles, routing-policies, policy-report) and **benchmark pipeline** (promote, rollback, quarantine, reject).
- **Mission control**: `candidate_model_studio_state` (4b), `runtime_mesh` (11), `benchmark_board_state` (M42I–M42L block). Separate state keys; each in its own try/except.

No git merge commands were run; this deliverable validates and documents the existing integrated state.

---

## 2. Files that are conflict hotspots (and how they were resolved)

| File | Risk | Resolution |
|------|------|------------|
| **cli.py** | Same group name or subcommand clash | **Additive.** Distinct groups: `model_studio_group` (model-studio), `eval_group` (eval), `benchmarks_group` (benchmarks), `models_benchmark_group` (models). The **models** group carries two concerns: (1) registry/routing (list, show, route, availability, fallback-report, runtime-profiles, routing-policies, policy-report) and (2) promotion pipeline (promote, rollback, quarantine, reject). Subcommand names do not overlap. |
| **mission_control/state.py** | Same state key or overwritten block | **Additive.** Separate keys: `candidate_model_studio_state`, `runtime_mesh`, `benchmark_board_state`. Each block in its own try/except. |
| **mission_control/report.py** | Same report section | **Additive.** Runtime mesh has a report block; benchmark board has `[Benchmark board]`. Candidate model studio does not yet have a dedicated report line (see remaining risks). |
| **runtime_mesh/* vs model-studio vs benchmark_board*** | Cross-import or circular dependency | **No circular dependency.** runtime_mesh is standalone; candidate_model_studio and benchmark_board are separate packages. Benchmark board pipeline (promote/rollback) uses benchmark_board store/scorecards; it does not import runtime_mesh or candidate_model_studio for core logic. |
| **learning-lab / council / adaptation / personal** | Shared “candidate” or “model” concepts | **Clear boundaries.** Learning lab = improvement experiments (experiment_id, outcome). Council = multi-perspective review (review_id, synthesis). Candidate model studio = candidate_id, training path, slice. Benchmark board = scorecards, tracks, promote/rollback. Naming is distinct; no shared mutable state. |
| **trust / policy / approvals** | Weakening trust or review | **Preserved.** Model studio uses safety_profiles (distillation safety); benchmark pipeline is explicit promote/rollback/quarantine/reject with no auto-apply. |
| **Docs** | Overlap or conflict | **Additive.** Separate docs for M42A–M42D, M42D.1, M42E–M42H, M42I–M42L; this integration doc is additive. |

**Summary:** Hotspots are resolved by **additive command groups**, **distinct state keys**, **distinct packages**, and **no circular imports**. The single shared surface is the **models** group, which is intentionally the “model lifecycle” surface: registry/routing + promotion pipeline.

---

## 3. How each conflict was resolved

- **CLI:** `model-studio` and `benchmarks` are separate groups. `models` is the unified entry for “things you do with models”: registry (list, show, route, availability, fallback-report, runtime-profiles, routing-policies, policy-report) and pipeline (promote, rollback, quarantine, reject). No subcommand name collision.
- **Mission control state:** Three keys; failures in one block do not affect the others.
- **Local-first / approval-gated / inspectable:** Preserved. No cloud inference or auto-download; promotion/rollback are explicit; routing and policy report are explainable.
- **No new cloud or trust weakening:** Confirmed.

---

## 4. Tests run after merge

**Command run:**

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_model_registry_routing.py tests/test_candidate_model_studio.py tests/test_benchmark_board.py -v --tb=short -q
```

**Result:** **39 passed** in ~0.24s.

| Suite | Tests | Result |
|-------|-------|--------|
| test_model_registry_routing.py | 14 | All passed (registry, routing, profiles, policies, route outcome, fallback) |
| test_candidate_model_studio.py | 15 | All passed (candidates, create, dataset, lineage, report, templates, safety profiles) |
| test_benchmark_board.py | 10 | All passed (slices, tracks, compare, scorecard, pipeline, shadow, promotion) |

---

## 5. Final integrated command surface

**Pane 1 — Model registry + routing** (`workflow-dataset models ...` and `workflow-dataset runtime ...`)

| Command | Purpose |
|---------|--------|
| `models list` | List local model registry entries |
| `models show --id <id>` | Show one model entry |
| `models route --task <family>` | Route task family (optional --vertical, --policy, --explain) |
| `models availability` | Backends and task-family route status |
| `models fallback-report` | Per-task primary, fallback chain, degraded |
| `models runtime-profiles` | Vertical runtime profiles |
| `models routing-policies` | Routing policies (conservative, balanced, eval_heavy, production_safe) |
| `models policy-report` | Effect of vertical + policy on routing |
| `runtime backends` / `runtime catalog` / `runtime recommend` / `runtime summary` / `runtime validate` | Existing runtime mesh surface |

**Pane 2 — Candidate model studio** (`workflow-dataset model-studio ...`)

| Command | Purpose |
|---------|--------|
| `candidates` | List candidate models |
| `create --from <source> --path <path>` | Create candidate (e.g. prompt_config_only, lightweight_distillation) |
| `dataset --id <id>` | List dataset slices for candidate |
| `lineage --id <id>` | Lineage summary |
| `report --id <id>` | Full candidate report |
| `templates` | List candidate templates |
| `safety-profiles` | List distillation safety profiles |

**Pane 3 — Benchmark board + promotion pipeline** (`workflow-dataset benchmarks ...` and `workflow-dataset models ...`)

| Command | Purpose |
|---------|--------|
| `benchmarks list` | List benchmark slices |
| `benchmarks compare` | Run baseline vs candidate |
| `benchmarks scorecard` | Build scorecard |
| `benchmarks tracks` | List promotion tracks |
| `benchmarks shadow-report` | Shadow run report |
| `benchmarks production-vs-candidate` | Production vs candidate comparison |
| `eval board` | Eval board (latest runs, recommendation) |
| `models promote` | Promote candidate (experimental / limited_cohort / production_safe) |
| `models rollback` | Roll back to prior |
| `models quarantine` | Quarantine candidate |
| `models reject` | Reject candidate |

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **models group has two concerns** | Registry/routing vs promote/rollback are both under `models` by design (model lifecycle). Keep help text and docs clear. |
| **Candidate model studio not in mission control report** | State is in `candidate_model_studio_state`; the mission control **report** text does not yet include a dedicated “[Candidate model studio]” line. Optional: add one line (e.g. top_candidate_id, next_eval_step). |
| **No formal link candidate → benchmark scorecard** | Candidates are created in model-studio; scorecards are built in benchmarks. Operator must know to run `benchmarks compare` / `scorecard` for a candidate then `models promote`. Optional: document the flow or add a “next recommended action” that suggests benchmark step when a candidate exists. |
| **Mission control load time** | `get_mission_control_state()` imports many subsystems; first call can be slow. Use timeouts in CI if needed. |

---

## 7. Exact recommendation for the next batch

1. **Add Candidate model studio to mission control report:** In `mission_control/report.py`, add a short “[Candidate model studio]” block (e.g. top_candidate_id, candidates_count, next_eval_step from `candidate_model_studio_state`).
2. **Document the end-to-end flow:** One-page “From evidence → candidate → scorecard → promote” (model-studio create → benchmarks compare/scorecard → models promote) so operators and panes share the same mental model.
3. **Optional: link routing to candidate creation:** When creating a candidate in model-studio, optionally pass or display the current routing policy/vertical so the “recommended model” for the candidate’s task family is visible (no mandatory code change; CLI/docs sufficient for first iteration).
4. **CI:** Add a job that runs `pytest tests/test_model_registry_routing.py tests/test_candidate_model_studio.py tests/test_benchmark_board.py` (e.g. 60s timeout) to protect the integrated M42 surface on every push.

These steps preserve local-first, approval-gated, and inspectable behavior without adding cloud or weakening trust boundaries.
