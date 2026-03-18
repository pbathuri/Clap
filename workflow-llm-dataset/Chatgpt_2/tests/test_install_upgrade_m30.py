"""
M30A–M30D: Tests for install bundle, current-version, upgrade-plan, upgrade-apply, rollback, migration-report.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_product_version_roundtrip():
    from workflow_dataset.install_upgrade.models import (
        ProductVersion,
        product_version_to_dict,
        product_version_from_dict,
    )
    pv = ProductVersion(version="0.2.0", bundle_id="bundle_0_2_0", installed_at_iso="2025-01-01T00:00:00", source="pyproject")
    back = product_version_from_dict(product_version_to_dict(pv))
    assert back.version == pv.version
    assert back.bundle_id == pv.bundle_id


def test_rollback_checkpoint_roundtrip():
    from workflow_dataset.install_upgrade.models import (
        RollbackCheckpoint,
        rollback_checkpoint_to_dict,
        rollback_checkpoint_from_dict,
    )
    cp = RollbackCheckpoint(
        checkpoint_id="ck_abc",
        from_version="0.1.0",
        to_version="0.2.0",
        created_at_iso="2025-01-01T00:00:00",
        backup_paths=["/tmp/backup.json"],
    )
    back = rollback_checkpoint_from_dict(rollback_checkpoint_to_dict(cp))
    assert back.checkpoint_id == cp.checkpoint_id
    assert back.from_version == cp.from_version


def test_read_current_version_empty(tmp_path):
    from workflow_dataset.install_upgrade.version import read_current_version
    assert read_current_version(tmp_path) is None


def test_get_package_version_from_pyproject(tmp_path):
    from workflow_dataset.install_upgrade.version import get_package_version_from_pyproject
    # No pyproject
    assert get_package_version_from_pyproject(tmp_path) == "0.0.0"
    (tmp_path / "pyproject.toml").write_text('version = "0.3.0"\n', encoding="utf-8")
    assert get_package_version_from_pyproject(tmp_path) == "0.3.0"


def test_write_current_version(tmp_path):
    from workflow_dataset.install_upgrade.version import write_current_version, read_current_version
    from workflow_dataset.install_upgrade.models import ProductVersion
    pv = ProductVersion(version="0.1.0", bundle_id="b1", installed_at_iso="2025-01-01T00:00:00Z", source="test")
    path = write_current_version(pv, tmp_path)
    assert path.exists()
    back = read_current_version(tmp_path)
    assert back is not None
    assert back.version == "0.1.0"


def test_build_upgrade_plan_same_version(tmp_path):
    from workflow_dataset.install_upgrade.version import write_current_version
    from workflow_dataset.install_upgrade.models import ProductVersion
    from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan
    write_current_version(ProductVersion(version="0.1.0", source="test"), tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    plan = build_upgrade_plan(repo_root=tmp_path)
    assert plan.current_version == "0.1.0"
    assert plan.target_version == "0.1.0"
    assert not plan.can_proceed
    assert any("equals target" in r for r in plan.blocked_reasons)


def test_build_upgrade_plan_upgrade(tmp_path):
    (tmp_path / "pyproject.toml").write_text('version = "0.2.0"\n', encoding="utf-8")
    from workflow_dataset.install_upgrade.version import write_current_version
    from workflow_dataset.install_upgrade.models import ProductVersion
    from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan
    write_current_version(ProductVersion(version="0.1.0", source="test"), tmp_path)
    plan = build_upgrade_plan(repo_root=tmp_path)
    assert plan.current_version == "0.1.0"
    assert plan.target_version == "0.2.0"
    assert len(plan.migration_steps) >= 1
    assert plan.can_proceed


def test_apply_upgrade_and_rollback(tmp_path):
    (tmp_path / "pyproject.toml").write_text('version = "0.2.0"\n', encoding="utf-8")
    from workflow_dataset.install_upgrade.version import write_current_version, read_current_version
    from workflow_dataset.install_upgrade.models import ProductVersion
    from workflow_dataset.install_upgrade.apply_upgrade import apply_upgrade, perform_rollback, list_rollback_checkpoints
    write_current_version(ProductVersion(version="0.1.0", source="test"), tmp_path)
    result = apply_upgrade(target_version="0.2.0", repo_root=tmp_path)
    assert result["success"] is True
    assert result.get("checkpoint_id")
    pv = read_current_version(tmp_path)
    assert pv is not None
    assert pv.version == "0.2.0"
    roll = perform_rollback(checkpoint_id=result["checkpoint_id"], repo_root=tmp_path)
    assert roll["success"] is True
    pv2 = read_current_version(tmp_path)
    assert pv2 is not None
    assert pv2.version == "0.1.0"


def test_migration_report(tmp_path):
    from workflow_dataset.install_upgrade.reports import build_migration_report, format_migration_report
    report = build_migration_report(tmp_path)
    assert "current_version" in report
    assert "version_source" in report
    assert "rollback_checkpoints_count" in report
    text = format_migration_report(report=report)
    assert "Migration" in text or "migration" in text


def test_cmd_install_bundle(tmp_path):
    from workflow_dataset.install_upgrade.cli import cmd_install_bundle
    out = cmd_install_bundle(bundle_id="test_bundle", repo_root=tmp_path)
    assert out.get("success") is True
    assert "test_bundle" in out.get("bundle_id", "")
    assert Path(out["path"]).exists()


def test_cmd_current_version(tmp_path):
    from workflow_dataset.install_upgrade.cli import cmd_current_version
    out = cmd_current_version(repo_root=tmp_path)
    assert "version" in out
    assert "source" in out


def test_cmd_upgrade_plan(tmp_path):
    from workflow_dataset.install_upgrade.cli import cmd_upgrade_plan
    out = cmd_upgrade_plan(repo_root=tmp_path)
    assert "current_version" in out
    assert "target_version" in out
    assert "migration_steps" in out


# ----- M30D.1 Release channels + compatibility -----


def test_channels_list():
    from workflow_dataset.install_upgrade.channels import list_channels, get_channel, CHANNEL_STABLE, CHANNEL_PREVIEW, CHANNEL_INTERNAL
    channels = list_channels()
    assert len(channels) == 3
    ids = [ch.channel_id for ch in channels]
    assert CHANNEL_STABLE in ids and CHANNEL_PREVIEW in ids and CHANNEL_INTERNAL in ids
    ch = get_channel("stable")
    assert ch is not None
    assert ch.min_product_version
    assert ch.upgrade_paths_to


def test_compatibility_matrix():
    from workflow_dataset.install_upgrade.compatibility import build_compatibility_matrix, format_compatibility_matrix
    matrix = build_compatibility_matrix(product_versions=["0.1.0"], runtimes=["local"], policy_modes=["enforce"])
    assert "channels" in matrix
    assert "stable" in matrix["channels"]
    assert "rows" in matrix
    text = format_compatibility_matrix(matrix)
    assert "Compatibility" in text
    assert "stable" in text


def test_check_upgrade_path_internal_to_stable():
    from workflow_dataset.install_upgrade.compatibility import check_upgrade_path
    result = check_upgrade_path("0.1.0", "0.2.0", "internal", "stable")
    assert result.get("unsafe_reasons")
    assert any("internal" in r.lower() and "stable" in r.lower() for r in result["unsafe_reasons"])
    assert result.get("allowed") is False


def test_check_upgrade_path_preview_to_stable():
    from workflow_dataset.install_upgrade.compatibility import check_upgrade_path
    result = check_upgrade_path("0.1.0", "0.2.0", "preview", "stable")
    assert result.get("allowed") is True
    assert any("Preview" in w or "preview" in w for w in result.get("warnings", []))


def test_upgrade_plan_includes_channel_warnings(tmp_path):
    from workflow_dataset.install_upgrade.version import write_current_version
    from workflow_dataset.install_upgrade.models import ProductVersion
    from workflow_dataset.install_upgrade.upgrade_plan import build_upgrade_plan
    write_current_version(ProductVersion(version="0.1.0", source="test"), tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "0.2.0"\n', encoding="utf-8")
    plan = build_upgrade_plan(repo_root=tmp_path, current_channel="internal", target_channel="stable")
    assert plan.current_channel == "internal"
    assert plan.target_channel == "stable"
    assert any("internal" in r.lower() or "stable" in r.lower() for r in plan.blocked_reasons)
    assert plan.can_proceed is False


def test_cmd_channels_list():
    from workflow_dataset.install_upgrade.cli import cmd_channels_list
    out = cmd_channels_list()
    assert len(out) == 3
    assert any(c["channel_id"] == "stable" for c in out)


def test_cmd_compatibility_matrix(tmp_path):
    from workflow_dataset.install_upgrade.cli import cmd_compatibility_matrix
    mat = cmd_compatibility_matrix(repo_root=tmp_path, json_out=True)
    assert isinstance(mat, dict)
    assert "channels" in mat
    text = cmd_compatibility_matrix(repo_root=tmp_path, json_out=False)
    assert isinstance(text, str)
    assert "Compatibility" in text
