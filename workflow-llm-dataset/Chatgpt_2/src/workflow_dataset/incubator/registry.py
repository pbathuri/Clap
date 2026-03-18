"""
M22A / M23W: Incubator registry — local file store for workflow candidates. No cloud; operator-controlled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_STAGES = ("idea", "prototype", "benchmarked", "cohort_tested", "promoted", "rejected")
VALID_DECISIONS = ("none", "promoted", "rejected", "hold")


def _incubator_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root() / "data/local/incubator"
    except Exception:
        return Path.cwd() / "data/local/incubator"


def _candidate_path(candidate_id: str, root: Path) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in candidate_id.strip())
    return root / f"{safe}.json"


def list_candidates(root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all candidates from incubator root. root can be Path, str, or None (default repo data/local/incubator)."""
    base = _incubator_root(root)
    if not base.exists() or not base.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for f in sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix != ".json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data.setdefault("id", data.get("candidate_id", f.stem))
            data.setdefault("stage", "idea")
            data.setdefault("promotion_decision", "none")
            out.append(data)
        except Exception:
            continue
    return out


def add_candidate(
    candidate_id: str,
    description: str = "",
    target_user_value: str = "",
    stage: str = "idea",
    root: Path | str | None = None,
) -> None:
    """Add or overwrite a candidate. Raises ValueError if stage invalid."""
    if stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: {stage}. Use one of {VALID_STAGES}")
    base = _incubator_root(root)
    base.mkdir(parents=True, exist_ok=True)
    path = _candidate_path(candidate_id, base)
    data: dict[str, Any] = {
        "candidate_id": candidate_id,
        "id": candidate_id,
        "description": description,
        "target_user_value": target_user_value,
        "stage": stage,
        "promotion_decision": "none",
        "evidence_refs": [],
        "gate_results": None,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_candidate(candidate_id: str, root: Path | str | None = None) -> dict[str, Any] | None:
    """Get one candidate by id."""
    base = _incubator_root(root)
    path = _candidate_path(candidate_id, base)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("id", data.get("candidate_id", candidate_id))
        data.setdefault("stage", "idea")
        data.setdefault("promotion_decision", "none")
        data.setdefault("evidence_refs", [])
        return data
    except Exception:
        return None


def update_candidate(
    candidate_id: str,
    patch: dict[str, Any],
    root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Update candidate with patch (e.g. gate_results). Returns updated candidate or None."""
    c = get_candidate(candidate_id, root)
    if not c:
        return None
    base = _incubator_root(root)
    path = _candidate_path(candidate_id, base)
    for k, v in patch.items():
        c[k] = v
    path.write_text(json.dumps(c, indent=2), encoding="utf-8")
    return c


def set_promotion_decision(
    candidate_id: str,
    decision: str,
    root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Set promotion_decision to promoted, rejected, or hold."""
    if decision not in ("promoted", "rejected", "hold"):
        return None
    return update_candidate(candidate_id, {"promotion_decision": decision}, root)


def mark_stage(
    candidate_id: str,
    stage: str,
    root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Set candidate stage. Returns updated candidate or None if invalid stage."""
    if stage not in VALID_STAGES:
        return None
    return update_candidate(candidate_id, {"stage": stage}, root)


def attach_evidence(
    candidate_id: str,
    evidence_ref: str,
    root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Append evidence_ref to candidate. Returns updated candidate or None."""
    c = get_candidate(candidate_id, root)
    if not c:
        return None
    refs = list(c.get("evidence_refs", []))
    if evidence_ref not in refs:
        refs.append(evidence_ref)
    return update_candidate(candidate_id, {"evidence_refs": refs}, root)
