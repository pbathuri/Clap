"""M23: Tests for first real role pack (ops_reporting_pack) — install, activate, resolution, release/pilot, report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.packs import (
    install_pack,
    uninstall_pack,
    list_installed_packs,
    get_installed_manifest,
    resolve_active_capabilities,
)
from workflow_dataset.packs.pack_state import get_active_role, set_active_role, clear_active_role
from workflow_dataset.packs.pack_validator import validate_pack_manifest_and_recipes
from workflow_dataset.packs.pack_report import write_pack_report


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_MANIFEST_PATH = REPO_ROOT / "packs" / "ops_reporting_pack" / "manifest.json"


def test_real_pack_manifest_exists_and_valid() -> None:
    """Real ops_reporting_pack manifest exists and validates."""
    if not PACK_MANIFEST_PATH.exists():
        pytest.skip("packs/ops_reporting_pack/manifest.json not found (run from repo root)")
    data = json.loads(PACK_MANIFEST_PATH.read_text(encoding="utf-8"))
    valid, errs = validate_pack_manifest_and_recipes(data)
    assert valid, errs
    assert data.get("pack_id") == "ops_reporting_pack"
    assert "ops" in data.get("role_tags", [])
    assert "ops_summarize_reporting" in data.get("templates", [])


def test_install_real_pack(tmp_path: Path) -> None:
    """Install the real pack from repo path (or copy manifest into tmp)."""
    if PACK_MANIFEST_PATH.exists():
        manifest_path = PACK_MANIFEST_PATH
    else:
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps({
            "pack_id": "ops_reporting_pack",
            "name": "Ops reporting pack",
            "version": "1.0.0",
            "role_tags": ["ops"],
            "templates": ["ops_summarize_reporting", "ops_scaffold_status", "ops_next_steps"],
            "output_adapters": ["ops_handoff"],
            "recipe_steps": [{"type": "register_templates"}],
            "safety_policies": {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True},
        }), encoding="utf-8")
    ok, msg = install_pack(manifest_path, tmp_path)
    assert ok, msg
    assert "ops_reporting_pack" in msg
    installed = list_installed_packs(tmp_path)
    assert any(r.get("pack_id") == "ops_reporting_pack" for r in installed)
    uninstall_pack("ops_reporting_pack", tmp_path)
    assert not any(r.get("pack_id") == "ops_reporting_pack" for r in list_installed_packs(tmp_path))


def test_activate_deactivate(tmp_path: Path) -> None:
    """Activate sets role; deactivate clears it."""
    clear_active_role(tmp_path)
    assert get_active_role(tmp_path) == ""
    set_active_role("ops", tmp_path)
    assert get_active_role(tmp_path) == "ops"
    clear_active_role(tmp_path)
    assert get_active_role(tmp_path) == ""


def test_resolution_with_ops_pack_installed(tmp_path: Path) -> None:
    """With ops_reporting_pack installed, resolve --role ops returns its templates."""
    if not PACK_MANIFEST_PATH.exists():
        pytest.skip("packs/ops_reporting_pack/manifest.json not found")
    ok, _ = install_pack(PACK_MANIFEST_PATH, tmp_path)
    assert ok
    try:
        cap = resolve_active_capabilities(role="ops", packs_dir=str(tmp_path))
        assert len(cap.active_packs) >= 1
        assert any(m.pack_id == "ops_reporting_pack" for m in cap.active_packs)
        assert "ops_summarize_reporting" in cap.templates
        assert cap.retrieval_profile.get("top_k") == 5
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)


def test_pack_report_generation(tmp_path: Path) -> None:
    """Pack report can be written for an installed pack."""
    if not PACK_MANIFEST_PATH.exists():
        pytest.skip("packs/ops_reporting_pack/manifest.json not found")
    ok, _ = install_pack(PACK_MANIFEST_PATH, tmp_path)
    assert ok
    try:
        report_path = write_pack_report("ops_reporting_pack", packs_dir=tmp_path, output_path=tmp_path / "report.md")
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "ops_reporting_pack" in content
        assert "ops_summarize_reporting" in content or "templates" in content.lower()
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)


def test_pilot_status_includes_active_pack_ids() -> None:
    """pilot_status_dict can include active_pack_ids when scope=ops and pack installed."""
    from workflow_dataset.pilot.health import pilot_status_dict
    status = pilot_status_dict(packs_dir="data/local/packs")
    assert "active_pack_ids" in status
    assert isinstance(status["active_pack_ids"], list)


def test_cli_packs_activate_deactivate(tmp_path: Path) -> None:
    """CLI packs activate and deactivate run without error when pack installed."""
    if not PACK_MANIFEST_PATH.exists():
        pytest.skip("packs/ops_reporting_pack/manifest.json not found")
    ok, _ = install_pack(PACK_MANIFEST_PATH, tmp_path)
    assert ok
    try:
        from typer.testing import CliRunner
        from workflow_dataset.cli import app
        runner = CliRunner()
        r = runner.invoke(app, ["packs", "activate", "ops_reporting_pack", "--packs-dir", str(tmp_path)])
        assert r.exit_code == 0
        r2 = runner.invoke(app, ["packs", "deactivate", "--packs-dir", str(tmp_path)])
        assert r2.exit_code == 0
    finally:
        clear_active_role(tmp_path)
        uninstall_pack("ops_reporting_pack", tmp_path)


def test_cli_packs_report(tmp_path: Path) -> None:
    """CLI packs report generates report for installed pack."""
    if not PACK_MANIFEST_PATH.exists():
        pytest.skip("packs/ops_reporting_pack/manifest.json not found")
    ok, _ = install_pack(PACK_MANIFEST_PATH, tmp_path)
    assert ok
    try:
        from typer.testing import CliRunner
        from workflow_dataset.cli import app
        runner = CliRunner()
        r = runner.invoke(app, ["packs", "report", "ops_reporting_pack", "--packs-dir", str(tmp_path)])
        assert r.exit_code == 0
        assert (tmp_path / "ops_reporting_pack" / "report.md").exists()
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)
