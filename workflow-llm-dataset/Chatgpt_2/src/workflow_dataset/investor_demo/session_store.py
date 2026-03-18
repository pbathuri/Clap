"""
M51I–M51L: Investor demo session persistence (local JSON).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.investor_demo.models import (
    InvestorDemoSession,
    DemoNarrativeStage,
    DemoCompletionState,
    DegradedDemoWarning,
    STAGE_ORDER,
)
from workflow_dataset.investor_demo.narrative import guidance_for_stage, next_stage
from workflow_dataset.investor_demo.degraded import collect_degraded_warnings


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def session_path(repo_root: Path | str | None = None) -> Path:
    return _root(repo_root) / "data" / "local" / "investor_demo" / "session.json"


def start_demo_session(
    repo_root: Path | str | None = None,
    vertical_id: str = "",
    role_demo_pack_id: str = "founder_operator",
) -> InvestorDemoSession:
    root = _root(repo_root)
    now = datetime.now(timezone.utc).isoformat()[:19] + "Z"
    vid = vertical_id
    if not vid:
        try:
            from workflow_dataset.vertical_excellence.path_resolver import get_chosen_vertical_id
            vid = get_chosen_vertical_id(root) or ""
        except Exception:
            vid = ""
    degraded = collect_degraded_warnings(root)
    session = InvestorDemoSession(
        session_id=str(uuid.uuid4())[:12],
        started_at_iso=now,
        current_stage=DemoNarrativeStage.STARTUP_READINESS.value,
        vertical_id=vid,
        role_demo_pack_id=role_demo_pack_id,
        presenter_guidance=guidance_for_stage(DemoNarrativeStage.STARTUP_READINESS),
        degraded_warnings=degraded,
    )
    _save_session(root, session)
    return session


def load_demo_session(repo_root: Path | str | None = None) -> InvestorDemoSession | None:
    path = session_path(repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _session_from_dict(data)
    except Exception:
        return None


def advance_demo_stage(repo_root: Path | str | None = None) -> InvestorDemoSession | None:
    sess = load_demo_session(repo_root)
    if not sess:
        return None
    nxt = next_stage(sess.current_stage)
    root = _root(repo_root)
    if nxt is None:
        sess.completion = DemoCompletionState(
            completed=True,
            completed_at_iso=datetime.now(timezone.utc).isoformat()[:19] + "Z",
            stages_completed=[s.value for s in STAGE_ORDER],
            closing_summary="Demo narrative complete. Run: workflow-dataset investor-demo mission-control",
        )
        _save_session(root, sess)
        return sess
    sess.current_stage = nxt
    sess.presenter_guidance = guidance_for_stage(nxt)
    sess.degraded_warnings = collect_degraded_warnings(root)
    _save_session(root, sess)
    return sess


def _save_session(root: Path, session: InvestorDemoSession) -> None:
    path = session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")


def _session_from_dict(data: dict[str, Any]) -> InvestorDemoSession:
    gw = [DegradedDemoWarning(**w) for w in data.get("degraded_warnings", [])]
    comp = data.get("completion") or {}
    completion = DemoCompletionState(
        completed=bool(comp.get("completed")),
        completed_at_iso=comp.get("completed_at_iso", ""),
        stages_completed=list(comp.get("stages_completed", [])),
        closing_summary=comp.get("closing_summary", ""),
    )
    pg = data.get("presenter_guidance")
    from workflow_dataset.investor_demo.models import PresenterGuidanceNote
    presenter = None
    if pg:
        presenter = PresenterGuidanceNote(
            stage_id=pg.get("stage_id", ""),
            headline=pg.get("headline", ""),
            talking_points=list(pg.get("talking_points", [])),
            caution=pg.get("caution", ""),
        )
    return InvestorDemoSession(
        session_id=data.get("session_id", ""),
        started_at_iso=data.get("started_at_iso", ""),
        current_stage=data.get("current_stage", DemoNarrativeStage.STARTUP_READINESS.value),
        vertical_id=data.get("vertical_id", ""),
        role_demo_pack_id=data.get("role_demo_pack_id", "founder_operator"),
        presenter_guidance=presenter,
        degraded_warnings=gw,
        completion=completion,
        presenter_mode_enabled=bool(data.get("presenter_mode_enabled", False)),
    )
