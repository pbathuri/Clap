"""
M21X: Transparent local scoring — relevance, completeness, specificity, actionability, honesty.
No model-judge dependence; heuristic only unless operator_rating attached.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCORE_DIMENSIONS = (
    "relevance",
    "completeness",
    "specificity",
    "actionability",
    "blocker_quality",
    "risk_quality",
    "next_step_specificity",
    "stakeholder_readability",
    "honesty",
)


def score_artifact_heuristic(text: str, workflow: str) -> dict[str, float]:
    """Score artifact text on dimensions. Returns 0..1 per dimension. Transparent local heuristics."""
    t = (text or "").lower()
    scores: dict[str, float] = {}
    # Relevance: has summary/topic content
    scores["relevance"] = 0.3 + (0.4 if "summary" in t or "status" in t else 0) + (0.3 if len(t) > 80 else 0)
    scores["relevance"] = min(1.0, scores["relevance"])
    # Completeness: sections present
    scores["completeness"] = 0.2
    for tag in ("summary", "wins", "blockers", "risks", "next steps"):
        if tag in t:
            scores["completeness"] += 0.15
    scores["completeness"] = min(1.0, scores["completeness"])
    # Specificity
    scores["specificity"] = 0.3 + (0.35 if re.search(r"\d+\.", t) or "follow" in t or "unblock" in t else 0) + (0.35 if len(t) > 120 else 0)
    scores["specificity"] = min(1.0, scores["specificity"])
    # Actionability: next steps / actions
    scores["actionability"] = 0.4 if "next step" in t or "action" in t or "follow" in t else 0.2
    if re.search(r"1\.\s*\w+", t):
        scores["actionability"] = min(1.0, scores["actionability"] + 0.4)
    # Blocker quality: explicit blockers
    scores["blocker_quality"] = 0.5 if "blocker" in t else 0.2
    if "blocked by" in t or "blocking" in t:
        scores["blocker_quality"] = min(1.0, scores["blocker_quality"] + 0.3)
    # Risk quality
    scores["risk_quality"] = 0.5 if "risk" in t else 0.2
    if "schedule" in t or "dependency" in t:
        scores["risk_quality"] = min(1.0, scores["risk_quality"] + 0.3)
    # Next step specificity
    scores["next_step_specificity"] = scores["specificity"] * 0.9
    # Stakeholder readability
    scores["stakeholder_readability"] = 0.4 + (0.3 if len(t) < 800 else 0) + (0.3 if not re.search(r"[A-Z]{5,}", t) else 0)
    scores["stakeholder_readability"] = min(1.0, scores["stakeholder_readability"])
    # Honesty: mixed evidence / caveats
    scores["honesty"] = 0.5 + (0.2 if "risk" in t or "blocker" in t else 0) + (0.2 if "if " in t or "depends" in t else 0)
    scores["honesty"] = min(1.0, scores["honesty"])
    for d in SCORE_DIMENSIONS:
        if d not in scores:
            scores[d] = 0.3
        scores[d] = round(scores[d], 3)
    return scores


def score_run_case(case_dir: Path, case_spec: dict[str, Any]) -> dict[str, Any]:
    """Score one case directory: find artifact(s), run heuristic, attach operator_rating if present."""
    artifacts: dict[str, dict[str, float]] = {}
    workflow = case_spec.get("workflow", "weekly_status")
    for f in case_dir.iterdir():
        if f.is_file() and f.suffix.lower() in (".md", ".txt"):
            text = f.read_text(encoding="utf-8", errors="replace")
            artifacts[f.name] = score_artifact_heuristic(text, workflow)
    operator_rating = None
    rating_path = case_dir / "operator_rating.json"
    if rating_path.exists():
        try:
            operator_rating = json.loads(rating_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"artifacts": artifacts, "operator_rating": operator_rating}


def score_run(run_path: Path) -> dict[str, Any]:
    """Score a run: load manifest, score each case, write scores into manifest and return updated manifest."""
    run_path = Path(run_path)
    manifest_path = run_path / "run_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    cases = manifest.get("cases") or []
    for c in cases:
        out_dir = c.get("output_dir")
        if not out_dir:
            continue
        case_dir = Path(out_dir)
        if not case_dir.exists():
            continue
        scored = score_run_case(case_dir, c)
        c["scores"] = scored
    manifest["cases"] = cases
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def save_operator_rating(
    run_id: str,
    case_id: str,
    rating: dict[str, Any],
    root: Path | str | None = None,
) -> Path:
    """Save operator rating for a case. Writes operator_rating.json in case output dir."""
    from workflow_dataset.eval.board import get_run
    from workflow_dataset.eval.config import get_runs_dir
    manifest = get_run(run_id, root)
    run_dir = get_runs_dir(root) / run_id
    if manifest:
        run_dir = Path(manifest.get("run_path", run_dir))
        for c in manifest.get("cases") or []:
            if c.get("case_id") == case_id:
                case_dir = Path(c.get("output_dir", run_dir / case_id))
                case_dir.mkdir(parents=True, exist_ok=True)
                path = case_dir / "operator_rating.json"
                path.write_text(json.dumps(rating, indent=2), encoding="utf-8")
                return path
    if not run_dir.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    case_dir = run_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    path = case_dir / "operator_rating.json"
    path.write_text(json.dumps(rating, indent=2), encoding="utf-8")
    return path
