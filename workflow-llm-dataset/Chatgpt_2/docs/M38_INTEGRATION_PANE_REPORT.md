# M38 Integration Pane Report — Cohort, Triage, Safe Adaptation

Integration of the three M38 panes in order: **Pane 1 (Cohort + Supported Surface)** → **Pane 2 (Evidence + Triage)** → **Pane 3 (Safe Adaptation + Boundary)**. The codebase is integrated on a single branch; this report validates integration points, test slices, and consistency.

---

## 1. Merge steps executed

| Step | Block | Action | Result |
|------|--------|--------|--------|
| 1 | Pane 1 (M38A–M38D + M38D.1) | Confirm cohort profiles, surface matrix, gates, transitions, store, explain, bindings; CLI `cohort` group; mission_control `cohort_state`. | Present and wired. |
| 2 | Pane 2 (M38E–M38H + M38H.1) | Confirm evidence capture, issue triage, classification, clusters, playbooks, health; CLI `triage` group; mission_control `triage` block and report. | Present and wired. |
| 3 | Pane 3 (M38I–M38L) | Confirm safe_adaptation models, boundary, store, review, candidates; CLI `adaptation` group; mission_control `adaptation_state` and report. | Present and wired. |
| 4 | Cross-pane | Confirm Pane 3 uses Pane 1 (cohort.surface_matrix, cohort.models) for boundary checks; Pane 2 uses cohort_id in evidence/issues; mission_control aggregates all three. | Dependencies correct. |

No git merges were performed (single branch). Validation followed the required merge order: Pane 1 → Pane 2 → Pane 3.

---

## 2. Files with conflicts

**None.** Integration is additive:

- **cli.py**: Three separate Typer groups (`triage_group`, `cohort_group`, `adaptation_group`) with no overlapping command names.
- **mission_control/state.py**: Three separate blocks (`cohort_state`, `triage`, `adaptation_state`); no shared keys.
- **mission_control/report.py**: Three separate sections ([Triage / Cohort health], [Safe adaptation], plus existing cohort_state usage elsewhere); no overlapping output keys.
- **safe_adaptation/boundary.py**: Imports only from `workflow_dataset.cohort.*` and `workflow_dataset.safe_adaptation.*`; no changes to cohort or triage.
- **triage/health.py**: Uses triage store/loop/models and references `supportability.supported_surface_involved`; no dependency on safe_adaptation.

No file required conflict markers or manual resolution.

---

## 3. How each conflict was resolved

Not applicable — no conflicts. Any future merge from a branch that adds the same command names or state keys should:

- Prefer **additive** command groups (e.g. keep both `cohort health` and `triage list`).
- Keep **cohort_state** and **triage** and **adaptation_state** as distinct top-level keys in mission_control state.
- If the same CLI name appears (e.g. two `cohort apply`), keep Pane 1 semantics for cohort profile apply and do not overload with adaptation apply (use `adaptation apply` for adaptation).

---

## 4. Tests run after each merge

| After block | Test slice | Command | Result |
|-------------|------------|---------|--------|
| Pane 1 | Cohort profiles, matrix, store, explain, gates, transitions | `python3 -m pytest tests/test_cohort.py -v` | **15 passed** |
| Pane 2 | Triage evidence, issues, classification, health | `python3 -m pytest tests/test_triage.py -v` | **Collection error**: `ModuleNotFoundError: No module named 'pydantic'` (test env missing pydantic). |
| Pane 3 | Safe adaptation candidates, boundary, quarantine, accept/reject/apply | `python3 -m pytest tests/test_safe_adaptation.py -v` | **9 passed** |
| Integration | Mission control state/report | `python3 -m pytest tests/test_mission_control.py -v` | **Slow** (state loads many subsystems); may fail if triage/pydantic not installed. |

**Note:** In an environment with `pydantic` (and other triage deps) installed, run the full slice:

```bash
python3 -m pytest tests/test_cohort.py tests/test_triage.py tests/test_safe_adaptation.py tests/test_mission_control.py -v
```

---

## 5. Final integrated command surface

All commands under `workflow-dataset` (entrypoint: `workflow-dataset` in pyproject.toml).

### Pane 1 — Cohort (M38A–M38D + M38D.1)

| Command | Purpose |
|---------|--------|
| `workflow-dataset cohort profiles` | List cohort profile ids |
| `workflow-dataset cohort show --id <id>` | Show one cohort profile |
| `workflow-dataset cohort matrix --id <id>` | Supported-surface matrix for cohort |
| `workflow-dataset cohort apply --id <id>` | Set active cohort profile |
| `workflow-dataset cohort explain [--surface <id>] [--id <cohort>]` | Explain surface or cohort scope |
| `workflow-dataset cohort gates [--id <cohort>]` | Readiness gates for cohort |
| `workflow-dataset cohort transitions [--id <cohort>]` | Escalation/downgrade transitions |
| `workflow-dataset cohort recommend [--id <cohort>]` | Recommended transition |
| `workflow-dataset cohort health [--cohort <id>]` | Cohort health summary (uses triage) |

### Pane 2 — Triage (M38E–M38H + M38H.1)

| Command | Purpose |
|---------|--------|
| `workflow-dataset triage list [--cohort] [--status] [--limit]` | List triage issues |
| `workflow-dataset triage show --id <id>` | Show one issue |
| `workflow-dataset triage classify --id <id> [--severity|--impact-scope|...]` | Classify issue |
| `workflow-dataset triage reproduce --id <id> [--steps]` | Mark reproduced |
| `workflow-dataset triage resolve --id <id>` | Mark resolved |
| `workflow-dataset triage clusters [--cohort] [--by subsystem|workflow|cohort]` | Issue clusters |
| `workflow-dataset triage playbook [--id <playbook_id>]` | Mitigation playbooks |
| `workflow-dataset triage do-now [--issue-id|--cluster-id]` | Operator do-now guidance |

### Pane 3 — Safe adaptation (M38I–M38L)

| Command | Purpose |
|---------|--------|
| `workflow-dataset adaptation candidates [--cohort] [--status] [--limit]` | List adaptation candidates |
| `workflow-dataset adaptation show --id <id>` | Show one candidate |
| `workflow-dataset adaptation boundary-check --id <id> [--cohort]` | Run boundary check |
| `workflow-dataset adaptation accept --id <id> [--rationale] [--delta]` | Accept candidate |
| `workflow-dataset adaptation reject --id <id> [--rationale]` | Reject candidate |
| `workflow-dataset adaptation quarantine --id <id> [--reason] [--notes]` | Quarantine candidate |
| `workflow-dataset adaptation apply --id <id> [--delta]` | Apply accepted candidate within boundaries |

**Registration order in cli.py:** `triage_group` → `cohort_group` → `adaptation_group` (adaptation commands are defined before cohort commands but all three groups are added to `app`). No name clashes.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Triage tests require pydantic** | Install project deps (e.g. `pip install -e .` or add pydantic to dev deps) so CI can run `test_triage.py`. |
| **Mission control state heavy** | `get_mission_control_state()` imports many subsystems; failures in one (e.g. triage) produce an `"error"` key in that block only; rest of state still returned. |
| **Adaptation apply is record-only** | `adaptation apply` records the decision and behavior delta but does not yet mutate pack/correction/preference stores; follow-up work to wire apply to real surfaces. |
| **CLI order vs merge order** | Logically Pane 1 (cohort) defines boundaries, Pane 2 (triage) captures evidence, Pane 3 (adaptation) uses both; CLI order (triage, cohort, adaptation) is cosmetic and does not affect behavior. |
| **Docs spread** | Cohort, triage, and safe adaptation are documented in separate M38* docs; consider a single M38_OVERVIEW.md for operators. |

---

## 7. Exact recommendation for the next batch

1. **Environment / CI**  
   - Ensure `pydantic` (and any other triage deps) are installed in the test environment so `tests/test_triage.py` and `tests/test_mission_control.py` run reliably.

2. **Apply wiring**  
   - In a follow-up task, wire `safe_adaptation.review.apply_within_boundaries` to the intended surfaces (e.g. pack defaults, personal_adaptation, or corrections) so that “apply” persists behavior changes within allowed cohort/surface boundaries.

3. **Optional: CLI order**  
   - If desired for narrative consistency, reorder in `cli.py` so that the **cohort** group is registered and defined first, then **triage**, then **adaptation**. This is optional; behavior is unchanged.

4. **Optional: M38 overview doc**  
   - Add `docs/M38_OVERVIEW.md` (or similar) that summarizes: cohort profiles and supported surfaces (Pane 1), evidence and triage (Pane 2), and safe adaptation and boundaries (Pane 3), with one-page operator guidance and pointers to existing M38* docs.

5. **No further merge**  
   - No additional M38 panes are required for this integration; the three blocks are coherent and additive. Future work (e.g. rollout gates, release/*, support/*) should continue to use cohort_id and supported-surface awareness where relevant.
