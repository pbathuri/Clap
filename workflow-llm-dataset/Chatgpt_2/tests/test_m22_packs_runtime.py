"""M22: Tests for capability packs (install, resolve, validate) and runtime resolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.packs.pack_models import PackManifest, validate_pack_manifest
from workflow_dataset.packs.pack_state import load_pack_state, save_pack_state, get_packs_dir
from workflow_dataset.packs.pack_registry import list_installed_packs, get_installed_pack, get_installed_manifest
from workflow_dataset.packs.pack_installer import install_pack, uninstall_pack
from workflow_dataset.packs.pack_resolver import resolve_active_capabilities, ActiveCapabilities
from workflow_dataset.packs.pack_validator import validate_pack_manifest_and_recipes
from workflow_dataset.packs.pack_recipes import validate_recipe_steps, ALLOWED_RECIPE_STEP_TYPES
from workflow_dataset.capability_intake.source_cache import (
    record_source_metadata,
    load_source_metadata,
    list_cached_sources,
    link_snapshot_to_source,
)


# ----- Pack manifest validation -----


def test_validate_pack_manifest_required_fields() -> None:
    valid, errs = validate_pack_manifest({"pack_id": "x", "name": "X", "version": "0.1.0"})
    assert valid is True
    assert len(errs) == 0


def test_validate_pack_manifest_missing_pack_id() -> None:
    valid, errs = validate_pack_manifest({"name": "X", "version": "0.1.0"})
    assert valid is False
    assert any("pack_id" in e for e in errs)


def test_validate_pack_manifest_safety_policies() -> None:
    valid, errs = validate_pack_manifest({
        "pack_id": "x", "name": "X", "version": "0.1.0",
        "safety_policies": {"sandbox_only": False},
    })
    assert valid is False
    assert any("sandbox_only" in e for e in errs)


def test_validate_recipe_steps_allowed() -> None:
    steps = [{"type": "create_config", "name": "cfg"}, {"type": "register_templates"}]
    ok, errs = validate_recipe_steps(steps)
    assert ok is True
    assert len(errs) == 0


def test_validate_recipe_steps_disallowed() -> None:
    ok, errs = validate_recipe_steps([{"type": "run_shell", "cmd": "echo 1"}])
    assert ok is False
    assert any("run_shell" in e or "disallowed" in e for e in errs)


def test_validate_pack_manifest_and_recipes() -> None:
    data = {
        "pack_id": "p", "name": "P", "version": "0.1.0",
        "recipe_steps": [{"type": "create_config", "name": "c"}],
    }
    ok, errs = validate_pack_manifest_and_recipes(data)
    assert ok is True


# ----- Pack state / registry -----


def test_pack_state_load_save(tmp_path: Path) -> None:
    state = {"pack_a": {"path": "a/manifest.json", "version": "0.1.0", "installed_utc": 0}}
    save_pack_state(state, tmp_path)
    loaded = load_pack_state(tmp_path)
    assert loaded == state


def test_list_installed_packs_empty(tmp_path: Path) -> None:
    assert list_installed_packs(tmp_path) == []


# ----- Pack install / uninstall -----


@pytest.fixture
def valid_manifest_path(tmp_path: Path) -> Path:
    manifest = {
        "pack_id": "ops_pack",
        "name": "Ops reporting pack",
        "version": "0.1.0",
        "role_tags": ["ops"],
        "industry_tags": ["general"],
        "workflow_tags": ["reporting"],
        "task_tags": ["summarize"],
        "recommended_models": ["local/small"],
        "output_adapters": ["ops_handoff"],
        "recipe_steps": [{"type": "create_config", "name": "ops_config", "content": {}}],
    }
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(manifest), encoding="utf-8")
    return p


def test_install_pack(tmp_path: Path, valid_manifest_path: Path) -> None:
    ok, msg = install_pack(valid_manifest_path, tmp_path)
    assert ok is True
    assert "ops_pack" in msg
    state = load_pack_state(tmp_path)
    assert "ops_pack" in state
    assert state["ops_pack"]["version"] == "0.1.0"
    (tmp_path / "ops_pack" / "manifest.json").exists()
    (tmp_path / "ops_pack" / "ops_config.json").exists()


def test_uninstall_pack(tmp_path: Path, valid_manifest_path: Path) -> None:
    install_pack(valid_manifest_path, tmp_path)
    ok, msg = uninstall_pack("ops_pack", tmp_path)
    assert ok is True
    assert list_installed_packs(tmp_path) == []


def test_get_installed_manifest(tmp_path: Path, valid_manifest_path: Path) -> None:
    install_pack(valid_manifest_path, tmp_path)
    m = get_installed_manifest("ops_pack", tmp_path)
    assert m is not None
    assert m.pack_id == "ops_pack"
    assert m.role_tags == ["ops"]
    assert m.recommended_models == ["local/small"]


# ----- Pack resolution -----


def test_resolve_active_capabilities_all_when_no_filters(tmp_path: Path, valid_manifest_path: Path) -> None:
    install_pack(valid_manifest_path, tmp_path)
    cap = resolve_active_capabilities(packs_dir=str(tmp_path))
    assert len(cap.active_packs) == 1
    assert cap.active_packs[0].pack_id == "ops_pack"
    assert cap.recommended_models == ["local/small"]
    assert "ops_handoff" in cap.output_adapters


def test_resolve_active_capabilities_by_role(tmp_path: Path, valid_manifest_path: Path) -> None:
    install_pack(valid_manifest_path, tmp_path)
    cap = resolve_active_capabilities(role="ops", packs_dir=str(tmp_path))
    assert len(cap.active_packs) == 1
    cap2 = resolve_active_capabilities(role="analyst", packs_dir=str(tmp_path))
    assert len(cap2.active_packs) == 0


def test_resolve_active_capabilities_empty_when_none_installed(tmp_path: Path) -> None:
    cap = resolve_active_capabilities(packs_dir=str(tmp_path))
    assert len(cap.active_packs) == 0
    assert cap.recommended_models == []
    assert cap.output_adapters == []


# ----- Source cache -----


def test_source_cache_record_and_load(tmp_path: Path) -> None:
    record_source_metadata(
        "openclaw",
        repo_url="https://github.com/example/openclaw",
        commit="abc",
        version="0.1",
        license_info="MIT",
        adoption_decision="reference_only",
        cache_dir=tmp_path,
    )
    meta = load_source_metadata("openclaw", tmp_path)
    assert meta is not None
    assert meta["repo_url"] == "https://github.com/example/openclaw"
    assert meta["adoption_decision"] == "reference_only"


def test_source_cache_list_cached_sources(tmp_path: Path) -> None:
    record_source_metadata("a", "https://a", cache_dir=tmp_path)
    record_source_metadata("b", "https://b", cache_dir=tmp_path)
    listed = list_cached_sources(tmp_path)
    assert len(listed) == 2
    ids = {x["source_id"] for x in listed}
    assert ids == {"a", "b"}


def test_source_cache_link_snapshot(tmp_path: Path) -> None:
    record_source_metadata("x", "https://x", cache_dir=tmp_path)
    link_snapshot_to_source("x", "/tmp/snapshot_x", cache_dir=tmp_path)
    meta = load_source_metadata("x", tmp_path)
    assert meta is not None
    assert meta.get("snapshot_path") == "/tmp/snapshot_x"


# ----- External wrapper metadata -----


def test_openclaw_reference_metadata() -> None:
    from workflow_dataset.external_wrappers.openclaw_runtime_reference import REFERENCE
    assert REFERENCE["source_id"] == "openclaw"
    assert REFERENCE["adoption"] == "reference_only"
    assert "runtime_mapping" in REFERENCE
    assert "approved_patterns" in REFERENCE
    assert "rejected_or_unsafe" in REFERENCE


def test_wrapper_refs_exported() -> None:
    from workflow_dataset.external_wrappers import (
        OPENCLAW_REFERENCE,
        WORLDMONITOR_REFERENCE,
        CLIPROXY_REFERENCE,
        MIROFISH_REFERENCE,
    )
    assert OPENCLAW_REFERENCE["source_id"] == "openclaw"
    assert WORLDMONITOR_REFERENCE["source_id"] == "worldmonitor"
    assert CLIPROXY_REFERENCE["source_id"] == "cliproxyapi_plus"
    assert MIROFISH_REFERENCE["source_id"] == "mirofish"


# ----- CLI (invoke) -----


def test_cli_packs_list_empty(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["packs", "list", "--packs-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No packs installed" in result.output or "none" in result.output.lower()


def test_cli_packs_validate_valid(tmp_path: Path) -> None:
    manifest = {"pack_id": "v", "name": "V", "version": "0.1.0"}
    (tmp_path / "m.json").write_text(json.dumps(manifest), encoding="utf-8")
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["packs", "validate", str(tmp_path / "m.json")])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_cli_runtime_status(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["runtime", "status", "--packs-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Installed packs" in result.output or "packs" in result.output.lower()
