"""
M21T-F2: Compare two package versions (artifact inventory, manifest, changed/added/removed files).
Local-only; read-only. Operator-friendly output.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any

from workflow_dataset.release.package_revision import load_revision_meta

# Non-artifact files in a package dir (we compare artifact files only for content)
PACKAGE_META_FILES = frozenset({
    "package_manifest.json",
    "approved_summary.md",
    "handoff_readme.md",
    "revision_meta.json",
})


def load_package_manifest(package_path: str | Path) -> dict[str, Any] | None:
    """Load package_manifest.json from package dir. Returns None if missing or invalid."""
    p = Path(package_path).resolve()
    path = p / "package_manifest.json"
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_package_artifact_files(package_path: str | Path) -> list[str]:
    """
    Return list of artifact file names in package dir (files that are not meta files).
    Sorted for stable diff.
    """
    p = Path(package_path).resolve()
    if not p.exists() or not p.is_dir():
        return []
    return sorted(
        f.name for f in p.iterdir()
        if f.is_file() and f.name not in PACKAGE_META_FILES
    )


def compare_packages(
    path_a: str | Path,
    path_b: str | Path,
    include_content_diff: bool = True,
    max_diff_lines: int = 200,
) -> dict[str, Any]:
    """
    Compare two package dirs: manifest diff, artifact list diff (only_in_a, only_in_b, common),
    and optionally content diff for common artifact files.
    Does not mutate either path. Returns dict with path_a, path_b, manifest_diff, inventory_diff,
    files_only_in_a, files_only_in_b, files_common, artifact_deltas (if include_content_diff).
    """
    pa = Path(path_a).resolve()
    pb = Path(path_b).resolve()
    manifest_a = load_package_manifest(pa)
    manifest_b = load_package_manifest(pb)
    files_a = set(get_package_artifact_files(pa))
    files_b = set(get_package_artifact_files(pb))

    only_a = sorted(files_a - files_b)
    only_b = sorted(files_b - files_a)
    common = sorted(files_a & files_b)

    manifest_diff: dict[str, dict[str, Any]] = {}
    if manifest_a is not None and manifest_b is not None:
        all_keys = sorted(set(manifest_a.keys()) | set(manifest_b.keys()))
        for k in all_keys:
            va = manifest_a.get(k)
            vb = manifest_b.get(k)
            if va != vb:
                manifest_diff[k] = {"a": va, "b": vb}

    rev_a = load_revision_meta(pa)
    rev_b = load_revision_meta(pb)
    review_state_diff: dict[str, dict[str, Any]] = {}
    if rev_a.get("status") != rev_b.get("status"):
        review_state_diff["status"] = {"a": rev_a.get("status"), "b": rev_b.get("status")}
    if rev_a.get("supersedes") != rev_b.get("supersedes"):
        review_state_diff["supersedes"] = {"a": rev_a.get("supersedes"), "b": rev_b.get("supersedes")}
    if rev_a.get("superseded_by") != rev_b.get("superseded_by"):
        review_state_diff["superseded_by"] = {"a": rev_a.get("superseded_by"), "b": rev_b.get("superseded_by")}

    result: dict[str, Any] = {
        "path_a": str(pa),
        "path_b": str(pb),
        "name_a": pa.name,
        "name_b": pb.name,
        "manifest_a": manifest_a,
        "manifest_b": manifest_b,
        "manifest_diff": manifest_diff,
        "inventory_diff": {
            "only_in_a": only_a,
            "only_in_b": only_b,
            "common": common,
        },
        "files_only_in_a": only_a,
        "files_only_in_b": only_b,
        "files_common": common,
        "review_state_diff": review_state_diff,
        "artifact_deltas": {},
    }

    if not include_content_diff:
        return result

    for name in common:
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
        lines = list(difflib.unified_diff(
            ta, tb,
            fromfile=f"a/{name}",
            tofile=f"b/{name}",
            lineterm="\n",
        ))
        total_lines = len(lines)
        if total_lines > max_diff_lines:
            lines = lines[:max_diff_lines] + [f"... ({total_lines - max_diff_lines} more lines)\n"]
        result["artifact_deltas"][name] = {
            "diff_lines": total_lines,
            "preview": "".join(lines[:80]) if lines else "",
        }

    return result


def format_package_compare_for_console(result: dict[str, Any], max_preview_lines: int = 30) -> str:
    """
    Format compare result for console: sections for paths, inventory, manifest diff,
    review-state diff, and optional artifact deltas preview.
    """
    lines: list[str] = []
    lines.append("Package compare")
    lines.append(f"  A: {result.get('path_a', '')}")
    lines.append(f"  B: {result.get('path_b', '')}")
    lines.append("")

    inv = result.get("inventory_diff") or {}
    only_a = inv.get("only_in_a") or []
    only_b = inv.get("only_in_b") or []
    common = inv.get("common") or []
    lines.append("Artifact inventory")
    lines.append(f"  only in A: {only_a or '(none)'}")
    lines.append(f"  only in B: {only_b or '(none)'}")
    lines.append(f"  common: {common or '(none)'}")
    lines.append("")

    mdiff = result.get("manifest_diff") or {}
    if mdiff:
        lines.append("Manifest differences")
        for k, v in mdiff.items():
            lines.append(f"  {k}: A={v.get('a')!r}  B={v.get('b')!r}")
        lines.append("")
    else:
        lines.append("Manifest: no differences")
        lines.append("")

    rdiff = result.get("review_state_diff") or {}
    if rdiff:
        lines.append("Revision / review state differences")
        for k, v in rdiff.items():
            lines.append(f"  {k}: A={v.get('a')!r}  B={v.get('b')!r}")
        lines.append("")

    deltas = result.get("artifact_deltas") or {}
    if deltas:
        lines.append("Artifact content deltas")
        for name, info in deltas.items():
            if "error" in info:
                lines.append(f"  {name}: {info['error']}")
            else:
                lines.append(f"  {name}: {info.get('diff_lines', 0)} diff lines")
                preview = (info.get("preview") or "").strip()
                if preview:
                    for line in preview.split("\n")[:max_preview_lines]:
                        lines.append(f"    {line}")
                    if preview.count("\n") >= max_preview_lines:
                        lines.append("    ...")
        lines.append("")

    return "\n".join(lines)
