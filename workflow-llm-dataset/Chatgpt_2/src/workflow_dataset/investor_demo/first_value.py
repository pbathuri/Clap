"""
M51I–M51L: First-value demo path + deterministic artifact from state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from workflow_dataset.investor_demo.models import FirstValueDemoPath


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_first_value_demo_path(repo_root: Path | str | None = None) -> FirstValueDemoPath:
    root = _root(repo_root)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    vertical_id = ""
    stage_status = "unknown"
    next_cmd = "workflow-dataset value-packs first-run --help"
    friction = "—"
    try:
        if (root / "pyproject.toml").exists():
            from workflow_dataset.vertical_excellence.compression import assess_first_value_stage
            from workflow_dataset.vertical_excellence.mission_control import vertical_excellence_slice
            st = assess_first_value_stage(root)
            vertical_id = st.vertical_id or ""
            stage_status = st.status or "unknown"
            next_cmd = st.next_command_hint or next_cmd
            ve = vertical_excellence_slice(root)
            friction = ve.get("strongest_friction_label") or "—"
        else:
            stage_status = "not_in_product_repo"
            vertical_id = "demo_placeholder"
    except Exception as e:
        stage_status = f"error: {e}"

    opportunity = (
        f"Vertical `{vertical_id or 'default'}` first-value stage: **{stage_status}**. "
        f"Next safe step is a real CLI command (simulate where available)."
    )
    rationale = (
        f"Generated at {now} from local vertical_excellence assessment. "
        f"Strongest surfaced friction: {friction}. "
        "This artifact is deterministic—no LLM generation—so the demo stays auditable."
    )

    md = f"""# Investor demo — first-value snapshot

{opportunity}

## Why this artifact exists

{rationale}

## Suggested next command (presenter may run or narrate)

```
{next_cmd}
```

## Supervision

- Do not claim unattended execution.
- Prefer simulate paths until operator approves.
"""
    return FirstValueDemoPath(
        opportunity_line=opportunity.replace("**", ""),
        rationale_line=rationale,
        next_safe_command=next_cmd,
        artifact_markdown=md,
    )
