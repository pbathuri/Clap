"""
Main entry and menu loop for the Local Operator Console.

Rich-based guided flow; no headless CLI impact.
"""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import get_settings, get_home_counts
from workflow_dataset.ui.home_view import render_home
from workflow_dataset.ui.setup_view import render_setup
from workflow_dataset.ui.project_view import render_project
from workflow_dataset.ui.suggestions_view import render_suggestions
from workflow_dataset.ui.drafts_view import render_drafts
from workflow_dataset.ui.materialize_view import render_materialize
from workflow_dataset.ui.apply_view import render_apply
from workflow_dataset.ui.rollback_view import render_rollback
from workflow_dataset.ui.chat_view import render_chat
from workflow_dataset.ui.generation_view import render_generation
from workflow_dataset.ui.llm_status_view import render_llm_status


def run_console(config_path: str = "configs/settings.yaml") -> int:
    """
    Run the local operator console. Uses current config; fully local.
    Returns exit code (0 = normal exit, 1 = config/startup error).
    """
    console = Console()
    try:
        settings = get_settings(config_path)
    except Exception as e:
        console.print(f"[red]Failed to load config: {e}[/red]")
        return 1

    state = ConsoleState(config_path=config_path)
    state._raw_settings = settings

    # Resolve latest session for state
    from workflow_dataset.ui.services import _resolve_latest_session_id
    sid = _resolve_latest_session_id(settings)
    if sid:
        state.set_session(sid)

    current: Screen = Screen.HOME
    while True:
        if current == Screen.EXIT:
            console.print("[dim]Goodbye.[/dim]")
            return 0

        try:
            if current == Screen.HOME:
                current = render_home(console, state, settings)
            elif current == Screen.SETUP:
                current = render_setup(console, state, settings)
            elif current == Screen.PROJECT:
                current = render_project(console, state, settings)
            elif current == Screen.SUGGESTIONS:
                current = render_suggestions(console, state, settings)
            elif current == Screen.DRAFTS:
                current = render_drafts(console, state, settings)
            elif current == Screen.MATERIALIZE:
                current = render_materialize(console, state, settings)
            elif current == Screen.APPLY:
                current = render_apply(console, state, settings)
            elif current == Screen.ROLLBACK:
                current = render_rollback(console, state, settings)
            elif current == Screen.CHAT:
                current = render_chat(console, state, settings)
            elif current == Screen.GENERATION:
                current = render_generation(console, state, settings)
            elif current == Screen.LLM_STATUS:
                current = render_llm_status(console, state, settings)
            else:
                current = Screen.HOME
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Return to home (H) or exit (E)?[/dim]")
            choice = Prompt.ask("Choice", default="H").strip().upper()
            if choice == "E":
                return 0
            current = Screen.HOME
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            current = Screen.HOME


def main() -> None:
    """CLI entry when run as python -m workflow_dataset.ui."""
    config = "configs/settings.yaml"
    if len(sys.argv) > 1:
        config = sys.argv[1]
    sys.exit(run_console(config))
