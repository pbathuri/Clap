"""
M50E–M50H: v1 operational discipline — support posture, maintenance pack, incident/recovery/escalation, rollback readiness, runbook.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.v1_ops.models import (
    V1SupportPosture,
    MaintenanceRhythm,
    ReviewCadenceRef,
    IncidentClass,
    RecoveryPath,
    EscalationPath,
    RollbackReadiness,
    SupportOwnershipNote,
    StableV1MaintenancePack,
    MaintenanceObligation,
    MaintenanceObligationsSummary,
    SupportReviewSummary,
)
from workflow_dataset.v1_ops.posture import build_v1_support_posture
from workflow_dataset.v1_ops.store import save_maintenance_pack, load_maintenance_pack, list_maintenance_packs
from workflow_dataset.v1_ops.maintenance_obligations import build_maintenance_obligations_summary
from workflow_dataset.v1_ops.support_review_summary import build_support_review_summary
from workflow_dataset.v1_ops.maintenance_pack import build_stable_v1_maintenance_pack
from workflow_dataset.v1_ops.runbook import (
    get_daily_review_items,
    get_weekly_review_items,
    get_when_v1_degrades,
    get_safe_repair_actions,
    get_requires_rollback,
    get_requires_pause_or_narrow,
)
from workflow_dataset.v1_ops.mission_control import get_v1_ops_state


def test_v1_support_posture_model():
    p = V1SupportPosture(
        posture_id="v1_stable",
        support_level="sustained",
        support_paths=["release_readiness", "stability_reviews"],
        rollback_ready=True,
        as_of_utc="2025-01-01T12:00:00Z",
    )
    d = p.to_dict()
    assert d["posture_id"] == "v1_stable"
    assert d["support_level"] == "sustained"
    assert d["rollback_ready"] is True
    assert len(d["support_paths"]) == 2
    p2 = V1SupportPosture.from_dict(d)
    assert p2.posture_id == p.posture_id
    assert p2.rollback_ready == p.rollback_ready


def test_maintenance_rhythm_model():
    r = MaintenanceRhythm(
        rhythm_id="stable_v1",
        label="Stable v1 daily/weekly",
        daily_tasks=["supportability", "repair-loops list"],
        weekly_tasks=["stability-reviews generate"],
    )
    d = r.to_dict()
    assert d["rhythm_id"] == "stable_v1"
    assert len(d["daily_tasks"]) == 2
    assert len(d["weekly_tasks"]) == 1


def test_recovery_path_model():
    r = RecoveryPath(
        path_id="broken_pack_state",
        incident_class="broken_pack_state",
        label="Broken pack",
        steps=["packs list", "packs suspend"],
        first_step_command="workflow-dataset packs list",
    )
    d = r.to_dict()
    assert d["path_id"] == "broken_pack_state"
    assert len(d["steps"]) == 2
    assert RecoveryPath.from_dict(d).path_id == r.path_id


def test_rollback_readiness_model():
    rr = RollbackReadiness(ready=True, prior_stable_ref="ck_abc", reason="Checkpoint exists", recommended_action="Run release rollback if needed")
    d = rr.to_dict()
    assert d["ready"] is True
    assert d["prior_stable_ref"] == "ck_abc"
    assert RollbackReadiness.from_dict(d).ready == rr.ready


def test_stable_v1_maintenance_pack_roundtrip():
    posture = V1SupportPosture(posture_id="p1", support_level="sustained")
    rhythm = MaintenanceRhythm(rhythm_id="r1", label="Daily/weekly")
    rc = ReviewCadenceRef(cadence_id="rolling_stability", next_due_iso="2025-01-08T00:00:00Z")
    pack = StableV1MaintenancePack(
        pack_id="pack1",
        label="Stable v1 pack",
        support_posture=posture,
        maintenance_rhythm=rhythm,
        review_cadence_ref=rc,
        recovery_paths=[RecoveryPath(path_id="rp1", incident_class="other", label="Recovery", steps=[])],
        escalation_paths=[EscalationPath(path_id="e1", trigger_condition="guidance=rollback", escalate_to="Operator")],
        rollback_readiness=RollbackReadiness(ready=False),
        ownership_notes=[SupportOwnershipNote(role_or_owner="Operator", responsibility="Daily support")],
        generated_at_utc="2025-01-01T12:00:00Z",
    )
    d = pack.to_dict()
    assert d["pack_id"] == "pack1"
    assert d["support_posture"]["support_level"] == "sustained"
    assert len(d["recovery_paths"]) == 1
    assert len(d["escalation_paths"]) == 1
    pack2 = StableV1MaintenancePack.from_dict(d)
    assert pack2.pack_id == pack.pack_id
    assert pack2.support_posture and pack2.support_posture.support_level == "sustained"


def test_build_v1_support_posture(tmp_path: Path):
    posture = build_v1_support_posture(tmp_path)
    assert posture.posture_id == "v1_stable_posture"
    assert posture.support_level in ("sustained", "maintenance")
    assert isinstance(posture.support_paths, list)
    assert isinstance(posture.rollback_ready, bool)


def test_build_stable_v1_maintenance_pack(tmp_path: Path):
    pack = build_stable_v1_maintenance_pack(tmp_path)
    assert pack.pack_id == "stable_v1_maintenance_pack"
    assert pack.support_posture is not None
    assert pack.maintenance_rhythm is not None
    assert len(pack.recovery_paths) >= 1
    assert len(pack.escalation_paths) >= 1
    assert pack.rollback_readiness is not None
    assert len(pack.ownership_notes) >= 1


def test_runbook_daily_weekly():
    daily = get_daily_review_items()
    weekly = get_weekly_review_items()
    assert len(daily) >= 1
    assert len(weekly) >= 1
    assert any("supportability" in s.lower() for s in daily)
    assert any("stability" in s.lower() for s in weekly)


def test_runbook_when_degrades_safe_rollback_pause():
    deg = get_when_v1_degrades()
    safe = get_safe_repair_actions()
    rollback = get_requires_rollback()
    pause = get_requires_pause_or_narrow()
    assert len(deg) >= 1
    assert len(safe) >= 1
    assert len(rollback) >= 1
    assert len(pause) >= 1
    assert any("rollback" in r.lower() for r in rollback)
    assert any("pause" in p.lower() or "narrow" in p.lower() for p in pause)


def test_get_v1_ops_state(tmp_path: Path):
    state = get_v1_ops_state(tmp_path)
    assert "current_support_posture" in state
    assert "overdue_maintenance_or_review" in state
    assert "top_unresolved_v1_risk" in state
    assert "recommended_stable_v1_support_action" in state
    assert "rollback_readiness_posture" in state
    assert isinstance(state["current_support_posture"], dict)
    assert isinstance(state["rollback_readiness_posture"], dict)


def test_incident_class_enum():
    assert IncidentClass.DEGRADATION.value == "degradation"
    assert IncidentClass.OTHER.value == "other"
    assert IncidentClass.FAILED_UPGRADE.value == "failed_upgrade"


# ----- M50H.1 Stable-v1 maintenance packs + support review summaries -----


def test_maintenance_obligation_model():
    o = MaintenanceObligation(category="daily", label="Daily task", frequency="daily", command_or_description="Run supportability")
    d = o.to_dict()
    assert d["category"] == "daily"
    assert d["frequency"] == "daily"
    assert MaintenanceObligation.from_dict(d).category == o.category


def test_maintenance_obligations_summary_model():
    s = MaintenanceObligationsSummary(
        summary_id="obligations_1",
        obligations=[MaintenanceObligation(category="daily", label="X", frequency="daily", command_or_description="Y")],
        generated_at_utc="2025-01-01T12:00:00Z",
        summary_text="To preserve stable-v1...",
    )
    d = s.to_dict()
    assert d["summary_id"] == "obligations_1"
    assert len(d["obligations"]) == 1
    assert MaintenanceObligationsSummary.from_dict(d).summary_id == s.summary_id


def test_support_review_summary_model():
    s = SupportReviewSummary(
        review_id="review_1",
        period_label="Stable v1 support review",
        items_reviewed=["Supportability"],
        overdue_items=[],
        next_actions=["Run stability-reviews generate"],
        ownership_roles=["Operator: daily support"],
        summary_text="Support review: 1.",
        generated_at_utc="2025-01-01T12:00:00Z",
    )
    d = s.to_dict()
    assert d["review_id"] == "review_1"
    assert len(d["items_reviewed"]) == 1
    assert SupportReviewSummary.from_dict(d).review_id == s.review_id


def test_save_load_list_maintenance_pack(tmp_path: Path):
    pack = build_stable_v1_maintenance_pack(tmp_path)
    path = save_maintenance_pack(pack, tmp_path)
    assert path.exists()
    assert path.suffix == ".json"
    loaded = load_maintenance_pack("latest", tmp_path)
    assert loaded is not None
    assert loaded.pack_id == pack.pack_id
    packs = list_maintenance_packs(tmp_path)
    assert len(packs) >= 1
    assert packs[0].get("pack_id") == pack.pack_id


def test_build_maintenance_obligations_summary(tmp_path: Path):
    summary = build_maintenance_obligations_summary(tmp_path)
    assert summary.summary_id == "stable_v1_maintenance_obligations"
    assert len(summary.obligations) >= 1
    assert summary.summary_text
    categories = {o.category for o in summary.obligations}
    assert "daily" in categories or "weekly" in categories or "review_cadence" in categories


def test_build_support_review_summary(tmp_path: Path):
    summary = build_support_review_summary(tmp_path)
    assert summary.review_id.startswith("v1_support_review_")
    assert summary.period_label == "Stable v1 support review"
    assert isinstance(summary.items_reviewed, list)
    assert isinstance(summary.next_actions, list)
    assert isinstance(summary.ownership_roles, list)
