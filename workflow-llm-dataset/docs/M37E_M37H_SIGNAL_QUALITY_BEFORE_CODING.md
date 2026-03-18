# M37E–M37H — Signal Quality + Queue Calmness + Attention Protection

## BEFORE CODING

### 1. What queue/suggestion/noise-control behavior already exists

| Area | Existing behavior |
|------|-------------------|
| **Unified queue** | Priority + urgency ranking; mode views (focus, review, operator, wrap_up); overload threshold (20) and summary with suggested narrowing; focus_ready from current project; sections by project/episode. No per-item suppression or signal scoring. |
| **Assist engine** | Quiet hours (time windows); focus-safe (max interruptiveness, min confidence) when `--focus-safe`; interruptibility by work_mode/project/trust; **repeat suppression** (dismissed type+reason_title, ~24h/last 20); snooze until time; dismiss; held_back with reason. Scores: confidence, usefulness_score, interruptiveness_score (set in generation, not learned). Queue cap ~50 visible; max_new=15. |
| **Action cards** | Dismiss state; bundles and grouped flows; builder limit=30. No focus-safe or policy integration. |
| **Automation inbox** | Status filter, limit, exclude decided; digests (morning, project, blocked, approval) on demand; no drip. |
| **Review studio** | Inbox from multiple sources; digest views; limits. |
| **Portfolio/attention** | Work windows, focus modes, attention budgets (M28D.1); **not** wired to assist or queue. |
| **Trigger/automation** | Guardrail suppression (allowed kinds, suppression rules, debounce, daily cap); background_run suppress. |

### 2. What is missing for a calm daily-use product

- **Unified calm signal**: No single place combining queue + assist + inbox + attention; portfolio focus mode does not drive assist or queue.
- **Urgency vs usefulness**: Queue/assist use priority/urgency but do not explicitly separate "urgent (must see)" from "useful but deferrable"; no clear "low-value" or "noise" marker.
- **Repeat/noise markers**: Assist has repeat suppression; queue has no "repetitive" or "low-value" marker; no resurfacing rule for stale-but-important.
- **Focus protection**: No explicit "protected focus item" or "do not interrupt" that propagates to queue + assist + cards.
- **Rate/caps**: No per-hour or per-session cap on new suggestions; only max_new and queue length.
- **Digest vs drip**: Digests are on-demand; no "bundle rather than drip" or "show digest at start of day" to reduce spikes.
- **Visibility of suppression**: No CLI/report for "what was suppressed and why" or "resurfacing candidates".
- **Mission control**: No block for suppressed count, resurfacing candidates, focus-protected state, top high-signal item, or calmness score.

### 3. Exact file plan

| Phase | Action | Path |
|-------|--------|------|
| A | Create | `src/workflow_dataset/signal_quality/models.py` — SignalQualityScore, InterruptionCost, RepeatNoiseMarker, ProtectedFocusItem, LowValueSuggestion, SuppressedQueueItem, ResurfacingRule, StaleButImportantRule |
| A | Create | `src/workflow_dataset/signal_quality/__init__.py` |
| B | Create | `src/workflow_dataset/signal_quality/scoring.py` — urgency vs usefulness separation, repeat/noise detection, focus-safe suppression, stale-important resurfacing, grouped recs, role/mode calmness rules |
| B | Create | `src/workflow_dataset/signal_quality/quieting.py` — apply to queue items and assist suggestions (filter/tag, not delete); integrate with existing assist policy and queue |
| C | Create | `src/workflow_dataset/signal_quality/attention.py` — focus mode quieting, operator grouped review, review-mode surfacing, digest bundling, interruption thresholds |
| D | Create | `src/workflow_dataset/signal_quality/reports.py` — build_quality_report, build_suppressions_report, build_focus_protection_report, build_resurfacing_report |
| D | Modify | `src/workflow_dataset/cli.py` — queue quality, queue suppressions, assist signal-report, focus protection, queue resurfacing; optional mission_control hooks |
| D | Modify | `src/workflow_dataset/mission_control/state.py` — signal_quality block: suppressed_low_value_count, resurfacing_candidates_count, focus_protected_active, top_high_signal_item_id, noise_level / calmness_score |
| D | Modify | `src/workflow_dataset/mission_control/report.py` — [Signal quality] section |
| E | Create | `tests/test_signal_quality.py` — suppression, resurfacing, high-signal ranking, focus-safe interruption, stale-important, overload calmness |
| E | Create | `docs/M37E_M37H_SIGNAL_QUALITY_DELIVERABLE.md` |

### 4. Safety/risk note

**Over-suppression**: A single calmness layer that gates queue + assist could hide urgent or safety-critical items (blocked automation, approval, trust regression). **Mitigation**: Never suppress items above a defined urgency/safety tier (e.g. blocked, urgent, approval_queue, needs_approval) regardless of focus mode or rate limit. Document "never_suppress_sources" / "always_show_priority" in models and config; gates explicitly allow these tiers.

### 5. Attention-protection principles

1. **Respect focus mode**: When portfolio active_focus_mode or live_context work_mode indicates focus, reduce non-urgent suggestions and high-interrupt queue items; never hide urgent/blocked/approval by default.
2. **Urgency vs usefulness**: Separate "must see now" (urgent, blocked, approval) from "useful when you have time"; tag low-value and repetitive for suppression or grouping.
3. **Rate and cap**: Cap suggestions per hour/session; cap visible queue length per mode where appropriate.
4. **Digest-first when calm**: Prefer "daily digest" or "digest at start of window" over drip; bundle automation/review items.
5. **Explain hold-back**: Every suppressed or deprioritized item has an explainable reason (reuse held_back_reason / overflow_message style).
6. **Resurfacing**: Stale-but-important items (e.g. blocked > N days) get explicit resurfacing rule so they are not permanently buried.

### 6. What this block will NOT do

- **Replace** approval, human_policy, or trust tiers for execution; calmness only affects visibility and pacing.
- **Hide** critical trust/approval/review work; always allow those tiers through.
- **Rebuild** queue or assist from scratch; extend with scoring, quieting, and attention layers.
- **Make suppression opaque**: CLI and reports expose suppressed count, reasons, resurfacing candidates.
- **Overfit** to one workflow; use role/mode-aware rules that can be tuned.
- **Add telemetry or network**: All logic local and inspectable.
