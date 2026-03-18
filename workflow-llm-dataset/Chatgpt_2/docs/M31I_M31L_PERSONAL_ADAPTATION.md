# M31I–M31L Personal Adaptation Loop

## Overview

First-draft personal adaptation layer that:

1. Infers **preference** and **style pattern** candidates from observed work, corrections, routines, and teaching.
2. Tracks **confidence** and **evidence**; all candidates are **reviewable** and **inspectable**.
3. Applies **only accepted** preferences to surfaces (pack defaults, output framing, workspace preset, specialization_*); no silent apply of unreviewed candidates.
4. Exposes **explain-preference** for evidence and reasoning and **CLI** + **mission control** visibility.

## Models

- **PreferenceCandidate**: candidate_id, key, proposed_value, confidence, evidence, source, affected_surface, review_status (pending | accepted | dismissed).
- **StylePatternCandidate**: candidate_id, pattern_type, description, evidence, confidence, source, affected_surface, review_status, style_profile_ref.
- **AcceptedPreferenceUpdate**: update_id, candidate_id, candidate_type, key_or_pattern, applied_value, applied_surface, applied_utc.

**Affected surfaces**: pack_defaults, output_framing, workspace_preset, suggested_actions, notification_style, planning_style, specialization_params, specialization_paths, specialization_output_style.

## CLI

- `workflow-dataset personal preferences` — list preference candidates (optional `--refresh` to generate from corrections/routines).
- `workflow-dataset personal style-candidates` — list style pattern candidates (optional `--refresh` to generate from style profiles).
- `workflow-dataset personal apply-preference --id <candidate_id>` — accept the candidate and apply to the affected surface.
- `workflow-dataset personal explain-preference --id <candidate_id>` — show evidence, reasoning, and affected surface.

## Sample preference candidate

```json
{
  "candidate_id": "pref_abc123",
  "key": "output_style.weekly_report",
  "proposed_value": "bullet",
  "confidence": 0.75,
  "evidence": ["Correction(s): corr_xyz", "From correction: output_style_correction"],
  "source": "corrections",
  "source_reference_id": "corr_xyz",
  "affected_surface": "specialization_output_style",
  "review_status": "pending",
  "created_utc": "2025-03-16T12:00:00Z"
}
```

## Sample evidence/explanation output

```
# Preference / style candidate: pref_abc123

**Key/pattern:** output_style.weekly_report
**Proposed value:** bullet
**Confidence:** 0.75
**Affected surface:** specialization_output_style
**Source:** corrections

## Evidence
  - Correction(s): corr_xyz
  - From correction: output_style_correction

## Reasoning
Inferred from corrections. Confidence: 0.75. Affected surface: specialization_output_style. If accepted, this will be applied as: output_style.weekly_report → bullet.
```

## Sample applied adaptation output

After `personal apply-preference --id pref_abc123` (and when a matching proposed update exists):

```
Applied: Applied output_style to weekly_report.  surface=specialization_output_style
```

Or when recorded in preference store only:

```
Applied: Recorded in preference store (no matching job pack target).  surface=specialization_output_style
```

Applied preferences are also written to `data/local/personal_adaptation/applied_preferences.json` for downstream consumers.

## Mission control

The mission control state includes **personal_adaptation**: preference_candidates_count, style_candidates_count, accepted_count, low_confidence_count, strongest_patterns. The report prints a [Personal adaptation] line and CLI hints.

## Storage

- Candidates: `data/local/personal_adaptation/candidates/<candidate_id>.json`
- Accepted updates: `data/local/personal_adaptation/accepted/<update_id>.json`
- Applied preferences (fallback): `data/local/personal_adaptation/applied_preferences.json`

## Constraints

- No silent apply of unreviewed candidates.
- No trust/approval boundary changes from this layer.
- All adaptations are explicit and reviewable.
