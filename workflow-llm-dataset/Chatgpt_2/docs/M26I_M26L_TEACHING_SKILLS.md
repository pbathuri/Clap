# M26I–M26L — Agent Teaching Studio + Skill Capture

First-draft teaching system: record or import demonstrations, normalize into reusable skill definitions, attach to packs/jobs/goal families, and review/accept with explicit trust/readiness. No hidden continual learning; no auto-promotion of raw demos to trusted skills.

---

## 1. Files modified

- `src/workflow_dataset/mission_control/state.py` — Added teaching_skills section (candidate_skills, recently_accepted_skills, pack_linked_skills, skills_needing_review).
- `src/workflow_dataset/mission_control/report.py` — Added "[Teaching / skills]" section to mission-control report.
- `src/workflow_dataset/cli.py` — Added `skills_group` and commands: list, draft-from-demo, draft-from-correction, review, accept, reject, attach, report.

## 2. Files created

- `docs/M26I_M26L_PRE_CODING_ANALYSIS.md` — Pre-coding analysis (surfaces, gaps, file plan, safety, out-of-scope).
- `src/workflow_dataset/teaching/__init__.py` — Public API.
- `src/workflow_dataset/teaching/skill_models.py` — Skill dataclass and constants.
- `src/workflow_dataset/teaching/skill_store.py` — Persist/list skills under data/local/teaching/skills/.
- `src/workflow_dataset/teaching/normalize.py` — demo_to_skill_draft, correction_to_skill_draft, manual_skill_draft.
- `src/workflow_dataset/teaching/review.py` — list_candidate_skills, accept_skill, reject_skill, attach_skill_to_pack.
- `src/workflow_dataset/teaching/report.py` — build_skill_report, format_skill_report.
- `tests/test_teaching_skills.py` — Tests for model, store, normalization, review, report, blocked/unclear.
- `docs/M26I_M26L_TEACHING_SKILLS.md` — This doc.

---

## 3. Exact CLI usage

```bash
# List all skills (or filter by status)
workflow-dataset skills list
workflow-dataset skills list --status draft
workflow-dataset skills list --status accepted --limit 20

# Create draft skill from task demo
workflow-dataset skills draft-from-demo --id demo_123
workflow-dataset skills draft-from-demo --id demo_weekly --goal-family reporting --task-family weekly

# Create draft skill from correction
workflow-dataset skills draft-from-correction --id corr_1 --goal-family reporting

# Show skill for review (normalized steps, source, status)
workflow-dataset skills review --id skill_demo_demo_123_abc

# Accept draft (default: simulate_only)
workflow-dataset skills accept --id skill_demo_demo_123_abc
workflow-dataset skills accept --id skill_demo_demo_123_abc --trusted-real --notes "Verified in staging"

# Reject draft
workflow-dataset skills reject --id skill_demo_demo_123_abc --notes "Not reusable"

# Attach skill to pack
workflow-dataset skills attach --id skill_demo_demo_123_abc --pack founder_ops_plus

# Skill library report
workflow-dataset skills report
```

Mission control shows teaching/skills in the dashboard:

```bash
workflow-dataset mission-control
# [Teaching / skills] candidates=N  accepted_recent=M  pack_linked=P  needing_review=Q
```

---

## 4. Sample skill definition (JSON)

```json
{
  "skill_id": "skill_demo_weekly_report_a1b2c3",
  "source_type": "task_demo",
  "source_reference_id": "weekly_report",
  "goal_family": "reporting",
  "task_family": "weekly",
  "required_capabilities": [],
  "required_approvals": [],
  "pack_associations": ["founder_ops_plus"],
  "job_associations": [],
  "expected_inputs": [],
  "expected_outputs": [],
  "trust_readiness_status": "simulate_only",
  "operator_notes": "",
  "certification_notes": "",
  "status": "accepted",
  "simulate_only_or_trusted_real": "simulate_only",
  "normalized_steps": [
    {
      "adapter_id": "file_ops",
      "action_id": "inspect_path",
      "params": {"path": "/workspace/notes"},
      "notes": ""
    },
    {
      "adapter_id": "browser_open",
      "action_id": "open_url",
      "params": {"url": "https://example.com/report"},
      "notes": ""
    }
  ],
  "created_at": "2026-03-16T12:00:00Z",
  "updated_at": "2026-03-16T12:05:00Z",
  "accepted_at": "2026-03-16T12:05:00Z",
  "rejected_at": ""
}
```

---

## 5. Sample demo-to-skill normalization output

Input: task demo `weekly_report` with two steps (file_ops.inspect_path, browser_open.open_url).

After:

```bash
workflow-dataset skills draft-from-demo --id weekly_report --goal-family reporting
```

Output (created draft skill):

- `skill_id`: `skill_demo_weekly_report_<hash>`
- `source_type`: `task_demo`
- `source_reference_id`: `weekly_report`
- `status`: `draft`
- `normalized_steps`: list of `{adapter_id, action_id, params, notes}` from each TaskStep.

The draft is saved under `data/local/teaching/skills/<skill_id>.json` and is not accepted until the operator runs `skills accept --id <skill_id>`.

---

## 6. Sample skill review/accept flow

1. List drafts: `workflow-dataset skills list --status draft`
2. Review one: `workflow-dataset skills review --id skill_demo_weekly_report_abc`
3. Accept as simulate-only: `workflow-dataset skills accept --id skill_demo_weekly_report_abc`
4. Optional: attach to pack: `workflow-dataset skills attach --id skill_demo_weekly_report_abc --pack founder_ops_plus`
5. Optional: accept as trusted-real candidate: `workflow-dataset skills accept --id skill_demo_weekly_report_abc --trusted-real --notes "Verified"`

Reject path: `workflow-dataset skills reject --id skill_demo_weekly_report_abc --notes "Not reusable"`.

---

## 7. Sample skill report

Output of `workflow-dataset skills report`:

```
=== Teaching / Skill library ===

  draft: 2  accepted: 5  rejected: 1
  pack-linked: 3  needing_review: 2  weak/unclear: 1

  draft_ids (sample): skill_demo_weekly_xyz, skill_correction_corr_1_abc
  recent_accepted: skill_demo_weekly_report_a1b2, skill_manual_ops_1
  pack_linked (sample): skill_demo_weekly_report_a1b2, skill_manual_ops_1
```

---

## 8. Exact tests run

```bash
python3 -m pytest tests/test_teaching_skills.py -v
```

Covers: skill model roundtrip, store save/load/list/delete, demo_to_skill_draft (and missing demo), correction_to_skill_draft (and missing correction), manual_skill_draft, accept/reject, attach_skill_to_pack, list_candidate_skills, build_skill_report and format_skill_report, weak/unclear and blocked skill status in report.

---

## 9. Remaining gaps for later refinement

- **Session-pattern → skill**: Not yet implemented (repeated successful session patterns as source_type `session_pattern`); only task_demo, correction, and manual are supported.
- **Goal/task family taxonomy**: No enforced vocabulary; goal_family/task_family are free text.
- **Planner consumption**: Skills are stored and reportable but not yet wired as planning inputs (e.g. ProvenanceSource kind `skill` or planner reading from skill library).
- **Edit draft in place**: Review surface is read-only; no CLI to edit normalized_steps or expected_inputs/outputs after creation (can be done by editing JSON under data/local/teaching/skills/).
- **Certification workflow**: certification_notes field exists but no certification pipeline or approval gates.
- **Top reusable / weak skill heuristics**: Report counts weak/unclear by status and empty steps; no usage counts or success-rate signals yet.
- **Simulate-only vs trusted-real enforcement**: Marking is stored; enforcement (e.g. blocking real execution for simulate_only skills) is out of scope for this first draft.
