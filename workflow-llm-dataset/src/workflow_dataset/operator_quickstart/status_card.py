"""
M23X: Product status card — integrated modules available, missing optional pieces,
trusted-real vs simulate-only coverage, current recommended next action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


def build_status_card(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build product status card from mission_control state, first_run_summary, package_readiness.
    Keys: integrated_modules_available, missing_optional, trusted_real_vs_simulate, recommended_next_action, errors.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "integrated_modules_available": [],
        "missing_optional": [],
        "trusted_real_vs_simulate": {"trusted_real_count": 0, "simulate_only_count": 0, "summary": ""},
        "recommended_next_action": "",
        "errors": [],
    }
    state: dict[str, Any] = {}

    # Mission control state for integrated modules and next action
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        from workflow_dataset.mission_control.next_action import recommend_next_action
        state = get_mission_control_state(root)
        next_rec = recommend_next_action(state)

        # Integrated modules (present and not error)
        if not state.get("product_state", {}).get("error"):
            out["integrated_modules_available"].append("product_state")
        if not state.get("desktop_bridge", {}).get("error"):
            out["integrated_modules_available"].append("desktop_bridge")
        if not state.get("job_packs", {}).get("error"):
            out["integrated_modules_available"].append("job_packs")
        if not state.get("copilot", {}).get("error"):
            out["integrated_modules_available"].append("copilot")
        if not state.get("work_context", {}).get("error"):
            out["integrated_modules_available"].append("work_context")
        if not state.get("runtime_mesh", {}).get("error"):
            out["integrated_modules_available"].append("runtime_mesh")
        if not state.get("daily_inbox", {}).get("error"):
            out["integrated_modules_available"].append("daily_inbox")
        if not state.get("trust_cockpit", {}).get("error"):
            out["integrated_modules_available"].append("trust_cockpit")
        if not state.get("package_readiness", {}).get("error"):
            out["integrated_modules_available"].append("package_readiness")

        # Missing optional
        if state.get("incubator_state", {}).get("error"):
            out["missing_optional"].append("incubator")

        out["recommended_next_action"] = next_rec.get("action", "hold")
        out["recommended_next_rationale"] = next_rec.get("rationale", "")
        out["recommended_next_detail"] = next_rec.get("detail", "")
    except Exception as e:
        out["errors"].append(f"mission_control: {e}")
        out["recommended_next_action"] = "run mission-control"

    # Trusted-real vs simulate from job_packs / first_run_summary
    try:
        from workflow_dataset.onboarding.product_summary import build_first_run_summary
        summary = build_first_run_summary(repo_root=root)
        jp = state.get("job_packs", {}) if state else {}
        trusted = jp.get("trusted_for_real_count", 0) or (1 if summary.get("ready_for_real") else 0)
        sim_only = jp.get("simulate_only_count", 0)
        out["trusted_real_vs_simulate"] = {
            "trusted_real_count": trusted,
            "simulate_only_count": sim_only,
            "summary": f"Trusted for real: {trusted}. Simulate-only jobs: {sim_only}. Real execution requires approval registry.",
        }
    except Exception as e:
        out["trusted_real_vs_simulate"]["summary"] = f"(Could not compute: {e})"

    return out


def format_status_card_text(card: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Format product status card as plain text."""
    if card is None:
        card = build_status_card(repo_root)
    lines = [
        "=== Product status card (M23X) ===",
        "",
        "--- Integrated modules available ---",
        "",
        "  " + ", ".join(card.get("integrated_modules_available", []) or ["(none)"]),
        "",
        "--- Missing optional pieces ---",
        "",
        "  " + ", ".join(card.get("missing_optional", []) or ["(none)"]),
        "",
        "--- Trusted-real vs simulate-only ---",
        "",
        "  " + card.get("trusted_real_vs_simulate", {}).get("summary", ""),
        "",
        "--- Recommended next action ---",
        "",
        "  action: " + card.get("recommended_next_action", "hold"),
        "  rationale: " + card.get("recommended_next_rationale", ""),
        "",
    ]
    if card.get("recommended_next_detail"):
        lines.append("  detail: " + str(card["recommended_next_detail"]))
        lines.append("")
    if card.get("errors"):
        lines.append("--- Errors ---")
        lines.append("")
        for e in card["errors"]:
            lines.append("  · " + str(e))
        lines.append("")
    lines.append("(Run workflow-dataset mission-control for full report.)")
    return "\n".join(lines)
