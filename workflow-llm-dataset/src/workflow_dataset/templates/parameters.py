"""
M22E-F3: Typed template parameters — validation and parsing. No eval or code execution.
"""

from __future__ import annotations

from typing import Any

PARAM_TYPES = ("string", "integer", "boolean", "choice")


def _normalize_param_def(p: dict[str, Any]) -> dict[str, Any]:
    """Ensure param def has name, type, required, default, description."""
    out = dict(p)
    out.setdefault("name", "")
    out.setdefault("type", "string")
    if out["type"] not in PARAM_TYPES:
        out["type"] = "string"
    out.setdefault("required", False)
    if "default" not in out:
        out["default"] = None
    out.setdefault("description", "")
    if out["type"] == "choice":
        out.setdefault("choices", [])
    return out


def validate_template_parameters(
    template: dict[str, Any],
    params: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """
    Validate runtime params against template's parameter definitions.
    Returns (resolved_dict, errors). resolved_dict includes defaults for missing optional params.
    """
    defs = template.get("parameters") or []
    defs = [_normalize_param_def(d) for d in defs if isinstance(d, dict) and (d.get("name") or "").strip()]
    errors: list[str] = []
    resolved: dict[str, Any] = {}

    for d in defs:
        name = (d.get("name") or "").strip()
        if not name:
            continue
        typ = d.get("type", "string")
        required = d.get("required", False)
        default = d.get("default")
        value = params.get(name)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            if required:
                errors.append(f"Parameter '{name}' is required")
                continue
            resolved[name] = default
            continue
        # Coerce and validate
        if typ == "string":
            resolved[name] = str(value).strip()
        elif typ == "integer":
            try:
                resolved[name] = int(value)
            except (TypeError, ValueError):
                errors.append(f"Parameter '{name}' must be an integer")
        elif typ == "boolean":
            if isinstance(value, bool):
                resolved[name] = value
            else:
                v = str(value).strip().lower()
                if v in ("true", "1", "yes"):
                    resolved[name] = True
                elif v in ("false", "0", "no"):
                    resolved[name] = False
                else:
                    errors.append(f"Parameter '{name}' must be boolean (true/false)")
        elif typ == "choice":
            choices = list(d.get("choices") or [])
            s = str(value).strip()
            if s not in choices:
                errors.append(f"Parameter '{name}' must be one of {choices}")
            else:
                resolved[name] = s
        else:
            resolved[name] = str(value).strip()
    return resolved, errors


def parse_param_string(s: str) -> tuple[str, str]:
    """Parse 'key=value' into (key, value). Value is raw string (no unescaping)."""
    s = (s or "").strip()
    if "=" not in s:
        return s, ""
    k, _, v = s.partition("=")
    return k.strip(), v.strip()


def parse_param_list(param_list: list[str]) -> dict[str, str]:
    """Parse list of 'key=value' strings into dict. Later values override earlier."""
    out: dict[str, str] = {}
    for s in param_list:
        k, v = parse_param_string(s)
        if k:
            out[k] = v
    return out
