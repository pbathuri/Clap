"""
M51E: USB demo bootstrap — models, readiness, bundle root, blocked path.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from workflow_dataset.demo_usb.bundle_root import resolve_demo_bundle_root, _is_valid_demo_bundle
from workflow_dataset.demo_usb.models import (
    DemoCapabilityLevel,
    BlockedStartupReason,
    DemoBootstrapRun,
    BootstrapReadinessReport,
)
from workflow_dataset.demo_usb.bootstrap import (
    build_readiness_report,
    build_usb_demo_bundle,
    run_demo_bootstrap,
)


def _minimal_bundle(tmp: Path) -> Path:
    (tmp / "configs").mkdir(parents=True)
    (tmp / "configs" / "settings.yaml").write_text("demo_usb: true\n", encoding="utf-8")
    (tmp / "src" / "workflow_dataset").mkdir(parents=True)
    (tmp / "src" / "workflow_dataset" / "__init__.py").write_text("", encoding="utf-8")
    return tmp.resolve()


def test_is_valid_demo_bundle(tmp_path: Path) -> None:
    b = _minimal_bundle(tmp_path)
    assert _is_valid_demo_bundle(b)
    assert not _is_valid_demo_bundle(tmp_path / "empty")


def test_resolve_demo_bundle_root_explicit(tmp_path: Path) -> None:
    b = _minimal_bundle(tmp_path)
    assert resolve_demo_bundle_root(b).resolve() == b.resolve()


def test_build_usb_demo_bundle(tmp_path: Path) -> None:
    b = _minimal_bundle(tmp_path)
    ub = build_usb_demo_bundle(b, "explicit")
    assert ub.has_settings_yaml
    assert ub.bundle_writable


def test_readiness_full_or_degraded(tmp_path: Path) -> None:
    b = _minimal_bundle(tmp_path)
    rep = build_readiness_report(b, explicit_bundle=b)
    assert rep.capability_level in (DemoCapabilityLevel.FULL, DemoCapabilityLevel.DEGRADED)
    assert rep.blocked_reason == BlockedStartupReason.NONE or rep.ready_for_onboarding
    if rep.capability_level == DemoCapabilityLevel.DEGRADED:
        assert rep.degraded_explanation


def test_readiness_blocked_no_settings(tmp_path: Path) -> None:
    b = tmp_path
    (b / "src" / "workflow_dataset").mkdir(parents=True)
    (b / "configs").mkdir(parents=True)
    rep = build_readiness_report(b.resolve(), explicit_bundle=b)
    assert rep.capability_level == DemoCapabilityLevel.BLOCKED
    assert rep.blocked_reason == BlockedStartupReason.SETTINGS_MISSING


@pytest.mark.skipif(sys.platform == "win32", reason="chmod read-only differs on Windows")
def test_readiness_blocked_readonly_bundle(tmp_path: Path) -> None:
    b = _minimal_bundle(tmp_path)
    data_local = b / "data" / "local"
    data_local.mkdir(parents=True)
    try:
        os.chmod(data_local, 0o555)
        os.chmod(b / "data", 0o555)
        rep = build_readiness_report(b, explicit_bundle=b)
        assert rep.capability_level == DemoCapabilityLevel.BLOCKED
        assert rep.blocked_reason == BlockedStartupReason.BUNDLE_READ_ONLY_NO_FALLBACK
    finally:
        try:
            os.chmod(b / "data", 0o755)
            os.chmod(data_local, 0o755)
        except OSError:
            pass


def test_bootstrap_run_records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    b = _minimal_bundle(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        "workflow_dataset.demo_usb.bootstrap.default_host_workspace",
        lambda root: home / "demo_ws",
    )

    run = run_demo_bootstrap(bundle_root=b, explicit_bundle=b, skip_first_run=True)
    assert run.run_id.startswith("demo_usb_")
    assert run.readiness is not None
    assert (home / "demo_ws" / ".workflow-demo" / "last_bootstrap.json").is_file()


def test_demo_bootstrap_run_model_to_dict() -> None:
    run = DemoBootstrapRun(run_id="x", started_at_utc="t")
    d = run.to_dict()
    assert d["run_id"] == "x"


def test_bootstrap_readiness_report_to_dict() -> None:
    rep = BootstrapReadinessReport(capability_level=DemoCapabilityLevel.BLOCKED)
    assert rep.to_dict()["capability_level"] == "blocked"
