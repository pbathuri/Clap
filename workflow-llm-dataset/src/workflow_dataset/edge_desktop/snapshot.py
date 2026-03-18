"""
Single JSON snapshot for Edge Operator Desktop prototype.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def build_edge_desktop_snapshot(repo_root: Path | str | None = None) -> dict[str, Any]:
    root = _root(repo_root)
    out: dict[str, Any] = {
        "generated_at": utc_now_iso(),
        "repo_root": str(root),
        "sources_ok": [],
        "errors": {},
        "readiness": None,
        "bootstrap_last": None,
        "onboarding_ready": None,
        "workspace_home": None,
        "workspace_home_text": None,
        "day_status": None,
        "day_status_text": None,
        "guidance_next_action": None,
        "operator_summary": None,
        "inbox": [],
    }

    try:
        from workflow_dataset.demo_usb import build_readiness_report
        from workflow_dataset.demo_usb.bundle_root import resolve_demo_bundle_root

        out["readiness"] = build_readiness_report(resolve_demo_bundle_root(None)).to_dict()
        out["sources_ok"].append("readiness")
    except Exception as e:
        out["errors"]["readiness"] = str(e)[:500]

    try:
        host_base = Path.home() / ".workflow-demo-host"
        if host_base.is_dir():
            best: tuple[float, Path] | None = None
            for sub in host_base.iterdir():
                p = sub / ".workflow-demo" / "last_bootstrap.json"
                if p.is_file():
                    m = p.stat().st_mtime
                    if best is None or m > best[0]:
                        best = (m, p)
            if best:
                out["bootstrap_last"] = {
                    "path": str(best[1]),
                    "record": json.loads(best[1].read_text(encoding="utf-8")),
                }
                out["sources_ok"].append("bootstrap_last")
    except Exception as e:
        out["errors"]["bootstrap_last"] = str(e)[:500]

    try:
        from workflow_dataset.demo_onboarding import (
            build_ready_to_assist_state,
            build_completion_state,
        )

        st = build_ready_to_assist_state(root)
        comp = build_completion_state(root)
        out["onboarding_ready"] = {
            "ready_to_assist": st.to_dict(),
            "completion": comp.to_dict(),
        }
        out["sources_ok"].append("onboarding_ready")
    except Exception as e:
        out["errors"]["onboarding_ready"] = str(e)[:500]

    try:
        from workflow_dataset.workspace.state import build_workspace_home_snapshot

        out["workspace_home"] = build_workspace_home_snapshot(root).to_dict()
        out["sources_ok"].append("workspace_home")
    except Exception as e:
        out["errors"]["workspace_home"] = str(e)[:500]

    try:
        from workflow_dataset.workspace.cli import cmd_home

        out["workspace_home_text"] = cmd_home(
            repo_root=root, preset_id=None, profile_id="calm_default"
        )
        out["sources_ok"].append("workspace_home_text")
    except Exception as e:
        out["errors"]["workspace_home_text"] = str(e)[:500]

    try:
        from workflow_dataset.workday.surface import build_daily_operating_surface

        out["day_status"] = build_daily_operating_surface(root).to_dict()
        out["sources_ok"].append("day_status")
    except Exception as e:
        out["errors"]["day_status"] = str(e)[:500]

    try:
        from workflow_dataset.workday.cli import cmd_day_status

        out["day_status_text"] = cmd_day_status(root)
        out["sources_ok"].append("day_status_text")
    except Exception as e:
        out["errors"]["day_status_text"] = str(e)[:500]

    try:
        from workflow_dataset.quality_guidance.guidance import next_best_action_guidance

        g = next_best_action_guidance(root)
        if g:
            out["guidance_next_action"] = g.to_dict()
        out["sources_ok"].append("guidance_next_action")
    except Exception as e:
        out["errors"]["guidance_next_action"] = str(e)[:500]

    try:
        from workflow_dataset.quality_guidance.operator_summary import build_operator_summary

        out["operator_summary"] = build_operator_summary(root).to_dict()
        out["sources_ok"].append("operator_summary")
    except Exception as e:
        out["errors"]["operator_summary"] = str(e)[:500]

    try:
        from workflow_dataset.review_studio.inbox import build_inbox

        items = build_inbox(repo_root=root, status="pending", limit=25)
        out["inbox"] = [
            {
                "item_id": i.item_id,
                "kind": i.kind,
                "priority": i.priority,
                "summary": (i.summary or "")[:120],
            }
            for i in items
        ]
        out["sources_ok"].append("inbox")
    except Exception as e:
        out["errors"]["inbox"] = str(e)[:500]

    try:
        from workflow_dataset.investor_mission_control import build_mission_control_investor_home

        ih = build_mission_control_investor_home(root)
        out["investor_mission_control_home"] = ih.to_dict()
        out["sources_ok"].append("investor_mission_control_home")
    except Exception as e:
        out["errors"]["investor_mission_control_home"] = str(e)[:500]

    return out
