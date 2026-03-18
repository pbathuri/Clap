"""
M30I–M30L: Release readiness and supportability — models, readiness, pack, supportability, triage, handoff.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.release_readiness.models import (
    ReleaseReadinessStatus,
    ReleaseBlocker,
    ReleaseWarning,
    SupportedWorkflowScope,
    KnownLimitation,
    SupportabilityStatus,
    READINESS_READY,
    READINESS_BLOCKED,
    READINESS_DEGRADED,
    GUIDANCE_SAFE_TO_CONTINUE,
    GUIDANCE_NEEDS_OPERATOR,
    GUIDANCE_NEEDS_ROLLBACK,
)
from workflow_dataset.release_readiness.readiness import build_release_readiness, format_release_readiness_report
from workflow_dataset.release_readiness.pack import build_user_release_pack, format_user_release_pack
from workflow_dataset.release_readiness.supportability import (
    build_reproducible_state_summary,
    build_supportability_report,
    build_triage_output,
    TRIAGE_TEMPLATE,
)
from workflow_dataset.release_readiness.handoff_pack import build_handoff_pack, get_handoff_pack_dir, load_latest_handoff_pack


def test_release_blocker_roundtrip():
    b = ReleaseBlocker(id="b1", summary="Env failed", source="env_health", remediation_hint="Run health.")
    d = b.to_dict()
    assert d["id"] == "b1"
    assert "Env" in d["summary"]


def test_release_readiness_status_to_dict():
    r = ReleaseReadinessStatus(
        status=READINESS_BLOCKED,
        blockers=[ReleaseBlocker("b1", "Block", source="rollout")],
        warnings=[],
        supportability=SupportabilityStatus(confidence="low", guidance=GUIDANCE_NEEDS_OPERATOR, recommended_next_support_action="Fix blocks"),
    )
    d = r.to_dict()
    assert d["status"] == READINESS_BLOCKED
    assert len(d["blockers"]) == 1
    assert d["supportability"]["guidance"] == GUIDANCE_NEEDS_OPERATOR


def test_build_release_readiness_returns_status(tmp_path):
    r = build_release_readiness(tmp_path)
    assert r.status in (READINESS_READY, READINESS_BLOCKED, READINESS_DEGRADED)
    assert r.supportability.guidance in (GUIDANCE_SAFE_TO_CONTINUE, GUIDANCE_NEEDS_OPERATOR, GUIDANCE_NEEDS_ROLLBACK)
    assert r.supported_scope is not None
    assert len(r.known_limitations) >= 1


def test_format_release_readiness_report(tmp_path):
    text = format_release_readiness_report(tmp_path)
    assert "Release readiness" in text
    assert "Status" in text
    assert "Blockers" in text
    assert "Supportability" in text


def test_build_user_release_pack(tmp_path):
    p = build_user_release_pack(tmp_path)
    assert "install_profile" in p
    assert "first_run_guide" in p
    assert "quickstart_path" in p
    assert "supported_workflows" in p
    assert "known_limitations" in p
    assert "trust_explanation" in p
    assert "recovery_refs" in p
    assert "diagnostics_refs" in p
    assert p["readiness_status"] in (READINESS_READY, READINESS_BLOCKED, READINESS_DEGRADED)


def test_format_user_release_pack(tmp_path):
    text = format_user_release_pack(tmp_path)
    assert "User release pack" in text
    assert "Supported workflows" in text
    assert "Trust" in text or "trust" in text


def test_build_reproducible_state_summary(tmp_path):
    s = build_reproducible_state_summary(tmp_path)
    assert "release_readiness_status" in s
    assert "guidance" in s


def test_build_supportability_report(tmp_path):
    r = build_supportability_report(tmp_path)
    assert "release_readiness_status" in r
    assert "recommended_next_support_action" in r
    assert "guidance" in r
    assert "triage_template" in r


def test_build_triage_output(tmp_path):
    t = build_triage_output(tmp_path, latest_only=True)
    assert "reproducible_state_summary" in t
    assert "release_readiness_status" in t
    assert "guidance" in t
    assert "recommended_next_support_action" in t


def test_triage_template_has_fields():
    assert "fields" in TRIAGE_TEMPLATE
    assert "guidance" in TRIAGE_TEMPLATE["fields"]
    assert "recommended_next_support_action" in TRIAGE_TEMPLATE["fields"]


def test_build_handoff_pack_no_output_dir(tmp_path):
    out = build_handoff_pack(tmp_path, output_dir=None)
    assert "generated_at" in out
    assert "artifacts" in out
    assert "summary_md" in out
    assert "readiness_status" in out


def test_build_handoff_pack_with_output_dir(tmp_path):
    out_dir = tmp_path / "handoff_out"
    out = build_handoff_pack(tmp_path, output_dir=out_dir)
    assert out["output_path"] == str(out_dir)
    assert (out_dir / "handoff_pack.json").exists()
    assert (out_dir / "handoff_summary.md").exists()


def test_get_handoff_pack_dir(tmp_path):
    d = get_handoff_pack_dir(tmp_path)
    assert "release_readiness" in str(d)


def test_load_latest_handoff_pack_empty(tmp_path):
    assert load_latest_handoff_pack(tmp_path) is None


def test_load_latest_handoff_pack_after_build(tmp_path):
    build_handoff_pack(tmp_path, output_dir=get_handoff_pack_dir(tmp_path))
    loaded = load_latest_handoff_pack(tmp_path)
    assert loaded is not None
    assert "readiness_status" in loaded or "generated_at" in loaded
