"""
M22E-F3: Template export/import. Portable .tmpl.json / .tmpl.yaml format.
Export: serialize registered template to file. Import: validate then write to templates dir.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.templates.registry import TEMPLATES_DIR, load_template
from workflow_dataset.templates.validation import validate_template, STATUS_INVALID


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def _templates_path(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / TEMPLATES_DIR


def _export_dict(template: dict[str, Any]) -> dict[str, Any]:
    """Build portable dict for export (id, version, workflow_id, artifacts, parameters, etc.)."""
    out: dict[str, Any] = {
        "id": template.get("id"),
        "version": template.get("version"),
        "name": template.get("name"),
        "description": template.get("description"),
        "workflow_id": template.get("workflow_id"),
        "artifacts": list(template.get("artifacts") or []),
    }
    if template.get("deprecated") is not None:
        out["deprecated"] = template.get("deprecated")
    if template.get("compatibility_note") is not None:
        out["compatibility_note"] = template.get("compatibility_note")
    if template.get("migration_hints"):
        out["migration_hints"] = list(template["migration_hints"])
    if template.get("parameters"):
        out["parameters"] = list(template["parameters"])
    if template.get("wording_hints"):
        out["wording_hints"] = template["wording_hints"]
    return out


def export_template(
    template_id: str,
    output_path: Path | str,
    repo_root: Path | str | None = None,
    format: str = "json",
) -> Path:
    """
    Export a registered template to a local file (.tmpl.json or .tmpl.yaml).
    Returns the path written.
    """
    t = load_template(template_id.strip(), repo_root=repo_root)
    out_path = Path(output_path)
    payload = _export_dict(t)
    fmt = (format or "json").strip().lower()
    if fmt == "yaml" or out_path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
            text = yaml.safe_dump(payload, default_flow_style=False, allow_unicode=True)
        except ImportError:
            text = json.dumps(payload, indent=2)
    else:
        text = json.dumps(payload, indent=2)
    out_path.write_text(text, encoding="utf-8")
    return out_path


def import_template(
    file_path: Path | str,
    repo_root: Path | str | None = None,
    template_id: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Import a template from a local file. Validates before registration.
    If template_id is set, use it as the registered id; else use template["id"].
    If overwrite is False and a template with that id exists, raises FileExistsError.
    Returns summary dict: id, path, status, validated.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Import file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json" or ".tmpl.json" in path.name:
        data = json.loads(raw)
    else:
        try:
            import yaml
            data = yaml.safe_load(raw) or {}
        except ImportError:
            data = json.loads(raw) if raw.strip().startswith("{") else {}
    if not isinstance(data, dict):
        raise ValueError("Template file must be a JSON/YAML object")
    data = dict(data)
    data["id"] = data.get("id") or (template_id or path.stem).strip()
    if not data["id"]:
        raise ValueError("Template id is required (set in file or via --id)")
    # Validate before writing
    result = validate_template(data, repo_root=repo_root)
    if result.get("status") == STATUS_INVALID or not result.get("valid"):
        errors = result.get("errors") or ["Validation failed"]
        raise ValueError(f"Template validation failed: {'; '.join(errors)}")
    target_id = (template_id or data["id"]).strip()
    if not target_id:
        target_id = data["id"]
    base = _templates_path(repo_root)
    base.mkdir(parents=True, exist_ok=True)
    dest = base / f"{target_id}.yaml"
    if dest.exists() and not overwrite:
        raise FileExistsError(f"Template already exists: {target_id}. Use --overwrite to replace.")
    data["id"] = target_id
    try:
        import yaml
        out_text = yaml.safe_dump(data, default_flow_style=False, allow_unicode=True)
    except ImportError:
        out_text = json.dumps(data, indent=2)
    dest.write_text(out_text, encoding="utf-8")
    return {
        "id": target_id,
        "path": str(dest),
        "status": result.get("status", "valid"),
        "validated": True,
    }
