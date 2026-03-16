"""
M21U: Read-only dashboard data for the Local Reporting Command Center.
Aggregates pilot readiness, recent workspaces, review/package state, cohort, next actions.
All sources are local paths; no cloud or writes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.release.reporting_workspaces import get_workspace_inventory, list_reporting_workspaces
from workflow_dataset.release.review_state import get_approved_artifacts, load_review_state


def get_dashboard_data(
    repo_root: Path | None = None,
    pilot_dir: Path | str = "data/local/pilot",
    workspaces_root: Path | str = "data/local/workspaces",
    packages_root: Path | str = "data/local/packages",
    review_root: Path | str = "data/local/review",
    limit_workspaces: int = 10,
    config_path: str = "configs/settings.yaml",
    release_config_path: str = "configs/release_narrow.yaml",
    workflow_filter: str | None = None,
) -> dict[str, Any]:
    """
    Compose read-only dashboard state from local sources.
    When workflow_filter is set (e.g. weekly_status, ops_reporting_workspace), workspaces
    and counts are limited to that workflow. Returns: readiness, recent_workspaces,
    review_package, cohort, next_actions, local_sources, workflow_filter (when active).
    """
    if repo_root is None:
        from workflow_dataset.path_utils import get_repo_root
        repo_root = Path(get_repo_root())
    else:
        repo_root = Path(repo_root)
    pilot_path = repo_root / pilot_dir if not Path(pilot_dir).is_absolute() else Path(pilot_dir)
    ws_root = repo_root / workspaces_root if not Path(workspaces_root).is_absolute() else Path(workspaces_root)
    pkg_root = repo_root / packages_root if not Path(packages_root).is_absolute() else Path(packages_root)
    review_root_path = repo_root / review_root if not Path(review_root).is_absolute() else Path(review_root)
    staging_dir = repo_root / "data/local/staging"

    # Local source/state map: exact paths used (provenance)
    local_sources: dict[str, Any] = {
        "repo_root": str(repo_root.resolve()),
        "workspaces_root": str(ws_root.resolve()),
        "pilot_dir": str(pilot_path.resolve()),
        "packages_root": str(pkg_root.resolve()),
        "review_root": str(review_root_path.resolve()),
        "staging_dir": str(staging_dir.resolve()),
    }
    if (pilot_path / "pilot_readiness_report.md").exists():
        local_sources["pilot_readiness_report"] = str((pilot_path / "pilot_readiness_report.md").resolve())
    release_report = repo_root / "data/local/release/release_readiness_report.md"
    if release_report.exists():
        local_sources["release_readiness_report"] = str(release_report.resolve())

    out: dict[str, Any] = {
        "readiness": _read_readiness(config_path, release_config_path),
        "recent_workspaces": [],
        "review_package": {"unreviewed_count": 0, "package_pending_count": 0, "latest_package_path": None, "packages_count": 0},
        "cohort": {"cohort_reports": [], "aggregate_path": None, "recommendation": None, "sessions_count": 0, "avg_usefulness": None},
        "cohort_summary": {"active_cohort_name": None, "sessions_count": 0, "avg_usefulness": None, "recent_recommendation": None},
        "alerts": {"review_pending": False, "review_pending_count": 0, "package_ready": False, "staged_apply_plan_available": False, "benchmark_regression_detected": False},
        "next_actions": [],
        "local_sources": local_sources,
        "workflow_filter": workflow_filter,
    }

    workspaces = list_reporting_workspaces(ws_root, limit=limit_workspaces)
    if workflow_filter:
        workspaces = [w for w in workspaces if w.get("workflow") == workflow_filter]
    latest_package_path = None
    unreviewed_count = 0
    package_pending_count = 0

    for inv in workspaces:
        wp = inv.get("workspace_path")
        if not wp:
            continue
        ws_path = Path(wp)
        state = load_review_state(ws_path, repo_root=repo_root)
        approved = get_approved_artifacts(ws_path, repo_root=repo_root)
        has_package = bool(state.get("last_package_path"))
        artifacts_count = len(inv.get("artifacts") or [])
        has_any_review = bool(state.get("artifacts"))
        if not has_any_review and artifacts_count > 0:
            unreviewed_count += 1
        elif approved and not has_package:
            package_pending_count += 1
        if state.get("last_package_path"):
            latest_package_path = state["last_package_path"]
        out["recent_workspaces"].append({
            "workspace_path": wp,
            "workflow": inv.get("workflow", "?"),
            "timestamp": inv.get("timestamp"),
            "grounding": inv.get("grounding"),
            "artifact_count": artifacts_count,
            "approved_count": len(approved),
            "has_package": has_package,
            "status": "package_ready" if has_package else ("package_pending" if approved else "review_pending"),
        })

    out["review_package"]["unreviewed_count"] = unreviewed_count
    out["review_package"]["package_pending_count"] = package_pending_count
    out["review_package"]["latest_package_path"] = latest_package_path
    if pkg_root.exists():
        out["review_package"]["packages_count"] = len([d for d in pkg_root.iterdir() if d.is_dir()])

    try:
        from workflow_dataset.release.staging_board import load_staging_board
        board = load_staging_board(repo_root)
        staged = board.get("items") or []
        out["staging"] = {
            "staged_count": len(staged),
            "staged_items": [{"staged_id": i.get("staged_id"), "source_type": i.get("source_type"), "workflow": i.get("workflow")} for i in staged[:5]],
            "last_apply_plan_preview_path": board.get("last_apply_plan_preview_path"),
        }
    except Exception:
        out["staging"] = {"staged_count": 0, "staged_items": [], "last_apply_plan_preview_path": None}

    cohort_reports = []
    if pilot_path.exists():
        for p in sorted(pilot_path.glob("cohort_*_report.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            cohort_reports.append({"path": str(p), "name": p.stem.replace("cohort_", "").replace("_report", "")})
        agg_json = pilot_path / "aggregate_report.json"
        if agg_json.exists():
            out["cohort"]["aggregate_path"] = str(agg_json)
            try:
                data = json.loads(agg_json.read_text(encoding="utf-8"))
                out["cohort"]["sessions_count"] = data.get("sessions_count", 0)
                out["cohort"]["avg_usefulness"] = data.get("avg_usefulness")
                if data.get("graduation"):
                    out["cohort"]["recommendation"] = data["graduation"].get("recommendation") or data["graduation"].get("summary", "")
                elif data.get("recent_cohort") and data["recent_cohort"].get("cohort_outcome"):
                    out["cohort"]["recommendation"] = data["recent_cohort"]["cohort_outcome"].get("outcome", "")
            except Exception:
                pass
        if cohort_reports:
            out["cohort"]["cohort_reports"] = cohort_reports[:10]
            try:
                first = json.loads(Path(cohort_reports[0]["path"]).read_text(encoding="utf-8"))
                out["cohort"]["recommendation"] = (first.get("cohort_outcome") or {}).get("outcome") or out["cohort"].get("recommendation")
            except Exception:
                pass

    # C3: Cohort-aware summary (active cohort + recent recommendation)
    if cohort_reports:
        out["cohort_summary"]["active_cohort_name"] = cohort_reports[0]["name"]
    out["cohort_summary"]["sessions_count"] = out["cohort"]["sessions_count"]
    out["cohort_summary"]["avg_usefulness"] = out["cohort"]["avg_usefulness"]
    out["cohort_summary"]["recent_recommendation"] = out["cohort"].get("recommendation")
    if not out["cohort_summary"]["active_cohort_name"] and out["cohort"].get("aggregate_path"):
        out["cohort_summary"]["active_cohort_name"] = "aggregate"

    # C3: Lightweight alerts (read-only)
    out["alerts"]["review_pending"] = unreviewed_count > 0
    out["alerts"]["review_pending_count"] = unreviewed_count
    out["alerts"]["package_ready"] = any(w.get("status") == "package_ready" for w in out["recent_workspaces"])
    out["alerts"]["staged_apply_plan_available"] = bool(out.get("staging", {}).get("last_apply_plan_preview_path"))
    try:
        from workflow_dataset.eval.board import compare_latest_vs_best
        eval_root = repo_root / "data/local/eval"
        comp = compare_latest_vs_best(root=eval_root)
        out["alerts"]["benchmark_regression_detected"] = bool(comp.get("regressions"))
    except Exception:
        pass

    next_actions = []
    if out["readiness"].get("ready"):
        next_actions.append({"label": "Run workflow", "command": "workflow-dataset release demo --workflow ops_reporting_workspace --context-file <notes> --save-artifact"})
    if workspaces:
        latest = workspaces[0]
        wp = latest.get("workspace_path", "")
        short = Path(wp).name if wp else ""
        parent = Path(wp).parent.name if wp else ""
        ref = f"{parent}/{short}" if parent and short else wp
        next_actions.append({"label": "Inspect latest workspace", "command": f"workflow-dataset review show-workspace {ref}"})
        artifacts = latest.get("artifacts") or []
        first_artifact = artifacts[0] if artifacts else "<artifact_name>"
        if unreviewed_count > 0:
            next_actions.append({"label": "Review / approve artifacts", "command": f"workflow-dataset review approve-artifact {ref} --artifact {first_artifact}"})
        if package_pending_count > 0:
            next_actions.append({"label": "Build package", "command": f"workflow-dataset review build-package {ref}"})
    agg_md = pilot_path / "aggregate_report.md"
    if out["cohort"].get("aggregate_path"):
        next_actions.append({"label": "View aggregate report", "command": f"workflow-dataset pilot aggregate && cat {agg_md.resolve()}"})
    if cohort_reports:
        cohort_md = (Path(cohort_reports[0]["path"]).resolve().with_suffix(".md"))
        next_actions.append({"label": "View cohort report", "command": f"cat {cohort_md}"})
    if latest_package_path:
        next_actions.append({"label": "Apply-plan preview (package)", "command": f"workflow-dataset assist apply-plan {latest_package_path} <target_path>"})
    staging = out.get("staging") or {}
    if staging.get("staged_count", 0) > 0:
        next_actions.append({"label": "Build apply-plan from staging", "command": "workflow-dataset review build-apply-plan <target_path>"})
        if staging.get("last_apply_plan_preview_path"):
            next_actions.append({"label": "View last apply-plan preview", "command": f"cat {staging['last_apply_plan_preview_path']}"})
    out["next_actions"] = next_actions[:8]

    # C4: Action runner stubs / operator macros (command only, no execution here)
    action_macros: list[dict[str, Any]] = []
    if workspaces:
        latest = workspaces[0]
        wp = latest.get("workspace_path", "")
        short = Path(wp).name if wp else ""
        parent = Path(wp).parent.name if wp else ""
        ref = f"{parent}/{short}" if parent and short else wp
        action_macros.append({
            "id": "inspect-workspace",
            "label": "Inspect latest workspace",
            "command": f"workflow-dataset review show-workspace {ref}",
        })
    # Latest package: from review state or newest dir in packages_root
    pkg_path = latest_package_path
    if not pkg_path and pkg_root.exists():
        dirs = sorted([d for d in pkg_root.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
        if dirs:
            pkg_path = str(dirs[0].resolve())
    if pkg_path:
        action_macros.append({
            "id": "open-package",
            "label": "Open latest package",
            "command": "workflow-dataset dashboard package",
        })
    if cohort_reports:
        cohort_md = (Path(cohort_reports[0]["path"]).resolve().with_suffix(".md"))
        if cohort_md.exists():
            action_macros.append({
                "id": "open-cohort-report",
                "label": "Open latest cohort report",
                "command": f"cat {cohort_md}",
            })
        else:
            action_macros.append({
                "id": "open-cohort-report",
                "label": "Open latest cohort report",
                "command": f"cat {Path(cohort_reports[0]['path']).resolve()}",
            })
    action_macros.append({
        "id": "staging-board",
        "label": "Show staging board",
        "command": "workflow-dataset review staging-board",
    })
    action_macros.append({
        "id": "benchmark-board",
        "label": "Show benchmark board",
        "command": "workflow-dataset eval board",
    })
    out["action_macros"] = action_macros

    return out


def _read_readiness(config_path: str, release_config_path: str) -> dict[str, Any]:
    """Read pilot status for readiness panel."""
    try:
        from workflow_dataset.pilot.health import pilot_status_dict
        status = pilot_status_dict(config_path=config_path, release_config_path=release_config_path)
        return {
            "ready": status.get("ready", False),
            "safe_to_demo": status.get("safe_to_demo", False),
            "adapter_ok": status.get("adapter_ok", False),
            "degraded": status.get("degraded", False),
            "graph_ok": status.get("graph_ok", False),
            "blocking": status.get("blocking") or [],
            "warnings": status.get("warnings") or [],
            "latest_run_dir": status.get("latest_run_dir") or "",
        }
    except Exception:
        return {"ready": False, "safe_to_demo": False, "adapter_ok": False, "degraded": True, "graph_ok": False, "blocking": [], "warnings": [], "latest_run_dir": ""}


# C2: Drill-down data for workspace, package, cohort, apply-plan (read-only)
def get_dashboard_drilldown(
    repo_root: Path | None = None,
    drill: str = "workspace",
    workspaces_root: Path | str = "data/local/workspaces",
    packages_root: Path | str = "data/local/packages",
    pilot_dir: Path | str = "data/local/pilot",
    workflow_filter: str | None = None,
) -> dict[str, Any]:
    """
    Return read-only drill-down payload for one of: workspace, package, cohort, apply_plan.
    Keys: drill_type, path, ref (for workspace: workflow/run_id), payload (detail dict).
    """
    if repo_root is None:
        from workflow_dataset.path_utils import get_repo_root
        repo_root = Path(get_repo_root())
    else:
        repo_root = Path(repo_root)
    pilot_path = repo_root / pilot_dir if not Path(pilot_dir).is_absolute() else Path(pilot_dir)
    ws_root = repo_root / workspaces_root if not Path(workspaces_root).is_absolute() else Path(workspaces_root)
    pkg_root = repo_root / packages_root if not Path(packages_root).is_absolute() else Path(packages_root)

    out: dict[str, Any] = {"drill_type": drill, "path": None, "ref": None, "payload": {}}

    if drill == "workspace":
        workspaces = list_reporting_workspaces(ws_root, limit=50)
        if workflow_filter:
            workspaces = [w for w in workspaces if w.get("workflow") == workflow_filter]
        if not workspaces:
            return out
        inv = workspaces[0]
        wp = inv.get("workspace_path", "")
        out["path"] = wp
        short = Path(wp).name if wp else ""
        parent = Path(wp).parent.name if wp else ""
        out["ref"] = f"{parent}/{short}" if parent and short else wp
        state = load_review_state(Path(wp), repo_root=repo_root)
        approved = get_approved_artifacts(Path(wp), repo_root=repo_root)
        out["payload"] = {
            "workflow": inv.get("workflow"),
            "run_id": inv.get("run_id"),
            "timestamp": inv.get("timestamp"),
            "grounding": inv.get("grounding"),
            "artifacts": inv.get("artifacts") or [],
            "approved_artifacts": approved,
            "review_state": state.get("artifacts") or {},
            "last_package_path": state.get("last_package_path"),
            "inspect_command": f"workflow-dataset review show-workspace {out['ref']}",
            "build_package_command": f"workflow-dataset review build-package {out['ref']}",
        }
        return out

    if drill == "package":
        if not pkg_root.exists():
            return out
        dirs = sorted([d for d in pkg_root.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
        if not dirs:
            return out
        pkg_dir = dirs[0]
        out["path"] = str(pkg_dir.resolve())
        manifest_path = pkg_dir / "package_manifest.json"
        payload: dict[str, Any] = {"package_dir": out["path"], "files": [f.name for f in pkg_dir.iterdir() if f.is_file()]}
        if manifest_path.exists():
            try:
                payload["manifest"] = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                payload["manifest"] = None
        out["payload"] = payload
        out["ref"] = pkg_dir.name
        out["payload"]["open_command"] = f"cat {out['path']}/package_manifest.json"
        return out

    if drill == "cohort":
        if not pilot_path.exists():
            return out
        cohort_jsons = sorted(pilot_path.glob("cohort_*_report.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not cohort_jsons:
            agg_md = pilot_path / "aggregate_report.md"
            if agg_md.exists():
                out["path"] = str(agg_md.resolve())
                out["payload"] = {"type": "aggregate", "excerpt": _excerpt_file(agg_md, 800)}
                out["payload"]["open_command"] = f"cat {out['path']}"
            return out
        first = cohort_jsons[0]
        md_path = first.with_suffix(".md")
        out["path"] = str(md_path.resolve()) if md_path.exists() else str(first.resolve())
        out["payload"] = {"name": first.stem.replace("cohort_", "").replace("_report", ""), "excerpt": _excerpt_file(md_path if md_path.exists() else first, 800)}
        out["payload"]["open_command"] = f"cat {out['path']}"
        return out

    if drill == "apply_plan":
        try:
            from workflow_dataset.release.staging_board import load_staging_board, get_last_apply_plan_preview_path
            path = get_last_apply_plan_preview_path(repo_root)
            if not path or not Path(path).exists():
                return out
            out["path"] = path
            out["payload"] = {"excerpt": _excerpt_file(Path(path), 1200), "open_command": f"cat {path}"}
            board = load_staging_board(repo_root)
            out["payload"]["staged_count"] = len(board.get("items") or [])
        except Exception:
            pass
        return out

    return out


def _excerpt_file(path: Path, max_chars: int = 600) -> str:
    """Read file and return first max_chars, with newlines allowed."""
    if not path.exists() or not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars] + ("…" if len(text) > max_chars else "")
    except Exception:
        return ""
