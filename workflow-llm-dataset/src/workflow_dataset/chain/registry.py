"""
M23A: Chain definition registry. Load/list chains from data/local/chains/*.yaml|*.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CHAINS_DIR = "data/local/chains"
STEP_TYPES = ("command", "intake_add", "release_demo")


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def _chains_path(repo_root: Path | str | None) -> Path:
    return _repo_root(repo_root) / CHAINS_DIR


def _safe_id(cid: str) -> str:
    return "".join(c for c in (cid or "").strip() if c.isalnum() or c in "_-").strip() or "unnamed"


def _expand_step_to_cmd(step: dict[str, Any], repo_root: Path) -> str:
    """Expand a typed step to a workflow-dataset CLI command. Returns shell command string."""
    step_type = (step.get("type") or "command").strip().lower()
    if step_type == "command":
        return (step.get("cmd") or "").strip() or ""
    if step_type == "intake_add":
        params = step.get("params") or {}
        path = params.get("path", "")
        label = params.get("label", "")
        if not path or not label:
            return ""
        return f"workflow-dataset intake add --path {path!r} --label {label!r}"
    if step_type == "release_demo":
        params = step.get("params") or {}
        intake = params.get("intake", "")
        template = params.get("template", "")
        workflow = params.get("workflow", "")
        save = " --save-artifact" if params.get("save_artifact", True) else ""
        parts = ["workflow-dataset release demo"]
        if workflow:
            parts.append(f"--workflow {workflow!r}")
        if template:
            parts.append(f"--template {template!r}")
        if intake:
            parts.append(f"--intake {intake!r}")
        parts.append(save.strip())
        return " ".join(parts)
    return (step.get("cmd") or "").strip()


def load_chain(chain_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Load chain definition by id. Looks for <chains_dir>/<id>.yaml or .json.
    Returns dict with id, name?, steps: [{ id, type, params?|cmd? }], expected_artifacts?, stop_conditions?.
    """
    root = _repo_root(repo_root)
    cid = _safe_id(chain_id)
    if not cid:
        raise ValueError("chain id is required")
    base = root / CHAINS_DIR
    for ext in (".yaml", ".yml", ".json"):
        path = base / f"{cid}{ext}"
        if path.exists() and path.is_file():
            raw = path.read_text(encoding="utf-8")
            if ext == ".json":
                data = json.loads(raw)
            else:
                try:
                    import yaml
                    data = yaml.safe_load(raw) or {}
                except Exception:
                    data = json.loads(raw) if raw.strip().startswith("{") else {}
            data = dict(data)
            data["id"] = data.get("id") or cid
            steps = data.get("steps")
            if not isinstance(steps, list):
                data["steps"] = []
            else:
                data["steps"] = [
                    {"id": (s.get("id") or f"step_{i}"), "type": s.get("type") or "command", "params": s.get("params"), "cmd": s.get("cmd")}
                    for i, s in enumerate(steps)
                    if isinstance(s, dict)
                ]
            data.setdefault("expected_artifacts", [])
            data.setdefault("stop_conditions", {"on_step_failure": True})
            return data
    raise FileNotFoundError(f"Chain not found: {chain_id} (looked in {base})")


def get_chain(chain_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Return chain definition if found, else None."""
    try:
        return load_chain(chain_id, repo_root)
    except (FileNotFoundError, ValueError):
        return None


def list_chains(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List chains: scan chains dir for .yaml/.json; return list of { id, name?, steps_count }."""
    base = _chains_path(repo_root)
    if not base.exists() or not base.is_dir():
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(base.iterdir()):
        if not path.is_file() or path.suffix.lower() not in (".yaml", ".yml", ".json"):
            continue
        cid = path.stem
        if cid in seen:
            continue
        seen.add(cid)
        c = get_chain(cid, repo_root=_repo_root(repo_root))
        if c:
            out.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "steps_count": len(c.get("steps") or []),
                "expected_artifacts": c.get("expected_artifacts", []),
            })
    return out
