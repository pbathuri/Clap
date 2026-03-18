# M25A–M25D Pack Registry, Signing, Distribution, Updates — Before Coding

## 1. What pack/runtime/distribution behavior already exists

| Area | Location | What exists |
|------|----------|-------------|
| **Manifest** | packs/pack_models.py | PackManifest: pack_id, name, version, description, role_tags, workflow_tags, task_tags, dependencies, signature_metadata (placeholder), safety_policies. validate_pack_manifest(). |
| **Installed state** | packs/pack_state.py | installed_state.json: pack_id → { path, version, installed_utc }. load_pack_state, save_pack_state, get_packs_dir. active_role.txt. |
| **Activation** | packs/pack_activation.py | activation_state.json: primary_pack_id, secondary_pack_ids, pinned, suspended_pack_ids. set_primary_pack, pin_pack, suspend_pack, resume_pack, etc. |
| **Registry (installed only)** | packs/pack_registry.py | list_installed_packs(), get_installed_pack(), get_installed_manifest() — reads from installed state and manifest files. No “available” or “index” registry. |
| **Install/Uninstall** | packs/pack_installer.py | install_pack(manifest_path) — validate manifest, copy to packs dir, apply recipe steps, update state. uninstall_pack(pack_id) — remove from state only (does not delete files). |
| **Resolution** | packs/pack_resolver, pack_resolution_graph | resolve_with_priority(role, workflow, task); primary/pinned/secondary/suspended. |
| **Conflicts** | packs/pack_conflicts.py | detect_conflicts(manifests); ConflictClass; precedence and merge rules. |
| **CLI** | cli.py | packs list, show, install (manifest path arg), uninstall, activate, deactivate, pin, unpin, conflicts, explain, validate-manifest, etc. No registry list/show, no install by id from registry, no verify/update/history. |
| **Distribution (M24R–M24U)** | distribution/* | Install bundle, install-profile, update-plan (product-level), deploy readiness, handoff-pack. Not pack-level registry/update. |

## 2. What is missing for a true first-draft registry/update subsystem

- **Curated registry/index:** No representation of “available” packs (local or explicit external). Need: pack id, title, version, description, supported roles/workflows, compatibility, dependencies, local vs external source, trust notes, verification metadata, install status, update_availability, release_channel.
- **Install from registry:** Current install takes a manifest file path only. Need: install by pack id from a local registry (e.g. data/local/packs/registry/index.json or directory of manifests).
- **Verification:** PackManifest has signature_metadata but no checksum verification, no manifest integrity check, no version compatibility check, no reject/warn on invalid/tampered.
- **Update flow:** No “check for newer version” or “update pack” that preserves activation state and runs conflict check after.
- **Remove/rollback:** Uninstall exists; no “remove” alias; no rollback to previous installed version (no per-pack version history stored).
- **Pack history:** installed_state only stores current version per pack; no history of (version, installed_utc) for rollback.
- **CLI:** No packs registry list/show, packs install --source local_registry --id X, packs verify, packs update, packs remove, packs history.
- **Mission control:** No visibility for installed-by-version, update availability, verification failures, pack state history, registry status, blocked installs/updates.

## 3. Exact file plan

| File | Purpose |
|------|--------|
| **packs/registry_index.py** (new) | Registry index model: RegistryEntry (pack_id, title, version, description, supported_roles, supported_workflows, compatibility_requirements, dependencies, source_type local|external, source_path|url, trust_notes, checksum, signature_metadata, release_channel). load_local_registry(), get_registry_entry(), list_registry_entries(). Default index: data/local/packs/registry/index.json or bundled list. |
| **packs/verify.py** (new) | verify_pack(pack_id, packs_dir): checksum manifest if metadata present, manifest schema validation, version format; return (valid, warnings, errors). Optional: reject if signature_metadata.verified false when strict. |
| **packs/install_flows.py** (new) | install_pack_from_registry(registry_id, pack_id, packs_dir), update_pack(pack_id, packs_dir), remove_pack (alias uninstall), rollback_pack(pack_id, packs_dir). update_pack: resolve registry entry for pack_id, compare version, install new manifest, preserve activation (primary/pinned/suspended), run conflict check. rollback_pack: restore from pack_install_history. |
| **packs/pack_history.py** (new) | Per-pack install history: append_install_record(pack_id, version, installed_utc, packs_dir), get_pack_history(pack_id), get_previous_version(pack_id). Store in data/local/packs/install_history.json or data/local/packs/<pack_id>/install_history.json. |
| **packs/report.py** (new) or extend existing | format_registry_list, format_registry_show, format_verify_result, format_pack_history. |
| **pack_state.py** (modify) | Optional: extend installed_state to include previous_version or keep history in separate file (prefer separate for clarity). |
| **pack_installer.py** (modify) | No change to core install_pack; install_flows will call it. Optionally have install_pack return new version for history. |
| **cli.py** (modify) | Add: packs registry list, packs registry show --id; packs install --source local_registry --id X (optional args); packs verify --id; packs update --id; packs remove --id (alias uninstall); packs history --id. |
| **mission_control/state.py** (modify) | Add pack_registry block: installed_by_version, update_available_count, verification_failures, registry_status, blocked_install_reasons. |
| **mission_control/report.py** (modify) | Add [Pack registry] section. |
| **tests/test_pack_registry_m25.py** (new) | Registry load, verify success/failure, install from registry, update, remove, history, rollback, blocked install. |
| **docs/M25A_M25D_PACK_REGISTRY.md** (new) | Summary, CLI, sample registry entry, verification output, install/update/rollback/history samples, tests, gaps. |

## 4. Safety/risk note

- **Local-first:** Default registry is local (data/local/packs/registry). External URLs only when explicitly configured and approval-gated (e.g. allow-list or operator-approved source).
- **No silent updates:** Update flow requires explicit CLI invocation; no background update checks or auto-install.
- **Verification:** Checksum and manifest validation reject malformed or tampered manifests; optional signature_metadata can be used to warn. No full PKI; practical and inspectable.
- **Preserve activation:** On update, primary_pack_id and pinned/suspended state are preserved so resolution behavior does not change unexpectedly.
- **Conflict check after install/update:** Reuse detect_conflicts after install/update and report; do not block install by default (operator decides).

## 5. What this block will NOT do

- Build a public SaaS marketplace or blind internet pack installation.
- Implement full PKI or code-signing infrastructure.
- Auto-update packs silently or in the background.
- Bypass pack verification or trust gates.
- Rebuild pack runtime resolution (primary/pinned/suspended) from scratch.
- Delete pack files on uninstall/remove (current behavior: remove from state only; rollback restores state from history, not file restore).
