# M30D.1 — Release Channels + Compatibility Matrix

## Overview

First-draft support for release channels (stable / preview / internal), a compatibility matrix across product version, runtime, and policy mode, and warnings for unsafe or unsupported upgrade paths. Extends M30 install/upgrade; does not replace it.

## Sample release-channel definition (stable)

```python
ReleaseChannel(
    channel_id="stable",
    label="Stable",
    description="Production-ready releases. Recommended for non-developers.",
    min_product_version="0.1.0",
    allowed_policy_modes=("enforce", "audit", "disabled"),
    supports_downgrade=False,
    upgrade_paths_to=("stable",),  # only same channel
)
```

Preview allows `upgrade_paths_to=(preview, stable)`; internal allows `(internal, preview, stable)`. Internal → stable is explicitly marked unsupported and adds an unsafe reason to the upgrade plan.

## Sample compatibility matrix output

```
=== Compatibility matrix (M30D.1) ===

[Channels]
  stable: Stable  min_version=0.1.0  policy_modes=['enforce', 'audit', 'disabled']  upgrade_paths_to=['stable']
  preview: Preview  min_version=0.1.0  policy_modes=['enforce', 'audit', 'disabled']  upgrade_paths_to=['preview', 'stable']
  internal: Internal  min_version=0.0.1  policy_modes=['enforce', 'audit', 'disabled', 'permissive']  upgrade_paths_to=['internal', 'preview', 'stable']

[Sample rows: channel × product_version × policy_mode → supported]
  stable  0.1.0  enforce  supported=True
  stable  0.1.0  audit  supported=True
  stable  0.2.0  enforce  supported=True
  preview  0.1.0  enforce  supported=True
  internal  0.1.0  permissive  supported=True
  ...
```

## CLI

- **`workflow-dataset release channels`** [ `--json` ] — List release channels (stable, preview, internal).
- **`workflow-dataset release compatibility-matrix`** [ `--repo-root` ] [ `--json` ] — Print compatibility matrix (channels × version × runtime × policy).
- **`workflow-dataset release upgrade-plan`** — Now accepts **`--current-channel`** and **`--target-channel`**; applies compatibility checks and adds unsafe/warning reasons to the plan.

## Files modified / created

| Action | Path |
|--------|------|
| Modified | `src/workflow_dataset/install_upgrade/models.py` — ReleaseChannel, CHANNEL_* |
| Created | `src/workflow_dataset/install_upgrade/channels.py` |
| Created | `src/workflow_dataset/install_upgrade/compatibility.py` |
| Modified | `src/workflow_dataset/install_upgrade/upgrade_plan.py` — current_channel, target_channel, path_check, warnings |
| Modified | `src/workflow_dataset/install_upgrade/cli.py` — cmd_upgrade_plan channels, cmd_compatibility_matrix, cmd_channels_list |
| Modified | `src/workflow_dataset/cli.py` — release upgrade-plan --current-channel/--target-channel, release compatibility-matrix, release channels |
| Modified | `src/workflow_dataset/install_upgrade/__init__.py` — exports |
| Modified | `tests/test_install_upgrade_m30.py` — M30D.1 tests |
| Created | `docs/M30D1_RELEASE_CHANNELS.md` |

## Tests run

```bash
pytest tests/test_install_upgrade_m30.py -v
```

- **test_channels_list** — list_channels returns 3 channels; get_channel("stable") has min_product_version and upgrade_paths_to.
- **test_compatibility_matrix** — build and format matrix; channels and rows present.
- **test_check_upgrade_path_internal_to_stable** — internal → stable yields unsafe_reasons and allowed=False.
- **test_check_upgrade_path_preview_to_stable** — preview → stable allowed with warning.
- **test_upgrade_plan_includes_channel_warnings** — upgrade-plan with current_channel=internal, target_channel=stable has blocked_reasons and can_proceed=False.
- **test_cmd_channels_list**, **test_cmd_compatibility_matrix** — CLI output shape.

## Next recommended step for the pane

- **Persist current channel**: Store the active release channel (e.g. in `data/local/install/current_version.json` or a small `channel.json`) so `release upgrade-plan` can default `--current-channel` from disk and operators can switch channel explicitly.
- **Channel in mission control**: Add current_channel and compatibility warnings to the mission_control `install_upgrade` block and report so operators see channel and any unsafe upgrade path at a glance.
- **Policy mode detection**: Detect current policy mode (e.g. from trust/policy config) and include it in the compatibility matrix evaluation so “unsupported policy mode for channel” can be raised when applicable.
- **Packs in matrix**: Extend the matrix to include pack ids or pack version ranges (e.g. “pack X requires product >= 0.2.0 on stable”) and surface pack-related upgrade warnings.
