"""
M31I–M31L: Persist preference/style candidates and accepted updates. data/local/personal_adaptation/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.personal_adaptation.models import (
    PreferenceCandidate,
    StylePatternCandidate,
    AcceptedPreferenceUpdate,
    REVIEW_STATUS_ACCEPTED,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

ADAPTATION_DIR = "data/local/personal_adaptation"
CANDIDATES_SUBDIR = "candidates"
ACCEPTED_SUBDIR = "accepted"
PRESETS_SUBDIR = "presets"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_adaptation_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / ADAPTATION_DIR


def get_candidates_dir(repo_root: Path | str | None = None) -> Path:
    return get_adaptation_dir(repo_root) / CANDIDATES_SUBDIR


def get_accepted_dir(repo_root: Path | str | None = None) -> Path:
    return get_adaptation_dir(repo_root) / ACCEPTED_SUBDIR


def get_presets_dir(repo_root: Path | str | None = None) -> Path:
    return get_adaptation_dir(repo_root) / PRESETS_SUBDIR


def save_candidate(
    candidate: PreferenceCandidate | StylePatternCandidate,
    repo_root: Path | str | None = None,
) -> Path:
    """Save a preference or style candidate to candidates/<candidate_id>.json."""
    root = _repo_root(repo_root)
    dir_path = get_candidates_dir(root)
    dir_path.mkdir(parents=True, exist_ok=True)
    cid = candidate.candidate_id
    path = dir_path / f"{cid}.json"
    path.write_text(json.dumps(candidate.to_dict(), indent=2), encoding="utf-8")
    return path


def get_candidate(
    candidate_id: str,
    repo_root: Path | str | None = None,
) -> PreferenceCandidate | StylePatternCandidate | None:
    """Load a candidate by id. Tries preference then style pattern."""
    root = _repo_root(repo_root)
    path = get_candidates_dir(root) / f"{candidate_id}.json"
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if "key" in d and "proposed_value" in d:
            return PreferenceCandidate.from_dict(d)
        if "pattern_type" in d:
            return StylePatternCandidate.from_dict(d)
    except Exception:
        pass
    return None


def list_candidates(
    repo_root: Path | str | None = None,
    kind: str | None = None,
    review_status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List candidates (preference and/or style). kind: preference | style_pattern | None (both)."""
    root = _repo_root(repo_root)
    dir_path = get_candidates_dir(root)
    if not dir_path.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(dir_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit * 2]:
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            if kind == "preference" and "key" not in d:
                continue
            if kind == "style_pattern" and "pattern_type" not in d:
                continue
            if review_status and d.get("review_status") != review_status:
                continue
            d["candidate_id"] = d.get("candidate_id", path.stem)
            out.append(d)
            if len(out) >= limit:
                break
        except Exception:
            pass
    return out


def accept_candidate(
    candidate_id: str,
    repo_root: Path | str | None = None,
) -> AcceptedPreferenceUpdate | None:
    """
    Mark candidate as accepted and create an AcceptedPreferenceUpdate record.
    Updates the candidate's review_status to accepted. Returns the update record or None.
    """
    root = _repo_root(repo_root)
    cand = get_candidate(candidate_id, root)
    if not cand:
        return None
    ts = utc_now_iso()
    update_id = f"upd_{candidate_id}_{ts.replace(':', '-')[:19]}"
    if isinstance(cand, PreferenceCandidate):
        key_or_pattern = cand.key
        applied_value = cand.proposed_value
        applied_surface = cand.affected_surface
        candidate_type = "preference"
    else:
        key_or_pattern = cand.pattern_type
        applied_value = cand.description
        applied_surface = cand.affected_surface
        candidate_type = "style_pattern"
    update = AcceptedPreferenceUpdate(
        update_id=update_id,
        candidate_id=candidate_id,
        candidate_type=candidate_type,
        key_or_pattern=key_or_pattern,
        applied_value=applied_value,
        applied_surface=applied_surface,
        applied_utc=ts,
    )
    # Persist update
    acc_dir = get_accepted_dir(root)
    acc_dir.mkdir(parents=True, exist_ok=True)
    (acc_dir / f"{update_id}.json").write_text(json.dumps(update.to_dict(), indent=2), encoding="utf-8")
    # Update candidate review_status
    cand.review_status = REVIEW_STATUS_ACCEPTED
    cand.updated_utc = ts
    save_candidate(cand, root)
    return update


def list_accepted(
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List accepted preference updates."""
    root = _repo_root(repo_root)
    acc_dir = get_accepted_dir(root)
    if not acc_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(acc_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            out.append(d)
        except Exception:
            pass
    return out
