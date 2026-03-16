# D3 — Devlab proposal generator from repo intake + model compare

## Summary

Proposal generator that turns:
- **External repo intake reports** (`data/local/devlab/reports/repo_intake_report_*.json`)
- **Model comparison results** (`data/local/devlab/model_compare/model_compare_report.json`)

into local-only, advisory artifacts:
- **devlab_proposal.md** — advisory summary of intake + model compare + next steps
- **cursor_prompt.txt** — prompt for operator/Cursor to suggest concrete edits (no auto-apply)
- **rfc_skeleton.md** — RFC skeleton for operator to complete and approve

**Requirements met:** advisory only; no code modification; local-only artifacts.

---

## Files modified / added

| Action | Path |
|--------|------|
| Added | `src/workflow_dataset/devlab/proposal_generator.py` |
| Added | `src/workflow_dataset/devlab/config.py` (if missing in tree) |
| Modified | `src/workflow_dataset/devlab/proposals.py` (include devlab_proposal.md in get_proposal) |
| Modified | `src/workflow_dataset/cli.py` (devlab generate-proposal, show-proposal lists devlab_proposal_md) |
| Modified | `tests/test_devlab.py` (D3 tests) |
| Added | `docs/D3_PROPOSAL_GENERATOR_DELIVERY.md` (this file) |

---

## Exact proposal-generation CLI usage

```bash
# Generate proposal from current repo intake reports + model compare (if present)
workflow-dataset devlab generate-proposal

# Override devlab sandbox root
workflow-dataset devlab generate-proposal --devlab-root data/local/devlab

# List proposals (includes D3-generated ones)
workflow-dataset devlab proposal-queue

# Show a proposal (manifest + paths to devlab_proposal.md, cursor_prompt.txt, rfc_skeleton.md)
workflow-dataset devlab show-proposal <proposal_id>
workflow-dataset devlab show-proposal <proposal_id> --devlab-root data/local/devlab

# Update status (no code changes)
workflow-dataset devlab review-proposal <proposal_id> --status reviewed --notes "Accepted for review"
```

**Typical flow:**
1. `devlab add-repo` / `ingest-repo` / `repo-report` → intake reports in `reports/`
2. `devlab compare-models --workflow weekly_status --providers ollama` → model compare in `model_compare/`
3. `devlab generate-proposal` → new proposal under `proposals/<proposal_id>/`
4. Review `devlab_proposal.md`, use `cursor_prompt.txt` in Cursor, complete `rfc_skeleton.md` as needed.

---

## Sample proposal output

**Directory layout:** `data/local/devlab/proposals/<proposal_id>/`

```
proposals/
  <proposal_id>/
    manifest.json
    devlab_proposal.md
    cursor_prompt.txt
    rfc_skeleton.md
```

**manifest.json (D3-generated):**
```json
{
  "proposal_id": "a1b2c3d4e5f6",
  "source": "proposal_generator",
  "status": "pending",
  "created_at": "2026-03-16T15:00:00.000Z",
  "operator_notes": "",
  "intake_count": 2,
  "model_compare_present": true
}
```

**devlab_proposal.md (excerpt):**
```markdown
# Devlab proposal (advisory)

**Proposal ID:** a1b2c3d4e5f6
**Generated:** 2026-03-16T15:00:00.000Z

This document is advisory only. No code has been modified. Review and apply changes explicitly.

---

## Repo intake summary

**2** intake report(s) in devlab/reports.

- **foo_bar** (composite: 0.65)
  - Parsed repo foo_bar; 12 top-level items; README present
  - D2 recommendation: prototype_candidate
  - Use: inspiration

- **baz_qux** (composite: 0.48)
  - Parsed repo baz_qux; 5 top-level items; README present
  - D2 recommendation: inspect_further
  - Use: inspiration

---

## Model comparison summary

**Workflow:** weekly_status
**Providers/models compared:** 1

- **ollama** / llama3.2
  - Output preview: Done. Key wins: X. Blockers: Y...

Use this to decide which provider/model to use for ops/reporting workflows. No auto-switch.

---

## Next steps

1. Review repo intake reports; decide which repos (if any) to adopt patterns or code from.
2. Review model comparison; decide which provider/model to use for workflows.
3. Use cursor_prompt.txt in this proposal for a Cursor/operator prompt to suggest concrete edits.
4. Use rfc_skeleton.md to draft an RFC; complete and approve before implementation.

---
*Advisory only. Local-only artifacts. No automatic code changes.*
```

**cursor_prompt.txt (excerpt):**
```
Devlab proposal a1b2c3d4e5f6 (advisory). Do not modify code automatically.

Context:
- 2 repo intake report(s) in data/local/devlab/reports/. Review repo_intake_report_*.json for summary, D2 recommendation, and reuse vs inspiration.
  Repo IDs: foo_bar, baz_qux
- Model comparison in data/local/devlab/model_compare/model_compare_report.json (workflow: weekly_status). Use it to recommend which provider/model to use; do not auto-switch.

Task: Suggest concrete, minimal changes (config, prompts, or code) that would:
1. Incorporate useful patterns or modules from one intake repo (if any), with attribution.
2. Align provider/model choice with the model comparison (if present).
Output a list of suggested edits for operator review. Do not apply changes.
```

**rfc_skeleton.md (excerpt):**
```markdown
# RFC skeleton: Devlab adoption

**Proposal ID:** a1b2c3d4e5f6

## Summary
Adopt findings from devlab repo intake and/or model comparison. Scope and details to be filled by operator.

## Motivation
- 2 repo intake report(s) available; D2 recommendations and license triage inform reuse vs inspiration.
- Model comparison available for workflow: weekly_status; informs provider/model choice.

## Proposed changes
- [ ] Select repo(s) or patterns to adopt (from intake reports).
- [ ] Select provider/model for ops workflows (from model compare).
...
```

---

## Exact tests run

```bash
pytest workflow-llm-dataset/tests/test_devlab.py -v -k "proposal_generator or generate_proposal or devlab_proposal"
```

Or run all devlab tests:
```bash
pytest workflow-llm-dataset/tests/test_devlab.py -v
```

**D3-related tests:**
- `test_proposal_generator_load_intake_reports_empty`
- `test_proposal_generator_load_intake_reports_one`
- `test_proposal_generator_load_model_compare_missing`
- `test_proposal_generator_load_model_compare_present`
- `test_generate_proposal_empty`
- `test_generate_proposal_with_intake_and_model_compare`
- `test_get_proposal_includes_devlab_proposal_md`
