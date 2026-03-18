"""
A3: Workspace rerun, diff, and provenance timeline.
Local-only; no mutation of existing workspace dirs.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any

from workflow_dataset.release.reporting_workspaces import (
    get_workspace_inventory,
    list_reporting_workspaces,
)


def infer_rerun_args(manifest: dict[str, Any]) -> dict[str, Any]:
    """
    Infer release-demo args from a workspace manifest for rerun.
    Returns dict with context_file, input_pack, retrieval, workflow.
    Does not include context_text (not stored in manifest).
    """
    out: dict[str, Any] = {
        "context_file": "",
        "input_pack": "",
        "intake": "",
        "retrieval": False,
        "workflow": manifest.get("workflow") or "ops_reporting_workspace",
    }
    sources = manifest.get("input_sources_used") or []
    for s in sources:
        typ = s.get("type") or ""
        path_or_name = s.get("path_or_name") or s.get("path") or ""
        if typ == "context_file" and path_or_name and path_or_name != "(inline)":
            out["context_file"] = path_or_name
            break
    for s in sources:
        typ = s.get("type") or ""
        if typ in ("input_pack_file", "input_pack_snapshot"):
            out["input_pack"] = s.get("pack") or s.get("path_or_name") or ""
            if out["input_pack"] and "/" in str(out["input_pack"]):
                out["input_pack"] = str(out["input_pack"]).split("/")[0]
            if out["input_pack"]:
                break
    if not out["input_pack"]:
        for s in sources:
            if (s.get("type") or "").startswith("input_pack"):
                out["input_pack"] = s.get("pack") or ""
                break
    for s in sources:
        if (s.get("type") or "") == "intake":
            out["intake"] = s.get("path_or_name") or manifest.get("intake_name") or ""
            break
    if not out["intake"]:
        out["intake"] = manifest.get("intake_name") or ""
    out["retrieval"] = bool(manifest.get("retrieval_used"))
    return out


def diff_workspaces(
    path_a: str | Path,
    path_b: str | Path,
    include_artifact_diffs: bool = True,
    max_diff_lines: int = 200,
) -> dict[str, Any]:
    """
    Compare two workspace runs: inventory, manifest metadata, and optional artifact deltas.
    Does not mutate either path. Local-only.
    """
    pa = Path(path_a).resolve()
    pb = Path(path_b).resolve()
    inv_a = get_workspace_inventory(pa)
    inv_b = get_workspace_inventory(pb)

    result: dict[str, Any] = {
        "path_a": str(pa),
        "path_b": str(pb),
        "inventory_diff": {},
        "manifest_metadata_diff": {},
        "artifact_deltas": {},
    }

    arts_a = set(inv_a.get("artifacts") or []) if inv_a else set()
    arts_b = set(inv_b.get("artifacts") or []) if inv_b else set()
    result["inventory_diff"] = {
        "only_in_a": sorted(arts_a - arts_b),
        "only_in_b": sorted(arts_b - arts_a),
        "common": sorted(arts_a & arts_b),
        "all_a": sorted(arts_a),
        "all_b": sorted(arts_b),
    }

    man_a = (inv_a or {}).get("manifest") or {}
    man_b = (inv_b or {}).get("manifest") or {}
    meta_keys = (
        "workflow", "timestamp", "grounding", "retrieval_used",
        "explicit_context_used", "context_file_used", "input_pack_used",
        "retrieval_relevance", "retrieval_relevance_weak_or_mixed",
    )
    md: dict[str, dict[str, Any]] = {}
    for k in meta_keys:
        va = man_a.get(k)
        vb = man_b.get(k)
        if va != vb:
            md[k] = {"a": va, "b": vb}
    result["manifest_metadata_diff"] = md

    if not include_artifact_diffs:
        return result

    for name in result["inventory_diff"]["common"]:
        fa = pa / name
        fb = pb / name
        if not fa.is_file() or not fb.is_file():
            continue
        try:
            ta = fa.read_text(encoding="utf-8", errors="replace").splitlines()
            tb = fb.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            result["artifact_deltas"][name] = {"error": "read failed"}
            continue
        lines = list(difflib.unified_diff(ta, tb, fromfile=f"a/{name}", tofile=f"b/{name}", lineterm="\n"))
        total_lines = len(lines)
        if total_lines > max_diff_lines:
            lines = lines[:max_diff_lines] + [f"... ({total_lines - max_diff_lines} more lines)\n"]
        result["artifact_deltas"][name] = {"diff_lines": total_lines, "preview": "".join(lines[:80]) if lines else ""}

    return result


def workspace_timeline(
    root: str | Path,
    workflow: str | None = "ops_reporting_workspace",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Return a simple provenance timeline: recent runs with key metadata (timestamp, run_id, grounding, artifact count).
    Sorted newest first. Local-only.
    """
    root = Path(root).resolve()
    items = list_reporting_workspaces(root, limit=limit * 2)
    if workflow:
        items = [i for i in items if (i.get("workflow") or "") == workflow]
    items = items[:limit]
    timeline: list[dict[str, Any]] = []
    for inv in items:
        manifest = inv.get("manifest") or {}
        timeline.append({
            "run_id": inv.get("run_id") or Path(inv.get("workspace_path", "")).name,
            "workspace_path": inv.get("workspace_path"),
            "workflow": inv.get("workflow"),
            "timestamp": inv.get("timestamp") or manifest.get("timestamp"),
            "grounding": inv.get("grounding") or manifest.get("grounding"),
            "artifact_count": len(inv.get("artifacts") or []),
            "retrieval_used": manifest.get("retrieval_used"),
            "input_pack_used": manifest.get("input_pack_used"),
        })
    return timeline
