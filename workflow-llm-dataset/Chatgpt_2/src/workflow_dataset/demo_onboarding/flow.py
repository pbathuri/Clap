"""
M51E–M51H: Demo onboarding flow — start, role, bootstrap memory, ready state, sequence.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from workflow_dataset.demo_onboarding.models import (
    DemoOnboardingSession,
    DemoWorkspaceSource,
    MemoryBootstrapPlan,
    OnboardingCompletionState,
    ReadyToAssistState,
    BootstrapConfidence,
)
from workflow_dataset.demo_onboarding.presets import get_role_preset, get_default_role_preset, list_role_preset_ids
from workflow_dataset.demo_onboarding.user_presets import get_demo_user_preset, list_demo_user_preset_ids
from workflow_dataset.demo_onboarding.workspace_packs import resolve_workspace_pack_path
from workflow_dataset.demo_onboarding.store import (
    save_session,
    load_session,
    save_bootstrap_summary,
    load_bootstrap_summary,
)
from workflow_dataset.demo_onboarding.memory_bootstrap import (
    run_bounded_memory_bootstrap,
    default_bundled_sample_path,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def demo_onboarding_start(repo_root: Path | str | None = None, reset: bool = False) -> DemoOnboardingSession:
    """Start or reset demo onboarding session."""
    root = _repo_root(repo_root)
    if reset:
        session = DemoOnboardingSession(
            session_id=str(uuid.uuid4())[:12],
            started_at_utc=utc_now_iso(),
            role_preset_id="",
            memory_bootstrap_completed=False,
            trust_posture_id="",
            demo_user_preset_id="",
            workspace_pack_id="",
        )
    else:
        existing = load_session(root)
        if existing:
            return existing
        session = DemoOnboardingSession(
            session_id=str(uuid.uuid4())[:12],
            started_at_utc=utc_now_iso(),
            role_preset_id="",
            memory_bootstrap_completed=False,
            trust_posture_id="",
            demo_user_preset_id="",
            workspace_pack_id="",
        )
    save_session(session, root)
    return session


def demo_onboarding_select_role(
    preset_id: str,
    repo_root: Path | str | None = None,
) -> tuple[DemoOnboardingSession | None, str]:
    """Bind role preset. Returns (session, error_message)."""
    root = _repo_root(repo_root)
    preset = get_role_preset(preset_id)
    if not preset:
        return None, f"Unknown preset_id. Use one of: {', '.join(list_role_preset_ids())}"
    session = load_session(root) or demo_onboarding_start(root)
    session.role_preset_id = preset_id
    session.trust_posture_id = (preset.trust_posture.posture_id if preset.trust_posture else "demo_conservative")
    save_session(session, root)
    return session, ""


def demo_onboarding_apply_user_preset(
    user_preset_id: str,
    repo_root: Path | str | None = None,
) -> tuple[DemoOnboardingSession | None, str]:
    """Apply demo user preset: sets role, workspace pack id, trust. Returns (session, error)."""
    root = _repo_root(repo_root)
    up = get_demo_user_preset(user_preset_id)
    if not up:
        return None, f"Unknown user preset. Use one of: {', '.join(list_demo_user_preset_ids())}"
    preset = get_role_preset(up.role_preset_id)
    if not preset:
        return None, f"Role preset missing: {up.role_preset_id}"
    session = load_session(root) or demo_onboarding_start(root)
    session.demo_user_preset_id = user_preset_id
    session.role_preset_id = up.role_preset_id
    session.workspace_pack_id = up.workspace_pack_id
    session.trust_posture_id = (preset.trust_posture.posture_id if preset.trust_posture else "demo_conservative")
    session.memory_bootstrap_completed = False
    save_session(session, root)
    return session, ""


def demo_onboarding_bootstrap_memory(
    workspace_path: str | None,
    repo_root: Path | str | None = None,
    *,
    pack_id: str | None = None,
) -> dict[str, Any]:
    """Run bounded memory bootstrap. Path, --pack id, session workspace_pack_id, or default bundled path."""
    root = _repo_root(repo_root)
    session = load_session(root)
    if not session:
        return {"error": "No demo session. Run: workflow-dataset demo onboarding start"}
    ws: Path | None = None
    source_kind = "bundled_sample"
    if workspace_path:
        ws = Path(workspace_path).resolve()
        source_kind = "user_path"
    elif pack_id:
        ws = resolve_workspace_pack_path(pack_id.strip(), root)
        source_kind = "workspace_pack"
        if not ws:
            return {"error": f"Workspace pack not found: {pack_id}", "hint": "demo onboarding workspace-pack --list"}
    elif session.workspace_pack_id:
        ws = resolve_workspace_pack_path(session.workspace_pack_id, root)
        source_kind = "workspace_pack"
    if ws is None or not ws.is_dir():
        ws = default_bundled_sample_path(root)
        source_kind = "bundled_sample"
    if not ws.is_dir():
        return {"error": f"Demo workspace not found or not a directory: {ws}", "hint": "Use --path or --pack; see demo onboarding workspace-pack --list."}

    plan = MemoryBootstrapPlan(
        plan_id="demo_bootstrap_v1",
        workspace_root=str(ws),
        file_globs=["*.md", "*.txt"],
        max_files=15,
        ingest_to_memory_substrate=True,
        ingest_to_personal_graph=True,
    )
    summary = run_bounded_memory_bootstrap(ws, repo_root=root, plan=plan, session_id=session.session_id)
    summary["workspace_pack_id_used"] = pack_id or (session.workspace_pack_id if source_kind == "workspace_pack" else "")
    save_bootstrap_summary(summary, root)
    session.memory_bootstrap_completed = True
    session.workspace_source = DemoWorkspaceSource(
        source_kind=source_kind,
        path=str(ws),
        max_files=15,
        max_bytes_per_file=8192,
    )
    session.memory_bootstrap_plan = plan
    save_session(session, root)
    return summary


def build_completion_state(repo_root: Path | str | None = None) -> OnboardingCompletionState:
    root = _repo_root(repo_root)
    session = load_session(root)
    missing: list[str] = []
    role_selected = bool(session and session.role_preset_id)
    memory_done = bool(session and session.memory_bootstrap_completed)
    if not session:
        missing.extend(["start session", "select role", "bootstrap memory"])
    else:
        if not role_selected:
            missing.append("select role: demo onboarding user-preset --id investor_demo_primary  OR  role --id <preset>")
        if not memory_done:
            missing.append("bootstrap memory (demo onboarding bootstrap-memory)")
    trust_acknowledged = role_selected  # choosing role implies demo trust posture shown
    ready = role_selected and memory_done
    return OnboardingCompletionState(
        role_selected=role_selected,
        memory_bootstrapped=memory_done,
        trust_acknowledged=trust_acknowledged,
        ready_for_assist=ready,
        missing_steps=missing,
    )


def build_ready_to_assist_state(repo_root: Path | str | None = None) -> ReadyToAssistState:
    """Build ready-to-assist state from session + bootstrap summary."""
    root = _repo_root(repo_root)
    session = load_session(root)
    summary = load_bootstrap_summary(root)
    completion = build_completion_state(root)

    default_preset = get_default_role_preset()
    preset = get_role_preset(session.role_preset_id) if session and session.role_preset_id else None
    effective = preset or default_preset

    conf_dict = summary.get("confidence") or {}
    confidence = BootstrapConfidence.from_dict(conf_dict) if conf_dict else None

    next_setup = [
        f"workflow-dataset day preset set --id {effective.day_preset_id}",
        f"workflow-dataset defaults apply {effective.default_experience_profile}",
        "workflow-dataset onboard status",
    ]

    if not completion.ready_for_assist:
        return ReadyToAssistState(
            ready=False,
            chosen_role_label=preset.label if preset else "(role not selected — try founder_operator_demo)",
            vertical_pack_id=preset.vertical_pack_id if preset else "",
            memory_bootstrap_summary="Memory bootstrap not complete." if not completion.memory_bootstrapped else summary.get("disclaimer", ""),
            inferred_project_context=summary.get("project_hints", []),
            recurring_themes=summary.get("recurring_themes", []),
            work_style_hints=summary.get("work_style_hints", []),
            likely_priorities=summary.get("likely_priorities", []),
            recommended_first_value_action=effective.recommended_first_value_command,
            confirmation_message="Complete missing steps: " + "; ".join(completion.missing_steps),
            bootstrap_confidence=confidence,
            next_setup_commands=next_setup,
        )

    mem_summary = (
        f"Scanned {summary.get('files_scanned', 0)} sample files; "
        f"{summary.get('memory_units_created', 0)} memory unit(s). "
        f"{summary.get('disclaimer', '')}"
    )

    return ReadyToAssistState(
        ready=True,
        chosen_role_label=preset.label if preset else effective.label,
        vertical_pack_id=preset.vertical_pack_id if preset else effective.vertical_pack_id,
        memory_bootstrap_summary=mem_summary,
        inferred_project_context=list(summary.get("project_hints", [])),
        recurring_themes=list(summary.get("recurring_themes", [])),
        work_style_hints=list(summary.get("work_style_hints", [])),
        likely_priorities=list(summary.get("likely_priorities", [])),
        recommended_first_value_action=(preset or effective).recommended_first_value_command,
        confirmation_message="Ready to assist — demo onboarding complete. Role and sample context are loaded; full approvals still via onboard approve.",
        bootstrap_confidence=confidence,
        next_setup_commands=next_setup,
    )


def build_demo_sequence(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Ordered first-run sequence for investor demo."""
    return {
        "title": "USB demo → first-run sequence (M51)",
        "default_role": "founder_operator_demo",
        "steps": [
            {"step": 1, "command": "workflow-dataset demo onboarding start --reset", "description": "Create demo session (reset for clean investor run)."},
            {"step": 2, "command": "workflow-dataset demo onboarding user-preset --id investor_demo_primary", "description": "Apply demo user preset (role + workspace pack) — or role --id manually."},
            {"step": 3, "command": "workflow-dataset demo onboarding bootstrap-memory", "description": "Ingest pack tied to preset (or --path / --pack)."},
            {"step": 4, "command": "workflow-dataset demo onboarding ready-state", "description": "Show ready-to-assist summary."},
            {"step": 5, "command": "workflow-dataset day preset set --id founder_operator", "description": "Apply workday preset for chosen role (see ready-state for exact id)."},
            {"step": 6, "command": "workflow-dataset defaults apply calm_default", "description": "Apply experience profile."},
        ],
    }
