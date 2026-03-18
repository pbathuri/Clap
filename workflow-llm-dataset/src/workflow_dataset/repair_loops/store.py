"""
M46E–M46H: Persist repair loops and plans to data/local/repair_loops/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.repair_loops.models import (
    RepairLoop,
    RepairLoopStatus,
    BoundedRepairPlan,
    RepairResult,
    PostRepairVerification,
    RollbackOnFailedRepair,
    RequiredReviewGate,
    ReviewGateKind,
    RepairGuidance,
    RepairGuidanceKind,
    MaintenanceAction,
    Precondition,
    RepairTargetSubsystem,
)


REPAIR_LOOPS_DIR = "data/local/repair_loops"
LOOPS_SUBDIR = "loops"
PLANS_SUBDIR = "plans"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_repair_loops_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / REPAIR_LOOPS_DIR


def get_loops_dir(repo_root: Path | str | None = None) -> Path:
    return get_repair_loops_dir(repo_root) / LOOPS_SUBDIR


def get_plans_dir(repo_root: Path | str | None = None) -> Path:
    return get_repair_loops_dir(repo_root) / PLANS_SUBDIR


def _dict_to_precondition(d: dict[str, Any]) -> Precondition:
    return Precondition(
        precondition_id=d.get("precondition_id", ""),
        description=d.get("description", ""),
        check_command=d.get("check_command", ""),
        required=d.get("required", True),
    )


def _dict_to_subsystem(d: dict[str, Any]) -> RepairTargetSubsystem:
    return RepairTargetSubsystem(
        subsystem_id=d.get("subsystem_id", ""),
        name=d.get("name", ""),
        description=d.get("description", ""),
    )


def _dict_to_action(d: dict[str, Any]) -> MaintenanceAction:
    return MaintenanceAction(
        action_id=d.get("action_id", ""),
        name=d.get("name", ""),
        description=d.get("description", ""),
        run_command=d.get("run_command", ""),
        run_command_args=d.get("run_command_args", []),
        preconditions=[_dict_to_precondition(p) for p in d.get("preconditions", [])],
        rollback_command=d.get("rollback_command", ""),
        rollback_args=d.get("rollback_args", []),
    )


def _dict_to_review_gate(d: dict[str, Any] | None) -> RequiredReviewGate | None:
    if not d:
        return None
    kind = d.get("kind", "operator_approval")
    try:
        kind_enum = ReviewGateKind(kind)
    except ValueError:
        kind_enum = ReviewGateKind.operator_approval
    return RequiredReviewGate(
        gate_id=d.get("gate_id", ""),
        kind=kind_enum,
        description=d.get("description", ""),
        passed=d.get("passed", False),
        passed_at=d.get("passed_at", ""),
        passed_by=d.get("passed_by", ""),
    )


def _dict_to_plan(d: dict[str, Any]) -> BoundedRepairPlan:
    target = d.get("target_subsystem")
    return BoundedRepairPlan(
        plan_id=d.get("plan_id", ""),
        name=d.get("name", ""),
        description=d.get("description", ""),
        target_subsystem=_dict_to_subsystem(target) if target else None,
        actions=[_dict_to_action(a) for a in d.get("actions", [])],
        preconditions=[_dict_to_precondition(p) for p in d.get("preconditions", [])],
        required_review_gate=_dict_to_review_gate(d.get("required_review_gate")),
        verification_command=d.get("verification_command", ""),
        verification_args=d.get("verification_args", []),
        rollback_on_failed_repair=d.get("rollback_on_failed_repair", True),
        escalation_target=d.get("escalation_target", ""),
    )


def _dict_to_result(d: dict[str, Any]) -> RepairResult:
    return RepairResult(
        result_id=d.get("result_id", ""),
        plan_id=d.get("plan_id", ""),
        action_id=d.get("action_id", ""),
        success=d.get("success", False),
        details=d.get("details", ""),
        output=d.get("output", ""),
        duration_seconds=float(d.get("duration_seconds", 0)),
        timestamp=d.get("timestamp", ""),
    )


def _dict_to_verification(d: dict[str, Any] | None) -> PostRepairVerification | None:
    if not d:
        return None
    return PostRepairVerification(
        verification_id=d.get("verification_id", ""),
        plan_id=d.get("plan_id", ""),
        passed=d.get("passed", False),
        details=d.get("details", ""),
        run_command=d.get("run_command", ""),
        run_output=d.get("run_output", ""),
        timestamp=d.get("timestamp", ""),
    )


def _dict_to_guidance(d: dict[str, Any] | None) -> RepairGuidance | None:
    if not d:
        return None
    try:
        kind = RepairGuidanceKind(d.get("kind", "do_now"))
    except ValueError:
        kind = RepairGuidanceKind.do_now
    return RepairGuidance(
        kind=kind,
        reason=d.get("reason", ""),
        suggested_schedule=d.get("suggested_schedule", ""),
    )


def _dict_to_rollback(d: dict[str, Any] | None) -> RollbackOnFailedRepair | None:
    if not d:
        return None
    return RollbackOnFailedRepair(
        rollback_id=d.get("rollback_id", ""),
        plan_id=d.get("plan_id", ""),
        actions_rolled_back=d.get("actions_rolled_back", []),
        success=d.get("success", False),
        details=d.get("details", ""),
        timestamp=d.get("timestamp", ""),
    )


def save_repair_loop(loop: RepairLoop, repo_root: Path | str | None = None) -> Path:
    root = _repo_root(repo_root)
    loops_dir = get_loops_dir(root)
    loops_dir.mkdir(parents=True, exist_ok=True)
    path = loops_dir / f"{loop.repair_loop_id}.json"
    path.write_text(json.dumps(loop.to_dict(), indent=2), encoding="utf-8")
    return path


def load_repair_loop(repair_loop_id: str, repo_root: Path | str | None = None) -> RepairLoop | None:
    root = _repo_root(repo_root)
    path = get_loops_dir(root) / f"{repair_loop_id}.json"
    if not path.exists():
        return None
    d = json.loads(path.read_text(encoding="utf-8"))
    plan = _dict_to_plan(d.get("plan", {}))
    try:
        status = RepairLoopStatus(d.get("status", "proposed"))
    except ValueError:
        status = RepairLoopStatus.proposed
    loop = RepairLoop(
        repair_loop_id=d.get("repair_loop_id", repair_loop_id),
        plan=plan,
        status=status,
        source_signal_id=d.get("source_signal_id", ""),
        source_signal_type=d.get("source_signal_type", ""),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
        approved_at=d.get("approved_at", ""),
        approved_by=d.get("approved_by", ""),
        executed_at=d.get("executed_at", ""),
        results=[_dict_to_result(r) for r in d.get("results", [])],
        verification=_dict_to_verification(d.get("verification")),
        rollback=_dict_to_rollback(d.get("rollback")),
        escalation_reason=d.get("escalation_reason", ""),
        maintenance_profile_id=d.get("maintenance_profile_id", ""),
        repair_bundle_id=d.get("repair_bundle_id", ""),
        operator_guidance=_dict_to_guidance(d.get("operator_guidance")),
    )
    return loop


def list_repair_loops(
    limit: int = 50,
    status_filter: str | None = None,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    root = _repo_root(repo_root)
    loops_dir = get_loops_dir(root)
    if not loops_dir.exists():
        return []
    files = sorted(loops_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict[str, Any]] = []
    for p in files[:limit]:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if status_filter and d.get("status") != status_filter:
                continue
            out.append({
                "repair_loop_id": d.get("repair_loop_id", p.stem),
                "plan_id": d.get("plan_id"),
                "plan_name": d.get("plan_name"),
                "status": d.get("status"),
                "source_signal_id": d.get("source_signal_id"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            })
        except Exception:
            continue
    return out
