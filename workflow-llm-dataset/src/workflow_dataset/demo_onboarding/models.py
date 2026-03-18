"""
M51E–M51H: Demo onboarding models — session, role preset, workspace source, memory bootstrap, completion, ready-to-assist, trust, confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrustPostureSelection:
    """Trust/governance posture for demo mode (labels only; no auto-approve)."""
    posture_id: str = ""
    label: str = ""
    description: str = ""
    simulate_first: bool = True
    approval_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "posture_id": self.posture_id,
            "label": self.label,
            "description": self.description,
            "simulate_first": self.simulate_first,
            "approval_note": self.approval_note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TrustPostureSelection":
        return cls(
            posture_id=d.get("posture_id", ""),
            label=d.get("label", ""),
            description=d.get("description", ""),
            simulate_first=bool(d.get("simulate_first", True)),
            approval_note=d.get("approval_note", ""),
        )


@dataclass
class RolePreset:
    """Demo role preset: vertical pack, day preset, trust, explanation."""
    preset_id: str = ""
    label: str = ""
    description: str = ""
    vertical_pack_id: str = ""
    day_preset_id: str = ""
    default_experience_profile: str = ""   # calm_default | first_user
    trust_posture: TrustPostureSelection | None = None
    enabled_surfaces_hint: list[str] = field(default_factory=list)
    recommended_first_value_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "vertical_pack_id": self.vertical_pack_id,
            "day_preset_id": self.day_preset_id,
            "default_experience_profile": self.default_experience_profile,
            "trust_posture": self.trust_posture.to_dict() if self.trust_posture else None,
            "enabled_surfaces_hint": list(self.enabled_surfaces_hint),
            "recommended_first_value_command": self.recommended_first_value_command,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RolePreset":
        tp = d.get("trust_posture")
        return cls(
            preset_id=d.get("preset_id", ""),
            label=d.get("label", ""),
            description=d.get("description", ""),
            vertical_pack_id=d.get("vertical_pack_id", ""),
            day_preset_id=d.get("day_preset_id", ""),
            default_experience_profile=d.get("default_experience_profile", ""),
            trust_posture=TrustPostureSelection.from_dict(tp) if tp else None,
            enabled_surfaces_hint=list(d.get("enabled_surfaces_hint") or []),
            recommended_first_value_command=d.get("recommended_first_value_command", ""),
        )


@dataclass
class DemoWorkspaceSource:
    """Where demo sample files come from."""
    source_kind: str = ""   # bundled_sample | user_path
    path: str = ""
    max_files: int = 0
    max_bytes_per_file: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "path": self.path,
            "max_files": self.max_files,
            "max_bytes_per_file": self.max_bytes_per_file,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DemoWorkspaceSource":
        return cls(
            source_kind=d.get("source_kind", ""),
            path=d.get("path", ""),
            max_files=int(d.get("max_files", 0)),
            max_bytes_per_file=int(d.get("max_bytes_per_file", 0)),
        )


@dataclass
class MemoryBootstrapPlan:
    """Plan for bounded memory bootstrap."""
    plan_id: str = ""
    workspace_root: str = ""
    file_globs: list[str] = field(default_factory=list)
    max_files: int = 15
    ingest_to_memory_substrate: bool = True
    ingest_to_personal_graph: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "workspace_root": self.workspace_root,
            "file_globs": list(self.file_globs),
            "max_files": self.max_files,
            "ingest_to_memory_substrate": self.ingest_to_memory_substrate,
            "ingest_to_personal_graph": self.ingest_to_personal_graph,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MemoryBootstrapPlan":
        return cls(
            plan_id=d.get("plan_id", ""),
            workspace_root=d.get("workspace_root", ""),
            file_globs=list(d.get("file_globs") or []),
            max_files=int(d.get("max_files", 15)),
            ingest_to_memory_substrate=bool(d.get("ingest_to_memory_substrate", True)),
            ingest_to_personal_graph=bool(d.get("ingest_to_personal_graph", True)),
        )


@dataclass
class BootstrapConfidence:
    """How much we could infer (bounded demo)."""
    level: str = ""   # high | medium | low | insufficient
    rationale: str = ""
    files_scanned: int = 0
    memory_units_created: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "rationale": self.rationale,
            "files_scanned": self.files_scanned,
            "memory_units_created": self.memory_units_created,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BootstrapConfidence":
        return cls(
            level=d.get("level", ""),
            rationale=d.get("rationale", ""),
            files_scanned=int(d.get("files_scanned", 0)),
            memory_units_created=int(d.get("memory_units_created", 0)),
        )


@dataclass
class SampleWorkspacePack:
    """Bundled sample folder for investor-demo memory bootstrap (bounded .md/.txt)."""
    pack_id: str = ""
    label: str = ""
    description: str = ""
    path_relative: str = ""   # relative to repo root, e.g. docs/samples/demo_onboarding_workspace
    suggested_role_preset_ids: list[str] = field(default_factory=list)
    demo_talking_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "label": self.label,
            "description": self.description,
            "path_relative": self.path_relative,
            "suggested_role_preset_ids": list(self.suggested_role_preset_ids),
            "demo_talking_points": list(self.demo_talking_points),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SampleWorkspacePack":
        return cls(
            pack_id=d.get("pack_id", ""),
            label=d.get("label", ""),
            description=d.get("description", ""),
            path_relative=d.get("path_relative", ""),
            suggested_role_preset_ids=list(d.get("suggested_role_preset_ids") or []),
            demo_talking_points=list(d.get("demo_talking_points") or []),
        )


@dataclass
class DemoUserPreset:
    """Operator-facing demo user: role + workspace pack + staging hints (M51H.1)."""
    user_preset_id: str = ""
    label: str = ""
    role_preset_id: str = ""
    workspace_pack_id: str = ""
    investor_narrative: str = ""
    staging_checklist: list[str] = field(default_factory=list)
    operator_setup_commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_preset_id": self.user_preset_id,
            "label": self.label,
            "role_preset_id": self.role_preset_id,
            "workspace_pack_id": self.workspace_pack_id,
            "investor_narrative": self.investor_narrative,
            "staging_checklist": list(self.staging_checklist),
            "operator_setup_commands": list(self.operator_setup_commands),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DemoUserPreset":
        return cls(
            user_preset_id=d.get("user_preset_id", ""),
            label=d.get("label", ""),
            role_preset_id=d.get("role_preset_id", ""),
            workspace_pack_id=d.get("workspace_pack_id", ""),
            investor_narrative=d.get("investor_narrative", ""),
            staging_checklist=list(d.get("staging_checklist") or []),
            operator_setup_commands=list(d.get("operator_setup_commands") or []),
        )


@dataclass
class DemoOnboardingSession:
    """Demo onboarding session state."""
    session_id: str = ""
    started_at_utc: str = ""
    role_preset_id: str = ""
    workspace_source: DemoWorkspaceSource | None = None
    memory_bootstrap_completed: bool = False
    memory_bootstrap_plan: MemoryBootstrapPlan | None = None
    trust_posture_id: str = ""
    demo_user_preset_id: str = ""
    workspace_pack_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at_utc": self.started_at_utc,
            "role_preset_id": self.role_preset_id,
            "workspace_source": self.workspace_source.to_dict() if self.workspace_source else None,
            "memory_bootstrap_completed": self.memory_bootstrap_completed,
            "memory_bootstrap_plan": self.memory_bootstrap_plan.to_dict() if self.memory_bootstrap_plan else None,
            "trust_posture_id": self.trust_posture_id,
            "demo_user_preset_id": self.demo_user_preset_id,
            "workspace_pack_id": self.workspace_pack_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DemoOnboardingSession":
        ws = d.get("workspace_source")
        mp = d.get("memory_bootstrap_plan")
        return cls(
            session_id=d.get("session_id", ""),
            started_at_utc=d.get("started_at_utc", ""),
            role_preset_id=d.get("role_preset_id", ""),
            workspace_source=DemoWorkspaceSource.from_dict(ws) if ws else None,
            memory_bootstrap_completed=bool(d.get("memory_bootstrap_completed", False)),
            memory_bootstrap_plan=MemoryBootstrapPlan.from_dict(mp) if mp else None,
            trust_posture_id=d.get("trust_posture_id", ""),
            demo_user_preset_id=d.get("demo_user_preset_id", ""),
            workspace_pack_id=d.get("workspace_pack_id", ""),
        )


@dataclass
class OnboardingCompletionState:
    """Whether onboarding steps are done."""
    role_selected: bool = False
    memory_bootstrapped: bool = False
    trust_acknowledged: bool = False
    ready_for_assist: bool = False
    missing_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_selected": self.role_selected,
            "memory_bootstrapped": self.memory_bootstrapped,
            "trust_acknowledged": self.trust_acknowledged,
            "ready_for_assist": self.ready_for_assist,
            "missing_steps": list(self.missing_steps),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "OnboardingCompletionState":
        return cls(
            role_selected=bool(d.get("role_selected", False)),
            memory_bootstrapped=bool(d.get("memory_bootstrapped", False)),
            trust_acknowledged=bool(d.get("trust_acknowledged", False)),
            ready_for_assist=bool(d.get("ready_for_assist", False)),
            missing_steps=list(d.get("missing_steps") or []),
        )


@dataclass
class ReadyToAssistState:
    """Post-demo onboarding: ready to assist."""
    ready: bool = False
    chosen_role_label: str = ""
    vertical_pack_id: str = ""
    memory_bootstrap_summary: str = ""
    inferred_project_context: list[str] = field(default_factory=list)
    recurring_themes: list[str] = field(default_factory=list)
    work_style_hints: list[str] = field(default_factory=list)
    likely_priorities: list[str] = field(default_factory=list)
    recommended_first_value_action: str = ""
    confirmation_message: str = ""
    bootstrap_confidence: BootstrapConfidence | None = None
    next_setup_commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "chosen_role_label": self.chosen_role_label,
            "vertical_pack_id": self.vertical_pack_id,
            "memory_bootstrap_summary": self.memory_bootstrap_summary,
            "inferred_project_context": list(self.inferred_project_context),
            "recurring_themes": list(self.recurring_themes),
            "work_style_hints": list(self.work_style_hints),
            "likely_priorities": list(self.likely_priorities),
            "recommended_first_value_action": self.recommended_first_value_action,
            "confirmation_message": self.confirmation_message,
            "bootstrap_confidence": self.bootstrap_confidence.to_dict() if self.bootstrap_confidence else None,
            "next_setup_commands": list(self.next_setup_commands),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReadyToAssistState":
        bc = d.get("bootstrap_confidence")
        return cls(
            ready=bool(d.get("ready", False)),
            chosen_role_label=d.get("chosen_role_label", ""),
            vertical_pack_id=d.get("vertical_pack_id", ""),
            memory_bootstrap_summary=d.get("memory_bootstrap_summary", ""),
            inferred_project_context=list(d.get("inferred_project_context") or []),
            recurring_themes=list(d.get("recurring_themes") or []),
            work_style_hints=list(d.get("work_style_hints") or []),
            likely_priorities=list(d.get("likely_priorities") or []),
            recommended_first_value_action=d.get("recommended_first_value_action", ""),
            confirmation_message=d.get("confirmation_message", ""),
            bootstrap_confidence=BootstrapConfidence.from_dict(bc) if bc else None,
            next_setup_commands=list(d.get("next_setup_commands") or []),
        )
