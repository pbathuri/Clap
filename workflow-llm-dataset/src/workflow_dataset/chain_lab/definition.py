"""
M23A: Chain definition — local, inspectable format. No hidden agent framework.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.chain_lab.config import get_chains_dir


# Schema: chain definition
CHAIN_SCHEMA_KEYS = (
    "id",
    "description",
    "steps",
    "expected_inputs_per_step",
    "expected_outputs_per_step",
    "stop_conditions",
    "workflow_names",
    "variant_label",
)

STEP_KEYS = (
    "id",
    "type",
    "label",
    "params",
    "workflow_name",
    "expected_inputs",
    "expected_outputs",
    "failure_conditions",
    "resumable",
)

# Step contract: optional per-step expectations and failure/resume metadata
DEFAULT_RESUMABLE = True  # steps are resumable unless set false


def _step_sanitize(step: dict[str, Any]) -> dict[str, Any]:
    """Ensure step has id, type, label, params, workflow_name, and optional contract fields."""
    out = dict(step)
    out.setdefault("id", "")
    out.setdefault("type", "cli")
    out.setdefault("label", "")
    out.setdefault("params", {})
    out.setdefault("workflow_name", "")
    # Step contract (M23A-F2)
    out.setdefault("expected_inputs", [])
    out.setdefault("expected_outputs", [])
    out.setdefault("failure_conditions", [])
    if "resumable" not in out:
        out["resumable"] = DEFAULT_RESUMABLE
    else:
        out["resumable"] = bool(out["resumable"])
    return out


def get_step_by_id_or_index(definition: dict[str, Any], step_id_or_index: str | int) -> tuple[dict[str, Any], int] | None:
    """Return (step, index) for step_id or step index, or None."""
    steps = definition.get("steps") or []
    if isinstance(step_id_or_index, int):
        if 0 <= step_id_or_index < len(steps):
            return steps[step_id_or_index], step_id_or_index
        return None
    sid = str(step_id_or_index).strip()
    for i, s in enumerate(steps):
        if (s.get("id") or "").strip() == sid:
            return s, i
    return None


def validate_chain(data: dict[str, Any]) -> None:
    """Raise ValueError if required chain fields missing or invalid."""
    if not isinstance(data.get("id"), str) or not data["id"].strip():
        raise ValueError("chain must have non-empty id")
    if not isinstance(data.get("steps"), list) or len(data["steps"]) == 0:
        raise ValueError("chain must have non-empty steps list")
    for i, s in enumerate(data["steps"]):
        if not isinstance(s, dict):
            raise ValueError(f"step {i} must be a dict")
        _step_sanitize(s)


def load_chain(chain_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Load chain definition by id. File: chains/<id>.json. Raises FileNotFoundError if missing."""
    chains_dir = get_chains_dir(repo_root)
    path = chains_dir / f"{chain_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Chain not found: {chain_id} at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_chain(data)
    # Normalize steps
    data["steps"] = [_step_sanitize(s) for s in data["steps"]]
    data.setdefault("description", "")
    data.setdefault("expected_inputs_per_step", {})
    data.setdefault("expected_outputs_per_step", {})
    data.setdefault("stop_conditions", [])
    data.setdefault("workflow_names", [])
    data.setdefault("variant_label", "")
    return data


def save_chain(definition: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    """Save chain definition. Uses definition['id'] for filename. Returns path."""
    validate_chain(definition)
    chain_id = (definition.get("id") or "unnamed").strip()
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in chain_id).strip("_") or "chain"
    chains_dir = get_chains_dir(repo_root)
    path = chains_dir / f"{safe_id}.json"
    payload = {
        "id": definition.get("id", safe_id),
        "description": definition.get("description", ""),
        "steps": [_step_sanitize(s) for s in definition.get("steps", [])],
        "expected_inputs_per_step": definition.get("expected_inputs_per_step") or {},
        "expected_outputs_per_step": definition.get("expected_outputs_per_step") or {},
        "stop_conditions": definition.get("stop_conditions") or [],
        "workflow_names": definition.get("workflow_names") or [],
        "variant_label": definition.get("variant_label", ""),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def list_chains(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all chain definitions (id, description, step_count, variant_label)."""
    chains_dir = get_chains_dir(repo_root)
    out: list[dict[str, Any]] = []
    for p in sorted(chains_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            steps = data.get("steps") or []
            out.append({
                "id": data.get("id", p.stem),
                "description": (data.get("description") or "")[:200],
                "step_count": len(steps),
                "variant_label": data.get("variant_label", ""),
            })
        except Exception:
            pass
    return out
