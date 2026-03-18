"""
M45I–M45L: Persist supervisory control state under data/local/supervisory_control/.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.supervisory_control.models import (
    SupervisedLoopView,
    OperatorIntervention,
    PauseState,
    RedirectState,
    TakeoverState,
    HandbackState,
    OperatorRationale,
    LoopControlAuditNote,
    SupervisionPreset,
    TakeoverPlaybook,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _control_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / "data" / "local" / "supervisory_control"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# ----- Loop views -----
def _loops_path(root: Path) -> Path:
    return root / "loops.json"


def load_loop_views(repo_root: Path | str | None = None) -> list[SupervisedLoopView]:
    p = _loops_path(_control_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("loops", []):
            out.append(SupervisedLoopView(
                loop_id=d.get("loop_id", ""),
                label=d.get("label", ""),
                status=d.get("status", "active"),
                project_slug=d.get("project_slug", ""),
                goal_text=d.get("goal_text", ""),
                cycle_id=d.get("cycle_id", ""),
                pending_count=int(d.get("pending_count", 0)),
                last_activity_utc=d.get("last_activity_utc", ""),
                created_at_utc=d.get("created_at_utc", ""),
                updated_at_utc=d.get("updated_at_utc", ""),
            ))
        return out
    except Exception:
        return []


def save_loop_views(loops: list[SupervisedLoopView], repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    _ensure_dir(root)
    p = _loops_path(root)
    data = {"loops": [v.to_dict() for v in loops], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- Interventions -----
def _interventions_path(root: Path) -> Path:
    return root / "interventions.json"


def load_interventions(repo_root: Path | str | None = None) -> list[OperatorIntervention]:
    p = _interventions_path(_control_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("interventions", []):
            out.append(OperatorIntervention(
                intervention_id=d.get("intervention_id", ""),
                loop_id=d.get("loop_id", ""),
                kind=d.get("kind", ""),
                created_at_utc=d.get("created_at_utc", ""),
                operator_id=d.get("operator_id", ""),
                rationale_id=d.get("rationale_id", ""),
                payload=dict(d.get("payload", {})),
            ))
        return out
    except Exception:
        return []


def append_intervention(intervention: OperatorIntervention, repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    _ensure_dir(root)
    p = _interventions_path(root)
    data = {"interventions": [], "updated": utc_now_iso()}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["interventions"] = data.get("interventions", []) + [intervention.to_dict()]
    data["updated"] = utc_now_iso()
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- Pause / Redirect / Takeover / Handback (per-loop state) -----
def _loop_state_path(root: Path, loop_id: str, suffix: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in loop_id) or "default"
    return root / "loops" / safe / f"{suffix}.json"


def load_pause_state(loop_id: str, repo_root: Path | str | None = None) -> PauseState | None:
    p = _loop_state_path(_control_dir(repo_root), loop_id, "pause")
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return PauseState(loop_id=d.get("loop_id", loop_id), paused_at_utc=d.get("paused_at_utc", ""), reason=d.get("reason", ""), resumed_at_utc=d.get("resumed_at_utc", ""))
    except Exception:
        return None


def save_pause_state(state: PauseState | None, repo_root: Path | str | None = None, loop_id: str = "") -> None:
    root = _control_dir(repo_root)
    lid = (state.loop_id if state else "") or loop_id or "default"
    p = _loop_state_path(root, lid, "pause")
    if state is None:
        if p.exists():
            p.unlink()
        return
    _ensure_dir(p.parent)
    p.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_redirect_state(loop_id: str, repo_root: Path | str | None = None) -> RedirectState | None:
    p = _loop_state_path(_control_dir(repo_root), loop_id, "redirect")
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return RedirectState(loop_id=d.get("loop_id", loop_id), redirect_at_utc=d.get("redirect_at_utc", ""), next_step_hint=d.get("next_step_hint", ""), applied=d.get("applied", False))
    except Exception:
        return None


def save_redirect_state(state: RedirectState | None, repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    p = _loop_state_path(root, state.loop_id if state else "default", "redirect")
    if state is None:
        if p.exists():
            p.unlink()
        return
    _ensure_dir(p.parent)
    p.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_takeover_state(loop_id: str, repo_root: Path | str | None = None) -> TakeoverState | None:
    p = _loop_state_path(_control_dir(repo_root), loop_id, "takeover")
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return TakeoverState(loop_id=d.get("loop_id", loop_id), taken_over_at_utc=d.get("taken_over_at_utc", ""), operator_note=d.get("operator_note", ""), returned_at_utc=d.get("returned_at_utc", ""))
    except Exception:
        return None


def save_takeover_state(state: TakeoverState | None, repo_root: Path | str | None = None, loop_id: str = "") -> None:
    root = _control_dir(repo_root)
    lid = (state.loop_id if state else "") or loop_id or "default"
    p = _loop_state_path(root, lid, "takeover")
    if state is None:
        if p.exists():
            p.unlink()
        return
    _ensure_dir(p.parent)
    p.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_last_handback(loop_id: str, repo_root: Path | str | None = None) -> HandbackState | None:
    p = _loop_state_path(_control_dir(repo_root), loop_id, "handback")
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return HandbackState(loop_id=d.get("loop_id", loop_id), handback_at_utc=d.get("handback_at_utc", ""), handback_note=d.get("handback_note", ""), safe_to_resume=d.get("safe_to_resume", True))
    except Exception:
        return None


def save_handback_state(state: HandbackState, repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    p = _loop_state_path(root, state.loop_id, "handback")
    _ensure_dir(p.parent)
    p.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


# ----- Rationales -----
def _rationales_path(root: Path) -> Path:
    return root / "rationales.json"


def load_rationales(repo_root: Path | str | None = None) -> list[OperatorRationale]:
    p = _rationales_path(_control_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return [OperatorRationale(**{k: d.get(k, "") for k in ("rationale_id", "text", "created_at_utc", "attached_to_intervention_id", "attached_to_loop_id")}) for d in data.get("rationales", [])]
    except Exception:
        return []


def append_rationale(r: OperatorRationale, repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    _ensure_dir(root)
    p = _rationales_path(root)
    data = {"rationales": [], "updated": utc_now_iso()}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["rationales"] = data.get("rationales", []) + [r.to_dict()]
    data["updated"] = utc_now_iso()
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- Audit notes -----
def _audit_notes_path(root: Path) -> Path:
    return root / "audit_notes.json"


def load_audit_notes(repo_root: Path | str | None = None, loop_id: str = "") -> list[LoopControlAuditNote]:
    p = _audit_notes_path(_control_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = [LoopControlAuditNote(**{k: d.get(k, "") for k in ("note_id", "loop_id", "intervention_id", "created_at_utc", "note_text", "kind")}) for d in data.get("notes", [])]
        if loop_id:
            out = [n for n in out if n.loop_id == loop_id]
        return out
    except Exception:
        return []


def append_audit_note(note: LoopControlAuditNote, repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    _ensure_dir(root)
    p = _audit_notes_path(root)
    data = {"notes": [], "updated": utc_now_iso()}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["notes"] = data.get("notes", []) + [note.to_dict()]
    data["updated"] = utc_now_iso()
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- M45L.1: Supervision presets -----
def _presets_path(root: Path) -> Path:
    return root / "supervision_presets.json"


def load_supervision_presets(repo_root: Path | str | None = None) -> list[SupervisionPreset]:
    p = _presets_path(_control_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("presets", []):
            out.append(SupervisionPreset(
                preset_id=d.get("preset_id", ""),
                label=d.get("label", ""),
                description=d.get("description", ""),
                auto_pause_on_blocked=bool(d.get("auto_pause_on_blocked", False)),
                require_approval_before_real=bool(d.get("require_approval_before_real", True)),
                max_pending_before_escalation=int(d.get("max_pending_before_escalation", 0)),
                suggest_takeover_on_repeated_failure=bool(d.get("suggest_takeover_on_repeated_failure", False)),
                repeated_failure_count=int(d.get("repeated_failure_count", 3)),
                when_to_continue_hint=d.get("when_to_continue_hint", ""),
                when_to_intervene_hint=d.get("when_to_intervene_hint", ""),
                when_to_terminate_hint=d.get("when_to_terminate_hint", ""),
            ))
        return out
    except Exception:
        return []


def save_supervision_presets(presets: list[SupervisionPreset], repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    _ensure_dir(root)
    p = _presets_path(root)
    data = {"presets": [x.to_dict() for x in presets], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- M45L.1: Takeover playbooks -----
def _playbooks_path(root: Path) -> Path:
    return root / "takeover_playbooks.json"


def load_takeover_playbooks(repo_root: Path | str | None = None) -> list[TakeoverPlaybook]:
    p = _playbooks_path(_control_dir(repo_root))
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out = []
        for d in data.get("playbooks", []):
            out.append(TakeoverPlaybook(
                playbook_id=d.get("playbook_id", ""),
                label=d.get("label", ""),
                trigger_condition=d.get("trigger_condition", ""),
                description=d.get("description", ""),
                suggested_actions=list(d.get("suggested_actions", [])),
                when_to_continue=d.get("when_to_continue", ""),
                when_to_intervene=d.get("when_to_intervene", ""),
                when_to_terminate=d.get("when_to_terminate", ""),
            ))
        return out
    except Exception:
        return []


def save_takeover_playbooks(playbooks: list[TakeoverPlaybook], repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    _ensure_dir(root)
    p = _playbooks_path(root)
    data = {"playbooks": [x.to_dict() for x in playbooks], "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ----- M45L.1: Current preset (active) -----
def _current_preset_path(root: Path) -> Path:
    return root / "current_preset.json"


def load_current_preset_id(repo_root: Path | str | None = None) -> str:
    p = _current_preset_path(_control_dir(repo_root))
    if not p.exists():
        return "balanced"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return str(data.get("preset_id", "balanced"))
    except Exception:
        return "balanced"


def save_current_preset_id(preset_id: str, repo_root: Path | str | None = None) -> None:
    root = _control_dir(repo_root)
    _ensure_dir(root)
    p = _current_preset_path(root)
    data = {"preset_id": preset_id, "updated": utc_now_iso()}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
