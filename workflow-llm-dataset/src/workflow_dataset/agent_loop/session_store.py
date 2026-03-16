"""
Local persistence for agent sessions and responses.

Stores under data/local/agent_sessions/ and data/local/agent_responses/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.agent_loop.agent_models import AgentQuery, AgentResponse, AgentSession
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_session(session: AgentSession, base_dir: Path | str) -> Path:
    """Persist a session to base_dir/agent_sessions/<session_id>.json."""
    base = Path(base_dir)
    out_dir = base / "agent_sessions"
    ensure_dir(out_dir)
    path = out_dir / f"{session.session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(session.model_dump_json(indent=2))
    return path


def load_session(session_id: str, base_dir: Path | str) -> AgentSession | None:
    """Load a session by id."""
    path = Path(base_dir) / "agent_sessions" / f"{session_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return AgentSession.model_validate_json(f.read())


def list_sessions(base_dir: Path | str, limit: int = 50) -> list[AgentSession]:
    """List recent sessions by mtime."""
    out_dir = Path(base_dir) / "agent_sessions"
    if not out_dir.exists():
        return []
    paths = sorted(out_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in paths[:limit]:
        try:
            with open(p, "r", encoding="utf-8") as f:
                out.append(AgentSession.model_validate_json(f.read()))
        except Exception:
            continue
    return out


def save_response(response: AgentResponse, base_dir: Path | str) -> Path:
    """Append response to base_dir/agent_responses/<query_id>.json or responses.jsonl."""
    base = Path(base_dir)
    out_dir = base / "agent_responses"
    ensure_dir(out_dir)
    path = out_dir / "responses.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(response.model_dump_json() + "\n")
    return path


def load_responses_for_query(query_id: str, base_dir: Path | str) -> list[AgentResponse]:
    """Load all responses that match query_id."""
    path = Path(base_dir) / "agent_responses" / "responses.jsonl"
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = AgentResponse.model_validate_json(line)
                if r.query_id == query_id:
                    out.append(r)
            except Exception:
                continue
    return out


def save_query(query: AgentQuery, base_dir: Path | str) -> Path:
    """Append query to base_dir/agent_responses/queries.jsonl for logging."""
    base = Path(base_dir)
    out_dir = base / "agent_responses"
    ensure_dir(out_dir)
    path = out_dir / "queries.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(query.model_dump_json() + "\n")
    return path


def create_session(
    base_dir: Path | str,
    project_scope: str = "",
    domain_scope: str = "",
    use_llm: bool = False,
    use_retrieval: bool = True,
) -> AgentSession:
    """Create and persist a new agent session."""
    ts = utc_now_iso()
    session_id = stable_id("agent_session", ts, prefix="session")
    session = AgentSession(
        session_id=session_id,
        started_utc=ts,
        last_active_utc=ts,
        project_scope=project_scope,
        domain_scope=domain_scope,
        use_llm=use_llm,
        use_retrieval=use_retrieval,
    )
    save_session(session, base_dir)
    return session
