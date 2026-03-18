"""
M44E–M44H: Persist summaries, compression/forgetting candidates, archival state under data/local/memory_curation/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.memory_curation.models import (
    SummarizedMemoryUnit,
    CompressionCandidate,
    ForgettingCandidate,
    ReviewRequiredDeletionCandidate,
    ArchivalState,
    MemoryProtectionRule,
    ReviewPack,
    ReviewPackItem,
    ArchivalPolicyCuration,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _curation_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / "data" / "local" / "memory_curation"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# ----- Summaries -----
def _summaries_path(root: Path) -> Path:
    return root / "summaries.json"


def load_summaries(repo_root: Path | str | None = None) -> list[SummarizedMemoryUnit]:
    p = _summaries_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("summaries", []):
            out.append(SummarizedMemoryUnit(
                summary_id=d.get("summary_id", ""),
                summary_text=d.get("summary_text", ""),
                source_unit_ids=list(d.get("source_unit_ids", [])),
                source_session_ids=list(d.get("source_session_ids", [])),
                source_kind=d.get("source_kind", ""),
                created_at_utc=d.get("created_at_utc", ""),
                keyword_tags=list(d.get("keyword_tags", [])),
            ))
        return out
    except Exception:
        return []


def save_summaries(summaries: list[SummarizedMemoryUnit], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _summaries_path(root)
    data = {"summaries": [s.to_dict() for s in summaries], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_summary(unit: SummarizedMemoryUnit, repo_root: Path | str | None = None) -> None:
    summaries = load_summaries(repo_root)
    summaries.append(unit)
    save_summaries(summaries, repo_root)


# ----- Compression candidates -----
def _compression_candidates_path(root: Path) -> Path:
    return root / "compression_candidates.json"


def load_compression_candidates(repo_root: Path | str | None = None) -> list[CompressionCandidate]:
    p = _compression_candidates_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("candidates", []):
            out.append(CompressionCandidate(
                candidate_id=d.get("candidate_id", ""),
                unit_ids=list(d.get("unit_ids", [])),
                session_ids=list(d.get("session_ids", [])),
                reason=d.get("reason", ""),
                item_count=d.get("item_count", 0),
                created_at_utc=d.get("created_at_utc", ""),
                applied=d.get("applied", False),
                resulting_summary_id=d.get("resulting_summary_id", ""),
                operator_explanation=d.get("operator_explanation", ""),
            ))
        return out
    except Exception:
        return []


def save_compression_candidates(candidates: list[CompressionCandidate], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _compression_candidates_path(root)
    data = {"candidates": [c.to_dict() for c in candidates], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- Forgetting candidates -----
def _forgetting_candidates_path(root: Path) -> Path:
    return root / "forgetting_candidates.json"


def load_forgetting_candidates(repo_root: Path | str | None = None) -> list[ForgettingCandidate]:
    p = _forgetting_candidates_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("candidates", []):
            out.append(ForgettingCandidate(
                candidate_id=d.get("candidate_id", ""),
                unit_ids=list(d.get("unit_ids", [])),
                reason=d.get("reason", ""),
                created_at_utc=d.get("created_at_utc", ""),
                review_required=d.get("review_required", True),
                applied=d.get("applied", False),
                operator_explanation=d.get("operator_explanation", ""),
            ))
        return out
    except Exception:
        return []


def save_forgetting_candidates(candidates: list[ForgettingCandidate], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _forgetting_candidates_path(root)
    data = {"candidates": [c.to_dict() for c in candidates], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- Review-required deletion candidates -----
def _review_required_path(root: Path) -> Path:
    return root / "review_required_deletions.json"


def load_review_required(repo_root: Path | str | None = None) -> list[ReviewRequiredDeletionCandidate]:
    p = _review_required_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("candidates", []):
            out.append(ReviewRequiredDeletionCandidate(
                candidate_id=d.get("candidate_id", ""),
                forgetting_candidate_id=d.get("forgetting_candidate_id", ""),
                unit_ids=list(d.get("unit_ids", [])),
                reason=d.get("reason", ""),
                high_value_hint=d.get("high_value_hint", False),
                created_at_utc=d.get("created_at_utc", ""),
                reviewed=d.get("reviewed", False),
                approved_for_forget=d.get("approved_for_forget", False),
                operator_explanation=d.get("operator_explanation", ""),
            ))
        return out
    except Exception:
        return []


def save_review_required(candidates: list[ReviewRequiredDeletionCandidate], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _review_required_path(root)
    data = {"candidates": [c.to_dict() for c in candidates], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- Archival state -----
def _archival_path(root: Path) -> Path:
    return root / "archival_state.json"


def load_archival_states(repo_root: Path | str | None = None) -> list[ArchivalState]:
    p = _archival_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("archives", []):
            out.append(ArchivalState(
                archive_id=d.get("archive_id", ""),
                unit_ids=list(d.get("unit_ids", [])),
                scope=d.get("scope", ""),
                archived_at_utc=d.get("archived_at_utc", ""),
                location=d.get("location", ""),
                retrievable=d.get("retrievable", True),
                policy_id=d.get("policy_id", ""),
            ))
        return out
    except Exception:
        return []


def save_archival_states(states: list[ArchivalState], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _archival_path(root)
    data = {"archives": [a.to_dict() for a in states], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- M44H.1: Protection rules -----
def _protection_rules_path(root: Path) -> Path:
    return root / "protection_rules.json"


def load_protection_rules(repo_root: Path | str | None = None) -> list[MemoryProtectionRule]:
    p = _protection_rules_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("rules", []):
            out.append(MemoryProtectionRule(
                rule_id=d.get("rule_id", ""),
                label=d.get("label", ""),
                match_source=d.get("match_source", ""),
                match_tags=list(d.get("match_tags", [])),
                match_source_ref_pattern=d.get("match_source_ref_pattern", ""),
                protection_reason=d.get("protection_reason", ""),
                created_at_utc=d.get("created_at_utc", ""),
                active=d.get("active", True),
            ))
        return out
    except Exception:
        return []


def save_protection_rules(rules: list[MemoryProtectionRule], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _protection_rules_path(root)
    data = {"rules": [r.to_dict() for r in rules], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- M44H.1: Review packs -----
def _review_packs_path(root: Path) -> Path:
    return root / "review_packs.json"


def load_review_packs(repo_root: Path | str | None = None) -> list[ReviewPack]:
    p = _review_packs_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("packs", []):
            items = [
                ReviewPackItem(
                    item_id=it.get("item_id", ""),
                    kind=it.get("kind", ""),
                    candidate_id=it.get("candidate_id", ""),
                    unit_ids=list(it.get("unit_ids", [])),
                    reason=it.get("reason", ""),
                    operator_explanation=it.get("operator_explanation", ""),
                    approved=it.get("approved"),
                )
                for it in d.get("items", [])
            ]
            out.append(ReviewPack(
                pack_id=d.get("pack_id", ""),
                label=d.get("label", ""),
                items=items,
                created_at_utc=d.get("created_at_utc", ""),
                reviewed_at_utc=d.get("reviewed_at_utc", ""),
                status=d.get("status", "pending"),
            ))
        return out
    except Exception:
        return []


def save_review_packs(packs: list[ReviewPack], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _review_packs_path(root)
    data = {"packs": [pk.to_dict() for pk in packs], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- M44H.1: Archival policies -----
def _archival_policies_path(root: Path) -> Path:
    return root / "archival_policies.json"


def load_archival_policies(repo_root: Path | str | None = None) -> list[ArchivalPolicyCuration]:
    p = _archival_policies_path(_curation_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("policies", []):
            out.append(ArchivalPolicyCuration(
                policy_id=d.get("policy_id", ""),
                label=d.get("label", ""),
                min_age_days=d.get("min_age_days", 0),
                require_review_before_archive=d.get("require_review_before_archive", True),
                max_archives_per_scope=d.get("max_archives_per_scope", 0),
                description=d.get("description", ""),
            ))
        return out
    except Exception:
        return []


def save_archival_policies(policies: list[ArchivalPolicyCuration], repo_root: Path | str | None = None) -> None:
    root = _curation_dir(repo_root)
    _ensure_dir(root)
    p = _archival_policies_path(root)
    data = {"policies": [a.to_dict() for a in policies], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
