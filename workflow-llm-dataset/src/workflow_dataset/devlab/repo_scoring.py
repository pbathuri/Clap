"""
M21W-F2: Repo usefulness scoring for devlab intake.
Scores: relevance, code/doc clarity, reusable patterns, implementation complexity, operational/legal risk.
Advisory classification: inspect_further, borrow_pattern_only, prototype_candidate, do_not_use.
"""

from __future__ import annotations

from typing import Any

D2_RECOMMENDATIONS = ("inspect_further", "borrow_pattern_only", "prototype_candidate", "do_not_use")


def score_repo_usefulness(parsed: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, float]:
    """
    Score a parsed repo for usefulness. parsed: readme_preview, license_note, deps, file_tree, etc.
    context: optional { category } to boost relevance. Returns dict with relevance, code_doc_clarity,
    reusable_patterns, implementation_complexity, risk (each 0..1).
    """
    context = context or {}
    category = (context.get("category") or "").lower()
    readme = (parsed.get("readme_preview") or "").lower()
    license_note = (parsed.get("license_note") or "").lower()
    deps = parsed.get("deps") or {}
    file_tree = parsed.get("file_tree") or []
    if isinstance(file_tree, list) and file_tree and isinstance(file_tree[0], dict):
        paths = [str(x.get("path", "")) for x in file_tree]
    else:
        paths = [str(p) for p in file_tree] if isinstance(file_tree, list) else []

    # Relevance to product family (category + keywords)
    relevance = 0.3
    keywords = ["workflow", "eval", "evaluation", "harness", "ui", "dashboard", "packaging", "agent", "local", "model"]
    for kw in keywords:
        if kw in readme:
            relevance = min(1.0, relevance + 0.15)
    if category and any(c in readme or c in " ".join(paths) for c in [category, "eval", "ui", "workflow", "packag"]):
        relevance = min(1.0, relevance + 0.2)

    # Clarity of docs/code structure (readme length, structure hints)
    code_doc_clarity = 0.3
    if len(readme) > 200:
        code_doc_clarity += 0.2
    if "## " in readme or "### " in readme or "install" in readme or "usage" in readme:
        code_doc_clarity += 0.2
    if any("src" in p or "lib" in p or "docs" in p for p in paths):
        code_doc_clarity += 0.2
    code_doc_clarity = min(1.0, code_doc_clarity)

    # Likely reusable patterns (api, module, plugin, sdk)
    reusable_patterns = 0.2
    for term in ["api", "module", "plugin", "sdk", "library", "harness", "adapter"]:
        if term in readme:
            reusable_patterns = min(1.0, reusable_patterns + 0.15)
            break

    # Implementation complexity (inverse: more structure = manageable)
    implementation_complexity = 0.5
    if len(paths) > 20:
        implementation_complexity = 0.7
    elif len(paths) < 5 and len(readme) < 500:
        implementation_complexity = 0.3
    if "docker" in readme or "k8s" in readme or "kubernetes" in readme:
        implementation_complexity = min(1.0, implementation_complexity + 0.2)

    # Operational/legal risk (license + deps count)
    risk = 0.3
    if "mit" in license_note or "apache" in license_note or "bsd" in license_note:
        risk = 0.1
    elif "gpl" in license_note or "agpl" in license_note:
        risk = 0.6
    if not license_note.strip():
        risk = 0.5
    dep_count = sum(1 for v in (deps if isinstance(deps, dict) else {}) if v) if deps else 0
    if dep_count > 30:
        risk = min(1.0, risk + 0.2)
    risk = min(1.0, risk)

    return {
        "relevance": round(relevance, 3),
        "code_doc_clarity": round(code_doc_clarity, 3),
        "reusable_patterns": round(reusable_patterns, 3),
        "implementation_complexity": round(implementation_complexity, 3),
        "risk": round(risk, 3),
    }


def usefulness_composite(scores: dict[str, float]) -> float:
    """Single composite 0..1 from usefulness scores. Higher = more useful / lower risk."""
    r = scores.get("relevance", 0)
    c = scores.get("code_doc_clarity", 0)
    p = scores.get("reusable_patterns", 0)
    comp = scores.get("implementation_complexity", 0.5)
    risk = scores.get("risk", 0.3)
    # composite = relevance + clarity + patterns, minus complexity and risk
    comp_val = 0.35 * r + 0.25 * c + 0.2 * p + 0.1 * (1.0 - comp) + 0.1 * (1.0 - risk)
    return round(max(0.0, min(1.0, comp_val)), 3)


def recommend_d2(
    scores: dict[str, float],
    triage: dict[str, Any],
) -> str:
    """
    Advisory classification from scores + license triage.
    Returns one of: inspect_further, borrow_pattern_only, prototype_candidate, do_not_use.
    """
    comp = usefulness_composite(scores)
    risk = scores.get("risk", 0.5)
    use_as = (triage.get("use_as") or "unclear").lower()
    legal = (triage.get("legal_operational_risk") or triage.get("license_risk") or "unknown").lower()

    if risk >= 0.7 or legal == "high":
        return "do_not_use"
    if use_as == "inspiration" and comp < 0.4:
        return "do_not_use"
    if use_as == "direct_reuse" and comp >= 0.5 and risk <= 0.3:
        return "prototype_candidate"
    if comp >= 0.4 and risk <= 0.5:
        return "inspect_further"
    if comp >= 0.25 or use_as == "inspiration":
        return "borrow_pattern_only"
    return "do_not_use"
