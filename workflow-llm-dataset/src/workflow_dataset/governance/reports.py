"""
M48D.1: Operator-facing governance reports — active preset and implications.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.governance.presets import get_active_preset
from workflow_dataset.governance.scope_templates import get_scope_template


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def format_governance_preset_report(repo_root: Path | str | None = None) -> str:
    """
    Operator-facing report: which governance preset is active and what it implies.
    """
    root = _root(repo_root)
    preset = get_active_preset(root)
    lines = [
        "[Governance] Active preset",
        "",
    ]
    if preset is None:
        lines.append("  (none — default: solo_operator)")
        return "\n".join(lines)
    lines.append(f"  preset_id={preset.preset_id}  label={preset.label}")
    lines.append(f"  description: {preset.description}")
    lines.append(f"  primary_role={preset.primary_role_id}  trust_preset={preset.trust_preset_id}")
    if preset.scope_template_id:
        t = get_scope_template(preset.scope_template_id)
        if t:
            lines.append(f"  scope_template={t.template_id}  pattern={t.deployment_pattern}")
            lines.append(f"  default_scope_hint={t.default_scope_hint}")
    lines.append("")
    lines.append("  What this implies:")
    for impl in preset.implications:
        lines.append("    - " + impl)
    lines.append("")
    return "\n".join(lines)
