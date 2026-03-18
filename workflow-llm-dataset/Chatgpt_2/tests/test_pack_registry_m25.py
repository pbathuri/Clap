"""
M25A–M25D: Pack registry, verification, install/update/remove/rollback, history.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.packs.registry_index import (
    RegistryEntry,
    load_local_registry,
    get_registry_entry,
    list_registry_entries,
    get_registry_index_path,
)
from workflow_dataset.packs.verify import verify_pack
from workflow_dataset.packs.pack_history import (
    append_install_record,
    get_pack_history,
    get_previous_version,
    get_previous_manifest_path,
)
from workflow_dataset.packs.install_flows import (
    install_pack_from_registry,
    update_pack,
    remove_pack,
    rollback_pack,
    list_installed_with_updates,
)
from workflow_dataset.packs.pack_state import load_pack_state, save_pack_state, get_packs_dir
from workflow_dataset.packs.pack_installer import install_pack, uninstall_pack


def test_registry_load_empty(tmp_path):
    """Empty or missing index returns empty list."""
    entries = load_local_registry(tmp_path)
    assert entries == []


def test_registry_index_path(tmp_path):
    assert "registry" in str(get_registry_index_path(tmp_path))
    assert get_registry_index_path(tmp_path).name == "index.json"


def test_registry_load_from_json(tmp_path):
    """Load registry from index.json with entries array."""
    index_dir = tmp_path / "registry"
    index_dir.mkdir(parents=True)
    index_dir.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "entries": [
            {"pack_id": "test_pack", "title": "Test", "version": "1.0.0", "source_type": "local", "source_path": "test_pack/manifest.json"},
        ]
    }
    (tmp_path / "registry" / "index.json").write_text(json.dumps(data), encoding="utf-8")
    entries = load_local_registry(tmp_path)
    assert len(entries) == 1
    assert entries[0].pack_id == "test_pack"
    assert entries[0].version == "1.0.0"


def test_get_registry_entry(tmp_path):
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "registry" / "index.json").write_text(
        json.dumps({"entries": [{"pack_id": "founder_ops_pack", "version": "0.2.0", "source_path": "founder_ops_pack/manifest.json"}]}),
        encoding="utf-8",
    )
    entry = get_registry_entry("founder_ops_pack", tmp_path)
    assert entry is not None
    assert entry.pack_id == "founder_ops_pack"
    assert entry.version == "0.2.0"


def test_verify_pack_not_installed(tmp_path):
    valid, w, e = verify_pack("nonexistent", tmp_path)
    assert not valid
    assert any("not installed" in err.lower() or "missing" in err.lower() for err in e)


def test_verify_pack_installed_valid(tmp_path):
    """When pack is installed with valid manifest, verify passes."""
    (tmp_path / "valid_pack").mkdir(parents=True)
    manifest = {
        "pack_id": "valid_pack",
        "name": "Valid",
        "version": "0.1.0",
        "safety_policies": {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True},
    }
    (tmp_path / "valid_pack" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    save_pack_state({"valid_pack": {"path": "valid_pack/manifest.json", "version": "0.1.0", "installed_utc": 0}}, tmp_path)
    valid, w, e = verify_pack("valid_pack", tmp_path)
    assert valid
    assert len(e) == 0


def test_pack_history_append_and_get(tmp_path):
    append_install_record("hist_pack", "1.0.0", tmp_path)
    append_install_record("hist_pack", "1.1.0", tmp_path)
    hist = get_pack_history("hist_pack", tmp_path)
    assert len(hist) >= 2
    assert hist[0].get("version") == "1.1.0"
    assert get_previous_version("hist_pack", tmp_path) == "1.0.0"


def test_install_from_registry_no_entry(tmp_path):
    ok, msg, warning = install_pack_from_registry("no_such_pack", tmp_path, "local_registry")
    assert not ok
    assert "not in registry" in msg.lower() or "not found" in msg.lower()
    assert warning is None


def test_remove_pack(tmp_path):
    save_pack_state({"rem_pack": {"path": "rem_pack/manifest.json", "version": "0.1.0", "installed_utc": 0}}, tmp_path)
    ok, msg = remove_pack("rem_pack", tmp_path)
    assert ok
    assert load_pack_state(tmp_path).get("rem_pack") is None


def test_list_installed_with_updates(tmp_path):
    save_pack_state({"a": {"path": "a/manifest.json", "version": "0.1.0", "installed_utc": 0}}, tmp_path)
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "registry" / "index.json").write_text(
        json.dumps({"entries": [{"pack_id": "a", "version": "0.2.0", "source_path": "a/manifest.json"}]}),
        encoding="utf-8",
    )
    listed = list_installed_with_updates(tmp_path)
    assert len(listed) == 1
    assert listed[0].get("update_available") is True
    assert listed[0].get("registry_version") == "0.2.0"


def test_rollback_no_previous(tmp_path):
    ok, msg = rollback_pack("no_hist_pack", tmp_path)
    assert not ok
    assert "previous" in msg.lower() or "no" in msg.lower()


def test_format_registry_list():
    from workflow_dataset.packs.registry_report import format_registry_list
    entries = [RegistryEntry(pack_id="x", title="X", version="1.0.0")]
    out = format_registry_list(entries, {"x": "1.0.0"})
    assert "x" in out
    assert "1.0.0" in out


def test_format_verify_result():
    from workflow_dataset.packs.registry_report import format_verify_result
    out = format_verify_result(False, ["warn"], ["err"], "pid")
    assert "invalid" in out
    assert "err" in out
    assert "warn" in out


# ----- M25D.1 Release channels + registry policy -----


def test_load_registry_policy_default(tmp_path):
    """When no policy file, returns default channels (stable=allow, preview=warn, internal=block)."""
    from workflow_dataset.packs.registry_policy import load_registry_policy, get_registry_policy_path
    policy = load_registry_policy(tmp_path)
    assert policy["channels"].get("stable") == "allow"
    assert policy["channels"].get("preview") == "warn"
    assert policy["channels"].get("internal") == "block"
    assert policy.get("role_overrides") == {}
    assert not get_registry_policy_path(tmp_path).exists()


def test_load_registry_policy_from_file(tmp_path):
    """Load policy from registry/policy.json."""
    from workflow_dataset.packs.registry_policy import load_registry_policy
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "registry" / "policy.json").write_text(
        json.dumps({"channels": {"stable": "allow", "preview": "block"}, "role_overrides": {"ops": {"preview": "allow"}}}),
        encoding="utf-8",
    )
    policy = load_registry_policy(tmp_path)
    assert policy["channels"].get("preview") == "block"
    assert policy["role_overrides"].get("ops", {}).get("preview") == "allow"


def test_check_channel_policy_allow_block_warn(tmp_path):
    """check_channel_policy returns allow/warn/block and reason."""
    from workflow_dataset.packs.registry_policy import check_channel_policy, load_registry_policy
    # Default: stable=allow, preview=warn, internal=block
    action, reason = check_channel_policy("stable", "", tmp_path)
    assert action == "allow"
    action, reason = check_channel_policy("preview", "", tmp_path)
    assert action == "warn"
    action, reason = check_channel_policy("internal", "", tmp_path)
    assert action == "block"
    assert "internal" in reason


def test_check_channel_policy_role_override(tmp_path):
    """Per-role override can allow a channel that is blocked by default."""
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "registry" / "policy.json").write_text(
        json.dumps({"channels": {"internal": "block"}, "role_overrides": {"founder": {"internal": "allow"}}}),
        encoding="utf-8",
    )
    from workflow_dataset.packs.registry_policy import check_channel_policy
    action, _ = check_channel_policy("internal", "founder", tmp_path)
    assert action == "allow"
    action, _ = check_channel_policy("internal", "", tmp_path)
    assert action == "block"


def test_install_from_registry_blocked_by_channel(tmp_path):
    """When registry entry has release_channel=internal and policy blocks internal, install returns False."""
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "registry" / "index.json").write_text(
        json.dumps({
            "entries": [{
                "pack_id": "blocked_pack",
                "version": "0.1.0",
                "source_path": "blocked_pack/manifest.json",
                "release_channel": "internal",
            }]
        }),
        encoding="utf-8",
    )
    (tmp_path / "blocked_pack").mkdir(parents=True)
    (tmp_path / "blocked_pack" / "manifest.json").write_text(
        json.dumps({"pack_id": "blocked_pack", "name": "B", "version": "0.1.0", "safety_policies": {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True}}),
        encoding="utf-8",
    )
    # Default policy blocks "internal"
    ok, msg, warning = install_pack_from_registry("blocked_pack", tmp_path, "local_registry")
    assert not ok
    assert "blocked" in msg.lower() or "not allowed" in msg.lower()
    assert "internal" in msg.lower()
    assert warning is None


def test_install_from_registry_warn_channel(tmp_path):
    """When channel is 'warn', install succeeds but returns warning string."""
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "registry" / "index.json").write_text(
        json.dumps({
            "entries": [{
                "pack_id": "warn_pack",
                "version": "0.1.0",
                "source_path": "warn_pack/manifest.json",
                "release_channel": "preview",
            }]
        }),
        encoding="utf-8",
    )
    (tmp_path / "warn_pack").mkdir(parents=True)
    (tmp_path / "warn_pack" / "manifest.json").write_text(
        json.dumps({"pack_id": "warn_pack", "name": "W", "version": "0.1.0", "safety_policies": {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True}}),
        encoding="utf-8",
    )
    ok, msg, warning = install_pack_from_registry("warn_pack", tmp_path, "local_registry")
    assert ok
    assert warning is not None
    assert "preview" in warning.lower() or "not recommended" in warning.lower()
