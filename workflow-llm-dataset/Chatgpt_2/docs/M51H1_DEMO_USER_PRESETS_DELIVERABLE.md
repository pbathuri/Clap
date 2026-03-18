# M51H.1 — Demo User Presets + Sample Workspace Packs: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/demo_onboarding/models.py` | Added `SampleWorkspacePack`, `DemoUserPreset`; extended `DemoOnboardingSession` with `demo_user_preset_id`, `workspace_pack_id`. |
| `src/workflow_dataset/demo_onboarding/flow.py` | `demo_onboarding_apply_user_preset`; `demo_onboarding_bootstrap_memory(..., pack_id=)`; resolves path from `--pack`, session pack, `--path`, or default; updated `build_demo_sequence` / missing-step hint. |
| `src/workflow_dataset/demo_onboarding/__init__.py` | Exports for packs, user presets, staging guide, `demo_onboarding_apply_user_preset`. |
| `src/workflow_dataset/cli.py` | `bootstrap-memory --pack`; commands: `user-preset`, `workspace-packs`, `workspace-pack-path`, `staging-guide`. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/demo_onboarding/workspace_packs.py` | Registry `SAMPLE_WORKSPACE_PACKS`, `resolve_workspace_pack_path`, list helpers. |
| `src/workflow_dataset/demo_onboarding/user_presets.py` | `DEMO_USER_PRESETS` (3 investor-demo combos), `DEFAULT_DEMO_USER_PRESET_ID`. |
| `src/workflow_dataset/demo_onboarding/staging_guide.py` | `build_operator_staging_guide`, `format_staging_guide_text`. |
| `docs/samples/demo_workspace_document_review/*` | Pack `document_review_slice`. |
| `docs/samples/demo_workspace_analyst/*` | Pack `analyst_followup_slice`. |
| `tests/test_demo_onboarding_m51h1.py` | Pack registry, path resolution, user presets, staging guide, apply+bootstrap flow. |
| `docs/M51H1_DEMO_USER_PRESETS_DELIVERABLE.md` | This file. |

## 3. Sample demo user preset (`investor_demo_primary`)

```json
{
  "user_preset_id": "investor_demo_primary",
  "label": "Primary investor demo (founder + Acme sample)",
  "role_preset_id": "founder_operator_demo",
  "workspace_pack_id": "acme_operator_default",
  "investor_narrative": "New operator plugs in after USB boot, picks founder path, ingests a tiny sample workspace that looks like weekly ops — then sees ready-to-assist with workspace home as first value.",
  "staging_checklist": [
    "Fresh machine or reset demo session: demo onboarding start --reset",
    "Apply user preset: demo onboarding user-preset --id investor_demo_primary",
    "Run bootstrap-memory (uses pack automatically): demo onboarding bootstrap-memory",
    "Show ready-state, then day preset + defaults as printed",
    "Optional: dry-run package first-run on USB image before live demo"
  ]
}
```

Also: `investor_demo_documents`, `investor_demo_analyst`.

## 4. Sample workspace pack (`acme_operator_default`)

```json
{
  "pack_id": "acme_operator_default",
  "label": "Acme operator (primary investor demo)",
  "path_relative": "docs/samples/demo_onboarding_workspace",
  "suggested_role_preset_ids": ["founder_operator_demo"],
  "demo_talking_points": [
    "Small bounded sample — not the user's whole machine.",
    "Memory bootstrap picks up project folder name and priority lines from markdown."
  ]
}
```

Also: `document_review_slice` → `docs/samples/demo_workspace_document_review`; `analyst_followup_slice` → `docs/samples/demo_workspace_analyst`.

## 5. Exact tests run

```bash
pytest tests/test_demo_onboarding.py tests/test_demo_onboarding_m51h1.py -v
```

M51H.1-specific: `test_sample_workspace_packs_registry`, `test_resolve_workspace_pack_paths_exist`, `test_demo_user_presets`, `test_session_roundtrip_with_m51h1_fields`, `test_staging_guide_structure`, `test_user_preset_then_bootstrap_at_repo`.

## 6. Next recommended step for the pane

- **USB / installer**: Print `workflow-dataset demo onboarding staging-guide` (or first 10 lines) in post-boot README or `demo bootstrap` output.
- **Single “demo run” command**: Optional `demo onboarding run --preset investor_demo_primary` that chains start --reset → user-preset → bootstrap-memory → ready-state (non-interactive).
- **Pack verification in CI**: Add a CI step that runs `workspace-packs` and asserts all `resolved_path_exists` for release branches.

## Operator CLI quick reference

```bash
workflow-dataset demo onboarding staging-guide
workflow-dataset demo onboarding user-preset --list
workflow-dataset demo onboarding workspace-packs
workflow-dataset demo onboarding workspace-pack-path --id acme_operator_default
```
