"""
M21: Models for external source candidates, roles, and adoption decisions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceRole(str, Enum):
    """Role a source could play in the product."""

    AGENT_RUNTIME = "agent_runtime"
    AGENT_ORCHESTRATOR = "agent_orchestrator"
    RETRIEVAL_LAYER = "retrieval_layer"
    EMBEDDING_LAYER = "embedding_layer"
    PARSER = "parser"
    SPREADSHEET_TOOLING = "spreadsheet_tooling"
    CREATIVE_PACKAGING = "creative_packaging"
    SIMULATION_ENGINE = "simulation_engine"
    DASHBOARD_UI = "dashboard_ui"
    NETWORK_PROXY = "network_proxy"
    EVALUATION_HARNESS = "evaluation_harness"
    CAPABILITY_PACK_REFERENCE = "capability_pack_reference"
    UNSAFE_OR_REJECTED = "unsafe_or_rejected"


class SourceAdoptionDecision(str, Enum):
    """Recommended adoption outcome."""

    REJECT = "reject"
    REFERENCE_ONLY = "reference_only"
    BORROW_PATTERNS = "borrow_patterns"
    OPTIONAL_WRAPPER = "optional_wrapper"
    CANDIDATE_FOR_PACK = "candidate_for_pack"
    CORE_CANDIDATE = "core_candidate"


class ExternalSourceCandidate(BaseModel):
    """A single external repo/resource candidate for capability intake."""

    source_id: str = Field(default="", description="Unique id (e.g. openclaw, mirofish)")
    name: str = Field(default="")
    source_type: str = Field(default="repo", description="repo | dataset | model | toolkit")
    canonical_url: str = Field(default="")
    source_kind: str = Field(default="", description="e.g. github, huggingface")
    description: str = Field(default="")
    license: str = Field(default="")
    primary_language: str = Field(default="")
    stars_or_popularity: str = Field(default="")
    last_activity: str = Field(default="")
    maintainer_signal: str = Field(default="", description="active | stale | unknown")
    local_runtime_fit: str = Field(default="", description="high | medium | low | none")
    cloud_pack_fit: str = Field(default="", description="high | medium | low | none")
    recommended_role: str = Field(default="", description="SourceRole value")
    safety_risk_level: str = Field(default="", description="low | medium | high | unknown")
    adoption_recommendation: str = Field(default="", description="SourceAdoptionDecision value")
    notes: str = Field(default="")
    unresolved_reason: str = Field(default="", description="If source_id/url ambiguous")
    product_layers: list[str] = Field(default_factory=list, description="Architecture layers this touches")
