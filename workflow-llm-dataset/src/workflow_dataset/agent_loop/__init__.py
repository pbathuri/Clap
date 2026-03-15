"""
Local assistive agent loop: retrieval-backed, graph-grounded, no execution.

M6: query routing, explain/next-step engines, draft refinement, session persistence.
"""

from __future__ import annotations

from workflow_dataset.agent_loop.agent_models import (
    AgentQuery,
    AgentResponse,
    AgentSession,
)
from workflow_dataset.agent_loop.query_router import route_query, QueryType
from workflow_dataset.agent_loop.context_builder import build_context_bundle
from workflow_dataset.agent_loop.response_builder import build_response
from workflow_dataset.agent_loop.session_store import (
    create_session,
    load_session,
    list_sessions,
    save_session,
    save_query,
    save_response,
    load_responses_for_query,
)

__all__ = [
    "AgentQuery",
    "AgentResponse",
    "AgentSession",
    "route_query",
    "QueryType",
    "build_context_bundle",
    "build_response",
    "create_session",
    "load_session",
    "list_sessions",
    "save_session",
    "save_query",
    "save_response",
    "load_responses_for_query",
]
