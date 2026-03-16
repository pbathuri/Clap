"""
M23B: Edge readiness report, missing dependency report, workflow matrix. Local outputs only.
M23B-F2: Tier matrix report and tier comparison report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.edge.profile import (
    build_edge_profile,
    SUPPORTED_WORKFLOWS,
    SANDBOX_PATHS,
)
from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
from workflow_dataset.edge.package_report import build_workflow_matrix_by_tier, build_workflow_matrix_all_tiers

EDGE_OUTPUT_DIR = "data/local/edge"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def _ensure_edge_dir(repo_root: Path) -> Path:
    d = repo_root / EDGE_OUTPUT_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def generate_edge_readiness_report(
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> Path:
    """Generate full edge readiness report (profile, checks, summary). Writes Markdown to output_path."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path or (out_dir / "edge_readiness_report.md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    profile = build_edge_profile(repo_root=root, config_path=config_path)
    checks = run_readiness_checks(repo_root=root, config_path=config_path)
    summary = checks_summary(checks)

    lines: list[str] = []
    lines.append("# Edge Readiness Report")
    lines.append("")
    lines.append("Local deployment profile and readiness checks. No cloud; no hardware specs.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Ready:** {summary.get('ready', False)}")
    lines.append(f"- **Checks passed:** {summary.get('passed', 0)} / {len(checks)}")
    lines.append(f"- **Failed (required):** {summary.get('failed_required', 0)}")
    lines.append(f"- **Optional disabled:** {summary.get('optional_disabled', 0)}")
    lines.append("")
    lines.append("## Runtime requirements")
    lines.append("")
    for k, v in (profile.get("runtime_requirements") or {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Sandbox paths")
    lines.append("")
    for p in profile.get("sandbox_path_assumptions", {}).get("paths", []):
        full = root / p
        exists = full.exists()
        lines.append(f"- `{p}` — {'exists' if exists else 'missing'}")
    lines.append("")
    lines.append("## Readiness checks")
    lines.append("")
    for c in checks:
        status = "ok" if c.get("passed") else "FAIL"
        opt = " (optional)" if c.get("optional") else ""
        lines.append(f"- **{c.get('check_id')}** — {status}{opt}: {c.get('message')}")
    lines.append("")
    lines.append("## Supported workflows")
    lines.append("")
    for w in profile.get("supported_workflows", []):
        lines.append(f"- {w}")
    lines.append("")
    lines.append("---")
    lines.append("*Generated for local edge deployment. No cloud or production deployables.*")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_tier_matrix_report(
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
    tier: str | None = None,
    format: str = "markdown",
) -> Path:
    """
    Generate workflow support matrix by tier. If tier is set, single tier; else all tiers.
    format: markdown | json. Writes to output_path or data/local/edge/<tier>_workflow_matrix.md|.json.
    """
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path
    if path is None:
        path = out_dir / (f"{tier}_workflow_matrix" if tier else "all_tiers_workflow_matrix")
        path = path.with_suffix(".json" if format.lower() == "json" else ".md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    from workflow_dataset.edge.tiers import EDGE_TIERS, TIER_DESCRIPTIONS

    if tier:
        if tier not in EDGE_TIERS:
            raise ValueError(f"Unknown tier: {tier}. Use one of: {list(EDGE_TIERS)}")
        matrix = build_workflow_matrix_by_tier(tier, repo_root=root)
        if format.lower() == "json":
            path.write_text(
                json.dumps(
                    {"tier": tier, "tier_description": TIER_DESCRIPTIONS.get(tier, ""), "workflows": matrix},
                    indent=2,
                ),
                encoding="utf-8",
            )
            return path
        lines = [
            f"# Workflow Matrix — {tier}",
            "",
            TIER_DESCRIPTIONS.get(tier, ""),
            "",
            "| Workflow | Status | Description | Reason | Missing | Fallback |",
            "|----------|--------|-------------|--------|---------|----------|",
        ]
        for row in matrix:
            wf = row.get("workflow", "")
            st = row.get("status", "")
            desc = (row.get("description", "") or "")[:40]
            reason = (row.get("reason", "") or "")[:35]
            miss = ", ".join((row.get("missing_functionality") or [])[:2])
            fallback = (row.get("fallback") or "")[:30]
            lines.append(f"| {wf} | {st} | {desc} | {reason} | {miss} | {fallback} |")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # All tiers
    all_matrix = build_workflow_matrix_all_tiers(repo_root=root)
    if format.lower() == "json":
        path.write_text(
            json.dumps(
                {"tiers": {t: build_workflow_matrix_by_tier(t, repo_root=root) for t in EDGE_TIERS}},
                indent=2,
            ),
            encoding="utf-8",
        )
        return path
    lines = ["# Workflow Matrix — All Tiers", ""]
    for t in EDGE_TIERS:
        lines.append(f"## {t}")
        lines.append("")
        lines.append(TIER_DESCRIPTIONS.get(t, ""))
        lines.append("")
        for row in all_matrix.get(t, []):
            lines.append(f"- **{row.get('workflow')}**: {row.get('status')} — {row.get('reason', '')}")
            if row.get("fallback"):
                lines.append(f"  - Fallback: {row['fallback']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def compare_tiers(
    tier_a: str,
    tier_b: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Compare two tiers: workflow status diff, path diff, llm requirement diff.
    """
    from workflow_dataset.edge.tiers import (
        EDGE_TIERS,
        get_tier_definition,
        get_workflow_status_for_tier,
        TIER_DESCRIPTIONS,
    )
    root = _repo_root(repo_root)
    if tier_a not in EDGE_TIERS or tier_b not in EDGE_TIERS:
        return {"error": f"Unknown tier. Use: {list(EDGE_TIERS)}"}
    def_a = get_tier_definition(tier_a)
    def_b = get_tier_definition(tier_b)
    status_a = get_workflow_status_for_tier(tier_a)
    status_b = get_workflow_status_for_tier(tier_b)
    workflow_diff = []
    for wf in list(status_a.keys()) + [w for w in status_b if w not in status_a]:
        sa = (status_a.get(wf) or {}).get("status")
        sb = (status_b.get(wf) or {}).get("status")
        if sa != sb:
            workflow_diff.append({"workflow": wf, tier_a: sa, tier_b: sb})
    paths_a = set(def_a.get("required_paths") or [])
    paths_b = set(def_b.get("required_paths") or [])
    only_a = sorted(paths_a - paths_b)
    only_b = sorted(paths_b - paths_a)
    return {
        "tier_a": tier_a,
        "tier_b": tier_b,
        "description_a": TIER_DESCRIPTIONS.get(tier_a, ""),
        "description_b": TIER_DESCRIPTIONS.get(tier_b, ""),
        "llm_requirement_a": def_a.get("llm_requirement"),
        "llm_requirement_b": def_b.get("llm_requirement"),
        "workflow_status_diff": workflow_diff,
        "paths_only_in_a": only_a,
        "paths_only_in_b": only_b,
    }


def generate_compare_report(
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
    tier_a: str = "local_standard",
    tier_b: str = "constrained_edge",
) -> Path:
    """Generate tier comparison report (markdown)."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path or (out_dir / "tier_compare.md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    diff = compare_tiers(tier_a, tier_b, repo_root=root)
    if diff.get("error"):
        path.write_text(f"# Tier Compare\n\nError: {diff['error']}\n", encoding="utf-8")
        return path
    lines = [
        "# Tier Comparison",
        "",
        f"**{diff['tier_a']}** vs **{diff['tier_b']}**",
        "",
        f"- **{diff['tier_a']}**: {diff.get('description_a', '')}",
        f"- **{diff['tier_b']}**: {diff.get('description_b', '')}",
        "",
        "## LLM requirement",
        "",
        f"- {diff['tier_a']}: {diff.get('llm_requirement_a')}",
        f"- {diff['tier_b']}: {diff.get('llm_requirement_b')}",
        "",
        "## Workflow status diff",
        "",
    ]
    for w in diff.get("workflow_status_diff", []):
        lines.append(f"- **{w.get('workflow')}**: {diff['tier_a']}={w.get(diff['tier_a'])} → {diff['tier_b']}={w.get(diff['tier_b'])}")
    lines.append("")
    lines.append("## Paths only in first tier")
    for p in diff.get("paths_only_in_a", []):
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## Paths only in second tier")
    for p in diff.get("paths_only_in_b", []):
        lines.append(f"- {p}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_missing_dependency_report(
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
) -> Path:
    """Generate missing dependency report (checks that failed, required vs optional)."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path or (out_dir / "missing_dependency_report.md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    checks = run_readiness_checks(repo_root=root)
    failed = [c for c in checks if not c.get("passed")]

    lines: list[str] = []
    lines.append("# Missing Dependency Report")
    lines.append("")
    lines.append("Required and optional missing dependencies for edge/local deployment.")
    lines.append("")
    required = [c for c in failed if not c.get("optional")]
    optional = [c for c in failed if c.get("optional")]
    if required:
        lines.append("## Required (must fix)")
        lines.append("")
        for c in required:
            lines.append(f"- **{c.get('check_id')}**: {c.get('message')}")
        lines.append("")
    if optional:
        lines.append("## Optional (feature disabled when missing)")
        lines.append("")
        for c in optional:
            lines.append(f"- **{c.get('check_id')}**: {c.get('message')}")
        lines.append("")
    if not failed:
        lines.append("No missing dependencies detected.")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_workflow_matrix_report(
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
    format: str = "markdown",
) -> Path:
    """Generate supported workflow matrix (workflow, description, required/optional)."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path or (out_dir / "supported_workflow_matrix.md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Workflow descriptions (ops/reporting family)
    descriptions: dict[str, str] = {
        "weekly_status": "Single weekly status artifact (summary, wins, blockers, next steps).",
        "status_action_bundle": "Status brief + action register.",
        "stakeholder_update_bundle": "Stakeholder-facing update + decision requests.",
        "meeting_brief_bundle": "Meeting brief + action items.",
        "ops_reporting_workspace": "Multi-artifact workspace (all six artifacts).",
    }
    matrix: list[dict[str, Any]] = [
        {"workflow": w, "description": descriptions.get(w, "—"), "required_components": ["config", "sandbox"], "optional": ["llm_adapter", "retrieval_corpus"]}
        for w in SUPPORTED_WORKFLOWS
    ]

    if format.lower() == "json":
        path = path.with_suffix(".json")
        path.write_text(json.dumps({"workflows": matrix}, indent=2), encoding="utf-8")
        return path

    lines = []
    lines.append("# Supported Workflow Matrix")
    lines.append("")
    lines.append("| Workflow | Description | Required | Optional |")
    lines.append("|----------|-------------|----------|----------|")
    for m in matrix:
        lines.append(f"| {m['workflow']} | {m['description']} | config, sandbox | llm_adapter, retrieval_corpus |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_package_report(
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> Path:
    """Generate edge packaging metadata: package configs, workflow availability, local model/runtime deps."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path or (out_dir / "edge_package_report.md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    profile = build_edge_profile(repo_root=root, config_path=config_path)
    checks = run_readiness_checks(repo_root=root, config_path=config_path)
    summary = checks_summary(checks)

    lines: list[str] = []
    lines.append("# Edge Package Report")
    lines.append("")
    lines.append("Packaging metadata for edge-style deployment testing. Local and inspectable.")
    lines.append("")
    lines.append("## Package config")
    lines.append("")
    lines.append(f"- repo_root: `{profile.get('repo_root')}`")
    lines.append(f"- config: `{profile.get('config_path')}` (exists: {profile.get('config_exists')})")
    lines.append("")
    lines.append("## Workflow availability")
    lines.append("")
    for w in profile.get("supported_workflows", []):
        lines.append(f"- {w}")
    lines.append("")
    lines.append("## Local model / runtime dependencies")
    lines.append("")
    for k, v in (profile.get("model_assumptions") or {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Sandbox paths (package expects)")
    lines.append("")
    for p in SANDBOX_PATHS:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## Readiness")
    lines.append("")
    lines.append(f"- ready: {summary.get('ready')}")
    lines.append(f"- checks passed: {summary.get('passed')}/{len(checks)}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


