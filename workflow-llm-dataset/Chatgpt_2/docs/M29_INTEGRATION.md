# M29 Integration — Workspace + Conversational + Timeline/Inbox

## 1. Merge steps executed

| Step | Description |
|------|-------------|
| **Merge 1 (Pane 1)** | Confirmed existing workspace shell (M29A–M29D + M29D.1) as base. Ran `tests/test_workspace_m29.py` and `tests/test_mission_control.py`. **24 passed.** |
| **Merge 2 (Pane 3)** | Integrated conversational command center into workspace: added views `ask`, `timeline`, `inbox` to `WORKSPACE_VIEWS`; added workspace areas `conversational_ask`, `timeline`, `intervention_inbox`; added `resolve_view_target` branches for ask/timeline/inbox with suggested commands; added mission_control report line `[Ask]` for conversational. |
| **Merge 3 (Pane 2)** | Integrated activity timeline and intervention inbox: same view/area/navigation additions as above (timeline, inbox); workspace areas get counts from `review_studio.inbox.build_inbox` and `review_studio.timeline.build_timeline`; mission_control already had `review_studio` and `daily_inbox` in state and report. |

All three panes were already present in the same tree; integration was **additive** (no branch merge, no file conflict resolution).

---

## 2. Files with conflicts

**None.** Integration was additive only. No git merge conflicts occurred. No existing commands or behaviors were removed or replaced.

---

## 3. How each conflict was resolved

N/A — no conflicts. Where overlap existed (e.g. `inbox` as daily digest vs intervention inbox), both surfaces were preserved:

- **`inbox`** (daily): `workflow-dataset inbox` → daily digest; `inbox list` / `inbox review` delegate to `review_studio.cli`.
- **`inbox-studio`**: `workflow-dataset inbox-studio list` → same `review_studio.cli` backend; distinct name for “intervention inbox” focus.
- **Workspace view `inbox`**: suggests `inbox-studio list` and `inbox list` so operator can use either.

---

## 4. Tests run after each merge

| After | Command | Result |
|-------|---------|--------|
| Merge 1 | `pytest tests/test_workspace_m29.py tests/test_mission_control.py -v` | 24 passed |
| Merge 2 + 3 | `pytest tests/test_workspace_m29.py tests/test_conversational.py tests/test_review_studio.py tests/test_mission_control.py -v` | 64 passed |
| Integration tests | `pytest tests/test_workspace_m29.py::test_workspace_views_include_integrated_ask_timeline_inbox tests/test_workspace_m29.py::test_resolve_view_target_ask_timeline_inbox -v` | 2 passed |

**Total:** 66 tests in the integrated slice (workspace, conversational, review_studio, mission_control) plus 2 dedicated integration tests for ask/timeline/inbox views.

---

## 5. Final integrated command surface

### Workspace (Pane 1)

- `workflow-dataset workspace home` [ `--preset founder-operator | analyst | developer | document-heavy` ]
- `workflow-dataset workspace open --view <view>` [ `--project <id>` ] [ `--session <id>` ]  
  **Views:** home, portfolio, project, session, approvals, policy, lanes, packs, artifacts, outcomes, rollout, settings, **ask**, **timeline**, **inbox**
- `workflow-dataset workspace context`
- `workflow-dataset workspace next`
- `workflow-dataset workspace presets list`

### Conversational (Pane 3)

- `workflow-dataset ask "<phrase>"` [ `--no-preview` ] [ `--role operator | reviewer` ] [ `--json` ]

### Timeline (Pane 2)

- `workflow-dataset timeline latest` [ `--limit` ] [ `--since` ]
- `workflow-dataset timeline project --id <id>` [ `--limit` ]

### Intervention inbox (Pane 2)

- `workflow-dataset inbox-studio list` [ `--status` ] [ `--limit` ]
- `workflow-dataset inbox-studio review --id <item_id>`
- `workflow-dataset inbox-studio accept --id <id>` [ `--note` ]
- `workflow-dataset inbox-studio reject --id <id>` [ `--note` ]
- `workflow-dataset inbox-studio defer --id <id>` [ `--note` ] [ `--revisit-after` ]

### Daily inbox (existing, unchanged)

- `workflow-dataset inbox` [ `--explain` ] [ `--output` ]
- `workflow-dataset inbox list` | `inbox review` | `inbox accept` | `inbox reject` | `inbox defer` (delegate to review_studio)

### Mission control

- `workflow-dataset mission-control` — report now includes **[Review studio]** and **[Ask]** (conversational hint).

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Two inbox entry points** (`inbox` vs `inbox-studio`) | Documented: `inbox` = daily digest + same backend; `inbox-studio` = intervention-only. Both are valid. |
| **Workspace area count loading** | `build_workspace_areas` calls `build_inbox` and `build_timeline`; failures are caught and counts left at 0. |
| **Mission control state** | `review_studio` and `daily_inbox` already in state; only report line added for Ask. No new state keys for conversational. |
| **Trust/approval boundaries** | Unchanged: ask is read-only + preview; inbox accept/reject/defer remain explicit and approval-gated. |

---

## 7. Exact recommendation for the next batch

1. **Persist workspace preset**  
   Store default preset (e.g. `data/local/workspace/preset_id.txt` or env) so `workflow-dataset workspace home` can use it when `--preset` is omitted.

2. **Workspace open with recommended view**  
   Add `workflow-dataset workspace open --preset founder-operator` (or similar) that opens the preset’s `recommended_first_view` and prints suggested commands for that view.

3. **Single “inbox” mental model**  
   Consider documenting or renaming so that either `inbox` is the single entry point and `inbox-studio` is an alias, or the doc clearly states “daily digest vs intervention-only” to avoid operator confusion.

4. **Mission control next-action and Ask**  
   Optionally have `recommend_next_action` consider `review_studio.urgent_count` or suggest “ask” when context is ambiguous (additive hint only; no auto-execute).

5. **Integration test slice in CI**  
   Add a CI job that runs:  
   `pytest tests/test_workspace_m29.py tests/test_conversational.py tests/test_review_studio.py tests/test_mission_control.py -v`  
   so future changes don’t regress the integrated surface.
