"""
M23N Phase 4: Approval bootstrap UX. Batch review of approval requests, grouped scopes,
explicit refusal paths, clear explanation of consequences. No auto-grant.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.capability_discovery.approval_registry import (
    ApprovalRegistry,
    load_approval_registry,
    save_approval_registry,
    get_registry_path,
)
from workflow_dataset.capability_discovery.discovery import run_scan
from workflow_dataset.desktop_bench.trusted_actions import TRUSTED_ADAPTER_ACTIONS


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


def collect_approval_requests(
    repo_root: Path | str | None = None,
    *,
    include_trusted_scopes_only: bool = True,
) -> dict[str, Any]:
    """
    Collect approval requests: suggested paths, apps, and action scopes that the user
    may approve or refuse. Grouped by scope type. No writes; no auto-grant.
    """
    root = _repo_root(repo_root)
    reg_path = get_registry_path(root)
    existing = load_approval_registry(root) if reg_path.exists() and reg_path.is_file() else None
    profile = run_scan(repo_root=root)

    # Suggested paths: common sandbox roots (user can add more manually)
    suggested_paths: list[str] = [
        "data/local",
        "data/local/workspaces",
        "data/local/pilot",
        "data/local/notes",
    ]
    for p in (existing.approved_paths if existing else []):
        if p and p not in suggested_paths:
            suggested_paths.append(p)

    # Suggested apps: from profile or allowlist default
    suggested_apps = list(profile.approved_apps)[:20] if profile.approved_apps else []

    # Action scopes: from capability profile, optionally limited to trusted subset
    action_scopes: list[dict[str, Any]] = []
    for s in profile.action_scopes:
        adapter_id = getattr(s, "adapter_id", "") or (s.get("adapter_id") if isinstance(s, dict) else "")
        action_id = getattr(s, "action_id", "") or (s.get("action_id") if isinstance(s, dict) else "")
        executable = getattr(s, "executable", False) if not isinstance(s, dict) else s.get("executable", False)
        if include_trusted_scopes_only and (adapter_id, action_id) not in TRUSTED_ADAPTER_ACTIONS:
            continue
        action_scopes.append({
            "adapter_id": adapter_id,
            "action_id": action_id,
            "executable": executable,
            "description": f"{adapter_id}.{action_id}",
        })
    # Deduplicate by (adapter_id, action_id)
    seen: set[tuple[str, str]] = set()
    unique_scopes: list[dict[str, Any]] = []
    for s in action_scopes:
        key = (s.get("adapter_id", ""), s.get("action_id", ""))
        if key in seen:
            continue
        seen.add(key)
        unique_scopes.append(s)

    return {
        "registry_path": str(reg_path),
        "registry_exists": reg_path.exists() and reg_path.is_file(),
        "suggested_paths": suggested_paths,
        "suggested_apps": suggested_apps,
        "suggested_action_scopes": unique_scopes,
        "existing_paths": list(existing.approved_paths) if existing else [],
        "existing_apps": list(existing.approved_apps) if existing else [],
        "existing_action_scopes": list(existing.approved_action_scopes) if existing else [],
        "consequence_if_refuse": "Real execution for path-using and scope-listed actions will remain blocked until you add approvals to data/local/capability_discovery/approvals.yaml.",
        "consequence_if_approve": "Approved paths and action scopes will be written to the approval registry; run_execute will allow real execution only for those paths and scopes.",
    }


def format_approval_bootstrap_summary(requests: dict[str, Any]) -> str:
    """Format approval bootstrap summary for batch review: paths, apps, scopes, consequences."""
    lines = [
        "# Approval bootstrap — batch review",
        "",
        f"Registry path: {requests.get('registry_path', '')}",
        f"Registry exists: {requests.get('registry_exists')}",
        "",
        "## Suggested paths (approve = allow real execution for these directories)",
        "",
    ]
    for p in requests.get("suggested_paths", []):
        lines.append(f"- {p}")
    lines.extend(["", "## Suggested apps", ""])
    for a in requests.get("suggested_apps", [])[:15]:
        lines.append(f"- {a}")
    lines.extend(["", "## Suggested action scopes (adapter.action → executable)", ""])
    for s in requests.get("suggested_action_scopes", []):
        ex = "yes" if s.get("executable") else "no"
        lines.append(f"- {s.get('adapter_id', '')}.{s.get('action_id', '')}  executable={ex}")
    lines.extend([
        "",
        "## If you refuse",
        "",
        requests.get("consequence_if_refuse", ""),
        "",
        "## If you approve",
        "",
        requests.get("consequence_if_approve", ""),
        "",
        "To approve: run 'workflow-dataset onboard approve' and follow prompts, or edit the registry file manually.",
        "",
    ])
    return "\n".join(lines)


def apply_approval_choices(
    repo_root: Path | str | None = None,
    *,
    approve_paths: list[str] | None = None,
    refuse_paths: list[str] | None = None,
    approve_apps: list[str] | None = None,
    refuse_apps: list[str] | None = None,
    approve_scopes: list[dict[str, Any]] | None = None,
    refuse_scopes: list[dict[str, Any]] | None = None,
    merge_with_existing: bool = True,
) -> Path:
    """
    Apply user approval/refusal choices to the approval registry.
    - approve_*: add to registry (paths, apps, or scopes with executable=True).
    - refuse_*: do not add (explicit refusal; we do not store refusals, we simply omit).
    - merge_with_existing: if True, merge with current registry; else replace.
    No auto-grant: only explicitly approved items are added.
    """
    root = _repo_root(repo_root)
    reg_path = get_registry_path(root)
    existing = load_approval_registry(root) if reg_path.exists() and reg_path.is_file() else None

    paths = list(existing.approved_paths) if (merge_with_existing and existing) else []
    apps = list(existing.approved_apps) if (merge_with_existing and existing) else []
    scopes = list(existing.approved_action_scopes) if (merge_with_existing and existing) else []

    for p in approve_paths or []:
        p = (p or "").strip()
        if p and p not in paths:
            paths.append(p)
    for p in refuse_paths or []:
        p = (p or "").strip()
        if p in paths:
            paths.remove(p)

    for a in approve_apps or []:
        a = (a or "").strip()
        if a and a not in apps:
            apps.append(a)
    for a in refuse_apps or []:
        a = (a or "").strip()
        if a in apps:
            apps.remove(a)

    for s in approve_scopes or []:
        if not isinstance(s, dict):
            continue
        adapter_id = str(s.get("adapter_id", "")).strip()
        action_id = str(s.get("action_id", "")).strip()
        if not adapter_id or not action_id:
            continue
        entry = {"adapter_id": adapter_id, "action_id": action_id, "executable": True}
        if not any(
            str(x.get("adapter_id")) == adapter_id and str(x.get("action_id")) == action_id
            for x in scopes
        ):
            scopes.append(entry)
    for s in refuse_scopes or []:
        if not isinstance(s, dict):
            continue
        adapter_id = str(s.get("adapter_id", "")).strip()
        action_id = str(s.get("action_id", "")).strip()
        scopes = [x for x in scopes if not (str(x.get("adapter_id")) == adapter_id and str(x.get("action_id")) == action_id)]

    registry = ApprovalRegistry(
        approved_paths=paths,
        approved_apps=apps,
        approved_action_scopes=scopes,
    )
    return save_approval_registry(registry, root)
