# M34L.1 — Morning Briefs + Resume-Work Continuity Cards

First-draft support for morning brief cards, resume-work continuity cards, "what happened while you were away" summaries, and direct handoff into the most relevant next workspace/project/action. Extends M34I–M34L automation review layer; does not rebuild it.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/automation_inbox/models.py` | Added HandoffTarget, MorningBriefCard, ResumeWorkContinuityCard (to_dict/from_dict). |
| `src/workflow_dataset/automation_inbox/store.py` | Added BRIEFS_SUBDIR, save_brief_snapshot, load_brief_snapshot. |
| `src/workflow_dataset/automation_inbox/__init__.py` | Exported brief/card models, briefs builders, format_*, get_recommended_handoff, save/load_brief_snapshot. |
| `src/workflow_dataset/cli.py` | Added automation_brief_group (automation-brief morning, continuity, what-happened, handoff). |
| `src/workflow_dataset/mission_control/state.py` | automation_inbox section now includes recommended_handoff_label, recommended_handoff_command. |
| `tests/test_automation_inbox.py` | Added tests for morning brief, continuity card, what-happened, get_recommended_handoff. |

---

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/automation_inbox/briefs.py` | build_what_happened_summary, get_recommended_handoff, build_morning_brief, build_resume_continuity_card, format_morning_brief, format_continuity_card. |
| `docs/M34L1_BRIEFS_AND_CONTINUITY.md` | This doc. |

---

## 3. Sample morning brief

**Command:** `workflow-dataset automation-brief morning`

**Example output (plain-text):**

```
# Morning brief
Generated: 2025-03-16T15:00:00

## What happened while you were away
  (no recent activity)
  (or:   Completed: run_abc — Step 1 done.
  (or:   Blocked/failed: run_xyz — policy_suppressed)

## Top next action
  Review automation inbox: workflow-dataset automation-inbox list
  (or: No automation follow-up needed.)

## Handoff
  Open inbox: workflow-dataset inbox list
```

**Structured (MorningBriefCard):**

```json
{
  "brief_id": "brief_a1b2c3",
  "generated_at": "2025-03-16T15:00:00Z",
  "title": "Morning brief",
  "what_happened_while_away": ["  (no recent activity)"],
  "top_next_action": "Review automation inbox: workflow-dataset automation-inbox list",
  "handoff": {
    "label": "Open inbox",
    "target_type": "action",
    "view": "inbox",
    "command": "workflow-dataset inbox list",
    "ref": ""
  }
}
```

---

## 4. Sample continuity card

**Command:** `workflow-dataset automation-brief continuity`

**Example output:**

```
# Resume work
Generated: 2025-03-16T15:00:00

## Resume context
  Last context: founder_case_alpha
  (or: Resume from inbox or workspace)

## What happened while you were away
  (no recent activity)

## Suggested next
  workflow-dataset inbox list

## Handoff
  Open inbox: workflow-dataset inbox list
```

**Structured (ResumeWorkContinuityCard):**

```json
{
  "card_id": "card_x7y8z9",
  "generated_at": "2025-03-16T15:00:00Z",
  "title": "Resume work",
  "resume_context": "Last context: founder_case_alpha",
  "what_happened_while_away": ["  (no recent activity)"],
  "suggested_next": "workflow-dataset inbox list",
  "handoff": {
    "label": "Open inbox",
    "target_type": "action",
    "view": "inbox",
    "command": "workflow-dataset inbox list",
    "ref": ""
  }
}
```

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_automation_inbox.py -v --tb=short
```

**Result:** 16 passed (including test_morning_brief_card_model, test_continuity_card_model, test_build_morning_brief, test_build_resume_continuity_card, test_build_what_happened_summary, test_get_recommended_handoff).

---

## 6. Next recommended step for the pane

- **UI:** Surface morning brief and continuity card in the workspace shell or mission-control view (e.g. a “Morning brief” / “Resume work” card with what-happened bullets and a primary button that runs the recommended handoff command).
- **Handoff execution:** Optionally add a “run handoff” helper (e.g. `workflow-dataset automation-brief handoff --run`) that prints the command for the user to run, or document that the user runs the suggested command from the card.
- **Persistence:** Use `automation-brief morning --save` / `continuity --save` to persist latest snapshot; add a “compare with previous” view (load_brief_snapshot("latest") vs previous) in a later iteration.
- **Workspace/project handoff:** Extend get_recommended_handoff to return workspace_id or project_id when available (e.g. from live_context or mission_control) so the handoff target can be “Open workspace X” or “Open project Y” with a concrete ref.
