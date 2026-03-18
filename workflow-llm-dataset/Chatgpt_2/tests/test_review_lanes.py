"""M22C: Role-based review lanes — local, file-based. Tests for lane metadata, views, and assign."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.release.review_state import (
    LANES,
    load_review_state,
    save_review_state,
    set_workspace_lane,
)
from workflow_dataset.release.lane_views import (
    get_lane_summary,
    list_packages_in_lane,
    list_workspaces_in_lane,
    set_package_lane,
)


def test_lanes_constant():
    assert "operator" in LANES
    assert "reviewer" in LANES
    assert "stakeholder-prep" in LANES
    assert "approver" in LANES
    assert len(LANES) == 4


def test_save_review_state_persists_lane(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    save_review_state(
        ws,
        {},
        lane="reviewer",
        repo_root=tmp_path,
    )
    state = load_review_state(ws, repo_root=tmp_path)
    assert state.get("lane") == "reviewer"


def test_set_workspace_lane(tmp_path):
    ws = tmp_path / "data/local/workspaces/weekly_status/run1"
    ws.mkdir(parents=True)
    (tmp_path / "data/local/review/weekly_status").mkdir(parents=True)
    save_review_state(ws, {}, repo_root=tmp_path)
    set_workspace_lane(ws, "approver", repo_root=tmp_path)
    state = load_review_state(ws, repo_root=tmp_path)
    assert state.get("lane") == "approver"


def test_set_workspace_lane_invalid_raises(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    save_review_state(ws, {}, repo_root=tmp_path)
    with pytest.raises(ValueError, match="lane must be one of"):
        set_workspace_lane(ws, "invalid", repo_root=tmp_path)


def test_get_lane_summary_structure(tmp_path):
    summary = get_lane_summary(repo_root=tmp_path)
    for lane in LANES:
        assert lane in summary
        assert "count_workspaces" in summary[lane]
        assert "count_packages" in summary[lane]
        assert "pending_count" in summary[lane]


def test_list_workspaces_in_lane_empty(tmp_path):
    out = list_workspaces_in_lane("operator", repo_root=tmp_path)
    assert out == []


def test_list_packages_in_lane_empty(tmp_path):
    out = list_packages_in_lane("approver", repo_root=tmp_path)
    assert out == []


def test_set_package_lane(tmp_path):
    pkg = tmp_path / "data/local/packages/2025-03-15_abc"
    pkg.mkdir(parents=True)
    manifest = {
        "package_type": "ops_reporting",
        "source_workspace": "/some/ws",
        "workflow": "weekly_status",
        "artifact_count": 1,
    }
    (pkg / "package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    set_package_lane(pkg, "stakeholder-prep", repo_root=tmp_path)
    data = json.loads((pkg / "package_manifest.json").read_text(encoding="utf-8"))
    assert data.get("lane") == "stakeholder-prep"


def test_set_package_lane_invalid_raises(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "package_manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="lane must be one of"):
        set_package_lane(pkg, "invalid", repo_root=tmp_path)
