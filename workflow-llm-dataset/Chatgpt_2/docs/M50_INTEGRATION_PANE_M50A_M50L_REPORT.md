# M50 integration pane — M50A–M50L (three panes)

**Role:** Integrate Pane 1 (v1 contract freeze), Pane 2 (v1 ops/support), Pane 3 (stable v1 gate / release decision) safely.

---

## 1. Merge steps executed

| Step | Intended content | Git reality in this repo |
|------|------------------|-------------------------|
| **1 — Pane 1** | M50A–M50D: `v1_contract/`, production-cut adjacency, freeze report, communication pack (M50D.1) | No separate `pane-1` branch. Code lives under `workflow-llm-dataset/` (often **untracked** until committed). |
| **2 — Pane 2** | M50E–M50H: `v1_ops/`, support posture, maintenance packs, obligations | Same: co-located with Pane 1 on working tree / `feat/ops-product-next-integration`. |
| **3 — Pane 3** | M50I–M50L: `stable_v1_gate/`, final evidence, gate, decision, watch-state | Same. |

**No three-way git merge was run** because there are no remote branches named for the three panes—only `main` and `feat/ops-product-next-integration`. Integration here is **logical ordering in `cli.py` and mission_control**:

1. `production-cut` precedes `v1-contract` (freeze defines what v1 is).
2. `v1-ops` follows (how v1 stays healthy).
3. `stable-v1` follows (whether the system qualifies).

**If you split panes into branches later, merge in that order** and resolve `cli.py` by **appending** each pane’s `Typer` block in sequence (Pane 1 → 2 → 3).

---

## 2. Files with conflicts

**During this integration pass:** none (no merge commits).

**Expected hotspots when merging divergent branches:**

| Area | Risk |
|------|------|
| `src/workflow_dataset/cli.py` | Duplicate `app.add_typer(..., name="...")` or overlapping command names. |
| `mission_control/state.py`, `report.py`, `next_action.py` | Duplicate keys or conflicting slice shapes. |
| `production_cut/`, `release_readiness/`, `stability_reviews/`, `trust/` | Overlapping “gate” or readiness semantics. |
| `continuity_bundle/`, `migration_restore/`, `deploy_bundle/` | Copy that implies broader v1 scope post-freeze. |
| Docs under `docs/M50*.md` | Redundant or contradictory stable-v1 narratives. |

---

## 3. How each conflict should be resolved (playbook)

| Rule | Action |
|------|--------|
| CLI | Prefer **additive** groups: keep `v1-contract`, `v1-ops`, `stable-v1` as separate top-level groups; do not replace `production-cut` / `stability-reviews` with gate logic—**compose**. |
| Mission control | **Merge dict keys**: e.g. `v1_contract_state`, `v1_ops_state`, `stable_v1_gate_state` side by side; extend report sections rather than one blob. |
| Product principles | Preserve **local-first / privacy-first / approval-gated / inspectable**; do not auto-approve stable v1. |
| Scope | **Do not broaden** v1 after freeze; quarantined/experimental surfaces stay visible (M50D.1 communication pack, gate blockers). |
| Blockers | Gate and reports must **surface** blockers and residual experimental scope, not hide them. |

---

## 4. Tests run after each merge (recommended)

Run after **each** pane merge (or after full integration):

```bash
cd workflow-llm-dataset
# Pane 1 — contract / surfaces / freeze
python3 -m pytest tests/test_v1_contract.py tests/test_production_cut.py -q --tb=short

# Pane 2 — ops / support / maintenance
python3 -m pytest tests/test_v1_ops.py -q --tb=short

# Pane 3 — stable v1 gate / decision
python3 -m pytest tests/test_stable_v1_gate.py -q --tb=short

# Mission control + CLI wiring (broad slice; can be slow)
python3 -m pytest tests/test_mission_control.py -q --tb=short
```

**CLI smoke (requires deps, e.g. PyYAML):**

```bash
workflow-dataset v1-contract show
workflow-dataset v1-ops status
workflow-dataset stable-v1 gate
workflow-dataset mission-control report   # if available on your tree
```

---

## 5. Final integrated command surface (M50)

### `workflow-dataset v1-contract` (Pane 1 + M50D.1)

| Command | Purpose |
|---------|---------|
| `show` | Stable v1 contract JSON/text |
| `surfaces` | Core / advanced / quarantined / excluded |
| `workflows` | Stable workflow set |
| `explain --surface <id>` | Per-surface classification |
| `freeze-report` | Freeze narrative |
| `stable-pack` | Operator communication: safe to rely on |
| `experimental-summary` | Quarantine / exploratory summary |
| `safe-vs-exploratory` | Plain-language safe vs exploratory |

### `workflow-dataset v1-ops` (Pane 2)

| Command | Purpose |
|---------|---------|
| `status` | Posture, overdue, risk, recommended action |
| `support-posture` | Full posture |
| `maintenance-pack` | Rhythm, cadence, recovery, rollback |
| `review-cadence` | Review schedule |
| `recovery-path` | Recovery paths |
| `maintenance-pack-save` / `maintenance-pack-list` | Persisted packs |
| `support-review-summary` | Review summary |
| `maintenance-obligations` | What must be maintained |

### `workflow-dataset stable-v1` (Pane 3)

| Command | Purpose |
|---------|---------|
| `gate` | Blockers / warnings / passed |
| `report` | Evidence + gate + explain |
| `blockers` | Blocker list + remediation hints |
| `decision` | approved / narrow / repair / scope |
| `explain` | Why this recommendation |
| `watch-state` | Post-v1 monitoring |
| `carry-forward` | Carry-forward obligations |

---

## 6. Remaining risks

1. **Large uncommitted / untracked tree** — M50 modules may not be on `main`; integration is fragile until committed and CI runs.
2. **Duplicate Typer groups** — e.g. `personal` registered twice in `cli.py` (unrelated panes); last registration wins—verify with `workflow-dataset --help`.
3. **test_mission_control.py** — Slow or environment-sensitive; run in CI with timeout.
4. **Gate vs contract drift** — If production cut changes without re-freeze, gate evidence and v1-contract can disagree; operators should run `v1-contract show` and `stable-v1 report` together.
5. **Scope creep in docs** — Multiple M50 markdown files; align on single “source of truth” per concern.

---

## 7. Exact recommendation for post-v1 work

1. **Commit and push** the integrated `workflow-llm-dataset` tree (or merge `feat/ops-product-next-integration` to `main` after green CI).
2. **Add CI job** that runs: `test_v1_contract`, `test_v1_ops`, `test_stable_v1_gate`, and a subset of `test_mission_control` on every PR touching `v1_contract/`, `v1_ops/`, `stable_v1_gate/`, or M50 CLI blocks.
3. **Operator runbook (one page):** (1) `v1-contract freeze-report` → (2) `v1-ops maintenance-pack` → (3) `stable-v1 decision`; file blockers from `stable-v1 blockers` before calling stable v1 “approved.”
4. **Post-v1 product work:** defer to **watch-state** and **maintenance-obligations**; treat **quarantined surfaces** as backlog candidates for v1.1 only via explicit scope change, not silent expansion.

---

*Generated by integration pane narrative; align with team branch strategy if panes are split.*
