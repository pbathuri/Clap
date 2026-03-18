# M25A–M25D — Pack Registry, Signing, Distribution, Updates

First-draft pack registry and update layer: local curated registry, checksum/manifest verification, install from registry, update, remove, rollback, history. Local-first; no silent updates.

---

## 1. Files modified

| File | Change |
|------|--------|
| `packs/__init__.py` | Export RegistryEntry, load_local_registry, get_registry_entry, list_registry_entries, verify_pack, pack_history helpers, install_flows (install_pack_from_registry, update_pack, remove_pack, rollback_pack, list_installed_with_updates). |
| `cli.py` | packs install: optional manifest path when --source and --id given; add packs verify, update, remove, rollback, history; add packs registry list, packs registry show --id. |
| `mission_control/state.py` | Add pack_registry block: installed_count, installed_by_version, update_available_count, verification_failures, registry_entries_count, channel_policy (M25D.1), next_action. |
| `mission_control/report.py` | Add [Pack registry] section; channel_policy (block/warn/role) when present. |

## 2. Files created

| File | Purpose |
|------|--------|
| `packs/registry_index.py` | RegistryEntry model; load_local_registry, get_registry_entry, list_registry_entries; index from data/local/packs/registry/index.json. |
| `packs/verify.py` | verify_pack(pack_id): checksum (if in manifest), schema validation; return (valid, warnings, errors). |
| `packs/pack_history.py` | append_install_record, get_pack_history, get_previous_version, get_previous_manifest_path; store in install_history.json. |
| `packs/install_flows.py` | install_pack_from_registry, update_pack, remove_pack, rollback_pack, list_installed_with_updates; backup current manifest to versions/<ver>/ before update; preserve activation. |
| `packs/registry_report.py` | format_registry_list, format_registry_show, format_verify_result, format_pack_history. |
| `packs/registry_policy.py` | (M25D.1) load_registry_policy, check_channel_policy; registry/policy.json; stable/preview/internal allow/warn/block; role_overrides. |
| `tests/test_pack_registry_m25.py` | Registry load, get entry, verify (not installed / valid), history append/get, install from registry (no entry), remove, list_installed_with_updates, rollback no previous, format helpers. |
| `docs/M25A_M25D_PACK_REGISTRY_ANALYSIS.md` | Before-coding analysis. |
| `docs/M25A_M25D_PACK_REGISTRY.md` | This doc. |

---

## 3. Exact CLI usage

```bash
# Registry
workflow-dataset packs registry list [--packs-dir PATH] [--channel local|dev|stable]
workflow-dataset packs registry show --id <pack_id> [--packs-dir PATH]
workflow-dataset packs registry policy [--packs-dir PATH]

# Install from manifest file (existing) or from registry
workflow-dataset packs install <manifest_path> [--packs-dir PATH]
workflow-dataset packs install --source local_registry --id <pack_id> [--packs-dir PATH]

# Verify installed pack
workflow-dataset packs verify <pack_id> [--packs-dir PATH] [--strict]

# Update / remove / rollback / history
workflow-dataset packs update <pack_id> [--packs-dir PATH]
workflow-dataset packs remove <pack_id> [--packs-dir PATH]
workflow-dataset packs rollback <pack_id> [--packs-dir PATH]
workflow-dataset packs history <pack_id> [--packs-dir PATH] [--limit N]
```

---

## 4. Sample registry entry

**data/local/packs/registry/index.json:**

```json
{
  "entries": [
    {
      "pack_id": "founder_ops_pack",
      "title": "Founder / operator pack",
      "version": "0.2.0",
      "description": "Light ops, reporting, stakeholder updates.",
      "supported_roles": ["ops", "founder"],
      "supported_workflows": ["reporting", "simulation"],
      "source_type": "local",
      "source_path": "founder_ops_pack/manifest.json",
      "release_channel": "stable",
      "trust_notes": "Curated local pack.",
      "checksum": "",
      "dependencies": []
    }
  ]
}
```

`source_path` is relative to the packs dir (e.g. `data/local/packs/`) or an absolute path to a manifest file.

---

## 5. Sample verification output

```
=== Pack verify: founder_ops_pack ===

Result: valid
```

When invalid (e.g. pack not installed):

```
=== Pack verify: missing_pack ===

Result: invalid
  error: Pack not installed or manifest missing: missing_pack
```

When checksum mismatch:

```
Result: invalid
  error: Checksum mismatch: manifest may be tampered or corrupted
```

---

## 6. Sample install / update / rollback output

**Install from registry:**
```
Installed founder_ops_pack@0.2.0
```

**Update:**
```
Already at latest version 0.2.0
```
or
```
Installed founder_ops_pack@0.3.0
```

**Rollback:**
```
Installed founder_ops_pack@0.2.0
```

**Remove:**
```
Uninstalled founder_ops_pack
```

---

## 7. Sample pack history output

```
=== Pack history: founder_ops_pack ===

  1. version=0.3.0  installed_utc=2024-03-16T12:00:00Z
  2. version=0.2.0  installed_utc=2024-03-15T10:00:00Z
  3. version=0.1.0  installed_utc=2024-03-14T08:00:00Z
```

---

## 8. Exact tests run

```bash
pytest tests/test_pack_registry_m25.py -v --tb=short
```

Requires project dependencies (e.g. pydantic). Covers: registry load (empty, from JSON), get_registry_entry, verify (not installed, valid installed), pack history append/get/previous_version, install_from_registry (no entry, blocked by channel, warn channel), remove_pack, list_installed_with_updates, rollback (no previous), format_registry_list, format_verify_result; (M25D.1) load_registry_policy default/from file, check_channel_policy allow/warn/block and role override. **19 tests.**

---

## 9. Remaining gaps for later refinement

- **External URLs:** source_url in RegistryEntry is not used for install; external sources remain explicit and approval-gated; no fetch-from-URL in this block.
- **Full PKI:** No code-signing or full signature verification; only checksum and optional signature_metadata.verified flag.
- **Version ordering:** Update uses simple string inequality (registry version != current); no semver compare for “newer”.
- **Blocked install reasons:** Mission control pack_registry does not yet surface “blocked install/update” reasons (e.g. conflict with primary); can be added by running conflict check after install.
- **Registry index location:** Index path is fixed as `data/local/packs/registry/index.json`; no --registry flag to point to another file.
- **Delete files on remove:** remove/uninstall only clear state; pack files under packs dir are left on disk for safe rollback; optional “purge” could be added later.
