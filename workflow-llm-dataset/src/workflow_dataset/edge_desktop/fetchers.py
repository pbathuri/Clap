"""
Isolated fetchers for edge desktop snapshot (M52). Each runs in a worker thread with optional timeout.
Returns (ok_sources: list[str], patch: dict) where patch merges into snapshot (may include errors.*).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

FetcherResult = tuple[list[str], dict[str, Any]]


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def fetch_readiness(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.demo_usb import build_readiness_report
        from workflow_dataset.demo_usb.bundle_root import resolve_demo_bundle_root

        r = build_readiness_report(resolve_demo_bundle_root(None))
        return (["readiness"], {"readiness": r.to_dict()})
    except Exception as e:
        return ([], {"errors": {"readiness": str(e)[:500]}})


def fetch_bootstrap_last(root: Path) -> FetcherResult:
    try:
        host_base = Path.home() / ".workflow-demo-host"
        if not host_base.is_dir():
            return ([], {})
        best: tuple[float, Path] | None = None
        for sub in host_base.iterdir():
            p = sub / ".workflow-demo" / "last_bootstrap.json"
            if p.is_file():
                m = p.stat().st_mtime
                if best is None or m > best[0]:
                    best = (m, p)
        if best:
            return (
                ["bootstrap_last"],
                {
                    "bootstrap_last": {
                        "path": str(best[1]),
                        "record": json.loads(best[1].read_text(encoding="utf-8")),
                    }
                },
            )
    except Exception as e:
        return ([], {"errors": {"bootstrap_last": str(e)[:500]}})
    return ([], {})


def fetch_onboarding_ready(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.demo_onboarding import build_ready_to_assist_state, build_completion_state

        st = build_ready_to_assist_state(root)
        comp = build_completion_state(root)
        return (
            ["onboarding_ready"],
            {
                "onboarding_ready": {
                    "ready_to_assist": st.to_dict(),
                    "completion": comp.to_dict(),
                }
            },
        )
    except Exception as e:
        return ([], {"errors": {"onboarding_ready": str(e)[:500]}})


def fetch_workspace_home(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.workspace.state import build_workspace_home_snapshot

        return (["workspace_home"], {"workspace_home": build_workspace_home_snapshot(root).to_dict()})
    except Exception as e:
        return ([], {"errors": {"workspace_home": str(e)[:500]}})


def fetch_workspace_home_text(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.workspace.cli import cmd_home

        return (["workspace_home_text"], {"workspace_home_text": cmd_home(repo_root=root, preset_id=None, profile_id="calm_default")})
    except Exception as e:
        return ([], {"errors": {"workspace_home_text": str(e)[:500]}})


def fetch_day_status(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.workday.surface import build_daily_operating_surface

        return (["day_status"], {"day_status": build_daily_operating_surface(root).to_dict()})
    except Exception as e:
        return ([], {"errors": {"day_status": str(e)[:500]}})


def fetch_day_status_text(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.workday.cli import cmd_day_status

        return (["day_status_text"], {"day_status_text": cmd_day_status(root)})
    except Exception as e:
        return ([], {"errors": {"day_status_text": str(e)[:500]}})


def fetch_guidance_next_action(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.quality_guidance.guidance import next_best_action_guidance

        g = next_best_action_guidance(root)
        patch: dict[str, Any] = {}
        if g:
            patch["guidance_next_action"] = g.to_dict()
        return (["guidance_next_action"], patch)
    except Exception as e:
        return ([], {"errors": {"guidance_next_action": str(e)[:500]}})


def fetch_operator_summary(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.quality_guidance.operator_summary import build_operator_summary

        return (["operator_summary"], {"operator_summary": build_operator_summary(root).to_dict()})
    except Exception as e:
        return ([], {"errors": {"operator_summary": str(e)[:500]}})


def fetch_inbox(root: Path) -> FetcherResult:
    try:
        from workflow_dataset.review_studio.inbox import build_inbox

        items = build_inbox(repo_root=root, status="pending", limit=25)
        return (
            ["inbox"],
            {
                "inbox": [
                    {
                        "item_id": i.item_id,
                        "kind": i.kind,
                        "priority": i.priority,
                        "summary": (i.summary or "")[:120],
                    }
                    for i in items
                ]
            },
        )
    except Exception as e:
        return ([], {"errors": {"inbox": str(e)[:500]}})


# (id, fetch_fn, include_in_presenter_fast) — in presenter fast path skip slow text fetchers
FETCHERS: list[tuple[str, Callable[[Path], FetcherResult], bool]] = [
    ("readiness", fetch_readiness, True),
    ("bootstrap_last", fetch_bootstrap_last, True),
    ("onboarding_ready", fetch_onboarding_ready, True),
    ("workspace_home", fetch_workspace_home, True),
    ("workspace_home_text", fetch_workspace_home_text, False),
    ("day_status", fetch_day_status, True),
    ("day_status_text", fetch_day_status_text, False),
    ("guidance_next_action", fetch_guidance_next_action, True),
    ("operator_summary", fetch_operator_summary, True),
    ("inbox", fetch_inbox, True),
]


def merge_patches(base: dict[str, Any], patch: dict[str, Any]) -> None:
    for k, v in patch.items():
        if k == "errors":
            base.setdefault("errors", {}).update(v)
        else:
            base[k] = v
