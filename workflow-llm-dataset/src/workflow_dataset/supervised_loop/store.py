"""
M27E–M27H: Persist agent cycle, approval queue, and queue history.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.supervised_loop.models import (
    AgentCycle,
    ApprovalQueueItem,
    QueuedAction,
    ExecutionHandoff,
    OperatorPolicy,
)

LOOP_DIR = "data/local/supervised_loop"
CURRENT_CYCLE_FILE = "current_cycle.json"
QUEUE_FILE = "approval_queue.json"
QUEUE_HISTORY_FILE = "queue_history.json"
HANDOFFS_FILE = "handoffs.json"
OPERATOR_POLICY_FILE = "operator_policy.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_loop_dir(repo_root: Path | str | None = None) -> Path:
    root = _repo_root(repo_root)
    return root / LOOP_DIR


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_cycle(cycle: AgentCycle, repo_root: Path | str | None = None) -> Path:
    d = get_loop_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / CURRENT_CYCLE_FILE
    path.write_text(json.dumps(cycle.to_dict(), indent=2), encoding="utf-8")
    return path


def load_cycle(repo_root: Path | str | None = None) -> AgentCycle | None:
    path = get_loop_dir(repo_root) / CURRENT_CYCLE_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AgentCycle.from_dict(data)
    except Exception:
        return None


def load_queue(repo_root: Path | str | None = None) -> list[ApprovalQueueItem]:
    path = get_loop_dir(repo_root) / QUEUE_FILE
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = []
        for x in raw.get("items", []):
            act = x.get("action", {})
            action = QueuedAction(
                action_id=act.get("action_id", ""),
                label=act.get("label", ""),
                action_type=act.get("action_type", ""),
                plan_ref=act.get("plan_ref", ""),
                plan_source=act.get("plan_source", ""),
                mode=act.get("mode", ""),
                step_index=act.get("step_index"),
                why=act.get("why", ""),
                risk_level=act.get("risk_level", ""),
                trust_mode=act.get("trust_mode", ""),
                created_at=act.get("created_at", ""),
            )
            items.append(ApprovalQueueItem(
                queue_id=x.get("queue_id", ""),
                action=action,
                status=x.get("status", "pending"),
                decided_at=x.get("decided_at", ""),
                decision_note=x.get("decision_note", ""),
                cycle_id=x.get("cycle_id", ""),
                defer_reason=x.get("defer_reason", ""),
                revisit_after=x.get("revisit_after", ""),
            ))
        return items
    except Exception:
        return []


def save_queue(items: list[ApprovalQueueItem], repo_root: Path | str | None = None) -> Path:
    d = get_loop_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / QUEUE_FILE
    raw = {
        "items": [
            {
                "queue_id": q.queue_id,
                "action": {
                    "action_id": q.action.action_id,
                    "label": q.action.label,
                    "action_type": q.action.action_type,
                    "plan_ref": q.action.plan_ref,
                    "plan_source": q.action.plan_source,
                    "mode": q.action.mode,
                    "step_index": q.action.step_index,
                    "why": q.action.why,
                    "risk_level": q.action.risk_level,
                    "trust_mode": q.action.trust_mode,
                    "created_at": q.action.created_at,
                },
                "status": q.status,
                "decided_at": q.decided_at,
                "decision_note": q.decision_note,
                "cycle_id": q.cycle_id,
                "defer_reason": q.defer_reason,
                "revisit_after": q.revisit_after,
            }
            for q in items
        ],
    }
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return path


def append_queue_history(
    queue_id: str,
    status: str,
    decided_at: str,
    note: str = "",
    repo_root: Path | str | None = None,
) -> None:
    path = get_loop_dir(repo_root) / QUEUE_HISTORY_FILE
    history: list[dict[str, Any]] = []
    if path.exists():
        try:
            history = json.loads(path.read_text(encoding="utf-8")).get("history", [])
        except Exception:
            pass
    history.append({
        "queue_id": queue_id,
        "status": status,
        "decided_at": decided_at,
        "note": note,
    })
    _ensure_dir(path)
    path.write_text(json.dumps({"history": history[-500:]}, indent=2), encoding="utf-8")


def load_handoffs(repo_root: Path | str | None = None) -> list[ExecutionHandoff]:
    path = get_loop_dir(repo_root) / HANDOFFS_FILE
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        out = []
        for h in raw.get("handoffs", []):
            out.append(ExecutionHandoff(
                handoff_id=h.get("handoff_id", ""),
                queue_id=h.get("queue_id", ""),
                cycle_id=h.get("cycle_id", ""),
                action_type=h.get("action_type", ""),
                plan_ref=h.get("plan_ref", ""),
                plan_source=h.get("plan_source", ""),
                mode=h.get("mode", ""),
                run_id=h.get("run_id", ""),
                status=h.get("status", ""),
                outcome_summary=h.get("outcome_summary", ""),
                artifact_paths=list(h.get("artifact_paths", [])),
                error=h.get("error", ""),
                started_at=h.get("started_at", ""),
                ended_at=h.get("ended_at", ""),
            ))
        return out
    except Exception:
        return []


def append_handoff(handoff: ExecutionHandoff, repo_root: Path | str | None = None) -> Path:
    path = get_loop_dir(repo_root) / HANDOFFS_FILE
    handoffs = load_handoffs(repo_root)
    handoffs.append(handoff)
    _ensure_dir(path)
    raw = {
        "handoffs": [
            {
                "handoff_id": h.handoff_id,
                "queue_id": h.queue_id,
                "cycle_id": h.cycle_id,
                "action_type": h.action_type,
                "plan_ref": h.plan_ref,
                "plan_source": h.plan_source,
                "mode": h.mode,
                "run_id": h.run_id,
                "status": h.status,
                "outcome_summary": h.outcome_summary,
                "artifact_paths": list(h.artifact_paths),
                "error": h.error,
                "started_at": h.started_at,
                "ended_at": h.ended_at,
            }
            for h in handoffs[-200:]
        ],
    }
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return path


def load_operator_policy(repo_root: Path | str | None = None) -> OperatorPolicy:
    """Load operator policy from data/local/supervised_loop/operator_policy.json. Returns default if missing."""
    path = get_loop_dir(repo_root) / OPERATOR_POLICY_FILE
    if not path.exists():
        return OperatorPolicy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return OperatorPolicy.from_dict(data)
    except Exception:
        return OperatorPolicy()


def save_operator_policy(policy: OperatorPolicy, repo_root: Path | str | None = None) -> Path:
    """Save operator policy to data/local/supervised_loop/operator_policy.json."""
    d = get_loop_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / OPERATOR_POLICY_FILE
    path.write_text(json.dumps(policy.to_dict(), indent=2), encoding="utf-8")
    return path
