"""
Deterministic query routing for the assistive agent loop.

Classifies user questions into types for explain_engine, next_step_engine, draft_refiner.
Rule-based; no LLM required for classification.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any


class QueryType(str, Enum):
    """Supported query types for the agent loop."""

    EXPLAIN_PROJECT = "explain_project"
    EXPLAIN_STYLE = "explain_style"
    EXPLAIN_SUGGESTION = "explain_suggestion"
    EXPLAIN_DRAFT = "explain_draft"
    SUGGEST_NEXT_STEP = "suggest_next_step"
    REFINE_DRAFT_STRUCTURE = "refine_draft_structure"
    SUMMARIZE_PROJECT_PATTERNS = "summarize_project_patterns"
    SUMMARIZE_WORKFLOW_PATTERNS = "summarize_workflow_patterns"
    LIST_ACTIVE_PROJECTS = "list_active_projects"
    CREATIVE_SCAFFOLD_HELP = "creative_scaffold_help"
    FINANCE_OPS_SCAFFOLD_HELP = "finance_ops_scaffold_help"
    FOUNDER_ADMIN_SCAFFOLD_HELP = "founder_admin_scaffold_help"
    GENERAL_CHAT = "general_chat"


# Patterns: (regex or substring, QueryType)
_ROUTE_PATTERNS: list[tuple[Any, QueryType]] = [
    # Explain project
    (re.compile(r"\bwhat\s+is\s+(this\s+)?project\b", re.I), QueryType.EXPLAIN_PROJECT),
    (re.compile(r"\bexplain\s+(this\s+)?project\b", re.I), QueryType.EXPLAIN_PROJECT),
    (re.compile(r"\bdescribe\s+(this\s+)?project\b", re.I), QueryType.EXPLAIN_PROJECT),
    (re.compile(r"\bproject\s+overview\b", re.I), QueryType.EXPLAIN_PROJECT),
    # Explain style
    (re.compile(r"\bwhat\s+style\s+(pattern|did you detect)\b", re.I), QueryType.EXPLAIN_STYLE),
    (re.compile(r"\bexplain\s+(my\s+)?style\b", re.I), QueryType.EXPLAIN_STYLE),
    (re.compile(r"\bstyle\s+pattern\b", re.I), QueryType.EXPLAIN_STYLE),
    (re.compile(r"\bnaming\s+(convention|pattern)\b", re.I), QueryType.EXPLAIN_STYLE),
    # Explain suggestion
    (re.compile(r"\bwhy\s+did\s+you\s+suggest\b", re.I), QueryType.EXPLAIN_SUGGESTION),
    (re.compile(r"\bexplain\s+(this\s+)?suggestion\b", re.I), QueryType.EXPLAIN_SUGGESTION),
    (re.compile(r"\bwhat\s+evidence\s+(for\s+)?this\s+suggestion\b", re.I), QueryType.EXPLAIN_SUGGESTION),
    (re.compile(r"\brationale\s+for\s+suggestion\b", re.I), QueryType.EXPLAIN_SUGGESTION),
    # Explain draft
    (re.compile(r"\bwhy\s+is\s+this\s+draft\s+(structure\s+)?appropriate\b", re.I), QueryType.EXPLAIN_DRAFT),
    (re.compile(r"\bexplain\s+(this\s+)?draft\s+(structure)?\b", re.I), QueryType.EXPLAIN_DRAFT),
    (re.compile(r"\bwhat\s+draft\s+structure\b", re.I), QueryType.EXPLAIN_DRAFT),
    (re.compile(r"\bdraft\s+outline\s+explanation\b", re.I), QueryType.EXPLAIN_DRAFT),
    # Next step
    (re.compile(r"\bnext\s+step\b", re.I), QueryType.SUGGEST_NEXT_STEP),
    (re.compile(r"\bwhat\s+(should|to)\s+(i\s+)?(do|prepare)\s+next\b", re.I), QueryType.SUGGEST_NEXT_STEP),
    (re.compile(r"\bsensible\s+next\s+step\b", re.I), QueryType.SUGGEST_NEXT_STEP),
    (re.compile(r"\bmissing\s+artifact\s+(implied|by)\b", re.I), QueryType.SUGGEST_NEXT_STEP),
    (re.compile(r"\breusable\s+structure\s+(to\s+)?create\b", re.I), QueryType.SUGGEST_NEXT_STEP),
    (re.compile(r"\bwhat\s+to\s+prepare\s+next\b", re.I), QueryType.SUGGEST_NEXT_STEP),
    # Refine draft
    (re.compile(r"\brefine\s+(this\s+)?draft\b", re.I), QueryType.REFINE_DRAFT_STRUCTURE),
    (re.compile(r"\brefine\s+draft\s+structure\b", re.I), QueryType.REFINE_DRAFT_STRUCTURE),
    (re.compile(r"\bmake\s+(this\s+)?draft\s+(more\s+)?project\s*specific\b", re.I), QueryType.REFINE_DRAFT_STRUCTURE),
    (re.compile(r"\badapt\s+draft\s+to\s+(my\s+)?(project|style)\b", re.I), QueryType.REFINE_DRAFT_STRUCTURE),
    # Summarize project patterns
    (re.compile(r"\bsummarize\s+project\s+patterns\b", re.I), QueryType.SUMMARIZE_PROJECT_PATTERNS),
    (re.compile(r"\bproject\s+patterns\b", re.I), QueryType.SUMMARIZE_PROJECT_PATTERNS),
    # Summarize workflow patterns
    (re.compile(r"\bsummarize\s+workflow\s+patterns\b", re.I), QueryType.SUMMARIZE_WORKFLOW_PATTERNS),
    (re.compile(r"\bworkflow\s+patterns\b", re.I), QueryType.SUMMARIZE_WORKFLOW_PATTERNS),
    # List projects
    (re.compile(r"\blist\s+(active\s+)?projects\b", re.I), QueryType.LIST_ACTIVE_PROJECTS),
    (re.compile(r"\bwhat\s+projects\s+(do i have|are there)\b", re.I), QueryType.LIST_ACTIVE_PROJECTS),
    (re.compile(r"\bshow\s+(me\s+)?(my\s+)?projects\b", re.I), QueryType.LIST_ACTIVE_PROJECTS),
    # Scaffold help by domain
    (re.compile(r"\bcreative\s+(scaffold|brief|template)\s+help\b", re.I), QueryType.CREATIVE_SCAFFOLD_HELP),
    (re.compile(r"\bcreative\s+scaffold\b", re.I), QueryType.CREATIVE_SCAFFOLD_HELP),
    (re.compile(r"\bfinance\s+(scaffold|report|ops)\s+help\b", re.I), QueryType.FINANCE_OPS_SCAFFOLD_HELP),
    (re.compile(r"\bops\s+scaffold\s+help\b", re.I), QueryType.FINANCE_OPS_SCAFFOLD_HELP),
    (re.compile(r"\breconciliation\s+checklist\b", re.I), QueryType.FINANCE_OPS_SCAFFOLD_HELP),
    (re.compile(r"\bfounder\s+admin\s+help\b", re.I), QueryType.FOUNDER_ADMIN_SCAFFOLD_HELP),
    (re.compile(r"\badmin\s+scaffold\b", re.I), QueryType.FOUNDER_ADMIN_SCAFFOLD_HELP),
]

# Domain evidence / classification question
_DOMAIN_EVIDENCE = re.compile(r"\b(what\s+)?evidence\s+support(s)?\s+(this\s+)?domain\b", re.I)


def route_query(user_text: str, requested_mode: str = "") -> tuple[QueryType, dict[str, Any]]:
    """
    Classify the user query into a QueryType. Deterministic, rule-based.

    Returns (QueryType, extras). extras may include: matched_phrase, hint_id (e.g. suggestion_id, draft_id).
    """
    text = (user_text or "").strip()
    if not text:
        return QueryType.GENERAL_CHAT, {}

    # Explicit mode override from CLI/session
    if requested_mode:
        mode_lower = requested_mode.lower().strip()
        for qt in QueryType:
            if qt.value == mode_lower:
                return qt, {"requested_mode": requested_mode}
        if mode_lower in ("explain", "explain_project"):
            return QueryType.EXPLAIN_PROJECT, {"requested_mode": requested_mode}
        if mode_lower in ("next_step", "next-step"):
            return QueryType.SUGGEST_NEXT_STEP, {"requested_mode": requested_mode}
        if mode_lower in ("refine", "refine_draft"):
            return QueryType.REFINE_DRAFT_STRUCTURE, {"requested_mode": requested_mode}

    # Domain evidence -> explain_project (we explain domain classification evidence there)
    if _DOMAIN_EVIDENCE.search(text):
        return QueryType.EXPLAIN_PROJECT, {"matched": "domain_evidence"}

    for pattern, qtype in _ROUTE_PATTERNS:
        if hasattr(pattern, "search"):
            m = pattern.search(text)
            if m:
                return qtype, {"matched_phrase": m.group(0)}
        elif pattern in text.lower():
            return qtype, {"matched_phrase": pattern}

    return QueryType.GENERAL_CHAT, {}
