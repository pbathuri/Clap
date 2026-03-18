"""
M32I–M32L: One-click safe handoff — execute card handoff to planner/executor/workspace/review.
Explicit and previewable; respects approval/trust.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso

from workflow_dataset.action_cards.models import ActionCard, CardState, HandoffTarget
from workflow_dataset.action_cards.store import load_card, update_card_state


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def execute_handoff(
    card_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Execute the handoff for the given card. Respects trust/approval; no hidden execution.
    Returns outcome dict: ok, handoff_target, message, run_id, command_prefilled, etc.
    """
    root = _repo_root(repo_root)
    card = load_card(card_id, root)
    if not card:
        return {"ok": False, "error": "card_not_found", "card_id": card_id}
    if card.state == CardState.EXECUTED:
        return {"ok": True, "already_executed": True, "card_id": card_id, "outcome_summary": card.outcome_summary}
    if card.state == CardState.DISMISSED:
        return {"ok": False, "error": "card_dismissed", "card_id": card_id}
    if card.state == CardState.BLOCKED and card.blocked_reason:
        return {"ok": False, "error": "card_blocked", "blocked_reason": card.blocked_reason, "card_id": card_id}

    ts = utc_now_iso()
    outcome: dict[str, Any] = {"ok": True, "card_id": card_id, "handoff_target": card.handoff_target.value}

    try:
        if card.handoff_target == HandoffTarget.PREFILL_COMMAND:
            cmd = card.handoff_params.get("command", "")
            outcome["command_prefilled"] = cmd
            outcome["message"] = f"Prefill command: {cmd}. Run it manually or use agent-loop."
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

        elif card.handoff_target == HandoffTarget.COMPILE_PLAN:
            from workflow_dataset.planner.compile import compile_goal_to_plan
            goal = card.handoff_params.get("goal", "") or card.handoff_params.get("plan_ref", "")
            mode = card.handoff_params.get("mode", "simulate")
            plan = compile_goal_to_plan(goal, repo_root=root, mode=mode)
            outcome["plan_id"] = getattr(plan, "plan_id", "")
            outcome["steps_count"] = len(getattr(plan, "steps", []))
            outcome["message"] = f"Plan compiled: {outcome.get('plan_id')} ({outcome.get('steps_count')} steps). Use executor or agent-loop to run."
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

        elif card.handoff_target == HandoffTarget.QUEUE_SIMULATED:
            from workflow_dataset.supervised_loop.models import QueuedAction
            from workflow_dataset.supervised_loop.queue import enqueue_proposal
            plan_ref = card.handoff_params.get("plan_ref", "")
            plan_source = card.handoff_params.get("plan_source", "job")
            action = QueuedAction(
                action_id=card_id,
                label=card.title,
                action_type="executor_run",
                plan_ref=plan_ref,
                plan_source=plan_source,
                mode="simulate",
                why="Action card one-click handoff",
                risk_level="low",
                trust_mode="simulate",
                created_at=ts,
            )
            item = enqueue_proposal(action, cycle_id="", repo_root=root)
            outcome["queue_id"] = item.queue_id
            outcome["message"] = f"Queued for approval: {item.queue_id}. Run agent-loop approve to execute."
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

        elif card.handoff_target == HandoffTarget.APPROVAL_STUDIO:
            outcome["message"] = "Open review studio / approval queue: workflow-dataset review-studio inbox or agent-loop status"
            outcome["command_prefilled"] = "review-studio inbox"
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

        elif card.handoff_target == HandoffTarget.CREATE_DRAFT:
            sug_id = card.handoff_params.get("suggestion_id", "")
            if sug_id:
                try:
                    from workflow_dataset.settings import load_settings
                    from workflow_dataset.agent_loop.context_builder import build_context_bundle
                    settings = load_settings("configs/settings.yaml")
                    graph_path = Path(getattr(getattr(settings, "paths", None), "graph_store_path", "data/local/work_graph.sqlite"))
                    workspace_root = Path(getattr(getattr(settings.setup, "materialization_workspace_root", None), None) or "data/local/workspaces")
                    if not workspace_root.is_absolute():
                        workspace_root = root / workspace_root
                    ctx = build_context_bundle(graph_path, getattr(settings.setup, "style_signals_dir", ""), getattr(settings.setup, "parsed_artifacts_dir", ""), "")
                    from workflow_dataset.materialize.artifact_builder import materialize_from_suggestion
                    manifest, out_path = materialize_from_suggestion(ctx, workspace_root, suggestion_id=sug_id)
                    outcome["artifact_path"] = str(out_path)
                    outcome["message"] = f"Draft created: {out_path}"
                except Exception as e:
                    outcome["ok"] = False
                    outcome["error"] = str(e)
                    outcome["message"] = f"Create draft failed: {e}"
            else:
                outcome["message"] = "No suggestion_id in card; cannot create draft."
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

        elif card.handoff_target == HandoffTarget.OPEN_VIEW:
            view_id = card.handoff_params.get("view_id", "review_studio")
            outcome["message"] = f"Open view: {view_id}. (UI would navigate here.)"
            outcome["view_id"] = view_id
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

        elif card.handoff_target == HandoffTarget.EXECUTOR_RUN:
            outcome["message"] = "Executor run requires approval. Use queue_simulated or agent-loop approve."
            outcome["command_prefilled"] = "agent-loop status"
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

        else:
            outcome["message"] = f"Handoff target {card.handoff_target.value} not implemented for execute."
            update_card_state(card_id, CardState.EXECUTED, repo_root=root, updated_utc=ts, executed_at=ts, outcome_summary=outcome.get("message", ""))

    except Exception as e:
        outcome["ok"] = False
        outcome["error"] = str(e)
        update_card_state(card_id, CardState.BLOCKED, repo_root=root, updated_utc=ts, blocked_reason=str(e))

    return outcome
