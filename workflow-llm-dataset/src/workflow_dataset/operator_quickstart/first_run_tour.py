"""
M23X: Guided first-run tour — what the system can do, simulate-only, approvals, recommended first workflow,
how to interpret trust/runtime/profile. Uses existing first_run_summary, onboarding status, mission_control (read-only).
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


def build_first_run_tour(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build guided first-run tour from local sources only.
    Keys: what_system_can_do, simulate_only_explained, approvals_that_matter, recommended_first_workflow,
    how_to_interpret_trust, how_to_interpret_runtime, how_to_interpret_profile, optional_missing.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "what_system_can_do": [],
        "simulate_only_explained": [],
        "approvals_that_matter": [],
        "recommended_first_workflow": "",
        "how_to_interpret_trust": "",
        "how_to_interpret_runtime": "",
        "how_to_interpret_profile": "",
        "optional_missing": [],
    }

    # First-run summary
    try:
        from workflow_dataset.onboarding.product_summary import build_first_run_summary
        summary = build_first_run_summary(repo_root=root)
        out["what_system_can_do"] = list(summary.get("what_can_do_safely", []))
        out["simulate_only_explained"] = [
            "Adapters or actions marked simulate-only cannot perform real writes or app control; they only simulate.",
            "Jobs and routines can run in --mode simulate without any approval; real mode requires approval registry and trusted actions.",
        ]
        out["simulate_only_explained"].extend(
            str(s) for s in summary.get("simulate_only", [])[:5] if isinstance(s, str)
        )
        out["recommended_first_workflow"] = summary.get("recommended_first_workflow", "workflow-dataset onboard bootstrap")
    except Exception as e:
        out["what_system_can_do"].append(f"(Summary unavailable: {e})")
        out["recommended_first_workflow"] = "workflow-dataset onboard bootstrap"

    # Approvals that matter
    out["approvals_that_matter"] = [
        "Approval registry: data/local/capability_discovery/approvals.yaml. Without it, real execution is blocked.",
        "approved_paths: directories the system may read/write for real execution.",
        "approved_action_scopes: adapter.action_id entries you explicitly allow (executable: true).",
        "Run 'workflow-dataset onboard approve' to review and approve path/app/action scopes (no auto-grant).",
    ]

    # How to interpret trust
    out["how_to_interpret_trust"] = (
        "Trust cockpit (workflow-dataset trust cockpit) shows: benchmark trust status, whether the approval registry exists, "
        "and release-gate staged count. Simulate-only jobs always run in simulate; trusted_for_real jobs need the registry and "
        "approved scopes. Use trust release-gates to see what is staged for release."
    )

    # How to interpret runtime
    out["how_to_interpret_runtime"] = (
        "Runtime (workflow-dataset runtime backends | catalog | profile) shows: available backends, model catalog, "
        "recommended model per task class, integrations (local-only by default). Use runtime status for active capabilities; "
        "runtime recommend for task-specific model suggestions."
    )

    # How to interpret profile
    out["how_to_interpret_profile"] = (
        "Profile (workflow-dataset profile show) shows: user work profile (field, job family, automation preference) and "
        "bootstrap profile (machine_id, adapters, approvals count, trusted real actions, recommended job packs). "
        "profile operator-summary gives recommended domain pack, model classes, and specialization route."
    )

    # Optional missing (incubator, etc.)
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(root)
        if state.get("incubator_state", {}).get("error"):
            out["optional_missing"].append("Incubator module (optional): not installed; mission-control still runs.")
    except Exception:
        pass

    return out


def format_tour_text(tour: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Format first-run tour as plain text."""
    if tour is None:
        tour = build_first_run_tour(repo_root)
    lines = [
        "=== First-run guided tour (M23X) ===",
        "",
        "--- What the system can do now ---",
        "",
    ]
    for s in tour.get("what_system_can_do", []):
        lines.append(f"  · {s}")
    lines.extend([
        "",
        "--- What is still simulate-only ---",
        "",
    ])
    for s in tour.get("simulate_only_explained", []):
        lines.append(f"  · {s}")
    lines.extend([
        "",
        "--- What approvals matter ---",
        "",
    ])
    for s in tour.get("approvals_that_matter", []):
        lines.append(f"  · {s}")
    lines.extend([
        "",
        "--- Recommended first workflow ---",
        "",
        "  " + tour.get("recommended_first_workflow", "workflow-dataset onboard bootstrap"),
        "",
        "--- How to interpret trust ---",
        "",
        "  " + tour.get("how_to_interpret_trust", ""),
        "",
        "--- How to interpret runtime ---",
        "",
        "  " + tour.get("how_to_interpret_runtime", ""),
        "",
        "--- How to interpret profile ---",
        "",
        "  " + tour.get("how_to_interpret_profile", ""),
        "",
    ])
    if tour.get("optional_missing"):
        lines.append("--- Optional missing pieces ---")
        lines.append("")
        for m in tour["optional_missing"]:
            lines.append(f"  · {m}")
        lines.append("")
    lines.append("(Operator-controlled. No automatic changes.)")
    return "\n".join(lines)
