# M37E–M37H — Signal Quality + Queue Calmness + Attention Protection (Deliverable)

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `queue quality`, `queue suppressions`, `queue resurfacing`, `queue focus-protection`; added `assist signal-report`. |
| `src/workflow_dataset/mission_control/state.py` | Added `signal_quality` block: suppressed_low_value_count, resurfacing_candidates_count, focus_protected_active, top_high_signal_item_id, noise_level, calmness_score. |
| `src/workflow_dataset/mission_control/report.py` | Added [Signal quality] section: calmness, noise, suppressed, resurfacing_candidates, focus_protected, top_high_signal. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/signal_quality/__init__.py` | Package exports (models). |
| `src/workflow_dataset/signal_quality/models.py` | SignalQualityScore, InterruptionCost, RepeatNoiseMarker, ProtectedFocusItem, LowValueSuggestion, SuppressedQueueItem, ResurfacingRule, StaleButImportantRule; ALWAYS_SHOW_PRIORITY, NEVER_SUPPRESS_SOURCES. |
| `src/workflow_dataset/signal_quality/scoring.py` | score_queue_item, score_assist_suggestion, is_repeat_noise, eligible_resurfacing, rank_by_high_signal. |
| `src/workflow_dataset/signal_quality/quieting.py` | apply_queue_quieting, apply_assist_quieting (never suppress urgent tier). |
| `src/workflow_dataset/signal_quality/attention.py` | get_protected_focus, interruption_threshold_for_mode, digest_bundling_recommended, operator_grouped_review_cap. |
| `src/workflow_dataset/signal_quality/reports.py` | build_quality_report, build_suppressions_report, build_focus_protection_report, build_resurfacing_report. |
| `tests/test_signal_quality.py` | 15 tests: models, scoring, quieting (urgent never suppressed, focus-safe suppresses), attention, reports, resurfacing. |
| `docs/M37E_M37H_SIGNAL_QUALITY_BEFORE_CODING.md` | Before-coding analysis (existing behavior, gaps, file plan, safety, principles). |
| `docs/M37E_M37H_SIGNAL_QUALITY_DELIVERABLE.md` | This deliverable. |

## 3. Exact CLI usage

```bash
# Signal quality report (calmness, noise, suppressed, top high-signal)
workflow-dataset queue quality [--repo PATH] [--limit N] [--json]

# Suppressed items and resurfacing-eligible
workflow-dataset queue suppressions [--repo PATH] [--limit N] [--json]

# Resurfacing candidates (stale-but-important)
workflow-dataset queue resurfacing [--repo PATH] [--limit N] [--json]

# Focus protection state and interruption threshold
workflow-dataset queue focus-protection [--repo PATH] [--json]

# Assist signal report (calmness, suppressed, focus protected)
workflow-dataset assist signal-report [--repo PATH] [--json]
```

(Make sure the CLI entry point is `workflow-dataset` or your project’s CLI name; e.g. `python -m workflow_dataset.cli queue quality --json`.)

## 4. Sample signal-quality report

```json
{
  "generated_at_utc": "2025-03-16T14:00:00.000000+00:00",
  "calmness_score": 0.72,
  "noise_level": 0.35,
  "queue_item_count": 12,
  "suppressed_count": 3,
  "top_high_signal_item_id": "uq_rs_abc123",
  "focus_protected_active": false,
  "digest_recommended": false,
  "digest_message": ""
}
```

## 5. Sample suppressed / resurfaced item output

**Suppressions report (queue suppressions --json):**

```json
{
  "generated_at_utc": "2025-03-16T14:00:00.000000+00:00",
  "total_suppressed": 3,
  "by_reason": { "focus_safe": 2, "low_value": 1 },
  "by_source": { "queue": 3 },
  "resurfacing_eligible_count": 3,
  "resurfacing_eligible": [
    {
      "item_id": "uq_auto_xyz",
      "source": "queue",
      "reason": "focus_safe",
      "suppressed_at_utc": "2025-03-16T14:00:00+00:00"
    }
  ]
}
```

**Resurfacing report (queue resurfacing --json):**

```json
{
  "generated_at_utc": "2025-03-16T14:00:00.000000+00:00",
  "resurfacing_candidates_count": 2,
  "candidates": [
    { "item_id": "uq_rs_blocked_1", "section_id": "blocked", "created_at": "2025-03-10T08:00:00" }
  ]
}
```

## 6. Sample focus protection output

```json
{
  "active": true,
  "project_id": "founder_case_alpha",
  "work_mode": "focused",
  "focus_mode_id": "focus_deep",
  "allow_urgent_only": true,
  "interruption_threshold": 0.3,
  "message": "Focus protected; only urgent-tier items shown."
}
```

## 7. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python -m pytest tests/test_signal_quality.py -v
```

**Result:** 15 passed (signal quality model, score queue item urgent/approval, rank by high signal, apply queue quieting never suppress urgent / focus-safe suppresses, apply assist quieting, interruption threshold, digest bundling, build quality/suppressions/focus protection/resurfacing reports, eligible resurfacing, constants).

## 8. Exact remaining gaps for later refinement

- **Wire quieting into queue list/view**: `queue list` and `queue view` do not yet call `apply_queue_quieting`; they show full ranked list. Optional: add `--quiet` to apply quieting and show suppressed count in summary.
- **Wire quieting into assist queue**: `assist queue` and `run_now` do not yet use `apply_assist_quieting`; assist policy (quiet hours, focus-safe) remains the only filter. Optional: run quieting after policy and cap visible list.
- **Portfolio focus_mode → assist**: `get_protected_focus` already reads portfolio `active_focus_mode_id`; ensure live_context and portfolio are both used when building assist policy context in `assist_engine/queue.py` so focus mode reduces interruptions without code change in assist.
- **Repeat noise for queue**: `is_repeat_noise` exists but is not yet used for queue items (only assist has repeat suppression today). Add queue-side repeat detection if queue items can repeat.
- **Resurfacing automation**: Resurfacing report is advisory; no automatic “un-suppress” or “bump to top” at a schedule. Can add a cron or CLI “resurface” that promotes eligible items.
- **Config file**: No `calmness.yaml` or `signal_quality.yaml` yet; thresholds (max_visible, suppress_low_value_below, overload_threshold) are in code. Add config for operators.
- **Action cards**: No focus-safe or signal-quality filtering in action_cards builder; cards are built from assist/personal without quieting.
- **Digest bundling**: `digest_bundling_recommended` is reported; no actual “drip N per hour” or “show only digest at 9am” scheduler.
