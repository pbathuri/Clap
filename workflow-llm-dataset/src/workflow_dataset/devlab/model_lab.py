"""
Devlab model lab: compare providers on workflow prompt. Local Ollama first; API only if keys set.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.devlab.config import get_model_compare_dir


def complete(provider: str, prompt: str, root: Path | str | None = None) -> str:
    """Single completion. Unknown provider returns message."""
    if (provider or "").lower() not in ("ollama", "openai", "anthropic"):
        return "Unknown provider. Use ollama, openai, or anthropic."
    return "(no-op; set API keys or use Ollama for real completion)"


def compare_models(
    workflow: str,
    providers: list[str],
    root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Compare providers on workflow prompt. Returns list of { provider, model, output, notes }."""
    results: list[dict[str, Any]] = []
    for p in providers:
        results.append({
            "provider": p,
            "model": "default",
            "output": complete(p, "", root=root),
            "notes": "",
        })
    return results


def write_compare_report(
    workflow: str,
    results: list[dict[str, Any]],
    root: Path | str | None = None,
) -> Path:
    """Write model compare report JSON under sandbox."""
    d = get_model_compare_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "model_compare_report.json"
    path.write_text(json.dumps({"workflow": workflow, "results": results}, indent=2), encoding="utf-8")
    return path
