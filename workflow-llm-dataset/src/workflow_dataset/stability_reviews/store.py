"""
M46I–M46L: Persist sustained deployment reviews under data/local/stability_reviews/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.stability_reviews.models import SustainedDeploymentReview


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _reviews_dir(root: Path) -> Path:
    return root / "data/local/stability_reviews"


def _reviews_index_path(root: Path) -> Path:
    return _reviews_dir(root) / "reviews_index.json"


def save_review(
    review: SustainedDeploymentReview,
    repo_root: Path | str | None = None,
) -> Path:
    """Persist a sustained deployment review; append to index. Returns path to index file."""
    root = _repo_root(repo_root)
    d = _reviews_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    index_path = _reviews_index_path(root)
    reviews: list[dict[str, Any]] = []
    if index_path.exists():
        try:
            reviews = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(reviews, list):
                reviews = []
        except Exception:
            reviews = []
    reviews.append(review.to_dict())
    index_path.write_text(json.dumps(reviews, indent=2), encoding="utf-8")
    return index_path


def load_latest_review(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load the most recent sustained deployment review from index (newest last)."""
    root = _repo_root(repo_root)
    path = _reviews_index_path(root)
    if not path.exists():
        return None
    try:
        reviews = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(reviews, list) or not reviews:
            return None
        return reviews[-1]
    except Exception:
        return None


def list_reviews(
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List sustained deployment reviews (newest first)."""
    root = _repo_root(repo_root)
    path = _reviews_index_path(root)
    if not path.exists():
        return []
    try:
        reviews = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(reviews, list):
            return []
        return list(reversed(reviews[-limit:]))
    except Exception:
        return []


def get_review_by_id(
    review_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Get a single review by review_id."""
    for r in list_reviews(repo_root, limit=500):
        if r.get("review_id") == review_id:
            return r
    return None
