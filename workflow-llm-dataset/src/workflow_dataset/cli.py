from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from workflow_dataset.settings import load_settings
from workflow_dataset.ingest.base import run_ingestion
from workflow_dataset.normalize.taxonomies import run_normalization
from workflow_dataset.map.industry_occupation import run_mapping
from workflow_dataset.infer.workflow import run_workflow_inference
from workflow_dataset.export.excel_export import export_excel
from workflow_dataset.export.csv_export import export_csv
from workflow_dataset.export.parquet_export import export_parquet
from workflow_dataset.export.qa_report import build_qa_report
from workflow_dataset.validate.qa_issues import build_qa_issues
from workflow_dataset.observe.file_activity import collect_file_events
from workflow_dataset.observe.local_events import append_events, load_all_events
from workflow_dataset.personal.work_graph import ingest_file_events, persist_routines
from workflow_dataset.personal.routine_detector import detect_routines
from workflow_dataset.personal.suggestion_engine import (
    generate_suggestions,
    persist_suggestions,
    load_suggestions,
)

app = typer.Typer()
console = Console()


@app.command()
def build(config: str = "configs/settings.yaml") -> None:
    """Run full dataset build (global work priors for personal agent)."""
    settings = load_settings(config)
    console.print("[bold]Starting full dataset build[/bold]")
    run_ingestion(settings)
    run_normalization(settings)
    run_mapping(settings)
    run_workflow_inference(settings)
    build_qa_issues(settings)
    export_csv(settings)
    export_parquet(settings)
    export_excel(settings)
    build_qa_report(settings)
    console.print("[green]Build complete[/green]")


@app.command()
def qa(config: str = "configs/settings.yaml") -> None:
    settings = load_settings(config)
    build_qa_report(settings)
    console.print("[green]QA report generated[/green]")


@app.command()
def observe(config: str = typer.Option("configs/settings.yaml", "--config", "-c")) -> None:
    """
    Run local observation (file metadata only). Config-gated: requires
    agent.observation_enabled and "file" in agent.allowed_observation_sources.
    Writes events to paths.event_log_dir and updates personal graph if enabled.
    """
    settings = load_settings(config)
    agent = settings.agent
    if not agent:
        console.print("[red]agent config missing; observation disabled[/red]")
        raise typer.Exit(1)
    if not agent.observation_enabled:
        console.print("[yellow]observation disabled (agent.observation_enabled is false)[/yellow]")
        raise typer.Exit(0)
    if "file" not in (agent.allowed_observation_sources or []):
        console.print("[yellow]file observer not allowed (add 'file' to agent.allowed_observation_sources)[/yellow]")
        raise typer.Exit(0)

    fo = agent.file_observer
    root_paths = (fo.root_paths if fo else []) or []
    if not root_paths:
        console.print("[yellow]no root_paths configured (agent.file_observer.root_paths); nothing to scan[/yellow]")
        raise typer.Exit(0)

    paths_obj = settings.paths
    log_dir = Path(paths_obj.event_log_dir)
    graph_path = Path(paths_obj.graph_store_path)
    roots = [Path(p).resolve() for p in root_paths if p]
    max_files = fo.max_files_per_scan if fo else 10_000
    exclude = set(fo.exclude_dirs) if fo else {".git", "__pycache__", "node_modules", ".venv"}
    allowed_ext = set(e.lstrip(".").lower() for e in (fo.allowed_extensions or [])) if fo else None
    if allowed_ext is not None and not allowed_ext:
        allowed_ext = None
    graph_update_enabled = fo.graph_update_enabled if fo else True

    events = collect_file_events(
        roots,
        max_files_per_scan=max_files,
        exclude_dirs=exclude,
        allowed_extensions=allowed_ext,
        device_id="",
        tier=agent.observation_tier or 1,
    )
    n_files = len(events)
    if not events:
        console.print("[dim]no file events collected[/dim]")
        raise typer.Exit(0)

    written_path = append_events(log_dir, events)
    console.print(f"[green]events written: {len(events)}[/green] -> {written_path}")

    nodes_delta = 0
    edges_delta = 0
    if graph_update_enabled and graph_path:
        nodes_delta, edges_delta = ingest_file_events(
            graph_path,
            events,
            root_paths=roots,
        )
        console.print(f"[green]graph updated: {nodes_delta} nodes, {edges_delta} edges[/green] -> {graph_path}")

    console.print(
        f"[bold]observe summary:[/bold] files_observed={n_files} events_written={len(events)} "
        f"nodes_created_or_updated={nodes_delta} edges_created={edges_delta}"
    )


@app.command()
def suggest(config: str = typer.Option("configs/settings.yaml", "--config", "-c")) -> None:
    """
    Run the interpretation loop: load local events, infer routines, generate suggestions.
    Writes routines to the personal graph and suggestions to the local store.
    No actions are executed; suggestion-only.
    """
    settings = load_settings(config)
    paths_obj = settings.paths
    log_dir = Path(paths_obj.event_log_dir)
    graph_path = Path(paths_obj.graph_store_path)

    events = load_all_events(log_dir, source_filter="file", max_events=5000)
    if not events:
        console.print("[dim]no file events in event log; run 'observe' first or add root_paths[/dim]")
        raise typer.Exit(0)

    root_paths: list[Path] = []
    if settings.agent and settings.agent.file_observer and settings.agent.file_observer.root_paths:
        root_paths = [Path(p).resolve() for p in settings.agent.file_observer.root_paths]

    # Infer routines (deterministic heuristics)
    routines = detect_routines(events, root_paths=root_paths if root_paths else None)
    n_routines = len(routines)
    if routines:
        n_persisted = persist_routines(graph_path, routines)
        console.print(f"[green]routines inferred: {n_routines}[/green] (persisted {n_persisted} to graph)")
    else:
        console.print("[dim]no routines inferred from events[/dim]")

    # Generate and persist suggestions
    suggestions = generate_suggestions(routines)
    if suggestions:
        persist_suggestions(graph_path, suggestions)
        console.print(f"[green]suggestions generated: {len(suggestions)}[/green] -> {graph_path}")
        for s in suggestions[:5]:
            console.print(f"  [bold]{s.title}[/bold]")
            console.print(f"  [dim]{s.description}[/dim]")
    else:
        console.print("[dim]no suggestions generated (need more routine evidence)[/dim]")

    # Summary
    pending = load_suggestions(graph_path, status_filter="pending", limit=100)
    console.print(f"[bold]suggest summary:[/bold] events_loaded={len(events)} routines={n_routines} suggestions={len(suggestions)} pending_total={len(pending)}")
