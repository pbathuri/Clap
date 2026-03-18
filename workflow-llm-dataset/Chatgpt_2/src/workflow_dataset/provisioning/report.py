"""
M24E: Format provisioning summary, domain environment summary, recipe run report for CLI.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.specialization.recipe_run_models import RecipeRun


def format_provisioning_result(result: dict[str, Any]) -> str:
    """Format run_provisioning() result for console."""
    if result.get("error") and not result.get("success"):
        lines = [
            "[Provisioning] Blocked or failed",
            "",
            "Error: " + (result.get("error") or ""),
        ]
        if result.get("missing_prerequisites"):
            lines.append("")
            lines.append("Missing prerequisites:")
            for m in result["missing_prerequisites"]:
                lines.append("  - " + m)
        return "\n".join(lines)
    lines = [
        "[Provisioning] " + (result.get("message") or "Done"),
        "",
        "Run ID: " + (result.get("run_id") or "—"),
        "Steps done: " + ", ".join(result.get("steps_done") or []),
    ]
    if result.get("outputs_produced"):
        lines.append("Outputs: " + ", ".join(result.get("outputs_produced", [])[:5]))
        if len(result.get("outputs_produced", [])) > 5:
            lines.append("  ... and more")
    return "\n".join(lines)


def format_domain_environment_summary(summary: dict[str, Any]) -> str:
    """Format domain_environment_summary() for console."""
    if summary.get("error"):
        return f"Error: {summary['error']}"
    lines = [
        "=== Domain environment: " + summary.get("pack_id", "") + " ===",
        "",
        "Pack: " + (summary.get("pack_name") or summary.get("pack_id", "")),
        "Provisioned: " + ("yes" if summary.get("provisioned") else "no"),
        "",
        "[Ready]",
        "  jobs: " + ", ".join(summary.get("jobs_ready") or []) or "—",
        "  routines: " + ", ".join(summary.get("routines_ready") or []) or "—",
        "  macros: " + ", ".join(summary.get("macros_ready") or []) or "—",
        "",
        "[Needs activation]",
        "  " + ", ".join(summary.get("needs_activation") or []) or "—",
        "",
        "[Simulate-only]",
    ]
    for s in summary.get("simulate_only") or []:
        lines.append("  " + s)
    if not summary.get("simulate_only"):
        lines.append("  —")
    lines.append("")
    lines.append("Recommended first-value run: " + (summary.get("recommended_first_value_run") or "—"))
    if summary.get("missing_prerequisites"):
        lines.append("")
        lines.append("Missing prerequisites:")
        for m in summary["missing_prerequisites"]:
            lines.append("  - " + m)
    return "\n".join(lines)


def format_recipe_run(run: RecipeRun | None) -> str:
    """Format a single recipe run for console."""
    if not run:
        return "Recipe run not found."
    lines = [
        f"Run ID: {run.run_id}",
        f"Recipe: {run.source_recipe_id}  Status: {run.status}",
        f"Target: domain={run.target_domain_pack_id}  value_pack={run.target_value_pack_id}",
        f"Steps done: {', '.join(run.steps_done) or '—'}",
        f"Dry run: {run.dry_run}",
    ]
    if run.error_message:
        lines.append("Error: " + run.error_message)
    if run.rollback_notes:
        lines.append("Rollback: " + run.rollback_notes)
    return "\n".join(lines)


def format_recipe_run_report(runs: list[RecipeRun], title: str = "Recipe runs") -> str:
    """Format list of recipe runs for CLI report."""
    lines = [f"=== {title} ===", ""]
    if not runs:
        lines.append("No runs found.")
        return "\n".join(lines)
    for r in runs:
        lines.append(f"  {r.run_id}  {r.source_recipe_id}  {r.target_value_pack_id or r.target_domain_pack_id}  {r.status}")
    return "\n".join(lines)
