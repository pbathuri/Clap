# M51E–M51H — First-Run Onboarding + Role/Memory Bootstrap: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `demo` Typer group with `demo onboarding` subcommands: `start`, `role`, `bootstrap-memory`, `ready-state`, `sequence`. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M51E_M51H_FIRST_RUN_DEMO_BEFORE_CODING.md` | Before-coding analysis (§1–7). |
| `src/workflow_dataset/demo_onboarding/__init__.py` | Package exports. |
| `src/workflow_dataset/demo_onboarding/models.py` | Demo session, role preset, workspace source, memory bootstrap plan, completion, ready-to-assist, trust posture, bootstrap confidence. |
| `src/workflow_dataset/demo_onboarding/presets.py` | `founder_operator_demo` (default), `document_review_demo`, `analyst_followup_demo`. |
| `src/workflow_dataset/demo_onboarding/store.py` | Session + bootstrap summary JSON under `data/local/demo_onboarding/`. |
| `src/workflow_dataset/demo_onboarding/memory_bootstrap.py` | Bounded scan (≤15 files, ≤8KB/file, `.md`/`.txt`), memory + graph ingest, heuristic themes/priorities. |
| `src/workflow_dataset/demo_onboarding/flow.py` | `start`, `select_role`, `bootstrap_memory`, `build_ready_to_assist_state`, `build_demo_sequence`. |
| `docs/samples/demo_onboarding_workspace/**` | Bundled sample workspace (README + `acme_weekly/` notes). |
| `tests/test_demo_onboarding.py` | Eight focused tests. |
| `docs/M51E_M51H_DELIVERABLE.md` | This file. |

## 3. Exact onboarding / CLI flow

```bash
# Ordered sequence (also: demo onboarding sequence)
workflow-dataset demo onboarding start
workflow-dataset demo onboarding role --id founder_operator_demo
# optional: demo onboarding role --list
workflow-dataset demo onboarding bootstrap-memory
# optional: demo onboarding bootstrap-memory --path /path/to/small/folder
workflow-dataset demo onboarding ready-state

# New session
workflow-dataset demo onboarding start --reset
```

Follow-on (existing product): `workflow-dataset day preset set --id <from_role>`, `workflow-dataset defaults apply calm_default`, `workflow-dataset onboard status`.

## 4. Sample role preset (`founder_operator_demo`)

```json
{
  "preset_id": "founder_operator_demo",
  "label": "Founder / operator (investor demo)",
  "description": "Ops reporting, daily priorities, inbox-style follow-ups. Best default for USB demo after boot.",
  "vertical_pack_id": "founder_operator_core",
  "day_preset_id": "founder_operator",
  "default_experience_profile": "calm_default",
  "trust_posture": {
    "posture_id": "demo_conservative",
    "label": "Demo conservative",
    "simulate_first": true,
    "approval_note": "workflow-dataset onboard status  →  onboard approve"
  },
  "recommended_first_value_command": "workflow-dataset workspace home --profile calm_default"
}
```

## 5. Sample bootstrap-memory summary (JSON excerpt)

```json
{
  "workspace_root": ".../docs/samples/demo_onboarding_workspace",
  "files_scanned": 3,
  "file_names": ["README.md", "followups.txt", "status.md"],
  "project_hints": ["acme_weekly"],
  "recurring_themes": ["weekly", "priority", "workflow", "demo", "..."],
  "work_style_hints": ["Report-style documents present.", "..."],
  "likely_priorities": ["- Close Q1 deck review by Friday", "- Priority: reply to two advisor emails", "..."],
  "memory_units_created": 2,
  "confidence": { "level": "medium", "rationale": "Multiple sample files ingested; themes are heuristic word counts only." },
  "disclaimer": "Inferences are from a small bounded sample only, not full-device learning."
}
```

## 6. Sample ready-to-assist output

- **ready**: `true` (after role + bootstrap-memory)
- **chosen_role_label**: `Founder / operator (investor demo)`
- **vertical_pack_id**: `founder_operator_core`
- **memory_bootstrap_summary**: `Scanned 3 sample files; N memory unit(s). Inferences are from a small bounded sample only...`
- **inferred_project_context**: `["acme_weekly"]`
- **recommended_first_value_action**: `workflow-dataset workspace home --profile calm_default`
- **confirmation_message**: `Ready to assist — demo onboarding complete. Role and sample context are loaded; full approvals still via onboard approve.`
- **next_setup_commands**: day preset, defaults apply, onboard status

## 7. Exact tests run

```bash
pytest tests/test_demo_onboarding.py -v
```

Tests: `test_demo_session_roundtrip`, `test_role_presets`, `test_demo_onboarding_start_and_role`, `test_bounded_memory_bootstrap_sample_files`, `test_bootstrap_empty_workspace`, `test_ready_state_incomplete`, `test_ready_state_complete`, `test_demo_sequence`.

## 8. Remaining gaps before investor-demo flow is complete

- **USB boot handoff**: Wire `package first-run` or USB demo script to print `demo onboarding sequence` as the post-boot CTA (docs or installer only).
- **TUI/console**: Optional single guided command that chains start → role → bootstrap → ready (non-interactive flags for CI).
- **Vertical pack activation**: Role preset names `founder_operator_core`; actual pack install/launch remains separate CLI (`vertical-packs` / launch kits) — document or optionally invoke one safe read-only command.
- **Trust UX**: No in-app acknowledgment step yet; trust is “documented + role select” only.
- **Richer inference**: Current themes/priorities are keyword/heuristic only; could add optional LLM summarization behind a flag (out of scope for this block).
