# M32E–M32H Just-in-Time Assist Engine — Pre-Coding Analysis

## 1. What suggestion/personalization pieces already exist

- **personal/suggestion_engine.py**: `Suggestion` (suggestion_id, type, title, description, confidence_score, supporting_signals, status pending|accepted|dismissed). `generate_suggestions(routines)` → focus_project, operations_workflow, named_project from routines only. Persisted via graph_store (persist_suggestions, load_suggestions). No live context, no prioritization queue, no snooze.
- **personal/style_suggestion_engine.py**: `StyleAwareSuggestion` (organization, workflow, style, draft_creation). `generate_style_aware_suggestions(context, style_profiles, imitation_candidates, routines)`. Rationale, confidence, priority; status pending|accepted|dismissed. No unified queue or “assist now”.
- **personal/graph_review_inbox.py**: `suggest_routines_for_review`, list_pending_routines, list_pending_patterns, accept/reject graph review items. Routine/pattern confirmation flow, not a general assist queue.
- **progress/recommendation.py**: `recommend_replan` (replan signals); not a suggestion queue.
- **daily/inbox.py**: `DailyDigest` with relevant_job_ids, blocked_items, reminders_due, recommended_next_action, top_next_recommended. Digest for “what to do”; not a persistent assist queue with accept/snooze/dismiss.
- **live_context**: `ActiveWorkContext`, `WorkMode`, `fuse_active_context` (imported in __init__; fusion module may be elsewhere), `get_live_context_state`. Substrate for context-aware assistance; not yet consumed by a single “assist now” flow.
- **assist_group (CLI)**: suggest, draft, explain, next-step, refine-draft, chat, materialize, etc. No `assist now` (generate from live context) or `assist queue` (reviewable queue with accept/snooze/dismiss).
- **personal_adaptation**: Preference/style candidates and apply; can feed “use this preference” into assist suggestions but no unified engine today.

**Gaps**: No single model for “assist suggestion” with reason, triggering context, usefulness/interruptiveness, required action; no queue that sorts and suppresses repeats; no snooze/dismiss/accept at the assist level; no mission-control visibility for “top suggestion” or “queue depth”.

---

## 2. What is missing for a true just-in-time assist engine

- **Unified assist suggestion model**: suggestion_id, reason, triggering_context, confidence, usefulness_score, interruptiveness_score, affected project/session, required_operator_action, status (pending | snoozed | accepted | dismissed), snoozed_until.
- **Generation from live context**: Fuse progress board (stalled/blockers), current goal/plan, routines, inbox/digest, recently accepted skills, pack behavior, personal preferences, pending approvals → generate concrete suggestions (next step, draft/summary, blocked-review, resume routine, open artifact).
- **Reviewable queue**: Persist suggestions; sort by usefulness/urgency/confidence; suppress repetitive (same reason/type recently shown or dismissed); snooze (hide until time or context change); dismiss; accept (record outcome, no auto-execute).
- **CLI**: `assist now`, `assist queue`, `assist explain --id`, `assist accept --id`, `assist snooze --id`, `assist dismiss --id`.
- **Mission control**: Top current suggestion, queue depth, repeated dismissed patterns, highest-confidence next, assistance “focus-safe” or silence state.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/assist_engine/models.py` — AssistSuggestion, suggestion_reason, triggering_context, usefulness_score, interruptiveness_score, required_operator_action, status (pending/snoozed/accepted/dismissed), snoozed_until |
| Generation | Create | `src/workflow_dataset/assist_engine/generation.py` — generate_assist_suggestions(repo_root) from progress board, goal/plan, routines, inbox, skills, preferences; types: next_step, draft_summary, blocked_review, resume_routine, open_artifact, use_preference |
| Queue | Create | `src/workflow_dataset/assist_engine/queue.py` — queue: add, list (sorted), get_by_id; suppress_repetitive; sort by usefulness/urgency/confidence |
| Store | Create | `src/workflow_dataset/assist_engine/store.py` — save_suggestion, load_suggestion, list_suggestions, update_status (snooze, dismiss, accept), list_dismissed_patterns |
| Explain | Create | `src/workflow_dataset/assist_engine/explain.py` — explain_suggestion(suggestion_id) → reason, context, evidence |
| Init | Create | `src/workflow_dataset/assist_engine/__init__.py` |
| CLI | Modify | `src/workflow_dataset/cli.py` — add to assist_group: now, queue, explain --id, accept --id, snooze --id, dismiss --id |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — add assist_engine block (top_suggestion, queue_depth, repeated_dismissed, highest_confidence_next, focus_safe) |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — [Assist] section |
| Tests | Create | `tests/test_assist_engine.py` |
| Docs | Create | `docs/M32E_M32H_ASSIST_ENGINE.md` |

---

## 4. Safety/risk note

- **No auto-execute**: Accepting a suggestion only records outcome; no automatic task execution or file writes.
- **Trust boundaries**: Suggestions do not bypass approval/trust; “blocked review” and “open artifact” are recommendations only.
- **Local-only**: Queue and state stored under data/local/assist_engine/; no telemetry.
- **Inspectable**: Every suggestion has reason, triggering context, and evidence; explain --id exposes them.

---

## 5. Spam/noise control principles

- **Suppress repetitive**: If the same suggestion_reason + type was dismissed or shown recently (e.g. last 24h or last N dismissals), do not re-enqueue or rank it low.
- **Cap queue size**: e.g. max 20 pending; oldest or lowest usefulness dropped when full.
- **Interruptiveness score**: Prefer lower-interruption suggestions when ranking; allow “focus-safe” mode (only high-confidence, high-usefulness).
- **Snooze**: User can snooze a suggestion; it is hidden until snoozed_until or next “assist now” after context change.
- **No generic filler**: Do not generate suggestions when there is no sufficient context (e.g. no goal, no routines, no blocked items); return empty or minimal set with “no strong signal” message.

---

## 6. What this block will NOT do

- **No constant interruptions** or system-tray popups; operator pulls via `assist now` / `assist queue`.
- **No ungrounded generic chatbot suggestions**; all suggestions tied to live context and evidence.
- **No hidden autonomous task execution**; accept only records outcome.
- **No rebuild** of planner, teaching, personal, or live_context; we consume their APIs.
- **No change** to trust/approval boundaries.
