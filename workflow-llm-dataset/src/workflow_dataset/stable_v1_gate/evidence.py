"""
M50I–M50L: Aggregate final evidence for stable-v1 readiness from existing layers (read-only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.stable_v1_gate.models import FinalEvidenceBundle


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_final_evidence_bundle(repo_root: Path | str | None = None) -> FinalEvidenceBundle:
    """
    Aggregate evidence from: v1 contract (production cut + scope), release readiness,
    launch decision pack, stability decision pack, v1_ops, continuity/migration, deploy health,
    sustained health, vertical value, drift/repair. Read-only; no writes.
    """
    root = _root(repo_root)
    raw: dict[str, Any] = {}

    # Production cut (scope freeze)
    production_cut_frozen = False
    production_cut_vertical_id = ""
    try:
        from workflow_dataset.production_cut import get_active_cut
        cut = get_active_cut(root)
        if cut and getattr(cut, "chosen_vertical", None):
            production_cut_frozen = True
            cv = cut.chosen_vertical
            production_cut_vertical_id = getattr(cv, "vertical_id", "") or ""
        raw["production_cut"] = {"frozen": production_cut_frozen, "vertical_id": production_cut_vertical_id}
    except Exception as e:
        raw["production_cut"] = {"error": str(e)}

    # Release readiness
    release_readiness_status = ""
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        rr = build_release_readiness(root)
        release_readiness_status = getattr(rr, "status", "") or str(getattr(rr, "readiness", ""))
        raw["release_readiness"] = {"status": release_readiness_status}
    except Exception as e:
        release_readiness_status = "error"
        raw["release_readiness"] = {"error": str(e)}

    # Launch decision pack
    launch_recommended_decision = ""
    try:
        from workflow_dataset.production_launch.decision_pack import build_launch_decision_pack
        pack = build_launch_decision_pack(root)
        launch_recommended_decision = pack.get("recommended_decision", "")
        raw["launch_pack"] = {"recommended_decision": launch_recommended_decision, "blocker_count": len(pack.get("open_blockers", []))}
    except Exception as e:
        launch_recommended_decision = "unknown"
        raw["launch_pack"] = {"error": str(e)}

    # Stability decision pack
    stability_recommended_decision = ""
    sustained_health_summary = ""
    try:
        from workflow_dataset.stability_reviews.pack_builder import build_stability_decision_pack
        spack = build_stability_decision_pack(root)
        stability_recommended_decision = spack.recommended_decision or ""
        if spack.evidence_bundle:
            sustained_health_summary = spack.evidence_bundle.health_summary or ""
        raw["stability_pack"] = {"recommended_decision": stability_recommended_decision}
    except Exception as e:
        stability_recommended_decision = "unknown"
        raw["stability_pack"] = {"error": str(e)}

    # v1 ops posture
    v1_ops_posture_summary = ""
    try:
        from workflow_dataset.v1_ops import build_v1_support_posture
        posture = build_v1_support_posture(root)
        v1_ops_posture_summary = f"support_level={getattr(posture, 'support_level', '')} rollback_ready={getattr(posture, 'rollback_ready', False)}"
        raw["v1_ops"] = {"support_level": getattr(posture, "support_level", "")}
    except Exception as e:
        v1_ops_posture_summary = f"error: {e}"
        raw["v1_ops"] = {"error": str(e)}

    # Migration / continuity readiness
    migration_continuity_readiness = ""
    try:
        from workflow_dataset.continuity_confidence import post_restore_safe_operating_guidance
        g = post_restore_safe_operating_guidance(bundle_ref="latest", repo_root=root)
        migration_continuity_readiness = g.summary[:200] if g.summary else "continuity guidance available"
        raw["continuity"] = {"device_class": g.device_class_id, "preset": g.recommended_preset_id}
    except Exception as e:
        migration_continuity_readiness = f"error: {e}"
        raw["continuity"] = {"error": str(e)}

    # Deploy bundle health
    deploy_health_summary = ""
    try:
        from workflow_dataset.deploy_bundle.health import build_deployment_health_summary
        health = build_deployment_health_summary(repo_root=root)
        deploy_health_summary = f"validation_passed={health.validation_passed} upgrade_readiness={health.upgrade_readiness}"
        raw["deploy_health"] = {"validation_passed": health.validation_passed}
    except Exception as e:
        deploy_health_summary = f"error: {e}"
        raw["deploy_health"] = {"error": str(e)}

    # Vertical value (from ongoing summary or stability evidence)
    vertical_value_retention = ""
    try:
        from workflow_dataset.production_launch.ongoing_summary import build_ongoing_production_summary
        ongoing = build_ongoing_production_summary(root)
        vertical_value_retention = (ongoing.get("one_liner") or ongoing.get("summary") or "")[:200]
        if not vertical_value_retention:
            vertical_value_retention = "No ongoing summary."
        raw["vertical_value"] = {"one_liner": vertical_value_retention[:100]}
    except Exception as e:
        vertical_value_retention = "Unknown"
        raw["vertical_value"] = {"error": str(e)}

    # Drift / repair (from stability evidence or launch pack)
    drift_repair_summary = ""
    try:
        if raw.get("stability_pack") and "error" not in str(raw.get("stability_pack")):
            from workflow_dataset.stability_reviews.pack_builder import build_stability_decision_pack
            sp = build_stability_decision_pack(root)
            if sp.evidence_bundle:
                drift_repair_summary = sp.evidence_bundle.repair_history_summary or ""
                if sp.evidence_bundle.drift_signals:
                    drift_repair_summary = "; ".join(sp.evidence_bundle.drift_signals[:3]) + ("; " + drift_repair_summary if drift_repair_summary else "")
        if not drift_repair_summary:
            drift_repair_summary = "No drift/repair summary in window."
        raw["drift_repair"] = {"summary": drift_repair_summary[:150]}
    except Exception as e:
        drift_repair_summary = f"error: {e}"
        raw["drift_repair"] = {"error": str(e)}

    # v1 contract summary (one-liner from production cut + release readiness)
    v1_contract_parts = []
    if production_cut_frozen and production_cut_vertical_id:
        v1_contract_parts.append(f"Scope frozen for vertical {production_cut_vertical_id}.")
    else:
        v1_contract_parts.append("Production cut not frozen or no vertical locked.")
    v1_contract_parts.append(f"Release readiness: {release_readiness_status}.")
    v1_contract_summary = " ".join(v1_contract_parts)

    return FinalEvidenceBundle(
        v1_contract_summary=v1_contract_summary,
        production_cut_frozen=production_cut_frozen,
        production_cut_vertical_id=production_cut_vertical_id,
        release_readiness_status=release_readiness_status,
        launch_recommended_decision=launch_recommended_decision,
        stability_recommended_decision=stability_recommended_decision,
        v1_ops_posture_summary=v1_ops_posture_summary[:200],
        migration_continuity_readiness=migration_continuity_readiness[:200],
        deploy_health_summary=deploy_health_summary[:200],
        sustained_health_summary=sustained_health_summary[:200],
        vertical_value_retention=vertical_value_retention[:200],
        drift_repair_summary=drift_repair_summary[:200],
        raw_snapshot=raw,
    )
