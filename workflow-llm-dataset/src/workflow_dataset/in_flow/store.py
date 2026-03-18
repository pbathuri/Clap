"""
M33I–M33L: Persist drafts, handoffs, checkpoints. Local-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.in_flow.models import (
    DraftArtifact,
    HandoffPackage,
    ReviewCheckpoint,
    RevisionEntry,
    ReviewBundle,
    HandoffKit,
)

IN_FLOW_DIR = Path("data/local/in_flow")
DRAFTS_FILE = "drafts.json"
HANDOFFS_FILE = "handoffs.json"
CHECKPOINTS_FILE = "checkpoints.json"
BUNDLES_FILE = "bundles.json"
KITS_FILE = "kits.json"


def get_in_flow_root(repo_root: Path | str | None = None) -> Path:
    """Root directory for in_flow data (drafts, handoffs, bundles, kits)."""
    return _root(repo_root)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve() / IN_FLOW_DIR
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve() / IN_FLOW_DIR
    except Exception:
        return Path.cwd().resolve() / IN_FLOW_DIR


def _load_json_list(path: Path, default: list[Any]) -> list[Any]:
    if not path.exists():
        return default
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else []
        return data if isinstance(data, list) else default
    except Exception:
        return default


def _save_json_list(path: Path, items: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


# ---- Drafts ----
def save_draft(draft: DraftArtifact, repo_root: Path | str | None = None) -> None:
    root = _root(repo_root)
    path = root / DRAFTS_FILE
    items = _load_json_list(path, [])
    items = [i for i in items if isinstance(i, dict) and i.get("draft_id") != draft.draft_id]
    items.append(draft.to_dict())
    _save_json_list(path, items)


def load_draft(draft_id: str, repo_root: Path | str | None = None) -> DraftArtifact | None:
    root = _root(repo_root)
    path = root / DRAFTS_FILE
    for d in _load_json_list(path, []):
        if isinstance(d, dict) and d.get("draft_id") == draft_id:
            return DraftArtifact.from_dict(d)
    return None


def list_drafts(
    repo_root: Path | str | None = None,
    project_id: str | None = None,
    session_id: str | None = None,
    review_status: str | None = None,
    limit: int = 50,
) -> list[DraftArtifact]:
    root = _root(repo_root)
    path = root / DRAFTS_FILE
    out: list[DraftArtifact] = []
    for d in _load_json_list(path, []):
        if not isinstance(d, dict):
            continue
        if project_id and d.get("project_id") != project_id:
            continue
        if session_id and d.get("session_id") != session_id:
            continue
        if review_status and d.get("review_status") != review_status:
            continue
        try:
            out.append(DraftArtifact.from_dict(d))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def append_revision(draft_id: str, entry: RevisionEntry, repo_root: Path | str | None = None) -> bool:
    draft = load_draft(draft_id, repo_root=repo_root)
    if not draft:
        return False
    draft.revision_history = list(draft.revision_history) + [entry]
    from workflow_dataset.utils.dates import utc_now_iso
    draft.updated_utc = utc_now_iso()
    save_draft(draft, repo_root=repo_root)
    return True


# ---- Handoffs ----
def save_handoff(handoff: HandoffPackage, repo_root: Path | str | None = None) -> None:
    root = _root(repo_root)
    path = root / HANDOFFS_FILE
    items = _load_json_list(path, [])
    items = [i for i in items if isinstance(i, dict) and i.get("handoff_id") != handoff.handoff_id]
    items.append(handoff.to_dict())
    _save_json_list(path, items)


def load_handoff(handoff_id: str, repo_root: Path | str | None = None) -> HandoffPackage | None:
    root = _root(repo_root)
    path = root / HANDOFFS_FILE
    for d in _load_json_list(path, []):
        if isinstance(d, dict) and d.get("handoff_id") == handoff_id:
            return HandoffPackage.from_dict(d)
    return None


def list_handoffs(
    repo_root: Path | str | None = None,
    limit: int = 30,
) -> list[HandoffPackage]:
    root = _root(repo_root)
    path = root / HANDOFFS_FILE
    out: list[HandoffPackage] = []
    for d in _load_json_list(path, []):
        if not isinstance(d, dict):
            continue
        try:
            out.append(HandoffPackage.from_dict(d))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


# ---- Checkpoints ----
def save_checkpoint(checkpoint: ReviewCheckpoint, repo_root: Path | str | None = None) -> None:
    root = _root(repo_root)
    path = root / CHECKPOINTS_FILE
    items = _load_json_list(path, [])
    items = [i for i in items if isinstance(i, dict) and i.get("checkpoint_id") != checkpoint.checkpoint_id]
    items.append(checkpoint.to_dict())
    _save_json_list(path, items)


def list_checkpoints(
    repo_root: Path | str | None = None,
    plan_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[ReviewCheckpoint]:
    root = _root(repo_root)
    path = root / CHECKPOINTS_FILE
    out: list[ReviewCheckpoint] = []
    for d in _load_json_list(path, []):
        if not isinstance(d, dict):
            continue
        if plan_id and d.get("plan_id") != plan_id:
            continue
        if status and d.get("status") != status:
            continue
        try:
            out.append(ReviewCheckpoint.from_dict(d))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


# ---- M33L.1 Bundles and Kits ----
def save_bundle(bundle: ReviewBundle, repo_root: Path | str | None = None) -> None:
    root = _root(repo_root)
    path = root / BUNDLES_FILE
    items = _load_json_list(path, [])
    items = [i for i in items if isinstance(i, dict) and i.get("bundle_id") != bundle.bundle_id]
    items.append(bundle.to_dict())
    _save_json_list(path, items)


def load_bundle(bundle_id: str, repo_root: Path | str | None = None) -> ReviewBundle | None:
    root = _root(repo_root)
    path = root / BUNDLES_FILE
    for d in _load_json_list(path, []):
        if isinstance(d, dict) and d.get("bundle_id") == bundle_id:
            return ReviewBundle.from_dict(d)
    return None


def list_bundles(repo_root: Path | str | None = None, limit: int = 50) -> list[ReviewBundle]:
    root = _root(repo_root)
    path = root / BUNDLES_FILE
    out: list[ReviewBundle] = []
    for d in _load_json_list(path, []):
        if not isinstance(d, dict):
            continue
        try:
            out.append(ReviewBundle.from_dict(d))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def save_kit(kit: HandoffKit, repo_root: Path | str | None = None) -> None:
    root = _root(repo_root)
    path = root / KITS_FILE
    items = _load_json_list(path, [])
    items = [i for i in items if isinstance(i, dict) and i.get("kit_id") != kit.kit_id]
    items.append(kit.to_dict())
    _save_json_list(path, items)


def load_kit(kit_id: str, repo_root: Path | str | None = None) -> HandoffKit | None:
    root = _root(repo_root)
    path = root / KITS_FILE
    for d in _load_json_list(path, []):
        if isinstance(d, dict) and d.get("kit_id") == kit_id:
            return HandoffKit.from_dict(d)
    return None


def list_kits(repo_root: Path | str | None = None, limit: int = 50) -> list[HandoffKit]:
    root = _root(repo_root)
    path = root / KITS_FILE
    out: list[HandoffKit] = []
    for d in _load_json_list(path, []):
        if not isinstance(d, dict):
            continue
        try:
            out.append(HandoffKit.from_dict(d))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out
