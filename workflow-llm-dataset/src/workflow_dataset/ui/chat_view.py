"""
Chat / assist view: ask explain, next-step, refine questions; show grounded answer and evidence.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen, evidence_snippet
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import run_assist_query


def render_chat(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Chat/explain: one question at a time, show answer and evidence. Returns next screen."""
    console.print(Panel(
        "[bold]Chat / explain[/bold]\n[dim]Ask about projects, style, suggestions, drafts. Answers are grounded in graph and retrieval.[/dim]",
        title="Assist",
        border_style="blue",
    ))

    while True:
        query = Prompt.ask("\n[cyan]Your question[/cyan] (or Enter to return)").strip()
        if not query:
            return Screen.HOME

        use_llm = Prompt.ask("Use LLM? (y/N)", default="n").strip().lower() == "y"

        try:
            out = run_assist_query(
                settings,
                query,
                project_id=state.selected_project_id,
                session_id=state.selected_session_id or None,
                use_llm=use_llm,
            )
            console.print(Panel(f"[bold]{out['title']}[/bold]\n\n{out['answer']}", title="Answer", border_style="green"))
            if out.get("supporting_evidence"):
                console.print(f"[dim]Evidence: {evidence_snippet(out['supporting_evidence'], 5)}[/dim]")
            console.print(f"[dim]confidence={out.get('confidence_score', 0):.2f} retrieval={out.get('used_retrieval')} llm={out.get('used_llm')}[/dim]")
            state.add_chat_turn("user", query)
            state.add_chat_turn("assistant", out.get("answer", ""))
        except Exception as e:
            console.print(f"[red]{e}[/red]")
