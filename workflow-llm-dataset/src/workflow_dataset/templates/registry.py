"""
M22E: Template registry. List, load, get template by id. Local YAML under data/local/templates/.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

TEMPLATES_DIR = "data/local/templates"

# Valid workflow ids (current ops/reporting family)
VALID_WORKFLOW_IDS = (
    "weekly_status",
    "status_action_bundle",
    "stakeholder_update_bundle",
    "meeting_brief_bundle",
    "ops_reporting_workspace",
)

# Artifact keys per workflow (subset that workflow can produce)
WORKFLOW_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "weekly_status": ("weekly_status",),
    "status_action_bundle": ("status_brief", "action_register"),
    "stakeholder_update_bundle": ("stakeholder_update", "decision_requests"),
    "meeting_brief_bundle": ("meeting_brief", "action_items"),
    "ops_reporting_workspace": (
        "weekly_status",
        "status_brief",
        "action_register",
        "stakeholder_update",
        "decision_requests",
    ),
}

# Artifact key -> filename
ARTIFACT_TO_FILENAME: dict[str, str] = {
    "weekly_status": "weekly_status.md",
    "status_brief": "status_brief.md",
    "action_register": "action_register.md",
    "stakeholder_update": "stakeholder_update.md",
    "decision_requests": "decision_requests.md",
    "meeting_brief": "meeting_brief.md",
    "action_items": "action_items.md",
}


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def _templates_path(repo_root: Path | str | None) -> Path:
    return _repo_root(repo_root) / TEMPLATES_DIR


def _safe_id(template_id: str) -> str:
    return "".join(c for c in (template_id or "").strip() if c.isalnum() or c in "_-").strip() or "unnamed"


def load_template(
    template_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Load template by id. Looks for <templates_dir>/<id>.yaml or <id>.json.
    Returns dict with id, name?, description?, workflow_id, artifacts (list), wording_hints?.
    Raises FileNotFoundError if not found; validates workflow_id and artifacts.
    """
    root = _repo_root(repo_root)
    tid = _safe_id(template_id)
    if not tid:
        raise ValueError("template id is required")
    base = root / TEMPLATES_DIR
    for ext in (".yaml", ".yml", ".json"):
        path = base / f"{tid}{ext}"
        if path.exists() and path.is_file():
            raw = path.read_text(encoding="utf-8")
            if ext == ".json":
                import json
                data = json.loads(raw)
            else:
                try:
                    import yaml
                    data = yaml.safe_load(raw) or {}
                except Exception:
                    import json
                    data = json.loads(raw) if raw.strip().startswith("{") else {}
            data = dict(data)
            data["id"] = data.get("id") or tid
            # M22E-F2: versioning metadata (optional; backward compatible)
            if "version" not in data:
                data["version"] = None
            if "deprecated" not in data:
                data["deprecated"] = False
            if "compatibility_note" not in data:
                data["compatibility_note"] = None
            if "migration_hints" not in data:
                data["migration_hints"] = []
            workflow_id = (data.get("workflow_id") or "").strip() or "ops_reporting_workspace"
            if workflow_id not in VALID_WORKFLOW_IDS:
                workflow_id = "ops_reporting_workspace"
            data["workflow_id"] = workflow_id
            artifacts = data.get("artifacts")
            if not isinstance(artifacts, list):
                artifacts = list(WORKFLOW_ARTIFACTS.get(workflow_id, ()))
            allowed = set(WORKFLOW_ARTIFACTS.get(workflow_id, ()))
            filtered = []
            for a in artifacts:
                key = (a if isinstance(a, str) else str(a)).strip().removesuffix(".md")
                if key in allowed:
                    filtered.append(key)
            data["artifacts"] = filtered if filtered else list(allowed)
            return data
    raise FileNotFoundError(f"Template not found: {template_id} (looked in {base})")


def get_template(
    template_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any] | None:
    """Return template dict if found, else None."""
    try:
        return load_template(template_id, repo_root)
    except (FileNotFoundError, ValueError):
        return None


def list_templates(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List templates: scan templates dir for .yaml/.yml/.json; return list of {id, name?, workflow_id, artifacts}."""
    base = _templates_path(repo_root)
    if not base.exists() or not base.is_dir():
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(base.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in (".yaml", ".yml", ".json"):
            tid = path.stem
            if tid in seen:
                continue
            seen.add(tid)
            t = get_template(tid, repo_root=_repo_root(repo_root))
            if t:
                out.append({
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "description": t.get("description"),
                    "workflow_id": t.get("workflow_id"),
                    "artifacts": t.get("artifacts", []),
                    "version": t.get("version"),
                    "deprecated": t.get("deprecated", False),
                    "compatibility_note": t.get("compatibility_note"),
                    "migration_hints": t.get("migration_hints") or [],
                })
    return out


def template_artifact_order_and_filenames(template: dict[str, Any]) -> list[tuple[str, str]]:
    """Return [(artifact_key, filename), ...] in template order for artifacts that exist in ARTIFACT_TO_FILENAME."""
    out: list[tuple[str, str]] = []
    for key in template.get("artifacts", []):
        key = key.removesuffix(".md") if isinstance(key, str) else str(key)
        if key in ARTIFACT_TO_FILENAME:
            out.append((key, ARTIFACT_TO_FILENAME[key]))
    return out
