"""M24: Tests for multi-pack coexistence, priority, conflicts, role/context switch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.packs import list_installed_packs, get_installed_manifest, resolve_active_capabilities
from workflow_dataset.packs.pack_activation import (
    load_activation_state,
    save_activation_state,
    get_primary_pack_id,
    set_primary_pack,
    clear_primary_pack,
    get_pinned,
    pin_pack,
    unpin_pack,
    get_suspended_pack_ids,
    suspend_pack,
    resume_pack,
    get_current_context,
    set_current_role,
    set_current_context,
    clear_context,
)
from workflow_dataset.packs.pack_state import get_active_role, set_active_role, clear_active_role
from workflow_dataset.packs.pack_conflicts import detect_conflicts, PackConflict, ConflictClass
from workflow_dataset.packs.pack_resolution_graph import resolve_with_priority, ResolutionExplanation
from workflow_dataset.packs.pack_installer import install_pack, uninstall_pack
from workflow_dataset.packs.pack_reporting import write_multi_pack_status_report, write_conflict_report


@pytest.fixture
def ops_manifest_path(tmp_path: Path) -> Path:
    p = tmp_path / "ops.json"
    p.write_text(json.dumps({
        "pack_id": "ops_reporting_pack",
        "name": "Ops pack",
        "version": "1.0.0",
        "role_tags": ["ops"],
        "workflow_tags": ["reporting"],
        "templates": ["ops_summarize_reporting", "ops_scaffold_status", "ops_next_steps"],
        "output_adapters": ["ops_handoff"],
        "retrieval_profile": {"top_k": 5},
        "recipe_steps": [{"type": "register_templates"}],
        "safety_policies": {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True},
    }), encoding="utf-8")
    return p


@pytest.fixture
def founder_manifest_path(tmp_path: Path) -> Path:
    p = tmp_path / "founder.json"
    p.write_text(json.dumps({
        "pack_id": "founder_ops_pack",
        "name": "Founder pack",
        "version": "0.1.0",
        "role_tags": ["founder"],
        "workflow_tags": ["project_scaffold"],
        "templates": ["founder_project_scaffold", "founder_cadence"],
        "output_adapters": ["ops_handoff", "design_package"],
        "retrieval_profile": {"top_k": 3},
        "recipe_steps": [{"type": "register_templates"}],
        "safety_policies": {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True},
    }), encoding="utf-8")
    return p


def test_activation_state_primary(tmp_path: Path) -> None:
    clear_primary_pack(tmp_path)
    assert get_primary_pack_id(tmp_path) == ""
    set_primary_pack("ops_reporting_pack", tmp_path)
    assert get_primary_pack_id(tmp_path) == "ops_reporting_pack"
    clear_primary_pack(tmp_path)
    assert get_primary_pack_id(tmp_path) == ""


def test_activation_state_pin_unpin(tmp_path: Path) -> None:
    assert get_pinned(tmp_path) == {}
    pin_pack("ops_reporting_pack", "session", tmp_path)
    assert get_pinned(tmp_path).get("session") == "ops_reporting_pack"
    unpin_pack(pack_id="ops_reporting_pack", scope=None, packs_dir=tmp_path)
    assert get_pinned(tmp_path) == {}


def test_activation_state_suspend_resume(tmp_path: Path) -> None:
    assert get_suspended_pack_ids(tmp_path) == []
    suspend_pack("founder_ops_pack", tmp_path)
    assert "founder_ops_pack" in get_suspended_pack_ids(tmp_path)
    resume_pack("founder_ops_pack", tmp_path)
    assert "founder_ops_pack" not in get_suspended_pack_ids(tmp_path)


def test_activation_state_context(tmp_path: Path) -> None:
    clear_context(tmp_path)
    assert get_current_context(tmp_path).get("current_role") == ""
    set_current_role("ops", tmp_path)
    assert get_current_context(tmp_path).get("current_role") == "ops"
    set_current_context(workflow="reporting", task="summarize", packs_dir=tmp_path)
    ctx = get_current_context(tmp_path)
    assert ctx.get("current_workflow") == "reporting"
    assert ctx.get("current_task") == "summarize"
    clear_context(tmp_path)
    assert get_current_context(tmp_path).get("current_role") == ""


def test_resolve_with_priority_primary(tmp_path: Path, ops_manifest_path: Path, founder_manifest_path: Path) -> None:
    install_pack(ops_manifest_path, tmp_path)
    install_pack(founder_manifest_path, tmp_path)
    try:
        set_primary_pack("ops_reporting_pack", tmp_path)
        set_current_role("ops", tmp_path)
        cap, expl = resolve_with_priority(role="ops", packs_dir=str(tmp_path))
        assert expl.primary_pack_id == "ops_reporting_pack"
        assert any(m.pack_id == "ops_reporting_pack" for m in cap.active_packs)
        assert "ops_summarize_reporting" in cap.templates
        assert cap.retrieval_profile.get("top_k") == 5
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)
        uninstall_pack("founder_ops_pack", tmp_path)
        clear_primary_pack(tmp_path)


def test_resolve_with_priority_role_filters(tmp_path: Path, ops_manifest_path: Path, founder_manifest_path: Path) -> None:
    install_pack(ops_manifest_path, tmp_path)
    install_pack(founder_manifest_path, tmp_path)
    try:
        cap_ops = resolve_active_capabilities(role="ops", packs_dir=str(tmp_path))
        cap_founder = resolve_active_capabilities(role="founder", packs_dir=str(tmp_path))
        assert any(m.pack_id == "ops_reporting_pack" for m in cap_ops.active_packs)
        assert any(m.pack_id == "founder_ops_pack" for m in cap_founder.active_packs)
        assert "founder_project_scaffold" in cap_founder.templates
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)
        uninstall_pack("founder_ops_pack", tmp_path)


def test_conflict_detection(tmp_path: Path, ops_manifest_path: Path, founder_manifest_path: Path) -> None:
    install_pack(ops_manifest_path, tmp_path)
    install_pack(founder_manifest_path, tmp_path)
    try:
        installed = list_installed_packs(tmp_path)
        manifests = [get_installed_manifest(r["pack_id"], tmp_path) for r in installed]
        manifests = [m for m in manifests if m]
        conflicts = detect_conflicts(manifests)
        assert isinstance(conflicts, list)
        for c in conflicts:
            assert c.conflict_class in ConflictClass
            assert c.capability
            assert c.pack_ids
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)
        uninstall_pack("founder_ops_pack", tmp_path)


def test_multi_pack_report(tmp_path: Path, ops_manifest_path: Path) -> None:
    install_pack(ops_manifest_path, tmp_path)
    try:
        path = write_multi_pack_status_report(packs_dir=tmp_path, output_path=tmp_path / "status.md")
        assert path.exists()
        assert "Installed packs" in path.read_text()
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)


def test_conflict_report(tmp_path: Path, ops_manifest_path: Path, founder_manifest_path: Path) -> None:
    install_pack(ops_manifest_path, tmp_path)
    install_pack(founder_manifest_path, tmp_path)
    try:
        path = write_conflict_report(packs_dir=tmp_path, output_path=tmp_path / "conflicts.md")
        assert path.exists()
        assert "conflict" in path.read_text().lower()
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)
        uninstall_pack("founder_ops_pack", tmp_path)


def test_cli_packs_list_all(tmp_path: Path, ops_manifest_path: Path) -> None:
    install_pack(ops_manifest_path, tmp_path)
    try:
        set_primary_pack("ops_reporting_pack", tmp_path)
        assert get_primary_pack_id(tmp_path) == "ops_reporting_pack"
        from typer.testing import CliRunner
        from workflow_dataset.cli import app
        runner = CliRunner()
        r = runner.invoke(app, ["packs", "list", "-a", "--packs-dir", str(tmp_path)])
        assert r.exit_code == 0
        assert "ops_reporting_pack" in r.output
    finally:
        clear_primary_pack(tmp_path)
        uninstall_pack("ops_reporting_pack", tmp_path)


def test_cli_runtime_switch_role(tmp_path: Path) -> None:
    from workflow_dataset.packs.pack_activation import set_current_role
    from workflow_dataset.packs.pack_state import set_active_role
    set_current_role("founder", tmp_path)
    set_active_role("founder", tmp_path)
    from workflow_dataset.packs.pack_activation import get_current_context
    assert get_current_context(tmp_path).get("current_role") == "founder"
    from workflow_dataset.packs.pack_activation import clear_context
    from workflow_dataset.packs.pack_state import clear_active_role
    clear_context(tmp_path)
    clear_active_role(tmp_path)


def test_cli_packs_conflicts(tmp_path: Path, ops_manifest_path: Path, founder_manifest_path: Path) -> None:
    install_pack(ops_manifest_path, tmp_path)
    install_pack(founder_manifest_path, tmp_path)
    try:
        from typer.testing import CliRunner
        from workflow_dataset.cli import app
        runner = CliRunner()
        r = runner.invoke(app, ["packs", "conflicts", "--packs-dir", str(tmp_path)])
        assert r.exit_code == 0
    finally:
        uninstall_pack("ops_reporting_pack", tmp_path)
        uninstall_pack("founder_ops_pack", tmp_path)
