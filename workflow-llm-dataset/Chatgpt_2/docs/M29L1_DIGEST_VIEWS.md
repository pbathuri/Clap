# M29L.1 — Digest Views + Operator Shift Summaries

First-draft digest views extending the M29I–M29L review studio. Each digest explains: **what changed**, **what is blocked**, **what needs approval**, **most important intervention next**.

---

## Commands

- `workflow-dataset digest morning [--limit 25] [--repo-root <path>]`
- `workflow-dataset digest end-of-day [--limit 40] [--repo-root <path>]`
- `workflow-dataset digest project --id <project_id> [--limit 30] [--repo-root <path>]`
- `workflow-dataset digest rollout-support [--repo-root <path>]`

---

## Digest types

| Type | Purpose |
|------|---------|
| **morning** | Start-of-day: recent activity, blocked, needs approval, top intervention. |
| **end-of-day** | Wrap-up: same structure, broader timeline window. |
| **project** | Project-specific: timeline and inbox filtered by project where applicable. |
| **rollout-support** | Staging count, rollout readiness, plus common blocked/approval/intervention. |

---

## Sample digest output (morning)

```
# Morning summary
Generated: 2026-03-17T02:44:17

## What changed
  [policy_override_revoked] 2026-03-17T02:18 — Policy override revoked: ov_4f90a1ce...
  [policy_override_applied] 2026-03-17T02:18 — Policy override: manual_only=False

## What is blocked
  (none)

## What needs approval
  (none)

## Most important intervention next
  Review inbox: workflow-dataset inbox list
```

---

## Sample project summary

```
# Project summary: founder_case_alpha
Generated: 2026-03-17T02:44:17

## What changed
  (no project activity in window)

## What is blocked
  (none)

## What needs approval
  (none)

## Most important intervention next
  Review project: workflow-dataset timeline project --id founder_case_alpha
```

---

## Tests

```bash
python3 -m pytest tests/test_review_studio.py -v -k digest
```

Covers: `test_digest_morning`, `test_digest_end_of_day`, `test_digest_project`, `test_digest_rollout_support`, `test_format_digest_view`.

---

## Next recommended step for the pane

- **Persist last digest**: Optionally save the last-generated digest (e.g. `data/local/review_studio/last_morning_digest.json`) so operators can compare “last morning” vs “this morning” or surface it in mission control.
- **Time-window filter**: Add `--since` / `--until` to morning and end-of-day so “what changed” is scoped to a time range (e.g. last 24h for morning, “today” for end-of-day).
