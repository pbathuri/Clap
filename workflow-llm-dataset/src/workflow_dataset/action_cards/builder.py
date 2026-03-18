"""
M32I–M32L: Suggestion-to-card — build action cards from personal suggestions, graph review, style, copilot.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.action_cards.models import (
    ActionCard,
    CardState,
    HandoffTarget,
    TrustRequirement,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def suggestion_to_cards(
    repo_root: Path | str | None = None,
    from_personal_suggestions: bool = True,
    from_assist_suggestions: bool = True,
    from_graph_routines: bool = True,
    from_style_suggestions: bool = False,
    from_copilot: bool = True,
    limit: int = 30,
) -> list[ActionCard]:
    """
    Build action cards from accepted/pending suggestions and recommendations.
    Pane 2 (assist) suggestions become cards when from_assist_suggestions=True.
    Does not persist; caller saves via store.save_card.
    """
    root = _repo_root(repo_root)
    cards: list[ActionCard] = []
    ts = utc_now_iso()

    if from_assist_suggestions:
        try:
            from workflow_dataset.assist_engine.store import list_suggestions as list_assist_suggestions
            pending = list_assist_suggestions(repo_root=root, status_filter="pending", limit=limit)
            for s in pending:
                card_id = stable_id("card", "assist", s.suggestion_id, prefix="card_")
                title = s.title or f"Assist: {s.suggestion_type}"
                cards.append(ActionCard(
                    card_id=card_id,
                    title=title[:80],
                    description=(s.reason.title if s.reason else "")[:200],
                    source_type="assist_suggestion",
                    source_ref=s.suggestion_id,
                    handoff_target=HandoffTarget.PREFILL_COMMAND,
                    handoff_params={"command": f"assist accept --id {s.suggestion_id}", "hint": "Accept assist suggestion"},
                    trust_requirement=TrustRequirement.NONE,
                    reversible=True,
                    state=CardState.PENDING,
                    created_utc=ts,
                    updated_utc=ts,
                ))
        except Exception:
            pass

    if from_personal_suggestions:
        try:
            from workflow_dataset.personal.graph_store import init_store, list_suggestions
            from workflow_dataset.settings import load_settings
            path = getattr(getattr(load_settings("configs/settings.yaml"), "paths", None), "graph_store_path", None)
            if path:
                path = root / path if not Path(path).is_absolute() else Path(path)
            else:
                path = root / "data/local/work_graph.sqlite"
            if path.exists():
                init_store(path)
                import sqlite3
                conn = sqlite3.connect(str(path))
                try:
                    rows = list_suggestions(conn, status_filter="pending", limit=limit)
                    for r in rows:
                        sug_id = r.get("suggestion_id", "")
                        sug_type = r.get("suggestion_type", "")
                        title = r.get("title", "") or f"Suggestion: {sug_type}"
                        card_id = stable_id("card", "sug", sug_id, prefix="card_")
                        handoff = HandoffTarget.PREFILL_COMMAND
                        params: dict[str, Any] = {"suggestion_id": sug_id}
                        if sug_type == "focus_project":
                            params["command"] = "projects set-current"
                            params["hint"] = "Set current project from suggestion"
                        elif sug_type == "operations_workflow":
                            params["command"] = "planner compile"
                            params["hint"] = "Compile plan for workflow"
                        else:
                            params["command"] = "assist suggest"
                        cards.append(ActionCard(
                            card_id=card_id,
                            title=title,
                            description=r.get("description", "")[:200],
                            source_type="personal_suggestion",
                            source_ref=sug_id,
                            handoff_target=handoff,
                            handoff_params=params,
                            trust_requirement=TrustRequirement.NONE,
                            reversible=True,
                            state=CardState.PENDING,
                            created_utc=ts,
                            updated_utc=ts,
                        ))
                finally:
                    conn.close()
        except Exception:
            pass

    if from_graph_routines:
        try:
            from workflow_dataset.personal.graph_reports import list_recent_routines
            from workflow_dataset.settings import load_settings
            path = getattr(getattr(load_settings("configs/settings.yaml"), "paths", None), "graph_store_path", None)
            if path:
                path = root / path if not Path(path).is_absolute() else Path(path)
            else:
                path = root / "data/local/work_graph.sqlite"
            routines = list_recent_routines(repo_root=root, graph_path=path, limit=10)
            for r in routines[:5]:
                node_id = r.get("node_id", "")
                label = r.get("label", "")
                card_id = stable_id("card", "routine", node_id, prefix="card_")
                cards.append(ActionCard(
                    card_id=card_id,
                    title=f"Routine: {label[:60]}",
                    description="Use this routine in planner or queue simulated run.",
                    source_type="graph_routine",
                    source_ref=node_id,
                    handoff_target=HandoffTarget.COMPILE_PLAN,
                    handoff_params={"plan_ref": node_id, "goal": label[:80], "mode": "simulate"},
                    trust_requirement=TrustRequirement.SIMULATE_ONLY,
                    reversible=True,
                    state=CardState.PENDING,
                    created_utc=ts,
                    updated_utc=ts,
                ))
        except Exception:
            pass

    if from_copilot:
        try:
            from workflow_dataset.copilot.recommendations import recommend_jobs
            recs = recommend_jobs(root, limit=5)
            for rec in recs:
                job_id = rec.get("job_pack_id", "")
                if not job_id:
                    continue
                card_id = stable_id("card", "copilot", job_id, prefix="card_")
                label = rec.get("label", "") or f"Run job {job_id}"
                blocking = rec.get("blocking_issues")
                cards.append(ActionCard(
                    card_id=card_id,
                    title=label[:80],
                    description="Recommended job; queue for approval or simulate.",
                    source_type="copilot",
                    source_ref=job_id,
                    handoff_target=HandoffTarget.QUEUE_SIMULATED,
                    handoff_params={"plan_ref": job_id, "plan_source": "job", "mode": "simulate"},
                    trust_requirement=TrustRequirement.APPROVAL_REQUIRED if blocking else TrustRequirement.SIMULATE_ONLY,
                    reversible=True,
                    state=CardState.BLOCKED if blocking else CardState.PENDING,
                    blocked_reason="; ".join(blocking[:2]) if blocking else "",
                    created_utc=ts,
                    updated_utc=ts,
                ))
        except Exception:
            pass

    if from_style_suggestions:
        try:
            from workflow_dataset.personal.style_suggestion_engine import load_style_aware_suggestions
            from workflow_dataset.settings import load_settings
            sug_dir = getattr(load_settings("configs/settings.yaml").setup, "suggestions_dir", "data/local/suggestions")
            sug_path = root / sug_dir if not Path(sug_dir).is_absolute() else Path(sug_dir)
            if sug_path.exists():
                style_sugs = load_style_aware_suggestions(sug_path)
                for s in style_sugs[:5]:
                    sid = getattr(s, "suggestion_id", "") or stable_id("style_sug", getattr(s, "suggestion_type", ""), prefix="sug")
                    card_id = stable_id("card", "style", sid, prefix="card_")
                    title = getattr(s, "title", "") or getattr(s, "suggestion_type", "style")
                    cards.append(ActionCard(
                        card_id=card_id,
                        title=str(title)[:80],
                        description=getattr(s, "rationale", "")[:200],
                        source_type="style_suggestion",
                        source_ref=sid,
                        handoff_target=HandoffTarget.CREATE_DRAFT,
                        handoff_params={"suggestion_id": sid},
                        trust_requirement=TrustRequirement.NONE,
                        reversible=True,
                        state=CardState.PENDING,
                        created_utc=ts,
                        updated_utc=ts,
                    ))
        except Exception:
            pass

    return cards[:limit]
