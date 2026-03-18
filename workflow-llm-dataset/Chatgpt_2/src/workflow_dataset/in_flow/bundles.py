"""
M33L.1: Review bundles, handoff kits, nav links, readiness states.

Apply reusable review bundles; create handoffs from common kits;
resolve nav links into approvals, planner, executor, workspace;
set/get ready_to_send, ready_to_approve, ready_to_continue.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.in_flow.models import (
    ReviewBundle,
    HandoffKit,
    HandoffPackage,
    DraftArtifact,
    AffectedWorkflowStep,
    READINESS_READY_TO_SEND,
    READINESS_READY_TO_APPROVE,
    READINESS_READY_TO_CONTINUE,
    DRAFT_TYPE_STATUS_SUMMARY,
    DRAFT_TYPE_REVIEW_CHECKLIST,
    REVIEW_STATUS_WAITING_REVIEW,
)
from workflow_dataset.in_flow.store import (
    load_bundle,
    list_bundles,
    load_kit,
    list_kits,
    save_bundle,
    save_kit,
    load_handoff,
    save_handoff,
    load_draft,
    save_draft,
    get_in_flow_root,
)
from workflow_dataset.in_flow.composition import create_draft, create_handoff
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def load_bundles_from_config(repo_root: Path | str | None = None) -> list[ReviewBundle]:
    """Load bundles from configs/in_flow/review_bundles.yaml if present."""
    root = _repo_root(repo_root)
    path = root / "configs" / "in_flow" / "review_bundles.yaml"
    if not path.exists():
        return []
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not data:
            return []
        items = data.get("bundles", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        out: list[ReviewBundle] = []
        for d in items:
            if isinstance(d, dict):
                out.append(ReviewBundle.from_dict(d))
        return out
    except Exception:
        return []


def load_kits_from_config(repo_root: Path | str | None = None) -> list[HandoffKit]:
    """Load handoff kits from configs/in_flow/handoff_kits.yaml if present."""
    root = _repo_root(repo_root)
    path = root / "configs" / "in_flow" / "handoff_kits.yaml"
    if not path.exists():
        return []
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not data:
            return []
        items = data.get("kits", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        out: list[HandoffKit] = []
        for d in items:
            if isinstance(d, dict):
                out.append(HandoffKit.from_dict(d))
        return out
    except Exception:
        return []


def list_bundles_with_config(repo_root: Path | str | None = None, limit: int = 50) -> list[ReviewBundle]:
    """List bundles from store and config; config entries override store by bundle_id."""
    from_store = {b.bundle_id: b for b in list_bundles(repo_root=repo_root, limit=limit)}
    from_config = load_bundles_from_config(repo_root=repo_root)
    for b in from_config:
        from_store[b.bundle_id] = b
    return list(from_store.values())[:limit]


def list_kits_with_config(repo_root: Path | str | None = None, limit: int = 50) -> list[HandoffKit]:
    """List kits from store and config; config overrides store by kit_id."""
    from_store = {k.kit_id: k for k in list_kits(repo_root=repo_root, limit=limit)}
    from_config = load_kits_from_config(repo_root=repo_root)
    for k in from_config:
        from_store[k.kit_id] = k
    return list(from_store.values())[:limit]


def apply_review_bundle(
    bundle_id: str,
    repo_root: Path | str | None = None,
    *,
    project_id: str = "",
    session_id: str = "",
    title_prefix: str = "",
) -> list[DraftArtifact]:
    """
    Apply a review bundle: create drafts for checklist and summary (from template).
    Returns list of created drafts.
    """
    bundle = load_bundle(bundle_id, repo_root=repo_root)
    if not bundle:
        bundle_list = load_bundles_from_config(repo_root=repo_root)
        bundle = next((b for b in bundle_list if b.bundle_id == bundle_id), None)
    if not bundle:
        return []
    root = _repo_root(repo_root)
    created: list[DraftArtifact] = []
    now = utc_now_iso()

    if DRAFT_TYPE_REVIEW_CHECKLIST in bundle.draft_types or not bundle.draft_types:
        checklist_content = f"# {bundle.name}\n\n"
        for item in bundle.checklist_items:
            checklist_content += f"- [ ] {item}\n"
        draft = create_draft(
            DRAFT_TYPE_REVIEW_CHECKLIST,
            repo_root=repo_root,
            project_id=project_id or "default",
            session_id=session_id,
            title=title_prefix + bundle.name + " checklist",
        )
        draft.content = checklist_content
        draft.updated_utc = now
        save_draft(draft, repo_root=repo_root)
        created.append(draft)

    if (DRAFT_TYPE_STATUS_SUMMARY in bundle.draft_types or not bundle.draft_types) and bundle.summary_template:
        draft = create_draft(
            DRAFT_TYPE_STATUS_SUMMARY,
            repo_root=repo_root,
            project_id=project_id or "default",
            session_id=session_id,
            title=title_prefix + bundle.name + " summary",
        )
        draft.content = bundle.summary_template
        draft.updated_utc = now
        save_draft(draft, repo_root=repo_root)
        created.append(draft)

    return created


def create_handoff_from_kit(
    kit_id: str,
    repo_root: Path | str | None = None,
    *,
    from_workflow: str = "latest",
    from_session_id: str = "",
    from_project_id: str = "",
    title_override: str = "",
    summary: str = "",
    next_steps: list[str] | None = None,
    draft_ids: list[str] | None = None,
    readiness: str = "",
) -> HandoffPackage | None:
    """
    Create a handoff package from a kit template. Uses kit's title_template,
    default_target, nav_links, and optional default_next_steps.
    """
    kit = load_kit(kit_id, repo_root=repo_root)
    if not kit:
        kit_list = load_kits_from_config(repo_root=repo_root)
        kit = next((k for k in kit_list if k.kit_id == kit_id), None)
    if not kit:
        return None
    title = title_override or kit.title_template.replace("{{workflow}}", from_workflow).replace("{{session}}", from_session_id or "")
    pkg = create_handoff(
        repo_root=repo_root,
        from_workflow=from_workflow,
        from_session_id=from_session_id,
        from_project_id=from_project_id,
        title=title,
        draft_ids=list(draft_ids or []),
        target=kit.default_target or "artifact",
    )
    handoff = load_handoff(pkg.handoff_id, repo_root=repo_root)
    if not handoff:
        return pkg
    handoff.nav_links = list(kit.nav_links)
    if next_steps is not None:
        handoff.next_steps = next_steps
    elif kit.default_next_steps and not handoff.next_steps:
        handoff.next_steps = list(kit.default_next_steps)
    if summary:
        handoff.summary = summary
    handoff.readiness = readiness or (READINESS_READY_TO_SEND if kit.default_target == "artifact" else "")
    save_handoff(handoff, repo_root=repo_root)
    return handoff


def resolve_nav_links(
    handoff_id: str,
    repo_root: Path | str | None = None,
    *,
    plan_ref: str = "",
    goal: str = "",
    run_id: str = "",
) -> list[dict[str, str]]:
    """
    Resolve nav links for a handoff: fill in refs for approval_studio, planner,
    executor, workspace. Returns list of {label, view, command, ref}.
    """
    handoff = load_handoff(handoff_id, repo_root=repo_root)
    if not handoff:
        return []
    links = list(handoff.nav_links)
    # Add default links by target if not already present
    seen_views = {l.get("view", "") for l in links if l.get("view")}
    if handoff.target == "approval_studio" and "approval_studio" not in seen_views:
        links.append({"label": "Open approval queue", "view": "approval_studio", "command": "workflow-dataset review-studio inbox"})
    if handoff.target == "planner" and "planner" not in seen_views:
        cmd = f"workflow-dataset planner compile --goal \"{goal or handoff.summary[:80]}\"" if (goal or handoff.summary) else "workflow-dataset planner compile"
        links.append({"label": "Open planner", "view": "planner", "command": cmd, "ref": plan_ref or ""})
    if handoff.target == "executor" and "executor" not in seen_views:
        links.append({"label": "Open executor", "view": "executor", "command": "workflow-dataset executor runs", "ref": run_id or ""})
    if handoff.target == "workspace" and "workspace" not in seen_views:
        links.append({"label": "Open timeline", "view": "timeline", "command": "workflow-dataset workspace timeline"})
    return links


def set_handoff_readiness(handoff_id: str, readiness: str, repo_root: Path | str | None = None) -> bool:
    """Set readiness state: ready_to_send, ready_to_approve, ready_to_continue."""
    handoff = load_handoff(handoff_id, repo_root=repo_root)
    if not handoff:
        return False
    handoff.readiness = readiness
    save_handoff(handoff, repo_root=repo_root)
    return True


def get_handoff_readiness(handoff_id: str, repo_root: Path | str | None = None) -> str:
    """Return current readiness state for handoff."""
    handoff = load_handoff(handoff_id, repo_root=repo_root)
    if not handoff:
        return ""
    return handoff.readiness or ""
