"""
B4: Read-only review queue metrics and revision burden summary.
Local-only; no writes. Uses data/local/workspaces and data/local/review.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from workflow_dataset.release.reporting_workspaces import get_workspace_inventory, list_reporting_workspaces
from workflow_dataset.release.review_state import get_approved_artifacts, load_review_state


def get_review_metrics(
    workspaces_root: str | Path,
    review_root: str | Path | None = None,
    repo_root: Path | None = None,
    limit_workspaces: int = 200,
) -> dict[str, Any]:
    """
    Compute review-queue metrics from local workspaces and review state. Read-only.
    Returns dict with:
      - workspaces_total, workspaces_pending_review (has at least one unreviewed artifact)
      - artifacts_total, artifacts_reviewed, artifacts_pending
      - artifacts_approved, artifacts_needs_revision, artifacts_excluded
      - revision_rate (needs_revision / reviewed), or None if no reviewed
      - avg_approved_per_workspace (mean over workspaces with at least one review)
      - workspaces_with_package (count that have built a package)
      - avg_approved_per_package (mean approved count over workspaces that have a package)
      - revision_reasons: list of { "reason": str, "count": int } sorted by count desc (from needs_revision notes)
    """
    workspaces_root = Path(workspaces_root)
    if repo_root is None:
        from workflow_dataset.path_utils import get_repo_root
        repo_root = Path(get_repo_root())
    else:
        repo_root = Path(repo_root)
    if review_root is None:
        review_root = repo_root / "data/local/review"
    else:
        review_root = Path(review_root)

    workspaces = list_reporting_workspaces(workspaces_root, limit=limit_workspaces)
    workspaces_total = len(workspaces)

    artifacts_total = 0
    artifacts_reviewed = 0
    artifacts_pending = 0
    artifacts_approved = 0
    artifacts_needs_revision = 0
    artifacts_excluded = 0
    workspaces_pending_review = 0
    approved_per_workspace: list[int] = []
    approved_per_package_workspace: list[int] = []
    revision_notes: list[str] = []

    for inv in workspaces:
        wp = inv.get("workspace_path")
        if not wp:
            continue
        ws_path = Path(wp)
        artifact_names = inv.get("artifacts") or []
        artifacts_total += len(artifact_names)
        state = load_review_state(ws_path, repo_root=repo_root)
        review_artifacts = state.get("artifacts") or {}
        has_unreviewed = False
        approved_count = 0
        for name in artifact_names:
            meta = review_artifacts.get(name) or {}
            s = (meta or {}).get("state")
            if not s:
                artifacts_pending += 1
                has_unreviewed = True
            else:
                artifacts_reviewed += 1
                if s == "approved":
                    artifacts_approved += 1
                    approved_count += 1
                elif s == "needs_revision":
                    artifacts_needs_revision += 1
                    note = (meta.get("note") or "").strip()
                    if note:
                        revision_notes.append(note)
                elif s == "excluded":
                    artifacts_excluded += 1
        if has_unreviewed:
            workspaces_pending_review += 1
        if review_artifacts:
            approved_per_workspace.append(approved_count)
        if state.get("last_package_path"):
            approved_per_package_workspace.append(approved_count)

    revision_rate: float | None = None
    if artifacts_reviewed > 0:
        revision_rate = artifacts_needs_revision / artifacts_reviewed

    avg_approved_per_workspace: float | None = None
    if approved_per_workspace:
        avg_approved_per_workspace = sum(approved_per_workspace) / len(approved_per_workspace)

    avg_approved_per_package: float | None = None
    if approved_per_package_workspace:
        avg_approved_per_package = sum(approved_per_package_workspace) / len(approved_per_package_workspace)

    # Normalize revision reasons: strip, lowercase, count; top 20
    reason_counts = Counter(n.strip().lower() for n in revision_notes if n.strip())
    revision_reasons = [{"reason": r, "count": c} for r, c in reason_counts.most_common(20)]

    return {
        "workspaces_total": workspaces_total,
        "workspaces_pending_review": workspaces_pending_review,
        "artifacts_total": artifacts_total,
        "artifacts_reviewed": artifacts_reviewed,
        "artifacts_pending": artifacts_pending,
        "artifacts_approved": artifacts_approved,
        "artifacts_needs_revision": artifacts_needs_revision,
        "artifacts_excluded": artifacts_excluded,
        "revision_rate": revision_rate,
        "avg_approved_per_workspace": avg_approved_per_workspace,
        "workspaces_with_package": len(approved_per_package_workspace),
        "avg_approved_per_package": avg_approved_per_package,
        "revision_reasons": revision_reasons,
    }
