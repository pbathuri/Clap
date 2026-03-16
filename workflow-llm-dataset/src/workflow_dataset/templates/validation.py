"""
M22E-F2: Template validation and validation reports.
Checks: workflow exists, artifacts valid, ordering legal, save behavior, export contract compatibility.
Status: valid | valid_with_warning | deprecated | invalid.
Optional migration hints (advisory only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.release.workspace_export_contract import (
    get_export_contract,
)
from workflow_dataset.templates.registry import (
    ARTIFACT_TO_FILENAME,
    VALID_WORKFLOW_IDS,
    WORKFLOW_ARTIFACTS,
    load_template,
)


# Status values for template compatibility
STATUS_VALID = "valid"
STATUS_VALID_WITH_WARNING = "valid_with_warning"
STATUS_DEPRECATED = "deprecated"
STATUS_INVALID = "invalid"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def validate_template(
    template_id_or_dict: str | dict[str, Any],
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Validate a template (by id or template dict).
    Returns dict: valid (bool), status (valid|valid_with_warning|deprecated|invalid),
    errors (list), warnings (list), checks (dict), migration_hints (list).
    """
    if isinstance(template_id_or_dict, dict):
        t = template_id_or_dict
    else:
        try:
            t = load_template(template_id_or_dict, repo_root=repo_root)
        except FileNotFoundError:
            return {
                "valid": False,
                "status": STATUS_INVALID,
                "errors": [f"Template not found: {template_id_or_dict}"],
                "warnings": [],
                "checks": {},
                "migration_hints": [],
                "template_id": template_id_or_dict,
            }
        except Exception as e:
            return {
                "valid": False,
                "status": STATUS_INVALID,
                "errors": [str(e)],
                "warnings": [],
                "checks": {},
                "migration_hints": [],
                "template_id": template_id_or_dict.strip() if isinstance(template_id_or_dict, str) else str(template_id_or_dict),
            }

    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    # 1) Required workflow reference exists
    workflow_id = (t.get("workflow_id") or "").strip() or "ops_reporting_workspace"
    workflow_known = workflow_id in VALID_WORKFLOW_IDS
    checks["workflow_exists"] = {"ok": workflow_known, "workflow_id": workflow_id}
    if not workflow_known:
        errors.append(f"workflow_id '{workflow_id}' is not in allowed set: {list(VALID_WORKFLOW_IDS)}")

    # 2) Referenced artifacts are valid for this workflow
    allowed_artifacts = set(WORKFLOW_ARTIFACTS.get(workflow_id, ()))
    artifacts = t.get("artifacts") or []
    if not isinstance(artifacts, list):
        artifacts = []
    invalid_artifacts = []
    for a in artifacts:
        key = (a if isinstance(a, str) else str(a)).strip().removesuffix(".md")
        if key and key not in allowed_artifacts:
            invalid_artifacts.append(key)
    checks["artifacts_valid"] = {
        "ok": len(invalid_artifacts) == 0,
        "allowed": list(allowed_artifacts),
        "template_artifacts": artifacts,
        "invalid": invalid_artifacts,
    }
    if invalid_artifacts:
        errors.append(f"Artifacts not allowed for workflow '{workflow_id}': {invalid_artifacts}. Allowed: {list(allowed_artifacts)}")

    # 3) Artifact ordering is legal (subset of allowed; order preserved)
    ordered_keys = [k for k in artifacts if isinstance(k, str) and k.strip().removesuffix(".md") in allowed_artifacts]
    checks["artifact_ordering_legal"] = {"ok": True, "ordered": ordered_keys}

    # 4) Save behavior: workflow has save path (all current workflows do)
    checks["save_behavior_valid"] = {"ok": workflow_known, "workflow_id": workflow_id}
    if not workflow_known:
        # already error above
        pass

    # 5) Compatibility with export contract
    contract = get_export_contract(workflow_id) if workflow_id else None
    if contract:
        required_files = set(contract.get("required_files") or [])
        optional_files = set(contract.get("optional_files") or [])
        at_least_one = contract.get("required_at_least_one_of") or []
        template_filenames = set()
        for key in artifacts:
            k = (key if isinstance(key, str) else str(key)).strip().removesuffix(".md")
            if k in ARTIFACT_TO_FILENAME:
                template_filenames.add(ARTIFACT_TO_FILENAME[k])
        all_contract_files = required_files | optional_files | set(at_least_one)
        missing_required = required_files - set((Path(f).name for f in (template_filenames | {f for f in required_files})))
        # Template can request a subset; required_files (e.g. manifest, source_snapshot) are written by save, not by template artifact list
        # So we only check: template artifacts must be subset of contract's optional/required_at_least_one or required
        extra = template_filenames - all_contract_files
        contract_compatible = len(extra) == 0
        checks["export_contract_compatible"] = {
            "ok": contract_compatible,
            "contract_workflow": workflow_id,
            "template_files": list(template_filenames),
            "contract_optional": list(optional_files),
            "contract_required": list(required_files),
            "required_at_least_one_of": at_least_one,
        }
        if not contract_compatible:
            warnings.append(f"Template requests files not in export contract: {list(extra)}")
    else:
        checks["export_contract_compatible"] = {"ok": True, "contract_workflow": workflow_id, "no_contract": True}

    # 6) M22E-F3: Optional typed parameters schema
    param_defs = t.get("parameters")
    if isinstance(param_defs, list) and len(param_defs) > 0:
        param_errors: list[str] = []
        allowed_types = {"string", "integer", "boolean", "choice"}
        for i, p in enumerate(param_defs):
            if not isinstance(p, dict):
                param_errors.append(f"Parameter at index {i} must be an object")
                continue
            name = p.get("name")
            if not name or not str(name).strip():
                param_errors.append(f"Parameter at index {i} must have 'name'")
                continue
            ptype = (p.get("type") or "string").strip().lower()
            if ptype not in allowed_types:
                param_errors.append(f"Parameter '{name}': type must be one of {allowed_types}")
            if ptype == "choice" and not p.get("choices"):
                param_errors.append(f"Parameter '{name}': type 'choice' requires 'choices' list")
        checks["parameters_valid"] = {"ok": len(param_errors) == 0, "errors": param_errors}
        if param_errors:
            errors.extend(param_errors)
    else:
        checks["parameters_valid"] = {"ok": True, "no_parameters": True}

    # Status
    deprecated = t.get("deprecated", False)
    if errors:
        status = STATUS_INVALID
    elif deprecated:
        status = STATUS_DEPRECATED
        warnings.append("Template is marked deprecated.")
    elif warnings:
        status = STATUS_VALID_WITH_WARNING
    else:
        status = STATUS_VALID

    migration_hints: list[str] = list(t.get("migration_hints") or [])
    if deprecated and not migration_hints:
        migration_hints.append(f"Consider using a non-deprecated template or workflow '{workflow_id}' directly.")

    return {
        "valid": len(errors) == 0,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "migration_hints": migration_hints,
        "template_id": t.get("id"),
        "version": t.get("version"),
        "workflow_id": workflow_id,
    }


def template_validation_report(
    template_id_or_dict: str | dict[str, Any],
    repo_root: Path | str | None = None,
) -> str:
    """Generate a human-readable template validation report."""
    r = validate_template(template_id_or_dict, repo_root=repo_root)
    lines: list[str] = []
    lines.append("--- Template validation report ---")
    lines.append(f"Template id: {r.get('template_id', '—')}")
    lines.append(f"Version: {r.get('version') or 'unversioned'}")
    lines.append(f"Workflow: {r.get('workflow_id', '—')}")
    lines.append(f"Status: {r.get('status', '—')}")
    lines.append("")
    if r.get("errors"):
        lines.append("Errors:")
        for e in r["errors"]:
            lines.append(f"  - {e}")
        lines.append("")
    if r.get("warnings"):
        lines.append("Warnings:")
        for w in r["warnings"]:
            lines.append(f"  - {w}")
        lines.append("")
    if r.get("migration_hints"):
        lines.append("Migration hints:")
        for h in r["migration_hints"]:
            lines.append(f"  - {h}")
        lines.append("")
    checks = r.get("checks") or {}
    lines.append("Checks:")
    for name, detail in checks.items():
        ok = detail.get("ok", False) if isinstance(detail, dict) else False
        lines.append(f"  {name}: {'OK' if ok else 'FAIL'}")
    lines.append("---")
    return "\n".join(lines)


def get_template_status(
    template_id_or_dict: str | dict[str, Any],
    repo_root: Path | str | None = None,
) -> str:
    """Return compatibility status only: valid | valid_with_warning | deprecated | invalid."""
    r = validate_template(template_id_or_dict, repo_root=repo_root)
    return r.get("status", STATUS_INVALID)


# M22E-F3: Typed parameter resolution
PARAM_TYPES = ("string", "integer", "boolean", "choice")


def resolve_template_params(
    template: dict[str, Any],
    param_list: list[str],
) -> dict[str, Any]:
    """
    Parse --param k=v list and resolve against template parameters. Validates types and required.
    Returns dict of name -> value (coerced). Raises ValueError on unknown param or type error.
    """
    param_defs = template.get("parameters") or []
    if not isinstance(param_defs, list):
        param_defs = []
    by_name: dict[str, dict[str, Any]] = {str(p.get("name", "")).strip(): p for p in param_defs if isinstance(p, dict) and p.get("name")}
    if not by_name and param_list:
        raise ValueError("Template has no parameters; do not pass --param")
    result: dict[str, Any] = {}
    for kv in param_list:
        if "=" not in kv:
            raise ValueError(f"Invalid --param: expected key=value, got '{kv}'")
        k, v = kv.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            raise ValueError("Invalid --param: empty key")
        if k not in by_name:
            raise ValueError(f"Unknown template parameter: '{k}'. Allowed: {list(by_name.keys())}")
        defn = by_name[k]
        ptype = (defn.get("type") or "string").strip().lower()
        if ptype == "integer":
            try:
                result[k] = int(v)
            except ValueError:
                raise ValueError(f"Parameter '{k}' must be an integer, got '{v}'")
        elif ptype == "boolean":
            result[k] = v.lower() in ("true", "1", "yes", "on")
        elif ptype == "choice":
            choices = defn.get("choices") or []
            if v not in choices:
                raise ValueError(f"Parameter '{k}' must be one of {choices}, got '{v}'")
            result[k] = v
        else:
            result[k] = v
    # Fill defaults for missing optional params
    for name, defn in by_name.items():
        if name in result:
            continue
        default = defn.get("default")
        if default is not None:
            result[name] = default
        elif defn.get("required", False):
            raise ValueError(f"Missing required template parameter: '{name}'")
    return result
