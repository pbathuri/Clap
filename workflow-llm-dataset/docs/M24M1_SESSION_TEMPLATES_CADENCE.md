# M24M.1 — Session Templates + Daily Cadence Flows

First-draft session templates and daily cadence flows on top of the live session layer. Defines starting board state, recommended jobs/routines/macros, expected artifacts, and next-step chain per template; cadence = ordered sequence of templates.

---

## 1. Files modified

| File | Change |
|------|--------|
| `session/launch.py` | `start_session(pack_id=None, ..., template_id=None)`: optional pack_id; if template_id given, overlay template's job_ids, routine_ids, macro_ids, active_tasks, recommended_next_actions. If pack_id omitted, use template's value_pack_id. |
| `session/__init__.py` | Export SessionTemplate, list_session_templates, get_session_template, CadenceFlow, CadenceStep, list_cadence_flows, get_cadence_flow, resolve_cadence_pack. |
| `cli.py` | `session start`: --pack optional, add --template; require at least one. Add `session templates`, `session cadence [cadence_id]`. |
| `tests/test_session.py` | Add tests: list/get templates, template expected_artifacts/chain, list/get cadence, resolve_cadence_pack, start_session with template overlays state. |

## 2. Files created

| File | Purpose |
|------|--------|
| `session/templates.py` | SessionTemplate dataclass; BUILTIN_SESSION_TEMPLATES (morning_review, analyst_deep_work, founder_ops_session, developer_focus, document_review); list_session_templates, get_session_template. |
| `session/cadence.py` | CadenceStep, CadenceFlow; BUILTIN_CADENCE_FLOWS (daily_founder, daily_analyst, daily_developer, daily_document, morning_only); list_cadence_flows, get_cadence_flow, resolve_cadence_pack. |
| `docs/M24M1_SESSION_TEMPLATES_CADENCE.md` | This doc. |

---

## 3. Sample session template

```python
SessionTemplate(
    template_id="morning_review",
    name="Morning review",
    description="Start-of-day: inbox, reminders, overnight changes, first priorities.",
    value_pack_id="founder_ops_plus",
    active_tasks=["Check inbox", "Review reminders", "Pick first priority"],
    job_ids=["weekly_status_from_notes", "weekly_status"],
    routine_ids=["morning_reporting", "morning_ops", "weekly_review"],
    macro_ids=["morning_ops"],
    expected_artifacts=["inbox summary", "morning brief", "plan run record"],
    next_step_chain=[
        "workflow-dataset inbox",
        "workflow-dataset macro run --id morning_ops --mode simulate",
        "workflow-dataset session board",
    ],
)
```

---

## 4. Sample daily cadence flow

```python
CadenceFlow(
    cadence_id="daily_founder",
    name="Daily founder / operator",
    description="Morning review → founder ops session. Pack: founder_ops_plus.",
    steps=[
        CadenceStep("morning_review", "Morning review"),
        CadenceStep("founder_ops_session", "Founder ops session"),
    ],
)
```

CLI:

```bash
workflow-dataset session cadence
#   daily_founder   Daily founder / operator
#   daily_analyst   Daily analyst
#   ...

workflow-dataset session cadence daily_founder
# daily_founder  Daily founder / operator
#   Morning review → founder ops session. Pack: founder_ops_plus.
#   1. Morning review  (template=morning_review)
#   2. Founder ops session  (template=founder_ops_session)
```

---

## 5. Exact tests run

```bash
pytest tests/test_session.py -v --tb=short
```

**Result: 18 passed** (13 existing + 5 new: list/get templates, template expected_artifacts/chain, list/get cadence, resolve_cadence_pack, start_session with template overlays state).

---

## 6. Next recommended step for the pane

- **Cadence-driven start:** Add `session start --cadence daily_founder` that starts the first step’s template (morning_review) and optionally records “current cadence step” so the next command can suggest “start founder_ops_session” after morning_review.
- **Handoff between steps:** When closing a session started from a template, optionally call `set_handoff()` with a summary and next step from the template’s next_step_chain or the next cadence step.
- **Session template from file:** Allow loading a SessionTemplate from `data/local/session/templates/<id>.json` so operators can add custom templates without code changes.
