"""
M34A–M34D: Persist trigger and recurring workflow definitions. Local only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.automations.models import (
    TriggerDefinition,
    RecurringWorkflowDefinition,
    TriggerKind,
    AutomationTemplate,
    AutomationTemplateKind,
    GuardrailProfile,
    GuardrailProfileKind,
)

AUTOMATIONS_DIR = Path("data/local/automations")
TRIGGERS_SUBDIR = "triggers"
WORKFLOWS_SUBDIR = "workflows"
TEMPLATES_SUBDIR = "templates"
GUARDRAILS_SUBDIR = "guardrails"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _triggers_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / AUTOMATIONS_DIR / TRIGGERS_SUBDIR


def _workflows_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / AUTOMATIONS_DIR / WORKFLOWS_SUBDIR


def list_trigger_ids(repo_root: Path | str | None = None) -> list[str]:
    """List all trigger definition ids (from JSON files in triggers dir)."""
    d = _triggers_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_trigger(trigger_id: str, repo_root: Path | str | None = None) -> TriggerDefinition | None:
    """Load a trigger definition by id."""
    path = _triggers_dir(repo_root) / f"{trigger_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") and isinstance(data["kind"], str):
            data["kind"] = TriggerKind(data["kind"])
        return TriggerDefinition.model_validate(data)
    except Exception:
        return None


def save_trigger(trigger: TriggerDefinition, repo_root: Path | str | None = None) -> Path:
    """Save a trigger definition. Creates dir if needed."""
    d = _triggers_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{trigger.trigger_id or 'trigger'}.json"
    data = trigger.model_dump()
    data["kind"] = trigger.kind.value
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def list_workflow_ids(repo_root: Path | str | None = None) -> list[str]:
    """List all recurring workflow definition ids."""
    d = _workflows_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_workflow(workflow_id: str, repo_root: Path | str | None = None) -> RecurringWorkflowDefinition | None:
    """Load a recurring workflow definition by id."""
    path = _workflows_dir(repo_root) / f"{workflow_id}.json"
    if not path.exists():
        return None
    try:
        return RecurringWorkflowDefinition.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def save_workflow(workflow: RecurringWorkflowDefinition, repo_root: Path | str | None = None) -> Path:
    """Save a recurring workflow definition."""
    d = _workflows_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{workflow.workflow_id or 'workflow'}.json"
    path.write_text(json.dumps(workflow.model_dump(), indent=2), encoding="utf-8")
    return path


# ----- M34D.1 Templates -----


def _templates_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / AUTOMATIONS_DIR / TEMPLATES_SUBDIR


def list_template_ids(repo_root: Path | str | None = None) -> list[str]:
    """List all automation template ids."""
    d = _templates_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_template(template_id: str, repo_root: Path | str | None = None) -> AutomationTemplate | None:
    """Load an automation template by id."""
    path = _templates_dir(repo_root) / f"{template_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") and isinstance(data["kind"], str):
            data["kind"] = AutomationTemplateKind(data["kind"])
        return AutomationTemplate.model_validate(data)
    except Exception:
        return None


def save_template(template: AutomationTemplate, repo_root: Path | str | None = None) -> Path:
    """Save an automation template."""
    d = _templates_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{template.template_id or 'template'}.json"
    data = template.model_dump()
    data["kind"] = template.kind.value
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


# ----- M34D.1 Guardrail profiles -----


def _guardrails_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / AUTOMATIONS_DIR / GUARDRAILS_SUBDIR


def list_guardrail_profile_ids(repo_root: Path | str | None = None) -> list[str]:
    """List all guardrail profile ids."""
    d = _guardrails_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_guardrail_profile(profile_id: str, repo_root: Path | str | None = None) -> GuardrailProfile | None:
    """Load a guardrail profile by id."""
    path = _guardrails_dir(repo_root) / f"{profile_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") and isinstance(data["kind"], str):
            data["kind"] = GuardrailProfileKind(data["kind"])
        return GuardrailProfile.model_validate(data)
    except Exception:
        return None


def save_guardrail_profile(profile: GuardrailProfile, repo_root: Path | str | None = None) -> Path:
    """Save a guardrail profile."""
    d = _guardrails_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{profile.profile_id or 'profile'}.json"
    data = profile.model_dump()
    data["kind"] = profile.kind.value
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def get_active_guardrail_profile(repo_root: Path | str | None = None) -> GuardrailProfile | None:
    """Return the active guardrail profile (first with is_default=True, else first by id)."""
    root = _root(repo_root)
    ids = list_guardrail_profile_ids(repo_root=root)
    default: GuardrailProfile | None = None
    first: GuardrailProfile | None = None
    for pid in ids:
        p = get_guardrail_profile(pid, repo_root=root)
        if not p:
            continue
        if first is None:
            first = p
        if p.is_default:
            default = p
            break
    return default if default is not None else first
