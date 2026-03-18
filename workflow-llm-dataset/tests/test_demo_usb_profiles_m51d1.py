"""M51D.1: Demo bundle profiles + playbooks."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.demo_usb.models import BootstrapReadinessReport, DemoCapabilityLevel
from workflow_dataset.demo_usb.profiles_playbooks import (
    load_demo_bundle_profiles,
    load_usb_playbooks,
    suggest_profile_for_readiness,
    suggest_playbook_for_readiness,
    format_playbook_text,
    format_operator_safe_launch_guide,
    DemoBundleProfile,
    UsbLaunchPlaybook,
)


@pytest.fixture
def repo_root() -> Path:
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        pytest.skip("repo root")


def test_load_profiles(repo_root: Path) -> None:
    profiles = load_demo_bundle_profiles(repo_root)
    assert "full_demo" in profiles
    assert "lightweight_demo" in profiles
    assert "degraded_laptop_demo" in profiles
    assert profiles["full_demo"].label


def test_load_playbooks(repo_root: Path) -> None:
    pbs = load_usb_playbooks(repo_root)
    assert "usb_fresh_laptop" in pbs
    assert len(pbs["usb_fresh_laptop"].steps) >= 3


def test_suggest_profile_and_playbook() -> None:
    full = BootstrapReadinessReport(capability_level=DemoCapabilityLevel.FULL)
    assert suggest_profile_for_readiness(full) == "full_demo"
    assert suggest_playbook_for_readiness(full) == "usb_fresh_laptop"
    deg = BootstrapReadinessReport(capability_level=DemoCapabilityLevel.DEGRADED)
    assert suggest_profile_for_readiness(deg) == "lightweight_demo"
    assert suggest_playbook_for_readiness(deg) == "usb_lightweight"
    blk = BootstrapReadinessReport(capability_level=DemoCapabilityLevel.BLOCKED)
    assert suggest_profile_for_readiness(blk) == "degraded_laptop_demo"
    assert suggest_playbook_for_readiness(blk) == "usb_degraded_honest"


def test_format_playbook(repo_root: Path) -> None:
    pbs = load_usb_playbooks(repo_root)
    pb = pbs["usb_fresh_laptop"]
    text = format_playbook_text(pb)
    assert "unfamiliar laptop" in text.lower() or "USB" in text
    assert "1." in text


def test_safe_launch_guide_contains_local() -> None:
    g = format_operator_safe_launch_guide()
    assert "local" in g.lower()
    assert "venv" in g.lower() or "python" in g.lower()


def test_profile_model_to_dict() -> None:
    p = DemoBundleProfile(profile_id="x", label="L")
    assert p.to_dict()["profile_id"] == "x"


def test_playbook_model_to_dict() -> None:
    pb = UsbLaunchPlaybook(playbook_id="p", title="T", steps=[{"action": "a", "detail": "d"}])
    d = pb.to_dict()
    assert d["steps"][0]["action"] == "a"
