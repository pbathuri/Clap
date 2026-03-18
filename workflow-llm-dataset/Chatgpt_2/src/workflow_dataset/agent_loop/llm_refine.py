"""
Optional local LLM refinement for draft structures.

When agent_loop_default_use_llm is True and a base_model is configured,
returns a callable that refines draft text using retrieved context.
Otherwise returns None. Grounded in context; no fabrication.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def get_llm_refine_fn(
    base_model: str = "",
    llm_config_path: Path | str | None = None,
    max_tokens: int = 500,
) -> Callable[..., str] | None:
    """
    Return a callable (draft_outline, context_snippet, domain) -> refined_str,
    or None if no local model is configured/available.
    """
    if not base_model and llm_config_path:
        try:
            import yaml
            path = Path(llm_config_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                base_model = cfg.get("base_model") or ""
        except Exception:
            pass
    if not base_model:
        return None

    def refine(draft_outline: str = "", context_snippet: str = "", domain: str = "") -> str:
        if not draft_outline:
            return ""
        prompt = (
            "Refine this draft outline to be more specific to the user's project. "
            "Only adjust wording and add brief notes; do not invent new sections or facts. "
            "Keep the same structure.\n\n"
            "Context (use only to ground wording):\n" + (context_snippet[:1500] or "None") + "\n\n"
            "Draft outline to refine:\n" + draft_outline[:3000]
        )
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "mlx_lm.generate",
                    "--model", base_model,
                    "--prompt", prompt,
                    "--max-tokens", str(max_tokens),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout:
                out = result.stdout.strip()
                return out if out else draft_outline
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        return draft_outline

    return refine
