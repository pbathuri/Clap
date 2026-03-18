"""
Build apply plan: source paths from workspace/manifest, target paths, conflicts, overwrite candidates.
Deterministic and dry-run safe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.apply.apply_models import ApplyRequest, ApplyPlan
from workflow_dataset.materialize.manifest_store import load_manifest
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _list_workspace_files(workspace_path: Path, selected_rel: list[str] | None) -> list[str]:
    """List relative paths of files (and dirs to create) under workspace. If selected_rel non-empty, filter to those."""
    if not workspace_path.exists() or not workspace_path.is_dir():
        return []
    out: list[str] = []
    for p in workspace_path.rglob("*"):
        if p.name in ("MANIFEST.json", ".git", "__pycache__"):
            continue
        try:
            rel = str(p.relative_to(workspace_path))
        except ValueError:
            continue
        if selected_rel and rel not in selected_rel:
            # Also include if any selected is a prefix (e.g. selected "a" -> include "a/b")
            if not any(rel.startswith(s + "/") or rel == s for s in selected_rel):
                continue
        out.append(rel)
    return sorted(out)


def build_apply_plan(
    workspace_path: str | Path,
    target_root: str | Path,
    selected_paths: list[str] | None = None,
    allow_overwrite: bool = False,
    dry_run: bool = True,
) -> tuple[ApplyPlan | None, str]:
    """
    Build apply plan from workspace to target. Returns (plan, error_message).
    If dry_run True, no files are modified. Plan lists create/overwrite/skip.
    """
    ws = Path(workspace_path).resolve()
    target = Path(target_root).resolve()
    if not ws.exists() or not ws.is_dir():
        return None, "Workspace path does not exist or is not a directory"
    manifest = load_manifest(ws)
    if manifest:
        rel_paths = list(manifest.output_paths) if manifest.output_paths else _list_workspace_files(ws, selected_paths or None)
    else:
        rel_paths = _list_workspace_files(ws, selected_paths or None)
    if selected_paths:
        rel_paths = [r for r in rel_paths if r in selected_paths or any(r.startswith(s + "/") for s in selected_paths)]
    if not rel_paths:
        return None, "No files to apply (empty workspace or selection)"
    operations: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    overwrite_candidates: list[str] = []
    skipped: list[str] = []
    for rel in rel_paths:
        src = ws / rel
        if not src.exists():
            skipped.append(rel)
            continue
        tgt = target / rel
        if tgt.exists():
            if tgt.is_file() and src.is_file():
                if allow_overwrite:
                    operations.append({"op": "overwrite", "source": rel, "target": str(tgt)})
                    overwrite_candidates.append(rel)
                else:
                    conflicts.append({"source": rel, "target": str(tgt), "reason": "exists"})
                    skipped.append(rel)
            elif tgt.is_dir() and src.is_dir():
                operations.append({"op": "create", "source": rel, "target": str(tgt)})
            else:
                skipped.append(rel)
        else:
            operations.append({"op": "create", "source": rel, "target": str(tgt)})
    if not operations and not allow_overwrite and conflicts:
        plan_id = stable_id("plan", str(ws), str(target), utc_now_iso(), prefix="plan")
        plan = ApplyPlan(
            plan_id=plan_id,
            apply_id="",
            source_paths=rel_paths,
            target_paths=[str(target / r) for r in rel_paths],
            operations=[],
            conflicts=conflicts,
            overwrite_candidates=overwrite_candidates,
            skipped_paths=skipped,
            estimated_file_count=0,
            created_utc=utc_now_iso(),
        )
        return plan, "Conflicts present; run with allow_overwrite or resolve conflicts"
    plan_id = stable_id("plan", str(ws), str(target), utc_now_iso(), prefix="plan")
    plan = ApplyPlan(
        plan_id=plan_id,
        apply_id="",
        source_paths=[o["source"] for o in operations],
        target_paths=[o["target"] for o in operations],
        operations=operations,
        conflicts=conflicts,
        overwrite_candidates=overwrite_candidates,
        skipped_paths=skipped,
        estimated_file_count=len(operations),
        created_utc=utc_now_iso(),
    )
    return plan, ""
