"""
M25E–M25H: Pack-driven behavior models — prompt assets, task-level defaults, resolution result.
Explicit, inspectable; no code execution from packs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Prompt asset kinds (manifest-declared)
PROMPT_ASSET_KINDS = (
    "system_guidance",
    "task_prompt",
    "workflow_prompt",
    "explanation_style_hint",
    "output_framing_hint",
)


@dataclass
class PackPromptAsset:
    """Pack-provided prompt asset: manifest-declared, inspectable, overrideable by precedence."""

    kind: str  # one of PROMPT_ASSET_KINDS
    key: str = ""  # e.g. task_id, workflow_id, or scope name
    content: str = ""
    pack_id: str = ""
    priority_hint: str = ""  # low, medium, high — used in precedence when same key


@dataclass
class PackTaskDefaults:
    """Task-level pack defaults: preferred adapter, model class, retrieval profile, output mode. Do not bypass trust/approval."""

    task_id: str = ""
    workflow_id: str = ""  # optional scope
    pack_id: str = ""
    preferred_adapter: str = ""
    preferred_model_class: str = ""
    preferred_retrieval_profile: dict[str, Any] = field(default_factory=dict)
    preferred_output_mode: str = ""  # e.g. ops_handoff, document
    execution_mode_hint: str = ""  # e.g. simulate_first, real_after_approval


# M25H.1: Allowed retrieval profile keys (safer tuning; no arbitrary keys)
RETRIEVAL_PROFILE_ALLOWED_KEYS = frozenset(("top_k", "corpus_filter", "max_tokens", "min_score", "rerank", "include_metadata"))

# M25H.1: Allowed output profile keys (preset only; no code)
OUTPUT_PROFILE_ALLOWED_KEYS = frozenset(("adapter", "format_hint", "max_length_hint", "sections_hint"))

# M25H.1: Allowed parser/output hint keys (safe hints only)
PARSER_OUTPUT_HINT_ALLOWED_KEYS = frozenset(("preferred_format", "max_length_hint", "bullet_preference", "stakeholder_safe"))


@dataclass
class PackRetrievalProfilePreset:
    """Pack-specific retrieval profile tuning. Only allowed keys applied; inspectable."""

    preset_id: str = ""
    task_id: str = ""
    workflow_id: str = ""
    pack_id: str = ""
    top_k: int = 0  # 0 = not set
    corpus_filter: str = ""
    max_tokens: int = 0
    min_score: float = 0.0
    rerank: bool = False
    include_metadata: bool = False
    extra: dict[str, Any] = field(default_factory=dict)  # only allowed keys stored


@dataclass
class PackOutputProfilePreset:
    """Pack-specific output profile preset. Adapter, format hints; no code execution."""

    preset_id: str = ""
    task_id: str = ""
    workflow_id: str = ""
    pack_id: str = ""
    adapter: str = ""
    format_hint: str = ""
    max_length_hint: int = 0
    sections_hint: str = ""  # e.g. "bullets,summary"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParserOutputHint:
    """Safer parser/output hint: preferred format, length, style. No arbitrary logic."""

    key: str = ""  # task_id or workflow_id
    pack_id: str = ""
    preferred_format: str = ""  # e.g. markdown, plain
    max_length_hint: int = 0
    bullet_preference: str = ""  # bullets, paragraphs, either
    stakeholder_safe: bool = False


@dataclass
class ResolvedBehavior:
    """Resolved behavior for a task: merged prompt assets, task defaults, retrieval/output profiles with source attribution."""

    task_id: str = ""
    workflow_id: str = ""
    prompt_assets: list[PackPromptAsset] = field(default_factory=list)
    task_defaults: PackTaskDefaults | None = None
    retrieval_profile: dict[str, Any] = field(default_factory=dict)  # M25H.1 resolved preset (allowed keys only)
    output_profile: dict[str, Any] = field(default_factory=dict)  # M25H.1 resolved preset
    parser_output_hints: list[ParserOutputHint] = field(default_factory=list)
    winning_pack_id: str = ""  # pack that supplied the winning single-value defaults
    retrieval_profile_source_pack: str = ""  # pack that supplied winning retrieval preset
    output_profile_source_pack: str = ""  # pack that supplied winning output preset
    retrieval_profile_preset_id: str = ""  # M25H.1 which preset was applied (operator-readable)
    output_profile_preset_id: str = ""  # M25H.1 which preset was applied
    contributing_pack_ids: list[str] = field(default_factory=list)
    excluded_pack_ids: list[str] = field(default_factory=list)
    exclusion_reasons: dict[str, str] = field(default_factory=dict)  # pack_id -> reason
    conflict_summary: str = ""
    why_retrieval_profile: str = ""  # M25H.1 operator-readable explanation
    why_output_profile: str = ""  # M25H.1 operator-readable explanation


@dataclass
class BehaviorResolutionResult:
    """Full result of behavior resolution: resolved behavior + explanation."""

    resolved: ResolvedBehavior
    active_pack_ids: list[str] = field(default_factory=list)
    primary_pack_id: str = ""
    pinned_pack_id: str = ""
    secondary_pack_ids: list[str] = field(default_factory=list)
    why_winning: str = ""  # e.g. "pinned pack founder_ops_pack wins for task weekly_status"
    why_excluded: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
