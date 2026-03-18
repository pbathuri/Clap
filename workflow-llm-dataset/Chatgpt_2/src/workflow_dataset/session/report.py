"""
M24J–M24M: Session report formatting — status, board, artifact hub.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.session.models import Session
from workflow_dataset.session.board import SessionBoard
from workflow_dataset.session.artifacts import list_artifacts, get_notes, get_handoff


def format_session_status(session: Session | None) -> str:
    """Format current session status for console."""
    if not session:
        return "No active session. Run 'workflow-dataset session start --pack <value_pack_id>' to start."
    lines = [
        f"Session: {session.session_id}",
        f"  Pack: {session.value_pack_id}",
        f"  Starter kit: {session.starter_kit_id or '—'}",
        f"  State: {session.state}",
        f"  Created: {session.created_at}",
        f"  Updated: {session.updated_at}",
    ]
    if session.recommended_next_actions:
        lines.append("  Recommended next: " + "; ".join(session.recommended_next_actions[:3]))
    return "\n".join(lines)


def format_session_board(board: SessionBoard) -> str:
    """Format session task board for console."""
    lines = ["=== Session task board ===", ""]
    lines.append("[Active tasks]")
    for t in board.active_tasks[:20]:
        lines.append(f"  {t.get('kind', '')}  {t.get('label', t.get('id', ''))}")
    if not board.active_tasks:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Queued (paused / awaiting approval)]")
    for q in board.queued[:15]:
        lines.append(f"  {q.get('macro_id', '')}  run_id={q.get('run_id', '')}  status={q.get('status', '')}")
    if not board.queued:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Blocked]")
    for b in board.blocked[:15]:
        lines.append(f"  {b.get('kind', '')}  {b.get('id', b.get('macro_id', ''))}  {b.get('reason', '')}")
    if not board.blocked:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Ready]")
    for r in board.ready[:20]:
        lines.append(f"  {r.get('kind', '')}  {r.get('id', '')}")
    if not board.ready:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Recently completed]")
    for c in board.completed[:10]:
        lines.append(f"  {c.get('kind', '')}  {c.get('run_id', '')}  {c.get('job_pack_id', c.get('macro_id', ''))}  {c.get('outcome', '')}")
    if not board.completed:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Artifacts this session]")
    for a in board.artifacts_produced[:20]:
        lines.append(f"  {a.get('path_or_label', '')}  ({a.get('kind', '')})")
    if not board.artifacts_produced:
        lines.append("  (none)")
    return "\n".join(lines)


def format_session_artifact_hub(
    session_id: str,
    repo_root: Any = None,
    include_notes: bool = True,
    include_handoff: bool = True,
) -> str:
    """Format session artifact hub summary: artifacts, notes, handoff."""
    artifacts = list_artifacts(session_id, repo_root, limit=50)
    notes = get_notes(session_id, repo_root, limit=30) if include_notes else []
    handoff = get_handoff(session_id, repo_root) if include_handoff else {}

    lines = [f"=== Session artifacts ({session_id}) ===", ""]
    lines.append("[Artifacts]")
    for a in artifacts:
        lines.append(f"  {a.get('path_or_label', '')}  kind={a.get('kind', '')}")
    if not artifacts:
        lines.append("  (none)")
    if include_notes:
        lines.append("")
        lines.append("[Notes]")
        for n in notes:
            lines.append(f"  {n[:80]}{'...' if len(n) > 80 else ''}")
        if not notes:
            lines.append("  (none)")
    if include_handoff and (handoff.get("summary") or handoff.get("next_steps")):
        lines.append("")
        lines.append("[Handoff]")
        lines.append(f"  Summary: {handoff.get('summary', '')}")
        for s in handoff.get("next_steps", []):
            lines.append(f"  Next: {s}")
    return "\n".join(lines)
