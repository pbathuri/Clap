# Pilot feedback schema (M21)

Structured feedback for a single pilot session. Stored as JSON under `data/local/pilot/feedback/<session_id>_feedback.json`. Local-only; no remote submission.

---

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Pilot session id (from pilot start-session). |
| `timestamp` | string | ISO UTC when feedback was captured. |
| `usefulness_score` | int | 1–5. How useful was the output/flow? |
| `trust_score` | int | 1–5. How much did the user trust the system? |
| `clarity_score` | int | 1–5. How clear were prompts and next steps? |
| `adoption_likelihood` | int | 1–5. Would use again / recommend? |
| `blocker_encountered` | bool | True if a critical blocker occurred. |
| `top_failure_reason` | string | Short description of main failure, if any. |
| `operator_friction_notes` | string | Operator notes on friction (e.g. report location unclear, next steps not specific enough). |
| `user_quote` | string | One verbatim user quote (improves evidence quality; surfaced in aggregate). |
| `freeform_notes` | string | Any other notes; mention whether next steps felt specific and report location clear. |

**Evidence quality:** For stronger aggregate evidence, capture at least one `user_quote` and one `operator_friction_notes` entry per session. The aggregate report surfaces concern patterns (e.g. next steps specificity, report location clarity) from these fields.

---

## Example

```json
{
  "session_id": "pilot_20250315_120000_abc123",
  "timestamp": "2025-03-15T12:05:00Z",
  "usefulness_score": 4,
  "trust_score": 3,
  "clarity_score": 4,
  "adoption_likelihood": 4,
  "blocker_encountered": false,
  "top_failure_reason": "",
  "operator_friction_notes": "User asked where to find the report.",
  "user_quote": "The summary was helpful for our standup.",
  "freeform_notes": ""
}
```

---

## Capture via CLI

```bash
workflow-dataset pilot capture-feedback \
  --usefulness 4 --trust 3 --clarity 4 --adoption 4 \
  --friction "User asked where to find the report." \
  --user-quote "The summary was helpful for our standup."
```

If no `--session-id` is given, the current pilot session (from `pilot start-session`) is used.
