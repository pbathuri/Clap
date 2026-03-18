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
from workflow_dataset.edge.package_report import (
    build_workflow_matrix_by_tier,
    build_workflow_matrix_all_tiers,
    build_packaging_metadata,
)

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
    ready = summary.get("ready", False)
    failed_required = summary.get("failed_required", 0)

    lines: list[str] = []
    lines.append("# Edge Readiness Report")
    lines.append("")
    lines.append("Local deployment profile and readiness checks. No cloud; no hardware specs.")
    lines.append("")
    outcome_line = "**Outcome:** Ready — all required checks passed."
    if not ready:
        outcome_line = f"**Outcome:** Not ready — {failed_required} required check(s) failed. Fix required items below, then re-run."
    lines.append(outcome_line)
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Ready:** {ready}")
    lines.append(f"- **Checks passed:** {summary.get('passed', 0)} / {len(checks)}")
    lines.append(f"- **Failed (required):** {failed_required}")
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
    lines.append("Required checks must pass for *Ready* to be true; optional checks disable a feature when failed.")
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

    from workflow_dataset.edge.tiers import (
        EDGE_TIERS,
        TIER_DESCRIPTIONS,
        get_required_dependencies_for_tier,
    )

    if tier:
        if tier not in EDGE_TIERS:
            raise ValueError(f"Unknown tier: {tier}. Use one of: {list(EDGE_TIERS)}")
        matrix = build_workflow_matrix_by_tier(tier, repo_root=root)
        req_deps, opt_deps = get_required_dependencies_for_tier(tier)
        if format.lower() == "json":
            path.write_text(
                json.dumps(
                    {
                        "tier": tier,
                        "tier_description": TIER_DESCRIPTIONS.get(tier, ""),
                        "workflows": matrix,
                        "required_dependencies": req_deps,
                        "optional_dependencies": opt_deps,
                    },
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
            "## Required local dependencies",
            "",
        ]
        for d in req_deps:
            lines.append(f"- **{d.get('name')}** ({d.get('type', '')}): {d.get('note', '')}")
        lines.append("")
        if opt_deps:
            lines.append("## Optional dependencies (degraded when missing)")
            lines.append("")
            for d in opt_deps:
                lines.append(f"- **{d.get('name')}** ({d.get('type', '')}): {d.get('note', '')}")
            lines.append("")
        lines.extend([
            "## Workflow support",
            "",
            "| Workflow | Status | Description | Reason | Missing | Fallback |",
            "|----------|--------|-------------|--------|---------|----------|",
        ])
        for row in matrix:
            wf = row.get("workflow", "")
            st = row.get("status", "")
            desc = (row.get("description", "") or "")[:40]
            reason = (row.get("reason", "") or "")[:35]
            miss = ", ".join((row.get("missing_functionality") or [])[:2])
            fallback = (row.get("fallback") or "")[:30]
            lines.append(f"| {wf} | {st} | {desc} | {reason} | {miss} | {fallback} |")
        degraded = [r for r in matrix if (r.get("status") or "") == "degraded"]
        if degraded:
            lines.append("")
            lines.append("## Degraded workflows")
            lines.append("")
            lines.append("Workflows that are partially supported: why, what is missing, and what fallback is available.")
            lines.append("")
            for row in degraded:
                wf = row.get("workflow", "")
                lines.append(f"### {wf}")
                lines.append("")
                lines.append(f"- **Why partial:** {row.get('reason', '')}")
                miss = row.get("missing_functionality") or []
                if miss:
                    lines.append(f"- **Missing:** {', '.join(miss)}")
                fb = row.get("fallback")
                if fb:
                    lines.append(f"- **Fallback:** {fb}")
                lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # All tiers
    all_matrix = build_workflow_matrix_all_tiers(repo_root=root)
    if format.lower() == "json":
        from workflow_dataset.edge.tiers import get_required_dependencies_for_tier
        payload = {
            "tiers": {},
            "tier_descriptions": TIER_DESCRIPTIONS,
        }
        for t in EDGE_TIERS:
            req_d, opt_d = get_required_dependencies_for_tier(t)
            payload["tiers"][t] = {
                "workflows": all_matrix.get(t, []),
                "required_dependencies": req_d,
                "optional_dependencies": opt_d,
            }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
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
    """Generate tier comparison report (markdown): workflow diff, degraded workflows, path/dep differences."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path or (out_dir / "tier_compare.md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    diff = compare_tiers(tier_a, tier_b, repo_root=root)
    if diff.get("error"):
        path.write_text(f"# Tier Compare\n\nError: {diff['error']}\n", encoding="utf-8")
        return path

    from workflow_dataset.edge.tiers import get_workflow_status_for_tier

    status_a = get_workflow_status_for_tier(tier_a)
    status_b = get_workflow_status_for_tier(tier_b)
    degraded_a = [wf for wf, s in status_a.items() if (s or {}).get("status") == "degraded"]
    degraded_b = [wf for wf, s in status_b.items() if (s or {}).get("status") == "degraded"]

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

    if degraded_a or degraded_b:
        lines.append("## Degraded workflows")
        lines.append("")
        if degraded_a:
            lines.append(f"**In {tier_a}:** " + ", ".join(degraded_a))
            for wf in degraded_a:
                s = (status_a.get(wf) or {})
                lines.append(f"  - {wf}: {s.get('reason', '')}; fallback: {s.get('fallback') or '—'}")
            lines.append("")
        if degraded_b:
            lines.append(f"**In {tier_b}:** " + ", ".join(degraded_b))
            for wf in degraded_b:
                s = (status_b.get(wf) or {})
                lines.append(f"  - {wf}: {s.get('reason', '')}; fallback: {s.get('fallback') or '—'}")
            lines.append("")

    lines.append("## Missing dependencies (path difference)")
    lines.append("")
    lines.append("Paths required in first tier but not in second:")
    for p in diff.get("paths_only_in_a", []):
        lines.append(f"- {p}")
    if not diff.get("paths_only_in_a"):
        lines.append("- *(none)*")
    lines.append("")
    lines.append("Paths required in second tier but not in first:")
    for p in diff.get("paths_only_in_b", []):
        lines.append(f"- {p}")
    if not diff.get("paths_only_in_b"):
        lines.append("- *(none)*")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_degraded_report(
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
    tier: str | None = None,
    format: str = "markdown",
) -> Path:
    """
    Generate degraded-mode report: for each workflow that is partially supported,
    explain why, what is missing, and what fallback is available.
    If tier is set, only that tier; else all tiers with degraded workflows.
    """
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path
    if path is None:
        path = out_dir / (f"{tier}_degraded_report" if tier else "degraded_workflows_report")
        path = path.with_suffix(".json" if format.lower() == "json" else ".md")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    from workflow_dataset.edge.tiers import EDGE_TIERS, TIER_DESCRIPTIONS, get_workflow_status_for_tier

    tiers_to_report = [tier] if tier and tier in EDGE_TIERS else list(EDGE_TIERS)
    by_tier: dict[str, list[dict[str, Any]]] = {}
    for t in tiers_to_report:
        status = get_workflow_status_for_tier(t)
        degraded = []
        for wf, s in status.items():
            if (s or {}).get("status") == "degraded":
                degraded.append({
                    "workflow": wf,
                    "reason": (s or {}).get("reason", ""),
                    "missing_functionality": list((s or {}).get("missing_functionality") or []),
                    "fallback": (s or {}).get("fallback"),
                })
        if degraded:
            by_tier[t] = degraded

    if format.lower() == "json":
        path.write_text(
            json.dumps({"tiers": by_tier, "tier_descriptions": TIER_DESCRIPTIONS}, indent=2),
            encoding="utf-8",
        )
        return path

    lines = [
        "# Degraded Workflow Report",
        "",
        "Workflows that are only partially supported: why, what is missing, and what fallback is available.",
        "",
    ]
    for t in tiers_to_report:
        if t not in by_tier:
            continue
        lines.append(f"## Tier: {t}")
        lines.append("")
        lines.append(TIER_DESCRIPTIONS.get(t, ""))
        lines.append("")
        for row in by_tier[t]:
            lines.append(f"### {row['workflow']}")
            lines.append("")
            lines.append(f"- **Why partial:** {row.get('reason', '')}")
            if row.get("missing_functionality"):
                lines.append(f"- **Missing:** {', '.join(row['missing_functionality'])}")
            if row.get("fallback"):
                lines.append(f"- **Fallback:** {row['fallback']}")
            lines.append("")
    if not by_tier:
        lines.append("No degraded workflows in the selected tier(s).")
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
    if required or optional:
        lines.append("## What this means")
        lines.append("")
        if required:
            lines.append("- **Required:** These must be fixed for the setup to be considered ready (e.g. create missing paths, add config).")
        if optional:
            lines.append("- **Optional:** When missing, the corresponding feature is disabled; the product can still run in a reduced mode.")
        lines.append("")
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
    tier: str | None = None,
    format: str = "markdown",
) -> Path:
    """Generate edge packaging metadata: package configs, workflow availability, local model/runtime deps.
    If tier is set, report is tier-scoped (required/optional components, supported/degraded workflows)."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    if tier and tier.strip():
        path = output_path or (out_dir / ("edge_package_report_" + tier.strip() + (".json" if format.lower() == "json" else ".md")))
    else:
        path = output_path or (out_dir / "edge_package_report.md")
    if path and format.lower() == "json" and path.suffix != ".json":
        path = path.with_suffix(".json")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if tier and tier.strip():
        meta = build_packaging_metadata(tier.strip(), repo_root=root, config_path=config_path)
        if meta.get("error"):
            path.write_text(f"# Edge Package Report\n\nError: {meta['error']}\n", encoding="utf-8")
            return path
        if format.lower() == "json":
            path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            return path
        lines = _format_packaging_metadata_md(meta, root)
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    profile = build_edge_profile(repo_root=root, config_path=config_path)
    checks = run_readiness_checks(repo_root=root, config_path=config_path)
    summary = checks_summary(checks)

    lines = []
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


def _format_packaging_metadata_md(meta: dict[str, Any], root: Path) -> list[str]:
    """Format build_packaging_metadata output as markdown."""
    lines = [
        "# Edge Packaging Metadata",
        "",
        f"**Tier:** {meta.get('tier')}",
        "",
        meta.get("tier_description", ""),
        "",
        "## Required runtime components",
        "",
    ]
    for d in meta.get("required_runtime_components") or []:
        lines.append(f"- **{d.get('name')}** ({d.get('type')}): {d.get('note', '')}")
    lines.append("")
    opt = meta.get("optional_runtime_components") or []
    if opt:
        lines.append("## Optional runtime components")
        lines.append("")
        for d in opt:
            lines.append(f"- **{d.get('name')}** ({d.get('type')}): {d.get('note', '')}")
        lines.append("")
    lines.append("## Supported workflows")
    lines.append("")
    for w in meta.get("supported_workflows") or []:
        lines.append(f"- {w}")
    lines.append("")
    deg = meta.get("degraded_workflows") or []
    if deg:
        lines.append("## Degraded workflows")
        lines.append("")
        for w in deg:
            lines.append(f"- {w}")
        lines.append("")
    unav = meta.get("unavailable_workflows") or []
    if unav:
        lines.append("## Unavailable workflows")
        lines.append("")
        for w in unav:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("## Local path assumptions")
    lines.append("")
    for p in meta.get("local_path_assumptions") or []:
        exists = (root / p).exists() if p else False
        lines.append(f"- `{p}` — {'exists' if exists else 'missing'}")
    lines.append("")
    lines.append("## Config assumptions")
    lines.append("")
    cfg = meta.get("config_assumptions") or {}
    lines.append(f"- config_path: {cfg.get('config_path')}")
    lines.append(f"- config_exists: {cfg.get('config_exists')}")
    lines.append(f"- llm_requirement: {cfg.get('llm_requirement')}")
    lines.append("")
    miss = meta.get("missing_dependency_summary") or {}
    lines.append("## Missing dependency summary")
    lines.append("")
    lines.append(f"- overall_ok: {miss.get('overall_ok')}")
    for m in (miss.get("missing_required") or [])[:10]:
        lines.append(f"- missing_required: {m}")
    for w in (miss.get("warnings") or [])[:5]:
        lines.append(f"- warning: {w}")
    lines.append("")
    lines.append("## Notes for packaging")
    lines.append("")
    lines.append(meta.get("notes_for_packaging", ""))
    lines.append("")
    return lines


def generate_smoke_check_report(
    smoke_result: dict[str, Any],
    output_path: Path | None = None,
    repo_root: Path | str | None = None,
    format: str = "markdown",
) -> Path:
    """Write smoke check result to a report file. Which workflows tested, pass/fail/skipped, degraded/missing reasons."""
    root = _repo_root(repo_root)
    out_dir = _ensure_edge_dir(root)
    path = output_path or (out_dir / "smoke_check_report.md")
    if format.lower() == "json":
        path = path.with_suffix(".json") if path.suffix != ".json" else path
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if smoke_result.get("error"):
        path.write_text(
            "# Smoke Check Report\n\nError: " + smoke_result.get("error", "") + "\n",
            encoding="utf-8",
        )
        return path

    if format.lower() == "json":
        # Minimal JSON: tier, overall_pass, workflow_results, readiness_ok
        payload = {
            "tier": smoke_result.get("tier"),
            "overall_pass": smoke_result.get("overall_pass"),
            "readiness_ok": smoke_result.get("readiness_ok"),
            "passed": smoke_result.get("passed"),
            "failed": smoke_result.get("failed"),
            "skipped": smoke_result.get("skipped"),
            "workflow_results": smoke_result.get("workflow_results", []),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    lines = [
        "# Edge Smoke Check Report",
        "",
        f"**Tier:** {smoke_result.get('tier')}",
        f"**Overall:** {'PASS' if smoke_result.get('overall_pass') else 'FAIL'}",
        "",
        "## Readiness",
        "",
        f"- ready: {smoke_result.get('readiness_ok')}",
        f"- checks passed: {smoke_result.get('readiness_summary', {}).get('passed')}/{len(smoke_result.get('readiness_checks') or [])}",
        "",
        "## Workflows tested",
        "",
        "| Workflow | Status | Message | Degraded reason | Missing reason |",
        "|----------|--------|---------|-----------------|----------------|",
    ]
    for r in smoke_result.get("workflow_results") or []:
        wf = r.get("workflow", "")
        st = r.get("status", "")
        msg = (r.get("message") or "")[:40].replace("|", " ")
        deg = (r.get("degraded_reason") or "")[:30].replace("|", " ")
        miss = (r.get("missing_reason") or "")[:30].replace("|", " ")
        lines.append(f"| {wf} | {st} | {msg} | {deg} | {miss} |")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- passed: {smoke_result.get('passed')}")
    lines.append(f"- failed: {smoke_result.get('failed')}")
    lines.append(f"- skipped: {smoke_result.get('skipped')}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

