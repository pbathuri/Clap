# M39H.1 — Vertical Playbooks + Common Failure Recovery (Deliverable)

First-draft support for vertical playbooks, common failure points by vertical, recovery paths to first-value, and stronger operator guidance when a curated path stalls. Extends M39E–M39H; does not rebuild the curated vertical layer.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/vertical_packs/__init__.py` | Exported playbooks: `get_playbook_for_vertical`, `get_recovery_path_for_failure`, `get_operator_guidance_when_stalled`, `list_vertical_playbook_ids`, `BUILTIN_VERTICAL_PLAYBOOKS`. |
| `src/workflow_dataset/vertical_packs/playbooks.py` | Added `Path` import; `get_operator_guidance_when_stalled(repo_root)` type hint fixed to `Path \| str \| None`. |
| `src/workflow_dataset/vertical_packs/progress.py` | `build_milestone_progress_output()` now includes `operator_guidance_when_stalled` when `blocked_step_index` is set (from vertical playbook). |
| `src/workflow_dataset/cli.py` | Added `vertical-packs playbook --id` and `vertical-packs recovery --id --step`; progress command prints operator guidance when stalled. |
| `tests/test_vertical_packs.py` | Added tests: `test_playbook_for_vertical`, `test_recovery_path_for_failure`, `test_operator_guidance_when_stalled`, `test_list_vertical_playbook_ids`, `test_progress_includes_operator_guidance_when_blocked`. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/samples/M39H1_vertical_playbook_sample.json` | Sample vertical playbook (founder_operator_playbook): failure_entries, recovery_paths, operator_guidance_stalled, operator_commands_stalled. |
| `docs/samples/M39H1_recovery_path_sample.json` | Sample failure recovery payload: failure_entry for step 3, recovery_path (recover_after_approval_block), operator_guidance, operator_commands. |
| `docs/M39H1_VERTICAL_PLAYBOOKS_DELIVERABLE.md` | This deliverable. |

Existing M39H.1 assets (unchanged): `vertical_packs/models.py` (RecoveryPath, RecoveryPathStep, VerticalPlaybook, VerticalPlaybookFailureEntry), `vertical_packs/playbooks.py` (BUILTIN_VERTICAL_PLAYBOOKS, get_playbook_for_vertical, get_recovery_path_for_failure, get_operator_guidance_when_stalled, list_vertical_playbook_ids).

---

## 3. Sample vertical playbook

See `docs/samples/M39H1_vertical_playbook_sample.json`. Summary:

- **playbook_id**: founder_operator_playbook  
- **curated_pack_id**: founder_operator_core  
- **failure_entries**: step 1 (install), 3 (approval block), 4 (simulate fail), 5 (real rejected); each has symptom, remediation_hint, escalation_command, recovery_path_id.  
- **recovery_paths**: recover_after_install, recover_after_approval_block, recover_after_simulate_fail, recover_after_real_rejected; each has steps (step_order, command, label) and target_milestone_id.  
- **operator_guidance_stalled**: guidance text when path stalls.  
- **operator_commands_stalled**: suggested CLI commands (e.g. vertical-packs recovery --id founder_operator_core --step 3, onboard status, trust cockpit).  

CLI: `workflow-dataset vertical-packs playbook --id founder_operator_core` (optionally `--json`).

---

## 4. Sample failure recovery path

See `docs/samples/M39H1_recovery_path_sample.json`. Summary:

- **curated_pack_id**: founder_operator_core  
- **blocked_step_index**: 3  
- **failure_entry**: step_index 3, symptom "No approval scope; real run blocked", remediation_hint "Add path_workspace via onboard approve", escalation_command "workflow-dataset onboard status".  
- **recovery_path**: recover_after_approval_block; steps: (1) onboard status, (2) onboard approve, (3) macro run morning_ops simulate; target_milestone_id first_simulate_done.  
- **operator_guidance** / **operator_commands**: same as playbook stalled guidance.  

CLI: `workflow-dataset vertical-packs recovery --id founder_operator_core --step 3` (optionally `--json`).

---

## 5. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python3 -m pytest tests/test_vertical_packs.py -v
```

**Result:** 10 passed (existing 5 + test_playbook_for_vertical, test_recovery_path_for_failure, test_operator_guidance_when_stalled, test_list_vertical_playbook_ids, test_progress_includes_operator_guidance_when_blocked).

---

## 6. Next recommended step for the pane

- **Wire mission control**: When `vertical_packs_state` is present and there is a blocked step, mission control report could show a one-line “Operator guidance: …” and a link to `vertical-packs recovery --id <pack> --step <N>`. Currently progress CLI and progress JSON include `operator_guidance_when_stalled`; the mission control report section for vertical packs does not yet render it.
- **Auto-suggest recovery in progress**: If `blocked_step_index` is inferred from queue/approval/executor state (future work), automatically attach the playbook recovery suggestion to that step.
- **Optional**: Add `vertical-packs playbook list` (or reuse `vertical-packs list` with a note that each has a playbook) so operators can discover playbooks without knowing pack ids.
