# M29 Integration Pane Report

Integration of three completed panes in the specified merge order, with validation and conflict resolution.

---

## 1. Merge steps executed

The codebase already contained all three panes; integration consisted of **verification** and **naming consistency** rather than a git merge of separate branches.

| Step | Pane | Action |
|------|------|--------|
| **1** | Pane 1 — M29A–M29D (+ M29D.1) Unified Workspace Shell | Verified present: `workspace/` (models, state, navigation, cli), `workspace_group` in cli.py with home, open, context, next, presets. Workspace areas and views include `conversational_ask`, `timeline`, `intervention_inbox` and deep-link commands. |
| **2** | Pane 3 — M29E–M29H (+ M29H.1) Conversational Command Center | Verified present: `conversational/` (intents, interpreter, explain, preview, ask, suggested_queries, dialogues, roles). Top-level `workflow-dataset ask "<phrase>"` registered. Mission control report includes `[Ask]` hint. |
| **3** | Pane 2 — M29I–M29L (+ M29L.1) Activity Timeline + Review Studio | Verified present: `review_studio/` (timeline, inbox, studio, digests, store). CLI: `timeline latest|project`, `inbox list|review|accept|reject|defer`, `digest morning|end-of-day|project|rollout-support`. Mission control has `review_studio` state block and `[Review studio]` report section. |
| **4** | Consistency pass | Aligned references from `inbox-studio` to primary `inbox` command group so workspace and mission-control point to `inbox list` / `inbox review`. |

---

## 2. Files with conflicts

There were **no merge conflicts** in the git sense. Two **naming inconsistencies** were found and fixed:

| File | Issue |
|------|--------|
| `src/workflow_dataset/workspace/state.py` | Intervention-inbox area used `workflow-dataset inbox-studio list` while the main CLI exposes `workflow-dataset inbox list`. |
| `src/workflow_dataset/mission_control/report.py` | Review studio hint said `inbox-studio list` and `inbox-studio review`; primary commands are `inbox list` and `inbox review`. |

---

## 3. How each conflict was resolved

- **workspace/state.py**  
  In `build_workspace_areas()`, the `intervention_inbox` `WorkspaceArea` command hint was changed from `"workflow-dataset inbox-studio list"` to `"workflow-dataset inbox list"`.

- **mission_control/report.py**  
  The Review studio hint line was changed from  
  `timeline latest  |  inbox-studio list  |  inbox-studio review --id <item_id>`  
  to  
  `timeline latest  |  inbox list  |  inbox review --id <item_id>`.

The `inbox_studio_group` Typer remains registered as `inbox-studio` for backward compatibility; operators can use either `inbox list` or `inbox-studio list`.

---

## 4. Tests run after integration

Single validation run after the consistency pass:

```bash
python3 -m pytest tests/test_workspace_m29.py tests/test_review_studio.py tests/test_conversational.py tests/test_mission_control.py -v --tb=short
```

**Result:** **66 passed** (16 workspace, 15 review_studio, 25 conversational, 10 mission_control).

CLI smoke checks (all succeeded):

- `workflow-dataset workspace home` — home snapshot and areas (Ask, Timeline, Intervention Inbox)
- `workflow-dataset timeline latest --limit 3`
- `workflow-dataset inbox list --limit 3`
- `workflow-dataset digest morning --limit 5`
- `workflow-dataset ask "What should I do next?"`
- `workflow-dataset mission-control` — includes `[Review studio]` and `[Ask]`

---

## 5. Final integrated command surface

| Surface | Commands |
|---------|----------|
| **Workspace (Pane 1)** | `workflow-dataset workspace home` \| `open` \| `context` \| `next` \| `presets list` \| `presets apply` |
| **Ask (Pane 3)** | `workflow-dataset ask "<phrase>"` [--no-preview] [--role operator\|reviewer] [--json] |
| **Timeline (Pane 2)** | `workflow-dataset timeline latest` [--limit] [--since] \| `timeline project --id <id>` |
| **Inbox (Pane 2)** | `workflow-dataset inbox` (daily digest) \| `inbox list` \| `inbox review --id <id>` \| `inbox accept` \| `inbox reject` \| `inbox defer` \| `inbox explain` \| `inbox compare` \| `inbox snapshot` |
| **Digest (Pane 2)** | `workflow-dataset digest morning` \| `end-of-day` \| `project --id <id>` \| `rollout-support` |
| **Mission control** | `workflow-dataset mission-control` — includes product, evaluation, development, incubator, coordination, desktop bridge, job packs, copilot, context, corrections, teaching, runtime, inbox, trust, package readiness, **review_studio**, **Ask**, next action. |

Workspace areas shown on `workspace home` include **Ask** (`workflow-dataset ask "..."`), **Timeline** (`workflow-dataset timeline latest`), **Intervention Inbox** (`workflow-dataset inbox list`).

---

## 6. Remaining risks

- **Duplicate entry points:** Both `inbox` and `inbox-studio` expose list/review/accept/reject/defer. Keeping both avoids breaking anyone using `inbox-studio`; long term one could be deprecated and documented as an alias.
- **Order of registration:** If new top-level groups are added in cli.py, ensure they do not shadow or conflict with `ask` (currently `@app.command("ask")`) or workspace/timeline/inbox/digest groups.
- **Mission control size:** State and report already aggregate many blocks; adding more panes may require report sections to be collapsible or split (e.g. by “workspace” vs “ops”).
- **Conversational state:** Ask is grounded in mission_control and related state; large changes to mission_control structure may require updates in `conversational/explain.py` and related modules.

---

## 7. Recommendation for the next batch

1. **Deprecate or alias:** Decide whether `inbox-studio` should be documented as an alias of `inbox` and eventually removed, or kept indefinitely.
2. **Workspace open → view:** Ensure `workflow-dataset workspace open --view timeline` (and `inbox`, `ask`) resolve to the same deep-link commands as in workspace areas and in mission-control hints.
3. **Regression suite:** Add a single integration test that (a) runs `workspace home`, (b) runs `ask "What should I do next?"`, (c) runs `inbox list`, (d) runs `timeline latest`, (e) runs `mission-control`, and asserts each exits 0 and that mission-control output contains `[Review studio]` and `[Ask]`.
4. **Docs:** Add a short “M29 operator quick reference” that lists workspace → ask → timeline → inbox → digest in one place and points to mission-control for the full picture.
