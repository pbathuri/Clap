"""
M24J–M24M: Session launch, resume, close — start from provisioned pack, resume prior, close/archive.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from workflow_dataset.session.models import Session
from workflow_dataset.session.storage import (
    save_session,
    load_session,
    load_current_session_id,
    set_current_session_id,
    archive_session,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def start_session(
    pack_id: str | None = None,
    repo_root: Path | str | None = None,
    profile_ref: str = "",
    template_id: str | None = None,
) -> tuple[Session | None, list[str]]:
    """
    Start a new session for the given value pack (and optional template).
    If template_id is given, overlay template's board state and next_step_chain.
    If pack_id is omitted but template_id is given, use template's value_pack_id.
    Validates pack exists and is provisioned. Returns (session, errors).
    """
    root = _repo_root(repo_root)
    errors: list[str] = []

    # Resolve pack_id from template if needed
    effective_pack_id = pack_id
    template = None
    if template_id:
        try:
            from workflow_dataset.session.templates import get_session_template
            template = get_session_template(template_id)
            if template and not effective_pack_id:
                effective_pack_id = template.value_pack_id
        except Exception as e:
            errors.append(f"Template: {e}")
    if not effective_pack_id:
        errors.append("No pack_id and no template with value_pack_id. Use --pack or --template.")
        return None, errors

    pack = None
    try:
        from workflow_dataset.value_packs.registry import get_value_pack
        pack = get_value_pack(effective_pack_id)
    except Exception as e:
        errors.append(str(e))
    if not pack:
        errors.append(f"Value pack not found: {effective_pack_id}")
        return None, errors

    try:
        from workflow_dataset.provisioning.domain_environment import domain_environment_summary
        env = domain_environment_summary(effective_pack_id, root)
        if env.get("error"):
            errors.append(env.get("error", "Unknown error"))
            return None, errors
        if not env.get("provisioned"):
            errors.append(f"Pack {effective_pack_id} is not provisioned. Run: workflow-dataset packs provision --id {effective_pack_id}")
            return None, errors
    except Exception as e:
        errors.append(f"Provisioning check: {e}")
        return None, errors

    # Base session from pack
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    now = utc_now_iso()
    job_ids = list(pack.recommended_job_ids or [])[:30]
    routine_ids = list(pack.recommended_routine_ids or [])[:30]
    macro_ids = list(pack.recommended_macro_ids or [])[:30]
    active_tasks: list[str] = []
    recommended_next_actions: list[str] = []

    # Overlay template if given
    if template:
        if template.job_ids:
            job_ids = list(template.job_ids)[:30]
        if template.routine_ids:
            routine_ids = list(template.routine_ids)[:30]
        if template.macro_ids:
            macro_ids = list(template.macro_ids)[:30]
        if template.active_tasks:
            active_tasks = list(template.active_tasks)
        if template.next_step_chain:
            recommended_next_actions = list(template.next_step_chain)[:15]

    session = Session(
        session_id=session_id,
        value_pack_id=effective_pack_id,
        starter_kit_id=getattr(pack, "starter_kit_id", "") or "",
        profile_ref=profile_ref,
        active_tasks=active_tasks,
        active_job_ids=job_ids,
        active_routine_ids=routine_ids,
        active_macro_ids=macro_ids,
        recommended_next_actions=recommended_next_actions,
        state="open",
        created_at=now,
        updated_at=now,
    )
    save_session(session, root)
    set_current_session_id(session_id, root)
    return session, []


def resume_session(session_id: str, repo_root: Path | str | None = None) -> tuple[Session | None, list[str]]:
    """
    Resume a prior session by id. Loads and sets as current if state is open.
    Returns (session, errors). If session not found or closed/archived, errors non-empty.
    """
    root = _repo_root(repo_root)
    session = load_session(session_id, root)
    if not session:
        return None, [f"Session not found: {session_id}"]
    if session.state != "open":
        return None, [f"Session is {session.state}; cannot resume. Use session list to see open sessions."]
    set_current_session_id(session_id, root)
    return session, []


def close_session(session_id: str, repo_root: Path | str | None = None) -> tuple[bool, list[str]]:
    """
    Close and archive the session. If it was current, clear current.
    Returns (success, errors).
    """
    root = _repo_root(repo_root)
    session = load_session(session_id, root)
    if not session:
        return False, [f"Session not found: {session_id}"]
    session.state = "closed"
    session.closed_at = utc_now_iso()
    save_session(session, root)
    archive_session(session_id, root)
    return True, []


def get_current_session(repo_root: Path | str | None = None) -> Session | None:
    """Return the current open session if any."""
    current_id = load_current_session_id(repo_root)
    if not current_id:
        return None
    session = load_session(current_id, repo_root)
    if session and session.state == "open":
        return session
    return None
