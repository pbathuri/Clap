"""
M51I–M51L: Demo mission-control presentation panel (narrow, storytelling).
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.investor_demo.models import DemoMissionControlPanel, DegradedDemoWarning
from workflow_dataset.investor_demo.degraded import collect_degraded_warnings


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_demo_mission_control_panel(repo_root: Path | str | None = None) -> DemoMissionControlPanel:
    root = _root(repo_root)
    degraded = collect_degraded_warnings(root)

    device_line = "Device: local workspace"
    try:
        from workflow_dataset.validation.env_health import check_environment_health
        env = check_environment_health(root)
        device_line = "Environment: required_ok=" + str(env.get("required_ok", False))
    except Exception as e:
        device_line = f"Environment: check failed ({e})"

    role_pack = "founder_operator (demo default)"
    vertical_id = ""
    try:
        from workflow_dataset.vertical_excellence.path_resolver import get_chosen_vertical_id
        vertical_id = get_chosen_vertical_id(root) or ""
        role_pack = vertical_id or role_pack
    except Exception:
        pass

    memory_line = "Memory bootstrap: local continuity state."
    state: dict = {}
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(root)
        ce = state.get("continuity_engine_state") or {}
        if not ce.get("error"):
            cf = (ce.get("most_important_carry_forward") or "")[:120]
            res = (ce.get("strongest_resume_target_label") or "")[:80]
            if cf or res:
                memory_line = f"Carry-forward: {cf or '—'}  Resume: {res or '—'}"
    except Exception:
        memory_line = "Continuity: unavailable in this run."

    project_ctx = "Active context: from local mission-control aggregates."
    try:
        sl = state.get("supervised_loop") or {}
        if not sl.get("error") and sl.get("goal_text"):
            project_ctx = "Goal (supervised loop): " + str(sl.get("goal_text", ""))[:100]
    except Exception:
        pass

    first_value = "First value: run vertical path when ready."
    safe_action = "Safe next: workflow-dataset mission-control"
    evidence = "Evidence: first-value stage and cohort signals from local data."
    try:
        from workflow_dataset.vertical_excellence.mission_control import vertical_excellence_slice
        ve = vertical_excellence_slice(root)
        stage = ve.get("current_first_value_stage") or {}
        first_value = f"First-value stage: {stage.get('status', '—')}  vertical={ve.get('vertical_id', '—')}"
        rec = ve.get("next_recommended_excellence_action") or {}
        if rec.get("command"):
            safe_action = f"Recommended: {rec.get('label', rec.get('command', ''))[:80]}"
        evidence = f"Friction: {ve.get('strongest_friction_label') or 'none surfaced'}  blocked_cases={ve.get('blocked_first_value_cases_count', 0)}"
    except Exception:
        pass

    supervised = "Supervision: simulate-only demos; approval before real execution."
    try:
        sl = state.get("supervised_loop") or {}
        if sl.get("next_proposed_action_label"):
            supervised = f"Next proposed (needs approval): {sl.get('next_proposed_action_label', '')[:100]}"
    except Exception:
        pass

    return DemoMissionControlPanel(
        device_readiness_line=device_line,
        chosen_role_demo_pack=role_pack,
        memory_bootstrap_summary=memory_line,
        active_project_context=project_ctx,
        first_value_opportunity=first_value,
        recommended_safe_action=safe_action,
        evidence_system_learned=evidence,
        supervised_and_safe_posture=supervised,
        degraded_warnings=degraded,
    )


def format_demo_mission_control_text(panel: DemoMissionControlPanel) -> str:
    lines = [
        "=== Investor demo — Mission control (presentation) ===",
        "",
        f"1. Readiness     {panel.device_readiness_line}",
        f"2. Role / pack   {panel.chosen_role_demo_pack}",
        f"3. Memory        {panel.memory_bootstrap_summary}",
        f"4. Context       {panel.active_project_context}",
        f"5. First value   {panel.first_value_opportunity}",
        f"6. Safe action   {panel.recommended_safe_action}",
        f"7. Evidence      {panel.evidence_system_learned}",
        f"8. Supervised    {panel.supervised_and_safe_posture}",
        "",
    ]
    if panel.degraded_warnings:
        lines.append("[Degraded — disclose to audience]")
        for w in panel.degraded_warnings:
            lines.append(f"  • {w.message}")
        lines.append("")
    return "\n".join(lines)
