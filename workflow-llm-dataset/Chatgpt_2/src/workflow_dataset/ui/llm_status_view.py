"""
LLM status panel: latest run, smoke/full adapter, comparison report, demo-suite hint.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import get_llm_status


def render_llm_status(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Show LLM run status, adapter availability, comparison report path, and hint to run demo-suite."""
    llm = get_llm_status()
    lines = []
    lines.append(f"Latest run type: {llm.get('latest_run_type') or '—'}")
    lines.append(f"Latest run dir:  {llm.get('latest_run_dir') or '—'}")
    lines.append(f"Smoke adapter:   {'yes' if llm.get('smoke_available') else 'no'}")
    lines.append(f"Full adapter:    {'yes' if llm.get('full_available') else 'no'}")
    lines.append(f"Comparison:      {llm.get('comparison_report') or '—'}")
    lines.append("")
    lines.append("To run qualitative demo:  workflow-dataset llm demo-suite")
    lines.append("With retrieval:           workflow-dataset llm demo-suite --retrieval")
    lines.append("Compare runs:             workflow-dataset llm compare-runs")
    console.print(Panel("\n".join(lines), title="LLM status", border_style="blue"))
    Prompt.ask("Press Enter to return to Home", default="")
    return Screen.HOME
