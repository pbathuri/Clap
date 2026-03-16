from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

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
from workflow_dataset.ui import run_console

app = typer.Typer()
console = Console()


def _resolve_path(path: str) -> Path | None:
    """Resolve relative path against project root so configs work from any cwd. Returns None if path is empty."""
    from workflow_dataset.path_utils import resolve_config_path
    return resolve_config_path(path)


def _repo_root() -> Path:
    """Project root for error messages and docs."""
    from workflow_dataset.path_utils import get_repo_root
    return get_repo_root()


# ----- M9 Local Operator Console -----


@app.command("console")
def launch_console_cmd(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Launch the local operator console (guided TUI). Setup, projects, suggestions, drafts, materialize, apply, rollback, chat."""
    sys.exit(run_console(config))


# LLM workflow command group
llm_group = typer.Typer(
    help="Local LLM training: corpus, SFT, train, eval, demo.")
app.add_typer(llm_group, name="llm")


def _load_llm_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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
        console.print(
            "[yellow]observation disabled (agent.observation_enabled is false)[/yellow]")
        raise typer.Exit(0)
    if "file" not in (agent.allowed_observation_sources or []):
        console.print(
            "[yellow]file observer not allowed (add 'file' to agent.allowed_observation_sources)[/yellow]")
        raise typer.Exit(0)

    fo = agent.file_observer
    root_paths = (fo.root_paths if fo else []) or []
    if not root_paths:
        console.print(
            "[yellow]no root_paths configured (agent.file_observer.root_paths); nothing to scan[/yellow]")
        raise typer.Exit(0)

    paths_obj = settings.paths
    log_dir = Path(paths_obj.event_log_dir)
    graph_path = Path(paths_obj.graph_store_path)
    roots = [Path(p).resolve() for p in root_paths if p]
    max_files = fo.max_files_per_scan if fo else 10_000
    exclude = set(fo.exclude_dirs) if fo else {
        ".git", "__pycache__", "node_modules", ".venv"}
    allowed_ext = set(e.lstrip(".").lower()
                      for e in (fo.allowed_extensions or [])) if fo else None
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
    console.print(
        f"[green]events written: {len(events)}[/green] -> {written_path}")

    nodes_delta = 0
    edges_delta = 0
    if graph_update_enabled and graph_path:
        nodes_delta, edges_delta = ingest_file_events(
            graph_path,
            events,
            root_paths=roots,
        )
        console.print(
            f"[green]graph updated: {nodes_delta} nodes, {edges_delta} edges[/green] -> {graph_path}")

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
        console.print(
            "[dim]no file events in event log; run 'observe' first or add root_paths[/dim]")
        raise typer.Exit(0)

    root_paths: list[Path] = []
    if settings.agent and settings.agent.file_observer and settings.agent.file_observer.root_paths:
        root_paths = [Path(p).resolve()
                      for p in settings.agent.file_observer.root_paths]

    # Infer routines (deterministic heuristics)
    routines = detect_routines(
        events, root_paths=root_paths if root_paths else None)
    n_routines = len(routines)
    if routines:
        n_persisted = persist_routines(graph_path, routines)
        console.print(
            f"[green]routines inferred: {n_routines}[/green] (persisted {n_persisted} to graph)")
    else:
        console.print("[dim]no routines inferred from events[/dim]")

    # Generate and persist suggestions
    suggestions = generate_suggestions(routines)
    if suggestions:
        persist_suggestions(graph_path, suggestions)
        console.print(
            f"[green]suggestions generated: {len(suggestions)}[/green] -> {graph_path}")
        for s in suggestions[:5]:
            console.print(f"  [bold]{s.title}[/bold]")
            console.print(f"  [dim]{s.description}[/dim]")
    else:
        console.print(
            "[dim]no suggestions generated (need more routine evidence)[/dim]")

    # Summary
    pending = load_suggestions(graph_path, status_filter="pending", limit=100)
    console.print(
        f"[bold]suggest summary:[/bold] events_loaded={len(events)} routines={n_routines} suggestions={len(suggestions)} pending_total={len(pending)}")


# ----- Setup/onboarding commands -----
setup_group = typer.Typer(
    help="Initial setup analyzer: long-running local onboarding.")
app.add_typer(setup_group, name="setup")


@setup_group.command("init")
def setup_init(config: str = typer.Option("configs/settings.yaml", "--config", "-c")) -> None:
    """Create setup session, validate config, initialize stores, register scan roots and adapters."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    if not setup_cfg.setup_scan_roots:
        console.print(
            "[yellow]setup_scan_roots is empty; add paths in config to analyze[/yellow]")
    from workflow_dataset.setup.setup_manager import SetupManager
    setup_dir = Path(setup_cfg.setup_dir)
    graph_path = getattr(settings.paths, "graph_store_path",
                         None) or "data/local/work_graph.sqlite"
    manager = SetupManager(
        setup_dir=setup_dir,
        parsed_dir=Path(setup_cfg.parsed_artifacts_dir),
        style_dir=Path(setup_cfg.style_signals_dir),
        reports_dir=Path(setup_cfg.setup_reports_dir),
        graph_path=Path(graph_path),
    )
    roots = [str(Path(p).resolve()) for p in setup_cfg.setup_scan_roots if p]
    onboarding_mode = getattr(setup_cfg, "setup_mode", None) or "conservative"
    config_snapshot = {
        "allow_raw_text_parsing": getattr(setup_cfg, "allow_raw_text_parsing", False),
        "allow_raw_text_persistence": getattr(setup_cfg, "allow_raw_text_persistence", False),
    }
    session = manager.create_session(
        scan_roots=roots or ["."],
        exclude_dirs=setup_cfg.exclude_paths,
        enabled_adapters=setup_cfg.enabled_domain_adapters,
        max_runtime_hours=setup_cfg.setup_max_runtime_hours,
        onboarding_mode=onboarding_mode,
        config_snapshot=config_snapshot,
    )
    console.print(
        f"[green]setup session created: {session.session_id}[/green]")
    console.print(f"  onboarding_mode: {session.onboarding_mode}")
    console.print(
        f"  scan_roots: {session.scan_scope.root_paths[:5]}{'...' if len(session.scan_scope.root_paths) > 5 else ''}")
    console.print(f"  adapters: {session.enabled_adapters}")


@setup_group.command("run")
def setup_run(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
) -> None:
    """Run the staged onboarding pipeline. Resumable; safe local-only."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    from workflow_dataset.setup.setup_manager import SetupManager
    from workflow_dataset.setup.job_store import load_session, list_jobs
    manager = SetupManager(
        setup_dir=Path(setup_cfg.setup_dir),
        parsed_dir=Path(setup_cfg.parsed_artifacts_dir),
        style_dir=Path(setup_cfg.style_signals_dir),
        reports_dir=Path(setup_cfg.setup_reports_dir),
        graph_path=Path(
            getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite")),
    )
    sid = session_id
    if not sid:
        import glob
        sessions_dir = Path(setup_cfg.setup_dir) / "sessions"
        if not sessions_dir.exists():
            console.print(
                "[red]no session found; run 'setup init' first[/red]")
            raise typer.Exit(1)
        latest = sorted(sessions_dir.glob("*.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
        if not latest:
            console.print(
                "[red]no session found; run 'setup init' first[/red]")
            raise typer.Exit(1)
        sid = latest[0].stem
    session = load_session(Path(setup_cfg.setup_dir), sid)
    if not session:
        console.print(f"[red]session not found: {sid}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]running setup stages for session {sid}[/bold]")
    progress = manager.run_stage(sid)
    console.print(f"[green]setup complete[/green]")
    console.print(
        f"  files_scanned={progress.files_scanned} artifacts_classified={progress.artifacts_classified} docs_parsed={progress.docs_parsed}")
    console.print(
        f"  graph_nodes_created={progress.graph_nodes_created} current_stage={progress.current_stage.value}")


@setup_group.command("status")
def setup_status(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
) -> None:
    """Show progress: files scanned, artifacts classified, docs parsed, projects, style patterns, graph nodes, errors."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    from workflow_dataset.setup.progress_tracker import get_progress
    from workflow_dataset.setup.job_store import load_session
    setup_dir = Path(setup_cfg.setup_dir)
    sid = session_id
    if not sid:
        sessions_dir = setup_dir / "sessions"
        if not sessions_dir.exists():
            console.print("[dim]no sessions yet; run 'setup init' first[/dim]")
            raise typer.Exit(0)
        latest = sorted(sessions_dir.glob("*.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
        sid = latest[0].stem if latest else None
    if not sid:
        console.print("[dim]no session[/dim]")
        raise typer.Exit(0)
    progress = get_progress(setup_dir, sid)
    session = load_session(setup_dir, sid)
    if not progress:
        console.print(f"[dim]no progress for session {sid}[/dim]")
        raise typer.Exit(0)
    console.print(f"[bold]Setup status — {sid}[/bold]")
    console.print(f"  current_stage: {progress.current_stage.value}")
    console.print(f"  files_scanned: {progress.files_scanned}")
    console.print(f"  artifacts_classified: {progress.artifacts_classified}")
    console.print(f"  docs_parsed: {progress.docs_parsed}")
    console.print(f"  projects_detected: {progress.projects_detected}")
    console.print(
        f"  style_patterns_extracted: {progress.style_patterns_extracted}")
    console.print(f"  graph_nodes_created: {progress.graph_nodes_created}")
    console.print(
        f"  adapter_errors: {progress.adapter_errors} adapter_skips: {progress.adapter_skips}")


@setup_group.command("summary")
def setup_summary(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
) -> None:
    """Produce a concise local summary: domains, projects, style count, artifact families, corpus/SFT status."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    reports_dir = Path(setup_cfg.setup_reports_dir)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    if not sid:
        console.print(
            "[dim]no session; run 'setup init' and 'setup run' first[/dim]")
        raise typer.Exit(0)
    report_path = reports_dir / f"{sid}_summary.md"
    if not report_path.exists():
        console.print(
            "[yellow]summary not generated yet; run 'setup run' to complete stages[/yellow]")
        raise typer.Exit(0)
    console.print(report_path.read_text(encoding="utf-8"))
    # LLM artifacts status (default paths)
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    sft_dir = Path("data/local/llm/personal_sft")
    corpus_ok = corpus_path.exists()
    sft_ok = (sft_dir / "train.jsonl").exists()
    console.print("[bold]LLM artifacts[/bold]")
    console.print(
        f"  personal_corpus: {'yes' if corpus_ok else 'no'} -> {corpus_path}")
    console.print(f"  personal_sft: {'yes' if sft_ok else 'no'} -> {sft_dir}")
    # M5 assistive: style profiles, imitation candidates, draft structures
    try:
        from workflow_dataset.personal.style_profiles import load_style_profiles
        from workflow_dataset.personal.imitation_candidates import collect_candidates_from_profiles
        from workflow_dataset.personal.draft_structure_engine import load_draft_structures
        profiles_dir = Path(
            getattr(setup_cfg, "style_profiles_dir", "data/local/style_profiles"))
        suggestions_dir = Path(
            getattr(setup_cfg, "suggestions_dir", "data/local/suggestions"))
        draft_dir = Path(
            getattr(setup_cfg, "draft_structures_dir", "data/local/draft_structures"))
        profiles = load_style_profiles(
            profiles_dir) if profiles_dir.exists() else []
        candidates = collect_candidates_from_profiles(
            profiles_dir) if profiles_dir.exists() else []
        drafts = load_draft_structures(draft_dir) if draft_dir.exists() else []
        console.print("[bold]Assistive (M5)[/bold]")
        console.print(f"  style_profiles: {len(profiles)}")
        console.print(f"  imitation_candidates: {len(candidates)}")
        console.print(f"  draft_structures: {len(drafts)}")
        if profiles:
            console.print("  top profiles: " +
                          ", ".join(p.profile_type for p in profiles[:3]))
        if drafts:
            console.print("  top drafts: " +
                          ", ".join(d.draft_type for d in drafts[:3]))
    except Exception:
        pass


def _resolve_latest_session_id(setup_cfg) -> str | None:
    if not setup_cfg:
        return None
    sessions_dir = Path(setup_cfg.setup_dir) / "sessions"
    if not sessions_dir.exists():
        return None
    latest = sorted(sessions_dir.glob("*.json"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    return latest[0].stem if latest else None


@setup_group.command("build-corpus")
def setup_build_corpus(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
    output_dir: str = typer.Option(
        "", "--output", "-o", help="Output dir; default data/local/llm/personal_corpus"),
) -> None:
    """Build personal corpus from setup outputs + style signals. Writes data/local/llm/personal_corpus/."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    if not getattr(setup_cfg, "allow_personal_corpus_from_setup", False):
        console.print(
            "[yellow]allow_personal_corpus_from_setup is false; enable in config to run[/yellow]")
        raise typer.Exit(0)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    if not sid:
        console.print(
            "[yellow]no setup session; run 'setup init' and 'setup run' first[/yellow]")
        raise typer.Exit(0)
    out_dir = Path(output_dir or "data/local/llm/personal_corpus")
    allow_raw = getattr(setup_cfg, "allow_raw_text_for_personal_corpus", False)
    from workflow_dataset.llm.corpus_builder import build_personal_corpus_from_setup_full
    total, counts = build_personal_corpus_from_setup_full(
        setup_cfg.parsed_artifacts_dir,
        setup_cfg.style_signals_dir,
        sid,
        out_dir,
        allow_raw_text=allow_raw,
        include_style_signals=True,
        include_session_summary=True,
    )
    console.print(f"[green]personal corpus: {total} docs[/green] -> {out_dir}")
    for k, v in counts.items():
        console.print(f"  {k}: {v}")


@setup_group.command("build-sft")
def setup_build_sft(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
    output_dir: str = typer.Option(
        "", "--output", "-o", help="Output dir; default data/local/llm/personal_sft"),
) -> None:
    """Build personal SFT from setup outputs + style signals. Writes train/val/test to data/local/llm/personal_sft/."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    if not getattr(setup_cfg, "allow_personal_sft_from_setup", False):
        console.print(
            "[yellow]allow_personal_sft_from_setup is false; enable in config to run[/yellow]")
        raise typer.Exit(0)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    if not sid:
        console.print(
            "[yellow]no setup session; run 'setup init' and 'setup run' first[/yellow]")
        raise typer.Exit(0)
    out_dir = Path(output_dir or "data/local/llm/personal_sft")
    allow_raw = getattr(setup_cfg, "allow_raw_text_for_personal_sft", False)
    from workflow_dataset.llm.sft_builder import build_personal_sft_from_setup
    n_train, n_val, n_test, counts = build_personal_sft_from_setup(
        setup_cfg.parsed_artifacts_dir,
        setup_cfg.style_signals_dir,
        sid,
        out_dir,
        allow_raw_text=allow_raw,
    )
    console.print(
        f"[green]personal SFT: train={n_train} val={n_val} test={n_test}[/green] -> {out_dir}")
    for task_type, c in counts.items():
        console.print(f"  {task_type}: {c}")


@setup_group.command("build-personal-corpus")
def build_personal_corpus(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    session_id: str = typer.Option("", "--session-id"),
    output: str = typer.Option(
        "", "--output", "-o", help="Output JSONL path; default data/local/llm/personal_corpus/personal_corpus.jsonl"),
) -> None:
    """Build personal corpus from setup outputs + style signals (full). Writes personal_corpus.jsonl."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    llm_cfg = _load_llm_config(llm_config)
    corpus_dir = Path(llm_cfg.get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")).parent
    if output:
        p = Path(output)
        out_dir = p if p.suffix != ".jsonl" else p.parent
    else:
        out_dir = Path("data/local/llm/personal_corpus")
    parsed_dir = Path(setup_cfg.parsed_artifacts_dir)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    if sid:
        session_parsed = parsed_dir / sid
        if session_parsed.exists():
            allow_raw = (
                getattr(setup_cfg, "allow_raw_text_for_personal_corpus", False)
                or getattr(setup_cfg, "allow_llm_corpus_from_raw_text", False)
                or getattr(setup_cfg, "allow_raw_text_persistence", False)
            )
            from workflow_dataset.llm.corpus_builder import build_personal_corpus_from_setup_full
            total, counts = build_personal_corpus_from_setup_full(
                setup_cfg.parsed_artifacts_dir,
                setup_cfg.style_signals_dir,
                sid,
                out_dir,
                allow_raw_text=allow_raw,
            )
            out_path = out_dir / "personal_corpus.jsonl"
            console.print(
                f"[green]personal corpus written: {total} docs[/green] -> {out_path}")
            for k, v in counts.items():
                console.print(f"  {k}: {v}")
        else:
            console.print(
                "[yellow]no parsed artifacts for session; run 'setup run' first[/yellow]")
    else:
        console.print(
            "[yellow]no setup session; run 'setup init' and 'setup run' first[/yellow]")


# ----- Assistive loop (M5: style-aware suggestions and draft structures) -----
assist_group = typer.Typer(
    help="Style-aware suggestions and draft structures from setup. No execution.")
app.add_typer(assist_group, name="assist")


# ----- M17 Workflow trials -----
trials_group = typer.Typer(
    help="Workflow task trials: run real scenarios across baseline / adapter / retrieval modes.")
app.add_typer(trials_group, name="trials")


@assist_group.command("suggest")
def assist_suggest(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
) -> None:
    """Load setup outputs + graph + style profiles; generate style-aware suggestions; persist locally; print summary."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    from workflow_dataset.personal.project_interpreter import get_assistive_context
    from workflow_dataset.setup.style_persistence import load_style_signals
    from workflow_dataset.personal.style_profiles import build_profiles_from_style_signals, save_style_profile, load_style_profiles
    from workflow_dataset.personal.imitation_candidates import collect_candidates_from_profiles
    from workflow_dataset.personal.style_suggestion_engine import (
        generate_style_aware_suggestions,
        persist_style_aware_suggestions,
    )
    from workflow_dataset.personal.assistive_graph import (
        persist_style_profile_nodes,
        persist_imitation_candidate_nodes,
        persist_style_aware_suggestion_nodes,
    )
    from workflow_dataset.observe.local_events import load_all_events
    from workflow_dataset.personal.routine_detector import detect_routines

    context = get_assistive_context(
        graph_path,
        setup_cfg.style_signals_dir,
        setup_cfg.parsed_artifacts_dir,
        sid or "",
    )
    style_records = load_style_signals(
        sid, setup_cfg.style_signals_dir) if sid else []
    profiles = build_profiles_from_style_signals(
        style_records, session_id=sid or "", project_id="")
    profiles_dir = Path(setup_cfg.style_profiles_dir)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    for p in profiles:
        save_style_profile(p, profiles_dir)
    existing_profiles = load_style_profiles(profiles_dir)
    candidates = collect_candidates_from_profiles(profiles_dir)
    routines: list = []
    if settings.agent and getattr(settings.paths, "event_log_dir", None):
        events = load_all_events(
            Path(settings.paths.event_log_dir), source_filter="file", max_events=2000)
        roots = [Path(r).resolve() for r in (settings.agent.file_observer.root_paths or [
        ])] if settings.agent and settings.agent.file_observer else []
        routines = detect_routines(events, root_paths=roots if roots else None)
    suggestions = generate_style_aware_suggestions(
        context, existing_profiles, candidates, routines=routines)
    suggestions_dir = Path(
        getattr(setup_cfg, "suggestions_dir", "data/local/suggestions"))
    persist_style_aware_suggestions(suggestions, suggestions_dir)
    project_id_by_label = {p.get("label", ""): p.get(
        "node_id", "") for p in context.get("projects", []) if p.get("label")}
    persist_style_profile_nodes(
        graph_path, existing_profiles, project_id_by_label)
    persist_imitation_candidate_nodes(
        graph_path, candidates, project_id_by_label)
    persist_style_aware_suggestion_nodes(
        graph_path, suggestions, project_id_by_label)
    console.print(
        f"[green]style-aware suggestions: {len(suggestions)}[/green] -> {suggestions_dir}")
    for s in suggestions[:5]:
        console.print(f"  [bold]{s.suggestion_type}[/bold] {s.title[:50]}")
        console.print(f"    [dim]{s.rationale[:80]}...[/dim]" if len(
            s.rationale) > 80 else f"    [dim]{s.rationale}[/dim]")


@assist_group.command("draft")
def assist_draft(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
) -> None:
    """Load setup outputs + graph + style profiles; generate draft structures; persist locally; print summary."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    from workflow_dataset.personal.project_interpreter import get_assistive_context
    from workflow_dataset.setup.style_persistence import load_style_signals
    from workflow_dataset.personal.style_profiles import build_profiles_from_style_signals, save_style_profile, load_style_profiles
    from workflow_dataset.personal.draft_structure_engine import (
        generate_draft_structures,
        persist_draft_structures,
    )
    from workflow_dataset.personal.assistive_graph import persist_draft_structure_nodes

    context = get_assistive_context(
        graph_path,
        setup_cfg.style_signals_dir,
        setup_cfg.parsed_artifacts_dir,
        sid or "",
    )
    style_records = load_style_signals(
        sid, setup_cfg.style_signals_dir) if sid else []
    profiles = build_profiles_from_style_signals(
        style_records, session_id=sid or "", project_id="")
    profiles_dir = Path(setup_cfg.style_profiles_dir)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    for p in profiles:
        save_style_profile(p, profiles_dir)
    existing_profiles = load_style_profiles(profiles_dir)
    drafts = generate_draft_structures(
        context, existing_profiles, project_id="", domain_hint="")
    draft_dir = Path(getattr(setup_cfg, "draft_structures_dir",
                     "data/local/draft_structures"))
    persist_draft_structures(drafts, draft_dir)
    project_id_by_label = {p.get("label", ""): p.get(
        "node_id", "") for p in context.get("projects", []) if p.get("label")}
    persist_draft_structure_nodes(graph_path, drafts, project_id_by_label)
    console.print(
        f"[green]draft structures: {len(drafts)}[/green] -> {draft_dir}")
    for d in drafts[:5]:
        console.print(f"  [bold]{d.draft_type}[/bold] {d.title}")
        console.print(
            f"    [dim]sections: {', '.join(d.recommended_sections[:4])}[/dim]")


# ----- M6 Agent loop: assist-explain, assist-next-step, assist-refine-draft, assist-chat -----
def _agent_loop_base_dir(settings) -> str:
    """Base dir for agent sessions/responses (data/local)."""
    if getattr(settings, "agent_loop", None) and getattr(settings.agent_loop, "agent_sessions_dir", None):
        return str(Path(settings.agent_loop.agent_sessions_dir).parent)
    return "data/local"


def _agent_loop_config(settings):
    """Agent loop config with defaults."""
    al = getattr(settings, "agent_loop", None)
    if not al:
        return type("AL", (), {
            "agent_loop_enabled": True,
            "agent_loop_default_use_retrieval": True,
            "agent_loop_default_use_llm": False,
            "agent_loop_max_context_docs": 5,
            "agent_loop_save_sessions": True,
        })()
    return al


@assist_group.command("explain")
def assist_explain(
    query: str = typer.Argument(
        ..., help="Question, e.g. 'explain this project', 'why did you suggest this?'"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    project_id: str = typer.Option("", "--project-id"),
    session_id: str = typer.Option(
        "", "--session-id", help="Setup session ID (default: latest)"),
    use_llm: bool = typer.Option(False, "--use-llm"),
) -> None:
    """Answer project/style/suggestion/draft questions. Grounded in graph + retrieval."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    al = _agent_loop_config(settings)
    base_dir = _agent_loop_base_dir(settings)
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    if not corpus_path.exists():
        corpus_path = None

    from workflow_dataset.agent_loop.agent_models import AgentQuery
    from workflow_dataset.agent_loop.response_builder import build_response
    from workflow_dataset.agent_loop.session_store import create_session, save_query, save_response, load_session
    from workflow_dataset.agent_loop.llm_refine import get_llm_refine_fn
    from workflow_dataset.utils.hashes import stable_id
    from workflow_dataset.utils.dates import utc_now_iso

    q = AgentQuery(
        query_id=stable_id("query", query[:50], utc_now_iso(), prefix="q"),
        user_text=query,
        project_id=project_id or getattr(
            al, "agent_loop_project_scope_default", "") or "",
        requested_mode="explain",
        created_utc=utc_now_iso(),
    )
    if getattr(al, "agent_loop_save_sessions", True):
        save_query(q, base_dir)

    llm_refine_fn = get_llm_refine_fn(llm_config_path=Path(
        "configs/llm_training.yaml")) if use_llm else None
    resp = build_response(
        q,
        graph_path=graph_path,
        style_signals_dir=setup_cfg.style_signals_dir,
        parsed_artifacts_dir=setup_cfg.parsed_artifacts_dir,
        style_profiles_dir=setup_cfg.style_profiles_dir,
        suggestions_dir=getattr(
            setup_cfg, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(
            setup_cfg, "draft_structures_dir", "data/local/draft_structures"),
        setup_session_id=sid or "",
        corpus_path=corpus_path,
        max_retrieval_docs=getattr(al, "agent_loop_max_context_docs", 5),
        use_llm=use_llm,
        llm_refine_fn=llm_refine_fn,
    )
    if getattr(al, "agent_loop_save_sessions", True):
        save_response(resp, base_dir)

    console.print(f"[bold]{resp.title}[/bold]")
    console.print(resp.answer)
    if resp.supporting_evidence:
        console.print("[dim]Evidence: " +
                      "; ".join(resp.supporting_evidence[:5]) + "[/dim]")
    console.print(
        f"[dim]confidence={resp.confidence_score:.2f} retrieval={resp.used_retrieval} llm={resp.used_llm}[/dim]")


@assist_group.command("next-step")
def assist_next_step(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    project_id: str = typer.Option("", "--project-id"),
    session_id: str = typer.Option("", "--session-id"),
) -> None:
    """Generate next-step guidance from current project/style/workflow evidence."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    al = _agent_loop_config(settings)
    base_dir = _agent_loop_base_dir(settings)
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    if not corpus_path.exists():
        corpus_path = None

    from workflow_dataset.agent_loop.agent_models import AgentQuery
    from workflow_dataset.agent_loop.response_builder import build_response
    from workflow_dataset.agent_loop.session_store import save_query, save_response
    from workflow_dataset.utils.hashes import stable_id
    from workflow_dataset.utils.dates import utc_now_iso

    q = AgentQuery(
        query_id=stable_id("query", "next_step", utc_now_iso(), prefix="q"),
        user_text="what is a sensible next step for this project?",
        project_id=project_id or getattr(
            al, "agent_loop_project_scope_default", "") or "",
        requested_mode="suggest_next_step",
        created_utc=utc_now_iso(),
    )
    if getattr(al, "agent_loop_save_sessions", True):
        save_query(q, base_dir)

    resp = build_response(
        q,
        graph_path=graph_path,
        style_signals_dir=setup_cfg.style_signals_dir,
        parsed_artifacts_dir=setup_cfg.parsed_artifacts_dir,
        style_profiles_dir=setup_cfg.style_profiles_dir,
        suggestions_dir=getattr(
            setup_cfg, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(
            setup_cfg, "draft_structures_dir", "data/local/draft_structures"),
        setup_session_id=sid or "",
        corpus_path=corpus_path,
        max_retrieval_docs=getattr(al, "agent_loop_max_context_docs", 5),
        use_llm=False,
    )
    if getattr(al, "agent_loop_save_sessions", True):
        save_response(resp, base_dir)

    console.print(f"[bold]{resp.title}[/bold]")
    console.print(resp.answer)
    if resp.supporting_evidence:
        console.print("[dim]Evidence: " +
                      "; ".join(resp.supporting_evidence[:5]) + "[/dim]")
    console.print(f"[dim]confidence={resp.confidence_score:.2f}[/dim]")


@assist_group.command("refine-draft")
def assist_refine_draft(
    draft_type: str = typer.Argument(
        "", help="Draft type (e.g. project_brief, creative_brief_outline) or leave empty for first available"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    project_id: str = typer.Option("", "--project-id"),
    session_id: str = typer.Option("", "--session-id"),
    use_llm: bool = typer.Option(False, "--use-llm"),
) -> None:
    """Refine a draft structure using project/style context. Prints refined structure and explanation."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    al = _agent_loop_config(settings)
    base_dir = _agent_loop_base_dir(settings)
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    if not corpus_path.exists():
        corpus_path = None

    from workflow_dataset.agent_loop.context_builder import build_context_bundle
    from workflow_dataset.agent_loop.draft_refiner import refine_draft
    from workflow_dataset.agent_loop.session_store import save_response
    from workflow_dataset.agent_loop.llm_refine import get_llm_refine_fn
    from workflow_dataset.utils.dates import utc_now_iso

    llm_refine_fn = get_llm_refine_fn(llm_config_path=Path(
        "configs/llm_training.yaml")) if use_llm else None
    context_bundle = build_context_bundle(
        graph_path=graph_path,
        style_signals_dir=setup_cfg.style_signals_dir,
        parsed_artifacts_dir=setup_cfg.parsed_artifacts_dir,
        style_profiles_dir=setup_cfg.style_profiles_dir,
        suggestions_dir=getattr(
            setup_cfg, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(
            setup_cfg, "draft_structures_dir", "data/local/draft_structures"),
        setup_session_id=sid or "",
        project_id=project_id or "",
        corpus_path=corpus_path,
        query="draft structure refinement",
        max_retrieval_docs=getattr(al, "agent_loop_max_context_docs", 5),
    )
    refined, resp = refine_draft(
        context_bundle,
        draft_id="",
        draft_type=draft_type or "",
        project_id=project_id or "",
        use_llm=use_llm,
        llm_refine_fn=llm_refine_fn,
    )
    if getattr(al, "agent_loop_save_sessions", True):
        save_response(resp, base_dir)

    console.print(f"[bold]{resp.title}[/bold]")
    console.print(resp.answer)
    if refined:
        outline = refined.get("structure_outline") if isinstance(
            refined, dict) else getattr(refined, "structure_outline", "")
        if outline:
            console.print("[bold]Refined outline:[/bold]")
            console.print(outline[:2000] +
                          ("..." if len(outline) > 2000 else ""))
    console.print(
        f"[dim]confidence={resp.confidence_score:.2f} retrieval={resp.used_retrieval} llm={resp.used_llm}[/dim]")


@assist_group.command("chat")
def assist_chat(
    query: str = typer.Argument(
        "", help="One-shot question, or leave empty for REPL"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    project_id: str = typer.Option("", "--project-id"),
    session_id: str = typer.Option("", "--session-id"),
    use_llm: bool = typer.Option(False, "--use-llm"),
) -> None:
    """One-shot or REPL: route query, build context, retrieve, answer with citations."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    al = _agent_loop_config(settings)
    base_dir = _agent_loop_base_dir(settings)
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    if not corpus_path.exists():
        corpus_path = None

    from workflow_dataset.agent_loop.agent_models import AgentQuery
    from workflow_dataset.agent_loop.response_builder import build_response
    from workflow_dataset.agent_loop.session_store import create_session, save_query, save_response, load_session
    from workflow_dataset.agent_loop.llm_refine import get_llm_refine_fn
    from workflow_dataset.utils.hashes import stable_id
    from workflow_dataset.utils.dates import utc_now_iso

    llm_refine_fn = get_llm_refine_fn(llm_config_path=Path(
        "configs/llm_training.yaml")) if use_llm else None

    def run_turn(user_text: str) -> None:
        q = AgentQuery(
            query_id=stable_id(
                "query", user_text[:50], utc_now_iso(), prefix="q"),
            user_text=user_text,
            project_id=project_id or getattr(
                al, "agent_loop_project_scope_default", "") or "",
            created_utc=utc_now_iso(),
        )
        if getattr(al, "agent_loop_save_sessions", True):
            save_query(q, base_dir)
        resp = build_response(
            q,
            graph_path=graph_path,
            style_signals_dir=setup_cfg.style_signals_dir,
            parsed_artifacts_dir=setup_cfg.parsed_artifacts_dir,
            style_profiles_dir=setup_cfg.style_profiles_dir,
            suggestions_dir=getattr(
                setup_cfg, "suggestions_dir", "data/local/suggestions"),
            draft_structures_dir=getattr(
                setup_cfg, "draft_structures_dir", "data/local/draft_structures"),
            setup_session_id=sid or "",
            corpus_path=corpus_path,
            max_retrieval_docs=getattr(al, "agent_loop_max_context_docs", 5),
            use_llm=use_llm,
            llm_refine_fn=llm_refine_fn,
        )
        resp.query_id = q.query_id
        if getattr(al, "agent_loop_save_sessions", True):
            save_response(resp, base_dir)
        console.print(f"[bold]{resp.title}[/bold]")
        console.print(resp.answer)
        if resp.supporting_evidence:
            console.print("[dim]Evidence: " +
                          "; ".join(resp.supporting_evidence[:5]) + "[/dim]")
        console.print(
            f"[dim]confidence={resp.confidence_score:.2f} retrieval={resp.used_retrieval} llm={resp.used_llm}[/dim]\n")

    if query:
        run_turn(query)
        return
    # REPL
    console.print(
        "[dim]Assist chat (REPL). Type a question and press Enter. Empty line or 'exit' to quit.[/dim]")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line or line.lower() in ("exit", "quit", "q"):
            break
        run_turn(line)


# ----- M7 Sandboxed materialization -----
def _materialization_config(settings):
    mat = getattr(settings, "materialization", None)
    if not mat:
        return type("Mat", (), {
            "materialization_enabled": True,
            "materialization_workspace_root": "data/local/workspaces",
            "materialization_save_manifests": True,
            "materialization_graph_persistence": True,
            "materialization_preview_enabled": True,
            "materialization_allow_markdown": True,
            "materialization_allow_csv": True,
            "materialization_allow_json": True,
            "materialization_allow_folder_scaffolds": True,
            "materialization_default_use_llm": False,
        })()
    return mat


@assist_group.command("materialize")
def assist_materialize(
    draft_type: str = typer.Argument(
        "", help="Draft type (e.g. project_brief, creative_brief_outline) or suggestion id"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    project_id: str = typer.Option("", "--project-id"),
    session_id: str = typer.Option("", "--session-id"),
    use_llm: bool = typer.Option(False, "--use-llm"),
    output_family: str = typer.Option(
        "", "--output-family", help="text | table | folder_scaffold | creative_scaffold"),
    workspace: str = typer.Option(
        "", "--workspace", help="Override workspace root"),
) -> None:
    """Materialize draft or suggestion into sandbox. Outputs only in data/local/workspaces."""
    settings = load_settings(config)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]setup config missing[/red]")
        raise typer.Exit(1)
    mat = _materialization_config(settings)
    if not getattr(mat, "materialization_enabled", True):
        console.print("[yellow]materialization disabled in config[/yellow]")
        raise typer.Exit(0)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    workspace_root = Path(workspace or getattr(
        mat, "materialization_workspace_root", "data/local/workspaces"))
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    if not corpus_path.exists():
        corpus_path = None

    from workflow_dataset.agent_loop.context_builder import build_context_bundle
    from workflow_dataset.materialize.artifact_builder import materialize_from_draft, materialize_from_suggestion
    from workflow_dataset.materialize.preview_renderer import render_preview
    from workflow_dataset.materialize.manifest_store import save_manifest
    from workflow_dataset.materialize.materialize_graph import persist_materialization_nodes
    from workflow_dataset.agent_loop.llm_refine import get_llm_refine_fn

    context_bundle = build_context_bundle(
        graph_path=graph_path,
        style_signals_dir=setup_cfg.style_signals_dir,
        parsed_artifacts_dir=setup_cfg.parsed_artifacts_dir,
        style_profiles_dir=setup_cfg.style_profiles_dir,
        suggestions_dir=getattr(
            setup_cfg, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(
            setup_cfg, "draft_structures_dir", "data/local/draft_structures"),
        setup_session_id=sid or "",
        project_id=project_id or "",
        corpus_path=corpus_path,
        query=draft_type,
        max_retrieval_docs=5,
    )
    project_id_by_label = {p.get("label", ""): p.get("node_id", "") for p in (
        context_bundle.get("project_context") or {}).get("projects", []) if p.get("label")}
    llm_refine_fn = get_llm_refine_fn(llm_config_path=Path(
        "configs/llm_training.yaml")) if use_llm else None

    if draft_type.startswith("sug_") or draft_type.startswith("suggestion_"):
        manifest, ws_path = materialize_from_suggestion(
            context_bundle,
            workspace_root,
            suggestion_id=draft_type,
            session_id=sid or "",
            project_id=project_id or "",
            save_manifests=getattr(
                mat, "materialization_save_manifests", True),
        )
    else:
        manifest, ws_path = materialize_from_draft(
            context_bundle,
            workspace_root,
            draft_type=draft_type or "project_brief",
            session_id=sid or "",
            project_id=project_id or "",
            use_llm=use_llm,
            llm_refine_fn=llm_refine_fn,
            allow_markdown=getattr(
                mat, "materialization_allow_markdown", True),
            allow_csv=getattr(mat, "materialization_allow_csv", True),
            allow_json=getattr(mat, "materialization_allow_json", True),
            allow_folder_scaffolds=getattr(
                mat, "materialization_allow_folder_scaffolds", True),
            save_manifests=getattr(
                mat, "materialization_save_manifests", True),
        )
    if getattr(mat, "materialization_graph_persistence", True) and graph_path.exists():
        persist_materialization_nodes(
            graph_path, manifest, ws_path, project_id_by_label)
    console.print(
        f"[green]Materialized: {len(manifest.output_paths)} output(s)[/green] -> {ws_path}")
    if getattr(mat, "materialization_preview_enabled", True):
        preview = render_preview(manifest, ws_path, max_file_preview_chars=400)
        console.print(preview[:2500] + ("..." if len(preview) > 2500 else ""))
    else:
        for p in manifest.output_paths:
            console.print(f"  {p}")
    console.print(f"[dim]Manifest: {ws_path / 'MANIFEST.json'}[/dim]")


@assist_group.command("preview")
def assist_preview(
    workspace_path: str = typer.Argument(
        ..., help="Path to materialized workspace (e.g. data/local/workspaces/materialized/req_xxx)"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Show preview of a materialized artifact/workspace."""
    from workflow_dataset.materialize.manifest_store import load_manifest
    from workflow_dataset.materialize.preview_renderer import render_preview, render_artifact_tree
    path = Path(workspace_path)
    if not path.exists():
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)
    manifest = load_manifest(path)
    if manifest:
        console.print(render_preview(
            manifest, path, max_file_preview_chars=500))
    else:
        console.print(render_artifact_tree(path))
        console.print("[dim]No MANIFEST.json in this workspace.[/dim]")


@assist_group.command("list-workspaces")
def assist_list_workspaces(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """List generated workspaces/manifests for a session or all."""
    settings = load_settings(config)
    mat = _materialization_config(settings)
    root = Path(getattr(mat, "materialization_workspace_root",
                "data/local/workspaces"))
    from workflow_dataset.materialize.workspace_manager import list_workspaces
    items = list_workspaces(root, session_id=session_id or "", limit=limit)
    if not items:
        console.print("[dim]No workspaces found.[/dim]")
        raise typer.Exit(0)
    for w in items:
        console.print(
            f"  [bold]{w.get('name', '')}[/bold] -> {w.get('path', '')}")


# ----- M8 User-approved apply-to-project -----
def _apply_config(settings):
    ap = getattr(settings, "apply", None)
    if not ap:
        return type("Apply", (), {
            "apply_enabled": False,
            "apply_require_confirm": True,
            "apply_default_dry_run": True,
            "apply_allow_overwrite": False,
            "apply_create_backups": True,
            "apply_manifest_root": "data/local/applies",
            "apply_allowed_target_roots": [],
            "apply_graph_persistence": True,
            "apply_rollback_enabled": True,
        })()
    return ap


@assist_group.command("apply-plan")
def assist_apply_plan(
    workspace_path: str = typer.Argument(
        ..., help="Path to sandbox workspace (e.g. data/local/workspaces/materialized/req_xxx)"),
    target_path: str = typer.Argument(...,
                                      help="Target directory to copy into"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    allow_overwrite: bool = typer.Option(False, "--allow-overwrite"),
) -> None:
    """Produce dry-run apply plan and diff preview. Does not copy anything."""
    settings = load_settings(config)
    ap = _apply_config(settings)
    from workflow_dataset.apply.target_validator import validate_target
    from workflow_dataset.apply.copy_planner import build_apply_plan
    from workflow_dataset.apply.diff_preview import render_diff_preview
    ws = Path(workspace_path).resolve()
    target = Path(target_path).resolve()
    ok, msg = validate_target(
        target,
        allowed_roots=getattr(ap, "apply_allowed_target_roots", None) or [],
        must_exist=False,
    )
    if not ok:
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)
    plan, err = build_apply_plan(
        ws, target, allow_overwrite=allow_overwrite, dry_run=True)
    if err and not plan:
        console.print(f"[red]{err}[/red]")
        raise typer.Exit(1)
    if plan:
        console.print(render_diff_preview(plan))
    else:
        console.print("[yellow]No plan generated.[/yellow]")


@assist_group.command("apply")
def assist_apply(
    workspace_path: str = typer.Argument(...,
                                         help="Path to sandbox workspace"),
    target_path: str = typer.Argument(...,
                                      help="Target directory to copy into"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    confirm: bool = typer.Option(
        False, "--confirm", help="Explicit confirmation required to copy"),
    allow_overwrite: bool = typer.Option(False, "--allow-overwrite"),
) -> None:
    """Apply sandbox outputs to target. Requires --confirm to execute."""
    settings = load_settings(config)
    ap = _apply_config(settings)
    if not getattr(ap, "apply_enabled", False):
        console.print(
            "[red]Apply is disabled. Enable apply.apply_enabled in config.[/red]")
        raise typer.Exit(1)
    if not confirm:
        console.print(
            "[yellow]Apply requires explicit --confirm. Run without --confirm to see plan first.[/yellow]")
        raise typer.Exit(0)
    from workflow_dataset.apply.target_validator import validate_target
    from workflow_dataset.apply.copy_planner import build_apply_plan
    from workflow_dataset.apply.apply_executor import execute_apply
    from workflow_dataset.apply.apply_models import ApplyRequest
    from workflow_dataset.apply.apply_manifest_store import save_apply_request, save_apply_plan, save_apply_result
    from workflow_dataset.apply.apply_graph import persist_apply_request, persist_apply_plan_node, persist_apply_result_node
    from workflow_dataset.utils.dates import utc_now_iso
    from workflow_dataset.utils.hashes import stable_id
    ws = Path(workspace_path).resolve()
    target = Path(target_path).resolve()
    ok, msg = validate_target(
        target,
        allowed_roots=getattr(ap, "apply_allowed_target_roots", None) or [],
        must_exist=False,
    )
    if not ok:
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)
    plan, err = build_apply_plan(
        ws, target, allow_overwrite=allow_overwrite, dry_run=True)
    if err and not plan:
        console.print(f"[red]{err}[/red]")
        raise typer.Exit(1)
    if not plan or not plan.operations:
        console.print("[yellow]Nothing to apply.[/yellow]")
        raise typer.Exit(0)
    apply_id = stable_id("apply", str(ws), str(
        target), utc_now_iso(), prefix="apply")
    plan.apply_id = apply_id
    manifest_root = Path(
        getattr(ap, "apply_manifest_root", "data/local/applies"))
    backup_root = Path(getattr(ap, "apply_backup_root", "data/local/applies"))
    req = ApplyRequest(
        apply_id=apply_id,
        workspace_path=str(ws),
        target_root=str(target),
        user_confirmed=True,
        created_utc=utc_now_iso(),
    )
    save_apply_request(req, manifest_root)
    save_apply_plan(plan, manifest_root)
    result, exec_err = execute_apply(
        plan,
        ws,
        target,
        user_confirmed=True,
        create_backups=getattr(ap, "apply_create_backups", True),
        backup_root=backup_root,
    )
    if not result:
        console.print(f"[red]{exec_err}[/red]")
        raise typer.Exit(1)
    result.apply_id = apply_id
    save_apply_result(result, manifest_root)
    if getattr(ap, "apply_graph_persistence", True):
        graph_path = getattr(settings.paths, "graph_store_path",
                             "data/local/work_graph.sqlite")
        if Path(graph_path).exists():
            persist_apply_request(graph_path, req)
            persist_apply_plan_node(graph_path, plan, apply_id)
            persist_apply_result_node(graph_path, result, apply_id)
    console.print(
        f"[green]Applied {len(result.applied_paths)} path(s)[/green] -> {target}")
    if result.rollback_token:
        console.print(f"[dim]Rollback token: {result.rollback_token}[/dim]")
    console.print(
        f"[dim]Manifest: {manifest_root / 'results' / f'{result.result_id}.json'}[/dim]")


@assist_group.command("rollback")
def assist_rollback(
    rollback_token: str = typer.Argument(...,
                                         help="Rollback token from apply output"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Restore files from backup using rollback token."""
    settings = load_settings(config)
    ap = _apply_config(settings)
    if not getattr(ap, "apply_rollback_enabled", True):
        console.print("[red]Rollback is disabled.[/red]")
        raise typer.Exit(1)
    from workflow_dataset.apply.rollback_store import perform_rollback
    manifest_root = Path(
        getattr(ap, "apply_manifest_root", "data/local/applies"))
    ok, msg = perform_rollback(rollback_token, manifest_root)
    if ok:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)


@assist_group.command("apply-preview")
def assist_apply_preview(
    workspace_path: str = typer.Argument(...,
                                         help="Path to sandbox workspace"),
    target_path: str = typer.Argument(..., help="Target directory"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    allow_overwrite: bool = typer.Option(False, "--allow-overwrite"),
) -> None:
    """Show structured preview of apply plan and conflicts."""
    settings = load_settings(config)
    from workflow_dataset.apply.copy_planner import build_apply_plan
    from workflow_dataset.apply.diff_preview import render_diff_preview
    plan, err = build_apply_plan(Path(workspace_path), Path(
        target_path), allow_overwrite=allow_overwrite, dry_run=True)
    if err and not plan:
        console.print(f"[red]{err}[/red]")
        raise typer.Exit(1)
    if plan:
        console.print(render_diff_preview(plan))
    else:
        console.print("[dim]No plan.[/dim]")


# ----- M10 Generation scaffolding -----
def _generation_config(settings):
    gen = getattr(settings, "generation", None)
    if not gen:
        return type("Gen", (), {
            "generation_enabled": True,
            "generation_workspace_root": "data/local/generation",
            "generation_allow_style_packs": True,
            "generation_allow_prompt_packs": True,
            "generation_allow_asset_plans": True,
            "generation_enable_demo_backend": False,
            "generation_graph_persistence": True,
        })()
    return gen


def _output_adapters_config(settings):
    oa = getattr(settings, "output_adapters", None)
    if not oa:
        return type("OA", (), {
            "output_adapters_enabled": True,
            "output_adapter_bundle_root": "data/local/bundles",
            "output_adapter_graph_persistence": True,
            "output_adapter_preview_enabled": True,
        })()
    return oa


@assist_group.command("generate-plan")
def assist_generate_plan(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    project_id: str = typer.Option("", "--project-id"),
    session_id: str = typer.Option("", "--session-id"),
    generation_type: str = typer.Option(
        "image_pack", "--type", "-t", help="image_pack, shot_plan, report_variant, design"),
    source_ref: str = typer.Option(
        "", "--source-ref", help="draft_id or suggestion_id"),
    source_type: str = typer.Option(
        "project", "--source-type", help="project, draft, suggestion"),
) -> None:
    """Produce style pack + prompt pack + asset plan; persist locally. Sandbox-only."""
    settings = load_settings(config)
    gen = _generation_config(settings)
    if not getattr(gen, "generation_enabled", True):
        console.print("[yellow]Generation is disabled in config.[/yellow]")
        raise typer.Exit(0)
    setup_cfg = settings.setup
    if not setup_cfg:
        console.print("[red]Setup config missing[/red]")
        raise typer.Exit(1)
    sid = session_id or _resolve_latest_session_id(setup_cfg)
    graph_path = Path(
        getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    workspace_root = Path(
        getattr(gen, "generation_workspace_root", "data/local/generation"))

    from workflow_dataset.generate.run_generation import run_generation_plan
    request, manifest, ws_path = run_generation_plan(
        graph_path=graph_path,
        style_signals_dir=setup_cfg.style_signals_dir,
        parsed_artifacts_dir=setup_cfg.parsed_artifacts_dir,
        style_profiles_dir=getattr(
            setup_cfg, "style_profiles_dir", "data/local/style_profiles"),
        suggestions_dir=getattr(
            setup_cfg, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(
            setup_cfg, "draft_structures_dir", "data/local/draft_structures"),
        generation_workspace_root=workspace_root,
        setup_session_id=sid or "",
        project_id=project_id or "",
        domain="",
        source_ref=source_ref,
        source_type=source_type,
        generation_type=generation_type,
        use_llm=False,
        allow_style_packs=getattr(gen, "generation_allow_style_packs", True),
        allow_prompt_packs=getattr(gen, "generation_allow_prompt_packs", True),
        allow_asset_plans=getattr(gen, "generation_allow_asset_plans", True),
        persist_to_graph=getattr(gen, "generation_graph_persistence", True),
    )
    console.print(f"[green]Generation plan: {request.generation_id}[/green]")
    console.print(
        f"  style_packs: {len(manifest.style_pack_refs)} prompt_packs: {len(manifest.prompt_pack_refs)} asset_plans: {len(manifest.asset_plan_refs)}")
    console.print(f"  workspace: {ws_path}")
    console.print(
        f"  manifest: {workspace_root / 'manifests' / (manifest.manifest_id + '.json')}")


@assist_group.command("generate-preview")
def assist_generate_preview(
    manifest_id: str = typer.Argument(...,
                                      help="Generation manifest ID (e.g. gm_...)"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    hydrate: bool = typer.Option(
        True, "--hydrate/--no-hydrate", help="Load prompt/asset/style packs from store"),
) -> None:
    """Inspect a generation manifest: packs, execution records, and generated outputs."""
    settings = load_settings(config)
    gen = _generation_config(settings)
    root = Path(getattr(gen, "generation_workspace_root",
                "data/local/generation"))
    from workflow_dataset.generate.sandbox_generation_store import (
        load_generation_manifest,
        load_packs_for_manifest,
    )
    manifest = load_generation_manifest(manifest_id, root)
    if not manifest:
        console.print(f"[red]Manifest not found: {manifest_id}[/red]")
        raise typer.Exit(1)
    if hydrate:
        load_packs_for_manifest(manifest, root)
    console.print(f"[bold]Manifest {manifest.manifest_id}[/bold]")
    console.print(f"  generation_id: {manifest.generation_id}")
    console.print(f"  workspace: {manifest.workspace_path}")
    console.print(f"  status: {manifest.status}")
    console.print(f"  backend_requested: {manifest.backend_requested or '-'}")
    console.print(f"  backend_executed: {manifest.backend_executed or '-'}")
    console.print(f"  style_pack_refs: {manifest.style_pack_refs}")
    console.print(f"  prompt_pack_refs: {manifest.prompt_pack_refs}")
    console.print(f"  asset_plan_refs: {manifest.asset_plan_refs}")
    if manifest.execution_records:
        console.print("[bold]Execution records[/bold]")
        for rec in manifest.execution_records:
            console.print(
                f"  backend: {rec.backend_name} v{rec.backend_version} status={rec.execution_status}")
            console.print(
                f"    used_llm={rec.used_llm} used_fallback={rec.used_fallback} executed_utc={rec.executed_utc}")
            for p in rec.generated_output_paths[:10]:
                console.print(f"    output: {p}")
            if rec.error_message:
                console.print(f"    error: {rec.error_message}")
    if manifest.generated_output_paths:
        console.print("[bold]Generated outputs[/bold]")
        for p in manifest.generated_output_paths[:15]:
            console.print(f"  {p}")
    if manifest.prompt_packs:
        for pp in manifest.prompt_packs[:5]:
            txt = (pp.prompt_text or "")[:120]
            console.print(
                f"  [cyan]PromptPack {pp.prompt_family}[/cyan]: {txt}...")
    if manifest.asset_plans:
        for ap in manifest.asset_plans[:2]:
            console.print(
                f"  [cyan]AssetPlan[/cyan] targets: {ap.target_outputs[:5]}")


@assist_group.command("list-generations")
def assist_list_generations(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    session_id: str = typer.Option("", "--session-id"),
    project_id: str = typer.Option("", "--project-id"),
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """List generation requests/manifests for session or project."""
    settings = load_settings(config)
    gen = _generation_config(settings)
    root = Path(getattr(gen, "generation_workspace_root",
                "data/local/generation"))
    from workflow_dataset.generate.sandbox_generation_store import list_generation_requests
    items = list_generation_requests(
        root, session_id=session_id, project_id=project_id, limit=limit)
    if not items:
        console.print("[dim]No generation requests yet.[/dim]")
        raise typer.Exit(0)
    for g in items:
        console.print(
            f"  [bold]{g['generation_id']}[/bold] {g['generation_type']} session={g['session_id']} project={g['project_id']}")


def _generation_backend_enabled(gen: Any, backend: str) -> bool:
    if backend == "mock":
        return getattr(gen, "generation_enable_demo_backend", False)
    if backend == "document":
        return getattr(gen, "generation_enable_document_backend", False)
    if backend == "image_demo":
        return getattr(gen, "generation_enable_image_demo_backend", False)
    return False


@assist_group.command("generate-run")
def assist_generate_run(
    generation_id: str = typer.Argument(...,
                                        help="Generation ID from generate-plan"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    backend: str = typer.Option(
        None, "--backend", "-b", help="Backend: mock, document, image_demo (default from config)"),
    use_llm: bool = typer.Option(
        False, "--use-llm", help="Use local LLM when backend supports it"),
    allow_fallback: bool = typer.Option(
        True, "--allow-fallback/--no-fallback", help="Allow deterministic fallback"),
) -> None:
    """Run generation backend in sandbox only. Config-gated; no writes outside sandbox."""
    import json
    settings = load_settings(config)
    gen = _generation_config(settings)
    backend = backend or getattr(gen, "generation_default_backend", "mock")
    if not _generation_backend_enabled(gen, backend):
        console.print(
            f"[yellow]Backend '{backend}' is disabled. Enable generation_enable_document_backend, "
            "generation_enable_image_demo_backend, or generation_enable_demo_backend for mock.[/yellow]"
        )
        raise typer.Exit(0)
    use_llm = use_llm and getattr(gen, "generation_backend_allow_llm", False)
    allow_fallback = allow_fallback and getattr(
        gen, "generation_backend_fallback_enabled", True)
    root = Path(getattr(gen, "generation_workspace_root",
                "data/local/generation"))
    from workflow_dataset.generate.sandbox_generation_store import (
        load_generation_manifest,
        load_packs_for_manifest,
        save_generation_manifest,
    )
    from workflow_dataset.generate.backend_registry import execute_generation, get_backend
    from workflow_dataset.generate.generate_models import GenerationRequest, GenerationStatus

    if get_backend(backend) is None:
        console.print(
            f"[red]Unknown backend: {backend}. Use assist list-generation-backends.[/red]")
        raise typer.Exit(1)
    req_path = root / "requests" / f"{generation_id}.json"
    if not req_path.exists():
        console.print(
            f"[red]Generation request not found: {generation_id}[/red]")
        raise typer.Exit(1)
    req_data = json.loads(req_path.read_text(encoding="utf-8"))
    req_data["status"] = GenerationStatus(
        req_data.get("status", "planned_only"))
    request = GenerationRequest.model_validate(req_data)
    manifest_id = None
    for p in (root / "manifests").glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("generation_id") == generation_id:
                manifest_id = p.stem
                break
        except Exception:
            continue
    manifest = load_generation_manifest(
        manifest_id, root) if manifest_id else None
    if not manifest:
        console.print(
            "[yellow]Manifest not found for this generation.[/yellow]")
        raise typer.Exit(0)
    load_packs_for_manifest(manifest, root)
    workspace_path = root / generation_id
    workspace_path.mkdir(parents=True, exist_ok=True)
    ok, msg, output_paths, execution_record = execute_generation(
        backend,
        request,
        manifest,
        workspace_path,
        prompt_packs=manifest.prompt_packs,
        asset_plans=manifest.asset_plans,
        style_packs=manifest.style_packs,
        use_llm=use_llm,
        allow_fallback=allow_fallback,
    )
    manifest.backend_requested = backend
    manifest.generated_output_paths = list(
        manifest.generated_output_paths) + output_paths
    if execution_record:
        manifest.execution_records = list(
            manifest.execution_records) + [execution_record]
    manifest.backend_executed = backend
    manifest.status = GenerationStatus.BACKEND_EXECUTED if ok else GenerationStatus.BACKEND_FAILED
    save_generation_manifest(manifest, root)
    if ok:
        console.print(f"[green]{msg}[/green]")
        for p in output_paths[:10]:
            console.print(f"  [dim]{p}[/dim]")
    else:
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)


@assist_group.command("list-generation-backends")
def assist_list_generation_backends(config: str = typer.Option("configs/settings.yaml", "--config", "-c")) -> None:
    """List registered generation backends and their capabilities."""
    from workflow_dataset.generate import list_backends
    for meta in list_backends():
        console.print(
            f"  [bold]{meta.backend_name}[/bold] ({meta.backend_type}) v{meta.version}")
        console.print(f"    families: {meta.supported_families}")
        console.print(f"    artifact types: {meta.supported_artifact_types}")


@assist_group.command("generate-review")
def assist_generate_review(
    generation_id: str = typer.Argument(..., help="Generation ID"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    manifest_id: str = typer.Option(
        "", "--manifest-id", "-m", help="Optional manifest ID to load paths from"),
    compare: bool = typer.Option(
        False, "--compare", help="List variants for comparison"),
) -> None:
    """Inspect generated outputs: preview and metadata. Optionally list variants."""
    settings = load_settings(config)
    gen = _generation_config(settings)
    if not getattr(gen, "generation_preview_enabled", True) or not getattr(gen, "generation_review_enabled", True):
        console.print(
            "[yellow]Generation review is disabled in config.[/yellow]")
        raise typer.Exit(0)
    root = Path(getattr(gen, "generation_workspace_root",
                "data/local/generation"))
    workspace_path = root / generation_id
    review_root = root / "review"
    from workflow_dataset.generate.sandbox_generation_store import load_generation_manifest, load_packs_for_manifest
    from workflow_dataset.review.artifact_preview import preview_artifacts_from_manifest

    manifest_id = manifest_id or ""
    if not manifest_id:
        for p in (root / "manifests").glob("*.json"):
            m = load_generation_manifest(p.stem, root)
            if m and m.generation_id == generation_id:
                manifest_id = p.stem
                manifest = m
                break
        else:
            manifest = None
    else:
        manifest = load_generation_manifest(manifest_id, root)
    if not manifest:
        console.print(
            "[yellow]Manifest not found; listing workspace files.[/yellow]")
        paths = [str(f) for f in workspace_path.rglob(
            "*") if f.is_file()] if workspace_path.exists() else []
    else:
        load_packs_for_manifest(manifest, root)
        paths = list(manifest.generated_output_paths or [])
    if not paths:
        console.print("[dim]No generated outputs to review.[/dim]")
        raise typer.Exit(0)
    previews = preview_artifacts_from_manifest(
        paths,
        workspace_path,
        generation_id=generation_id,
        execution_records=manifest.execution_records if manifest else None,
        style_pack_refs=manifest.style_pack_refs if manifest else [],
        prompt_pack_refs=manifest.prompt_pack_refs if manifest else [],
    )
    for review, body in previews:
        console.print(Panel(body[:2000] + ("..." if len(body) >
                      2000 else ""), title=review.summary, border_style="dim"))
    if compare:
        from workflow_dataset.review import get_variants_for_generation
        variants = get_variants_for_generation(generation_id, review_root)
        if variants:
            console.print("[bold]Variants[/bold]")
            for v in variants[:10]:
                console.print(
                    f"  {v.variant_id} {v.variant_type} {v.revision_note[:40]}...")
        else:
            console.print("[dim]No variants recorded.[/dim]")


@assist_group.command("generate-refine")
def assist_generate_refine(
    generation_id: str = typer.Argument(..., help="Generation ID"),
    artifact_path: str = typer.Argument(
        ..., help="Path to generated artifact (relative to generation workspace or absolute)"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    use_llm: bool = typer.Option(
        False, "--use-llm", help="Use local LLM refinement if enabled"),
    instruction: str = typer.Option(
        "", "--instruction", "-i", help="Optional refinement instruction"),
) -> None:
    """Refine a generated document artifact. Writes refined variant to sandbox. Records version lineage."""
    settings = load_settings(config)
    gen = _generation_config(settings)
    if not getattr(gen, "generation_refinement_enabled", True):
        console.print("[yellow]Generation refinement is disabled.[/yellow]")
        raise typer.Exit(0)
    use_llm = use_llm and getattr(
        gen, "generation_refinement_default_use_llm", False) or use_llm
    root = Path(getattr(gen, "generation_workspace_root",
                "data/local/generation"))
    workspace_path = root / generation_id
    review_root = root / "review"
    art_path = Path(artifact_path)
    if not art_path.is_absolute():
        art_path = workspace_path / artifact_path
    from workflow_dataset.review import build_refine_request, refine_document, get_llm_refine_fn_for_review
    req = build_refine_request(
        artifact_id=art_path.stem,
        generation_id=generation_id,
        use_llm=use_llm,
        user_instruction=instruction,
    )
    llm_fn = get_llm_refine_fn_for_review(
        Path("configs/llm_training.yaml")) if use_llm else None
    ok, msg, out_paths, variant = refine_document(
        art_path,
        workspace_path,
        req,
        style_packs=[],
        prompt_packs=[],
        llm_refine_fn=llm_fn,
        generation_id=generation_id,
        review_store_path=review_root,
    )
    if ok:
        console.print(f"[green]{msg}[/green]")
        for p in out_paths:
            console.print(f"  [dim]{p}[/dim]")
    else:
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)


@assist_group.command("generate-adopt")
def assist_generate_adopt(
    generation_id: str = typer.Argument(..., help="Generation ID"),
    paths: str = typer.Argument(
        ..., help="Comma-separated relative paths to adopt (e.g. creative_brief_generated.md)"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    target_project_id: str = typer.Option("", "--target-project"),
) -> None:
    """Mark selected generated outputs as adoption candidates. Bridges into apply flow; does not apply immediately."""
    settings = load_settings(config)
    gen = _generation_config(settings)
    if not getattr(gen, "generation_adoption_bridge_enabled", True):
        console.print("[yellow]Adoption bridge is disabled.[/yellow]")
        raise typer.Exit(0)
    root = Path(getattr(gen, "generation_workspace_root",
                "data/local/generation"))
    workspace_path = root / generation_id
    if not workspace_path.exists():
        console.print(f"[red]Workspace not found: {workspace_path}[/red]")
        raise typer.Exit(1)
    candidate_paths = [p.strip() for p in paths.split(",") if p.strip()]
    from workflow_dataset.review import create_adoption_candidate, save_adoption_candidate, build_apply_plan_for_adoption
    review_root = root / "review"
    candidate = create_adoption_candidate(
        generation_id=generation_id,
        workspace_path=workspace_path,
        candidate_paths=candidate_paths,
        target_project_id=target_project_id,
    )
    save_adoption_candidate(candidate, review_root)
    console.print(
        f"[green]Adoption candidate created: {candidate.adoption_id}[/green]")
    console.print("  workspace:", candidate.workspace_path)
    console.print("  paths:", candidate.candidate_paths)
    console.print(
        "[dim]To apply: use apply-plan with this workspace and target path, or use console Apply flow.[/dim]")


@assist_group.command("generate-compare")
def assist_generate_compare(
    path_a: str = typer.Argument(..., help="First artifact path"),
    path_b: str = typer.Argument(..., help="Second artifact path"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Compare two generated variants. Shows summary and preview."""
    settings = load_settings(config)
    gen = _generation_config(settings)
    if not getattr(gen, "generation_preview_enabled", True):
        console.print("[yellow]Generation preview is disabled.[/yellow]")
        raise typer.Exit(0)
    from workflow_dataset.review import compare_variants
    result = compare_variants(Path(path_a), Path(path_b))
    console.print(
        f"Path A: {result.get('path_a')}  lines={result.get('line_count_a')}  size={result.get('size_a')}")
    console.print(
        f"Path B: {result.get('path_b')}  lines={result.get('line_count_b')}  size={result.get('size_b')}")
    console.print(f"Same content: {result.get('same_content')}")
    if result.get("preview_a"):
        console.print(Panel(result["preview_a"][:1500],
                      title="Preview A", border_style="blue"))
    if result.get("preview_b"):
        console.print(Panel(result["preview_b"][:1500],
                      title="Preview B", border_style="green"))


# ----- M13 Output bundle commands -----


@assist_group.command("bundle-create")
def assist_bundle_create(
    adapter_type: str = typer.Argument(
        ..., help="Adapter: spreadsheet, creative_package, design_package, ops_handoff"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    generation_id: str = typer.Option("", "--generation-id"),
    review_id: str = typer.Option("", "--review-id"),
    artifact_path: str = typer.Option("", "--artifact-path"),
    project_id: str = typer.Option("", "--project-id"),
    domain: str = typer.Option("", "--domain"),
    populate: bool = typer.Option(
        False, "--populate", "-p", help="Populate bundle from source artifact content (M14)"),
) -> None:
    """Create a toolchain-native output bundle from an adapter. Sandbox-only. Use --populate for content-aware fill."""
    settings = load_settings(config)
    oa = _output_adapters_config(settings)
    if not getattr(oa, "output_adapters_enabled", True):
        console.print("[yellow]Output adapters are disabled.[/yellow]")
        raise typer.Exit(0)
    from workflow_dataset.output_adapters import create_bundle, list_adapters, get_adapter
    from workflow_dataset.output_adapters.adapter_models import OutputAdapterRequest
    from workflow_dataset.utils.dates import utc_now_iso
    from workflow_dataset.utils.hashes import stable_id
    if get_adapter(adapter_type) is None:
        console.print(
            f"[red]Unknown adapter: {adapter_type}. Use assist list-bundles to see adapters.[/red]")
        raise typer.Exit(1)
    bundle_root = Path(
        getattr(oa, "output_adapter_bundle_root", "data/local/bundles"))
    bundle_root.mkdir(parents=True, exist_ok=True)
    ts = utc_now_iso()
    req_id = stable_id("adreq", adapter_type,
                       generation_id or review_id or ts, prefix="adreq")
    request = OutputAdapterRequest(
        adapter_request_id=req_id,
        generation_id=generation_id,
        review_id=review_id,
        artifact_id="",
        project_id=project_id,
        domain=domain,
        adapter_type=adapter_type,
        source_artifact_path=artifact_path,
        workspace_path=str(bundle_root),
        created_utc=ts,
    )
    population_enabled = getattr(oa, "output_adapter_population_enabled", True)
    do_populate = populate and population_enabled
    allow_xlsx = getattr(oa, "output_adapter_allow_xlsx", False)
    max_rows = getattr(oa, "output_adapter_population_max_rows", 1000)
    max_sections = getattr(oa, "output_adapter_population_max_sections", 50)
    result = create_bundle(
        adapter_type,
        request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
        source_artifact_path=artifact_path or "",
        revision_note="",
        populate=do_populate,
        allow_xlsx=allow_xlsx,
        population_max_rows=max_rows,
        population_max_sections=max_sections,
    )
    if not result:
        console.print("[red]Bundle creation failed.[/red]")
        raise typer.Exit(1)
    bundle, manifest = result
    if getattr(oa, "output_adapter_graph_persistence", True):
        graph_path = Path(
            getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
        if graph_path.exists():
            from workflow_dataset.output_adapters.graph_integration import persist_adapter_request, persist_output_bundle
            persist_adapter_request(graph_path, request)
            persist_output_bundle(graph_path, bundle, manifest)
    console.print(f"[green]Bundle created: {bundle.bundle_id}[/green]")
    console.print(f"  workspace: {bundle.workspace_path}")
    if getattr(manifest, "populated_paths", None):
        console.print(
            f"  [dim]populated: {len(manifest.populated_paths)} paths[/dim]")
    if getattr(manifest, "xlsx_created", False):
        console.print("  [dim]XLSX workbook created[/dim]")
    for p in bundle.output_paths[:12]:
        console.print(f"  [dim]{p}[/dim]")


@assist_group.command("bundle-preview")
def assist_bundle_preview(
    bundle_id: str = typer.Argument(..., help="Bundle ID (e.g. bundle_...)"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Inspect output bundle contents and manifest."""
    settings = load_settings(config)
    oa = _output_adapters_config(settings)
    if not getattr(oa, "output_adapter_preview_enabled", True):
        console.print("[yellow]Output adapter preview is disabled.[/yellow]")
        raise typer.Exit(0)
    from workflow_dataset.output_adapters import load_manifest_for_bundle
    bundle_root = Path(
        getattr(oa, "output_adapter_bundle_root", "data/local/bundles"))
    manifest = load_manifest_for_bundle(bundle_id, bundle_root)
    if not manifest:
        console.print(f"[red]Bundle or manifest not found: {bundle_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]Bundle {bundle_id}[/bold]")
    console.print(f"  adapter: {manifest.adapter_used}")
    console.print(f"  created: {manifest.created_utc}")
    populated = getattr(manifest, "populated_paths", []) or []
    scaffold = getattr(manifest, "scaffold_only_paths", []) or []
    fallback = getattr(manifest, "fallback_used", False)
    xlsx_created = getattr(manifest, "xlsx_created", False)
    if populated or scaffold or fallback is not None:
        console.print(
            f"  population: {len(populated)} populated, {len(scaffold)} scaffold-only, fallback_used={fallback}")
    if xlsx_created:
        console.print("  xlsx: workbook.xlsx created")
    console.print("  paths:")
    for p in manifest.generated_paths[:20]:
        tag = " [green](populated)[/green]" if p in populated else " [dim](scaffold)[/dim]" if p in scaffold else ""
        console.print(f"    {p}{tag}")


@assist_group.command("bundle-adopt")
def assist_bundle_adopt(
    bundle_id: str = typer.Argument(..., help="Bundle ID"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Bridge output bundle into apply flow. Does not apply immediately."""
    settings = load_settings(config)
    oa = _output_adapters_config(settings)
    from workflow_dataset.output_adapters import load_manifest_for_bundle
    from workflow_dataset.review.adoption_bridge import create_adoption_candidate, save_adoption_candidate
    bundle_root = Path(
        getattr(oa, "output_adapter_bundle_root", "data/local/bundles"))
    manifest = load_manifest_for_bundle(bundle_id, bundle_root)
    if not manifest:
        console.print(f"[red]Bundle not found: {bundle_id}[/red]")
        raise typer.Exit(1)
    workspace_path = bundle_root / bundle_id
    if not workspace_path.exists():
        console.print(
            f"[red]Bundle workspace not found: {workspace_path}[/red]")
        raise typer.Exit(1)
    candidate = create_adoption_candidate(
        generation_id=bundle_id,
        workspace_path=workspace_path,
        candidate_paths=manifest.generated_paths,
        artifact_id=bundle_id,
    )
    review_root = Path(getattr(settings.generation, "generation_workspace_root", "data/local/generation")
                       ) / "review" if getattr(settings, "generation", None) else bundle_root / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    save_adoption_candidate(candidate, review_root)
    console.print(
        f"[green]Adoption candidate created: {candidate.adoption_id}[/green]")
    console.print("  Use Apply flow to copy bundle to target path.")


@assist_group.command("list-bundles")
def assist_list_bundles(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """List output bundles by adapter/date. Also list available adapters."""
    settings = load_settings(config)
    oa = _output_adapters_config(settings)
    from workflow_dataset.output_adapters import list_adapters, list_bundles
    bundle_root = Path(
        getattr(oa, "output_adapter_bundle_root", "data/local/bundles"))
    console.print("[bold]Available adapters[/bold]")
    for meta in list_adapters():
        console.print(f"  {meta.adapter_type}: {meta.label}")
    console.print("\n[bold]Bundles[/bold]")
    show_population = getattr(oa, "output_adapter_preview_enabled", True)
    for b in list_bundles(bundle_root, limit=limit):
        pop_count = len(b.get("populated_paths") or [])
        xlsx = b.get("xlsx_created", False)
        extra = ""
        if show_population and (pop_count or xlsx):
            extra = f"  populated={pop_count}" if pop_count else ""
            if xlsx:
                extra += " xlsx=yes"
        console.print(
            f"  {b['bundle_id']}  adapter={b['adapter_used']}  {b['created_utc'][:10]}{extra}")


# ----- LLM pipeline commands -----


@llm_group.command("verify")
def llm_verify(
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    json_output: bool = typer.Option(
        False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Verify LLM pipeline: corpus, SFT, config, backend, adapters, eval outputs, demo readiness."""
    from workflow_dataset.llm.verify import verify_llm_pipeline, VerifyResult
    res = verify_llm_pipeline(llm_config)
    if json_output:
        console.print(res.to_json())
        return
    console.print("[bold]LLM pipeline verification[/bold]")
    console.print(
        f"  corpus:        {'OK' if res.corpus_present else 'MISSING'}  ({res.corpus_path})  lines={res.corpus_count}")
    console.print(
        f"  sft train:     {'OK' if res.sft_train_present else 'MISSING'}  ({res.sft_dir})  lines={res.sft_train_count}")
    console.print(
        f"  sft test:      {'OK' if res.sft_test_present else 'MISSING'}  lines={res.sft_test_count}")
    console.print(
        f"  config:        {'OK' if res.config_present else 'MISSING'}  {res.config_path}")
    console.print(
        f"  base_model:    {'OK' if res.base_model_configured else 'MISSING'}  {res.base_model or '—'}")
    console.print(f"  backend deps:  {'OK' if res.backend_deps_available else 'MISSING'}  ({res.backend})" + (
        "  [dim](pip install mlx-lm)[/dim]" if not res.backend_deps_available and res.backend == "mlx" else ""))
    console.print(
        f"  run artifacts: {res.run_dirs_count} run dir(s), adapter={'OK' if res.adapter_artifacts_present else 'MISSING'}  {res.runs_dir}")
    console.print(
        f"  adapters:      {'OK' if res.adapter_artifacts_present else 'MISSING'}  latest={res.latest_run_dir or '—'}")
    console.print(
        f"  eval outputs:  {'OK' if res.eval_outputs_present else 'MISSING'}  predictions={res.eval_predictions_path or '—'}")
    console.print(
        f"  eval mode:     {'real_model' if res.eval_uses_real_model else 'baseline/dummy'}")
    console.print(
        f"  demo adapter:  {'OK' if res.demo_can_load_adapter else '—'}  {res.demo_adapter_path or '—'}")
    console.print(
        f"  demo base:     {'OK' if res.demo_can_load_base else '—'}")
    if res.errors:
        for e in res.errors:
            console.print(f"  [red]error: {e}[/red]")


@llm_group.command("prepare-corpus")
def llm_prepare_corpus(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
) -> None:
    """Build domain-adaptation corpus from processed repo outputs. Writes data/local/llm/corpus/corpus.jsonl."""
    settings = load_settings(config)
    llm_cfg = _load_llm_config(llm_config)
    processed = Path(settings.paths.processed)
    corpus_path = llm_cfg.get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    out_path = Path(corpus_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from workflow_dataset.llm.corpus_builder import build_corpus
    total, counts = build_corpus(processed, out_path)
    console.print(f"[green]corpus written: {total} docs[/green] -> {out_path}")
    for k, v in counts.items():
        console.print(f"  {k}: {v}")
    if total > 0:
        from workflow_dataset.llm.corpus_builder import load_corpus
        preview = load_corpus(out_path, limit=1)
        if preview:
            console.print("[dim]Preview (first doc):[/dim]",
                          preview[0].title[:60] + "...")


@llm_group.command("build-sft")
def llm_build_sft(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
) -> None:
    """Build SFT train/val/test from corpus + local graph. Writes data/local/llm/sft/*.jsonl."""
    settings = load_settings(config)
    llm_cfg = _load_llm_config(llm_config)
    corpus_path = llm_cfg.get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    sft_dir = llm_cfg.get("sft_train_dir", "data/local/llm/sft")
    graph_path = getattr(settings.paths, "graph_store_path",
                         None) or "data/local/work_graph.sqlite"
    from workflow_dataset.llm.sft_builder import build_sft
    n_train, n_val, n_test, counts = build_sft(
        Path(corpus_path),
        Path(graph_path),
        Path(sft_dir),
        seed=llm_cfg.get("random_seed", 42),
    )
    console.print(
        f"[green]SFT split: train={n_train} val={n_val} test={n_test}[/green] -> {sft_dir}")
    for task_type, c in counts.items():
        console.print(f"  {task_type}: {c}")


@llm_group.command("train")
def llm_train(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
) -> None:
    """Run LoRA fine-tuning via MLX backend. Writes to data/local/llm/runs/<timestamp>."""
    from workflow_dataset.llm.run_summary import write_run_summary

    llm_cfg = _load_llm_config(llm_config)
    if not llm_cfg.get("base_model"):
        console.print("[red]base_model not set in llm config[/red]")
        raise typer.Exit(1)
    backend_name = llm_cfg.get("backend", "mlx")
    sft_dir = Path(llm_cfg.get("sft_train_dir", "data/local/llm/sft"))
    if not (sft_dir / "train.jsonl").exists():
        console.print(
            "[red]SFT train.jsonl not found; run 'llm build-sft' first[/red]")
        raise typer.Exit(1)
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    run_name = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = runs_dir / run_name
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "resolved_llm_config.yaml", "w") as f:
        yaml.dump(llm_cfg, f)
    llm_config_path = str(Path(llm_config).resolve() if Path(
        llm_config).exists() else llm_config)
    start_time = datetime.now(timezone.utc).isoformat()
    from workflow_dataset.llm.schemas import TrainingRunConfig
    from workflow_dataset.llm.train_backend import get_backend
    train_config = TrainingRunConfig(
        backend=backend_name,
        base_model=llm_cfg["base_model"],
        adapter_type=llm_cfg.get("adapter_type", "lora"),
        output_dir=str(output_dir),
        max_seq_length=llm_cfg.get("max_seq_length", 2048),
        train_batch_size=llm_cfg.get("train_batch_size", 2),
        eval_batch_size=llm_cfg.get("eval_batch_size", 4),
        grad_accumulation=llm_cfg.get("grad_accumulation", 4),
        learning_rate=llm_cfg.get("learning_rate", 1e-5),
        num_epochs=llm_cfg.get("num_epochs", 3),
        warmup_ratio=llm_cfg.get("warmup_ratio", 0.1),
        lora_rank=llm_cfg.get("lora_rank", 8),
        lora_alpha=llm_cfg.get("lora_alpha", 16),
        lora_dropout=llm_cfg.get("lora_dropout", 0.05),
        random_seed=llm_cfg.get("random_seed", 42),
        train_data_path=str(sft_dir),
        eval_data_path=str(sft_dir),
    )
    try:
        backend = get_backend(backend_name)
        adapter_path = backend.train_lora(
            train_config,
            train_data_path=sft_dir,
            eval_data_path=sft_dir,
            output_dir=output_dir,
        )
        write_run_summary(
            output_dir,
            success=True,
            backend=backend_name,
            base_model=llm_cfg["base_model"],
            llm_config_path=llm_config_path,
            adapter_path=adapter_path,
            start_time=start_time,
            run_type="full",
        )
        console.print(
            f"[green]training complete; adapter -> {adapter_path}[/green]")
    except Exception as e:
        write_run_summary(
            output_dir,
            success=False,
            backend=backend_name,
            base_model=llm_cfg["base_model"],
            llm_config_path=llm_config_path,
            error=str(e),
            start_time=start_time,
            run_type="full",
        )
        console.print(f"[red]training failed: {e}[/red]")
        raise typer.Exit(1)


@llm_group.command("smoke-train")
def llm_smoke_train(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
) -> None:
    """Run a minimal training smoke test: tiny data, 2 steps, to verify the training path produces an adapter."""
    from workflow_dataset.llm.run_summary import write_run_summary

    llm_cfg = _load_llm_config(llm_config)
    if not llm_cfg.get("base_model"):
        console.print("[red]base_model not set in llm config[/red]")
        raise typer.Exit(1)
    base_model = llm_cfg["base_model"]
    backend_name = llm_cfg.get("backend", "mlx")
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    run_name = "smoke_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = runs_dir / run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[dim]interpreter:  {sys.executable}[/dim]")
    console.print(f"[dim]base_model:   {base_model}[/dim]")
    console.print(f"[dim]output run:   {output_dir}[/dim]")

    with open(output_dir / "resolved_llm_config.yaml", "w") as f:
        yaml.dump(llm_cfg, f)

    from workflow_dataset.llm.smoke_data import write_smoke_sft
    from workflow_dataset.llm.schemas import TrainingRunConfig
    from workflow_dataset.llm.train_backend import get_backend

    smoke_sft = runs_dir.parent / "smoke_sft"
    write_smoke_sft(smoke_sft)
    console.print(f"[dim]smoke SFT data -> {smoke_sft}[/dim]")

    train_config = TrainingRunConfig(
        backend=backend_name,
        base_model=base_model,
        adapter_type=llm_cfg.get("adapter_type", "lora"),
        output_dir=str(output_dir),
        max_seq_length=min(512, llm_cfg.get("max_seq_length", 2048)),
        train_batch_size=2,
        eval_batch_size=2,
        grad_accumulation=1,
        learning_rate=llm_cfg.get("learning_rate", 1e-5),
        num_epochs=1,
        warmup_ratio=0.0,
        lora_rank=4,
        lora_alpha=8,
        lora_dropout=0.05,
        random_seed=llm_cfg.get("random_seed", 42),
        train_data_path=str(smoke_sft),
        eval_data_path=str(smoke_sft),
        max_iters=2,
    )
    start_time = datetime.now(timezone.utc).isoformat()
    llm_config_path = str(Path(llm_config).resolve() if Path(
        llm_config).exists() else llm_config)
    try:
        backend = get_backend(backend_name)
        adapter_path = backend.train_lora(
            train_config,
            train_data_path=smoke_sft,
            eval_data_path=smoke_sft,
            output_dir=output_dir,
        )
        adapter_created = adapter_path.exists() and any(adapter_path.iterdir())
        write_run_summary(
            output_dir,
            success=True,
            backend=backend_name,
            base_model=base_model,
            llm_config_path=llm_config_path,
            adapter_path=adapter_path,
            start_time=start_time,
            run_type="smoke",
        )
        console.print(
            f"[green]smoke-train complete; adapter -> {adapter_path}[/green]")
        console.print(
            f"[dim]adapter artifacts: {'created' if adapter_created else 'missing'}[/dim]")
    except Exception as e:
        write_run_summary(
            output_dir,
            success=False,
            backend=backend_name,
            base_model=base_model,
            llm_config_path=llm_config_path,
            error=str(e),
            start_time=start_time,
            run_type="smoke",
        )
        console.print(f"[red]smoke-train failed: {e}[/red]")
        raise typer.Exit(1)


@llm_group.command("eval")
def llm_eval(
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    test_path: str = typer.Option("", "--test-path"),
    run_dir: str = typer.Option("", "--run-dir"),
    model: str = typer.Option(
        "", "--model", "-m", help="Path to base model for real inference (default: baseline)"),
    adapter: str = typer.Option(
        "", "--adapter", "-a", help="Path to trained adapter for real inference"),
    retrieval: bool = typer.Option(
        False, "--retrieval", "-r", help="Prepend retrieved corpus context to each prompt (real inference only)"),
    retrieval_top_k: int = typer.Option(
        5, "--retrieval-top-k", help="Number of docs to retrieve when --retrieval is set"),
) -> None:
    """Evaluate on test split. Default: baseline (reference-as-prediction). Use --model or --adapter for real inference, or omit both to use latest successful adapter. Use --retrieval to ground prompts with corpus context."""
    llm_cfg = _load_llm_config(llm_config)
    sft_dir = Path(llm_cfg.get("sft_train_dir", "data/local/llm/sft"))
    test_file = Path(test_path or str(sft_dir / "test.jsonl"))
    if not test_file.exists():
        console.print(
            "[yellow]test.jsonl not found; run 'llm build-sft' first[/yellow]")
        raise typer.Exit(0)
    from workflow_dataset.llm.eval import run_eval, _messages_to_prompt
    from workflow_dataset.llm.run_summary import find_latest_successful_adapter
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    run_dir_path = Path(run_dir) if run_dir else (runs_dir / "eval_out")
    if retrieval:
        run_dir_path = run_dir_path / "retrieval"
    run_dir_path.mkdir(parents=True, exist_ok=True)

    use_real = bool(model or adapter)
    model_path = model or adapter
    if not use_real:
        adapter_path_auto, _ = find_latest_successful_adapter(runs_dir)
        if adapter_path_auto:
            use_real = True
            model_path = adapter_path_auto
            console.print(
                f"[dim]Using latest successful adapter: {model_path}[/dim]")
    if use_real and not model_path:
        console.print(
            "[red]Provide --model or --adapter path for real inference[/red]")
        raise typer.Exit(1)
    if retrieval and not use_real:
        console.print(
            "[yellow]--retrieval has no effect for baseline (no model); ignoring.[/yellow]")

    if use_real:
        backend_name = llm_cfg.get("backend", "mlx")
        from workflow_dataset.llm.train_backend import get_backend
        backend = get_backend(backend_name)
        max_tokens = int(llm_cfg.get("max_seq_length", 2048) // 4)
        use_adapter = bool(adapter) or (not model)
        base_model = llm_cfg.get("base_model", "")
        if use_adapter and not base_model:
            console.print(
                "[red]base_model required in config for adapter inference[/red]")
            raise typer.Exit(1)
        corpus_path = llm_cfg.get(
            "corpus_path", "data/local/llm/corpus/corpus.jsonl")
        top_k = retrieval_top_k or int(llm_cfg.get("retrieval_top_k", 5))

        def real_predict(ex: dict) -> str:
            prompt = _messages_to_prompt(ex.get("messages", []))
            if not prompt:
                return ""
            if retrieval and Path(corpus_path).exists():
                from workflow_dataset.llm.retrieval_context import retrieve, format_context_for_prompt
                docs = retrieve(corpus_path, prompt, top_k=top_k)
                ctx = format_context_for_prompt(docs, max_chars=2000)
                if ctx:
                    prompt = "Context (retrieved):\n" + \
                        ctx + "\n\nUser: " + prompt
            if use_adapter and base_model:
                return backend.run_inference(base_model, prompt, max_tokens=max_tokens, adapter_path=model_path)
            return backend.run_inference(model_path, prompt, max_tokens=max_tokens)

        predict_fn = real_predict
        run_id = "real_model_retrieval" if retrieval else "real_model"
        model_id = str(model_path)
        prediction_mode = "real_model"
    else:
        def dummy_predict(ex: dict) -> str:
            msgs = ex.get("messages", [])
            for m in reversed(msgs):
                if m.get("role") == "assistant":
                    return m.get("content", "")
            return ""
        predict_fn = dummy_predict
        run_id = "baseline_from_ref"
        model_id = "n/a"
        prediction_mode = "baseline"

    result = run_eval(
        test_file,
        predict_fn,
        run_dir_path,
        run_id=run_id,
        model_id=model_id,
        retrieval_used=retrieval and use_real,
        prediction_mode=prediction_mode,
    )
    if use_real:
        console.print(f"[dim]model/adapter: {model_path}[/dim]")
    if retrieval and use_real:
        console.print("[dim]retrieval: on[/dim]")
    console.print(
        f"[green]eval done: {result.num_examples} examples  mode={result.prediction_mode}[/green] -> {result.predictions_path}")
    for k, v in result.metrics.items():
        console.print(f"  {k}: {v:.4f}")


@llm_group.command("compare-runs")
def llm_compare_runs(
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    test_path: str = typer.Option("", "--test-path"),
    output_dir: str = typer.Option("", "--output-dir"),
    retrieval_top_k: int = typer.Option(5, "--retrieval-top-k"),
    skip_missing: bool = typer.Option(
        True, "--skip-missing/--no-skip-missing"),
) -> None:
    """Compare baseline, smoke adapter, and full adapter with retrieval off/on. Writes comparison_latest.json and comparison_latest.md to runs_dir."""
    llm_cfg = _load_llm_config(llm_config)
    sft_dir = Path(llm_cfg.get("sft_train_dir", "data/local/llm/sft"))
    test_file = Path(test_path or str(sft_dir / "test.jsonl"))
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    out_dir = Path(output_dir) if output_dir else None
    if not test_file.exists():
        console.print(
            "[yellow]test.jsonl not found; run 'llm build-sft' first[/yellow]")
        raise typer.Exit(0)
    from workflow_dataset.llm.compare_runs import run_comparison
    payload = run_comparison(
        llm_cfg,
        test_file,
        runs_dir,
        output_dir=out_dir,
        corpus_path=llm_cfg.get(
            "corpus_path", "data/local/llm/corpus/corpus.jsonl"),
        retrieval_top_k=retrieval_top_k,
        skip_missing=skip_missing,
    )
    if payload.get("error"):
        console.print(f"[red]{payload['error']}[/red]")
        raise typer.Exit(1)
    console.print(
        f"[green]comparison done -> {payload.get('report_path', '')}[/green]")
    for s in payload.get("slices", []):
        if s.get("skipped"):
            console.print(f"  [dim]{s['slice_id']}: skipped[/dim]")
        else:
            m = s.get("metrics") or {}
            console.print(
                f"  {s['slice_id']}: token_overlap={m.get('token_overlap', 0):.4f}")


def _find_latest_adapter(runs_dir: Path) -> str:
    """Return path to adapters dir of most recent successful run, or ''."""
    from workflow_dataset.llm.run_summary import find_latest_successful_adapter
    adapter_path, _ = find_latest_successful_adapter(runs_dir)
    return adapter_path


@llm_group.command("demo")
def llm_demo(
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    prompt: str = typer.Option("", "--prompt", "-p"),
    retrieve: int = typer.Option(
        0, "--retrieve", "-r", help="Top-k corpus docs to retrieve and show as context"),
    adapter: str = typer.Option(
        "", "--adapter", "-a", help="Path to trained adapter (default: use latest run if present)"),
) -> None:
    """Single-prompt demo. Uses trained adapter if available, else base model. Optionally retrieve corpus context."""
    llm_cfg = _load_llm_config(llm_config)
    corpus_path = llm_cfg.get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    if retrieve > 0 and Path(corpus_path).exists():
        from workflow_dataset.llm.retrieval_context import retrieve as do_retrieve, format_context_for_prompt
        docs = do_retrieve(
            corpus_path, prompt or "workflow occupation", top_k=retrieve)
        ctx = format_context_for_prompt(docs, max_chars=1500)
        console.print("[bold]Retrieved context:[/bold]")
        console.print(ctx[:800] + ("..." if len(ctx) > 800 else ""))
    if prompt:
        adapter_path_val = adapter
        if not adapter_path_val:
            runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
            adapter_path_val = _find_latest_adapter(runs_dir)
        base_model = llm_cfg.get("base_model", "")
        mode = "adapter" if adapter_path_val else "base_model"
        if not adapter_path_val and not base_model:
            console.print(
                "[red]No adapter and no base_model. Run 'llm smoke-train' or set base_model in config.[/red]")
            raise typer.Exit(1)
        if mode == "adapter" and not base_model:
            console.print(
                "[red]base_model required in config for adapter inference.[/red]")
            raise typer.Exit(1)

        console.print(f"[dim]interpreter: {sys.executable}[/dim]")
        console.print(f"[dim]mode: {mode}[/dim]")
        console.print(f"[dim]base model: {base_model or '(none)'}[/dim]")
        console.print(f"[dim]adapter: {adapter_path_val or '(none)'}[/dim]")

        try:
            from workflow_dataset.llm.train_backend import get_backend
            backend = get_backend(llm_cfg.get("backend", "mlx"))
            if mode == "adapter":
                out = backend.run_inference(
                    base_model, prompt, max_tokens=150, adapter_path=adapter_path_val)
            else:
                out = backend.run_inference(base_model, prompt, max_tokens=150)
            if out.startswith("[inference error:"):
                msg = out.replace("[inference error: ", "").rstrip("]")
                if len(msg) > 400:
                    msg = msg[:397] + "..."
                console.print("[red]Inference failed.[/red]")
                console.print(f"[yellow]{msg}[/yellow]")
            else:
                console.print("[bold]Model output:[/bold]")
                console.print(out or "[no output]")
        except Exception as e:
            console.print("[red]Inference failed.[/red]")
            console.print(f"[yellow]{e}[/yellow]")
    else:
        console.print(
            "Use --prompt 'your question' to run a single prompt. Use --retrieve 3 for context, --adapter <path> to force adapter.")


DEMO_SUITE_PROMPTS = [
    "Summarize this user's workflow style.",
    "What recurring work patterns are visible?",
    "How would this user likely structure a new reporting project?",
    "What spreadsheet habits appear recurrent?",
    "How should a creative deliverable be scaffolded in this user's style?",
    "What should require explicit approval before execution?",
]


@llm_group.command("demo-suite")
def llm_demo_suite(
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    baseline: bool = typer.Option(
        False, "--baseline", help="Run with base model only (no adapter)"),
    retrieval: bool = typer.Option(
        False, "--retrieval", "-r", help="Prepend retrieved context to each prompt"),
    retrieval_top_k: int = typer.Option(3, "--retrieval-top-k"),
    adapter: str = typer.Option(
        "", "--adapter", "-a", help="Use this adapter; default: latest successful"),
) -> None:
    """Run a small set of personalization prompts for qualitative comparison (baseline vs adapter, retrieval on/off)."""
    llm_cfg = _load_llm_config(llm_config)
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    corpus_path = llm_cfg.get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    base_model = llm_cfg.get("base_model", "")
    if not base_model:
        console.print("[red]base_model required in config[/red]")
        raise typer.Exit(1)
    adapter_path = adapter
    if not baseline and not adapter_path:
        from workflow_dataset.llm.run_summary import find_latest_successful_adapter
        adapter_path, _ = find_latest_successful_adapter(runs_dir)
    if not baseline and not adapter_path:
        console.print(
            "[yellow]No adapter found; run with --baseline or run 'llm smoke-train' first[/yellow]")
    from workflow_dataset.llm.train_backend import get_backend
    backend = get_backend(llm_cfg.get("backend", "mlx"))
    mode = "baseline" if baseline else "adapter"
    console.print(
        f"[bold]Demo suite — mode={mode} retrieval={retrieval}[/bold]")
    if not baseline:
        console.print(f"[dim]adapter: {adapter_path}[/dim]")
    for i, prompt in enumerate(DEMO_SUITE_PROMPTS, 1):
        console.print(f"\n[bold]{i}. {prompt}[/bold]")
        user_prompt = prompt
        if retrieval and Path(corpus_path).exists():
            from workflow_dataset.llm.retrieval_context import retrieve as do_retrieve, format_context_for_prompt
            docs = do_retrieve(corpus_path, prompt, top_k=retrieval_top_k)
            ctx = format_context_for_prompt(docs, max_chars=1500)
            if ctx:
                user_prompt = "Context (retrieved):\n" + \
                    ctx + "\n\nUser: " + prompt
        try:
            if baseline:
                out = backend.run_inference(
                    base_model, user_prompt, max_tokens=200)
            else:
                out = backend.run_inference(
                    base_model, user_prompt, max_tokens=200, adapter_path=adapter_path)
            if out and out.startswith("[inference error:"):
                console.print(f"[red]{out[:200]}[/red]")
            else:
                console.print(
                    out[:500] + ("..." if len(out or "") > 500 else "") or "[no output]")
        except Exception as e:
            console.print(f"[red]{e}[/red]")
    console.print("\n[dim]Done.[/dim]")


@llm_group.command("latest-run")
def llm_latest_run(
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
) -> None:
    """Print the path to the latest successful training run dir, or exit nonzero if none."""
    from workflow_dataset.llm.run_summary import find_latest_successful_adapter
    llm_cfg = _load_llm_config(llm_config)
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    _, run_dir = find_latest_successful_adapter(runs_dir)
    if not run_dir:
        console.print(
            "[red]No successful run found. Run 'llm smoke-train' first.[/red]")
        raise typer.Exit(1)
    console.print(run_dir)


@llm_group.command("latest-adapter")
def llm_latest_adapter(
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
) -> None:
    """Print the path to the latest successful adapter dir, or exit nonzero if none."""
    from workflow_dataset.llm.run_summary import find_latest_successful_adapter
    llm_cfg = _load_llm_config(llm_config)
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    adapter_path, _ = find_latest_successful_adapter(runs_dir)
    if not adapter_path:
        console.print(
            "[red]No successful adapter found. Run 'llm smoke-train' first.[/red]")
        raise typer.Exit(1)
    console.print(adapter_path)


def _trials_ensure_registered() -> None:
    from workflow_dataset.trials.trial_registry import list_trials
    if not list_trials():
        from workflow_dataset.trials.trial_scenarios import register_all_trials
        register_all_trials()


def _trials_build_context(config: str, session_id: str = "", project_id: str = "") -> dict:
    from workflow_dataset.agent_loop.context_builder import build_context_bundle
    settings = load_settings(config)
    setup = getattr(settings, "setup", None)
    paths = getattr(settings, "paths", None)
    graph_path = Path(getattr(paths, "graph_store_path",
                      "data/local/work_graph.sqlite"))
    style_signals_dir = getattr(
        setup, "style_signals_dir", "data/local/setup/style_signals") if setup else "data/local/setup/style_signals"
    parsed_dir = getattr(setup, "parsed_artifacts_dir",
                         "data/local/setup/parsed") if setup else "data/local/setup/parsed"
    style_profiles_dir = getattr(
        setup, "style_profiles_dir", "data/local/setup/style_profiles") if setup else "data/local/setup/style_profiles"
    suggestions_dir = getattr(
        setup, "suggestions_dir", "data/local/suggestions") if setup else "data/local/suggestions"
    draft_structures_dir = getattr(
        setup, "draft_structures_dir", "data/local/drafts") if setup else "data/local/drafts"
    sid = session_id or (setup and getattr(
        setup, "setup_dir", "") and _resolve_latest_session_id(setup)) or ""
    return build_context_bundle(
        graph_path,
        style_signals_dir,
        parsed_dir,
        style_profiles_dir,
        suggestions_dir,
        draft_structures_dir,
        setup_session_id=sid,
        project_id=project_id,
    )


@trials_group.command("list")
def trials_list(
    domain: str = typer.Option(
        "", "--domain", help="Filter by domain: ops, spreadsheet, founder, creative"),
) -> None:
    """List available workflow trials."""
    _trials_ensure_registered()
    from workflow_dataset.trials.trial_registry import list_trials
    trials = list_trials(domain=domain or None)
    for t in trials:
        console.print(
            f"  [bold]{t.trial_id}[/bold]  {t.domain}  {t.workflow_type}  — {t.task_goal[:60]}...")


@trials_group.command("run")
def trials_run(
    trial_id: str = typer.Argument(...,
                                   help="Trial id (e.g. ops_summarize_reporting)"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    mode: str = typer.Option("adapter", "--mode", "-m",
                             help="baseline | adapter | retrieval_only | adapter_retrieval"),
    output_dir: str = typer.Option("data/local/trials", "--output-dir"),
) -> None:
    """Run a single workflow trial."""
    _trials_ensure_registered()
    from workflow_dataset.trials.trial_registry import get_trial
    from workflow_dataset.trials.trial_runner import run_trial
    from workflow_dataset.trials.trial_models import TrialMode
    t = get_trial(trial_id)
    if not t:
        console.print(f"[red]Unknown trial: {trial_id}[/red]")
        raise typer.Exit(1)
    try:
        mode_enum = TrialMode(mode)
    except ValueError:
        console.print(
            f"[red]Invalid mode: {mode}. Use baseline, adapter, retrieval_only, adapter_retrieval[/red]")
        raise typer.Exit(1)
    context = _trials_build_context(config)
    llm_cfg = _load_llm_config(
        llm_config) if mode_enum != TrialMode.BASELINE else None
    adapter_path = None
    if mode_enum in (TrialMode.ADAPTER, TrialMode.ADAPTER_RETRIEVAL):
        from workflow_dataset.llm.run_summary import find_latest_successful_adapter
        runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs")
                        ) if llm_cfg else Path("data/local/llm/runs")
        adapter_path, _ = find_latest_successful_adapter(runs_dir)
    corpus_path = (llm_cfg or {}).get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    result = run_trial(
        t, mode_enum,
        context_bundle=context,
        llm_config=llm_cfg,
        adapter_path=adapter_path,
        corpus_path=corpus_path,
        output_dir=Path(output_dir),
    )
    console.print(
        f"[green]Result: {result.result_id}[/green]  completion={result.completion_status}")
    console.print(
        f"  task_completion={result.task_completion_score:.2f}  style_match={result.style_match_score:.2f}")


@trials_group.command("run-suite")
def trials_run_suite(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    domain: str = typer.Option("", "--domain"),
    modes: str = typer.Option("baseline,adapter,adapter_retrieval", "--modes"),
    output_dir: str = typer.Option("data/local/trials", "--output-dir"),
) -> None:
    """Run a curated set of trials across selected modes."""
    _trials_ensure_registered()
    from workflow_dataset.trials.trial_registry import list_trials
    from workflow_dataset.trials.trial_runner import run_trial_suite
    from workflow_dataset.trials.trial_models import TrialMode
    trial_list = list_trials(domain=domain or None)
    if not trial_list:
        console.print("[yellow]No trials registered.[/yellow]")
        raise typer.Exit(0)
    mode_list = [TrialMode(m.strip()) for m in modes.split(",") if m.strip()]
    context = _trials_build_context(config)
    llm_cfg = _load_llm_config(llm_config)
    adapter_path = None
    from workflow_dataset.llm.run_summary import find_latest_successful_adapter
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    adapter_path, _ = find_latest_successful_adapter(runs_dir)
    corpus_path = llm_cfg.get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    results = run_trial_suite(
        trial_list, mode_list,
        context_bundle=context,
        llm_config=llm_cfg,
        adapter_path=adapter_path,
        corpus_path=corpus_path,
        output_dir=Path(output_dir),
    )
    console.print(
        f"[green]Run {len(results)} trial results -> {output_dir}[/green]")


@trials_group.command("compare")
def trials_compare(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    llm_config: str = typer.Option(
        "configs/llm_training.yaml", "--llm-config"),
    trial_id: str = typer.Option("", "--trial-id"),
    output_dir: str = typer.Option("data/local/trials", "--output-dir"),
) -> None:
    """Compare baseline vs adapter vs retrieval modes for one or all trials."""
    _trials_ensure_registered()
    from workflow_dataset.trials.trial_registry import list_trials, get_trial
    from workflow_dataset.trials.trial_runner import run_trial_suite
    from workflow_dataset.trials.trial_models import TrialMode
    trials = [get_trial(trial_id)] if trial_id else list_trials()
    trials = [t for t in trials if t]
    if not trials:
        console.print("[yellow]No trials to run.[/yellow]")
        raise typer.Exit(0)
    context = _trials_build_context(config)
    llm_cfg = _load_llm_config(llm_config)
    from workflow_dataset.llm.run_summary import find_latest_successful_adapter
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    adapter_path, _ = find_latest_successful_adapter(runs_dir)
    corpus_path = llm_cfg.get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    modes = [TrialMode.BASELINE, TrialMode.ADAPTER,
             TrialMode.RETRIEVAL_ONLY, TrialMode.ADAPTER_RETRIEVAL]
    results = run_trial_suite(
        trials, modes,
        context_bundle=context,
        llm_config=llm_cfg,
        adapter_path=adapter_path,
        corpus_path=corpus_path,
        output_dir=Path(output_dir),
    )
    console.print(f"[green]Compared {len(results)} results[/green]")


@trials_group.command("report")
def trials_report(
    output_dir: str = typer.Option("data/local/trials", "--output-dir"),
    report_path: str = typer.Option(
        "data/local/trials/latest_trial_report.md", "--report-path"),
) -> None:
    """Generate a readable workflow-trial report from persisted results."""
    from workflow_dataset.trials.trial_report import load_trial_results, write_trial_report
    results = load_trial_results(Path(output_dir))
    if not results:
        console.print(
            "[yellow]No trial results found. Run 'trials run-suite' or 'trials compare' first.[/yellow]")
        raise typer.Exit(0)
    path = write_trial_report(results, report_path)
    console.print(f"[green]Report written: {path}[/green]")


# ----- M19 Friendly user trial -----
trial_group = typer.Typer(
    help="Friendly user trial: start session, list tasks, record feedback, summary, aggregate.")
app.add_typer(trial_group, name="trial")


def _trial_store() -> Path:
    return Path("data/local/trials")


@trial_group.command("start")
def trial_start(
    user_alias: str = typer.Option(
        "", "--user", "-u", help="Optional user alias"),
    task_id: str = typer.Option("", "--task", help="Optional first task id"),
    store: str = typer.Option("data/local/trials", "--store"),
) -> None:
    """Initialize a trial session. Optionally choose a first task."""
    from workflow_dataset.feedback.session_store import set_current_session, get_current_session
    from workflow_dataset.feedback.trial_events import record_trial_event
    store_path = Path(store)
    store_path.mkdir(parents=True, exist_ok=True)
    sess = set_current_session(user_alias=user_alias, store_path=store_path)
    record_trial_event("trial_session_started", {
                       "user_alias": user_alias}, store_path=store_path)
    console.print(
        f"[green]Trial session started: {sess['session_id']}[/green]")
    if user_alias:
        console.print(f"  user_alias: {user_alias}")
    if task_id:
        console.print(f"  suggested first task: {task_id}")
    console.print(
        "[dim]Run 'workflow-dataset trial tasks' to list tasks.[/dim]")


@trial_group.command("tasks")
def trial_tasks(
    store: str = typer.Option("data/local/trials", "--store"),
    priority: str = typer.Option(
        "", "--priority", help="Filter: must_try | nice_to_try | boundary"),
) -> None:
    """List available friendly trial tasks."""
    from workflow_dataset.feedback.friendly_tasks import load_friendly_trial_tasks
    tasks_path = Path(store) / "friendly_trial_tasks.json"
    tasks = load_friendly_trial_tasks(tasks_path)
    if not tasks:
        console.print(
            "[yellow]No tasks found. Ensure data/local/trials/friendly_trial_tasks.json exists.[/yellow]")
        raise typer.Exit(0)
    if priority:
        tasks = [t for t in tasks if t.get("priority") == priority]
    for t in tasks:
        pid = t.get("priority", "")
        console.print(
            f"  [bold]{t.get('task_id', '')}[/bold]  [{pid}]  {t.get('short_description', '')[:60]}...")


@trial_group.command("record-feedback")
def trial_record_feedback(
    task_id: str = typer.Argument(...,
                                  help="Task id (e.g. ops_summarize_reporting)"),
    outcome: str = typer.Option(
        "", "--outcome", help="completed | partial | failed"),
    usefulness: int = typer.Option(0, "--usefulness", "-u", min=0, max=5),
    trust: int = typer.Option(0, "--trust", "-t", min=0, max=5),
    style_match: int = typer.Option(0, "--style", "-s", min=0, max=5),
    confusion: str = typer.Option("", "--confusion"),
    failure: str = typer.Option("", "--failure"),
    freeform: str = typer.Option("", "--freeform", "-f"),
    store: str = typer.Option("data/local/trials", "--store"),
) -> None:
    """Record structured feedback for a task/session."""
    from workflow_dataset.feedback.session_store import get_current_session
    from workflow_dataset.feedback.feedback_models import TrialFeedbackEntry
    from workflow_dataset.feedback.feedback_store import save_feedback_entry
    from workflow_dataset.feedback.trial_events import record_trial_event
    from datetime import datetime, timezone
    store_path = Path(store)
    sess = get_current_session(store_path)
    session_id = sess.get("session_id", "")
    user_alias = sess.get("user_alias", "")
    entry = TrialFeedbackEntry(
        user_id_or_alias=user_alias,
        session_id=session_id,
        task_id=task_id,
        workflow_type=task_id.split("_")[0] if "_" in task_id else "",
        outcome_rating=outcome or "partial",
        usefulness_rating=usefulness,
        trust_rating=trust,
        style_match_rating=style_match,
        confusion_points=confusion,
        failure_points=failure,
        freeform_feedback=freeform,
        created_utc=datetime.now(timezone.utc).isoformat(),
    )
    path = save_feedback_entry(entry, store_path)
    record_trial_event("feedback_recorded", {
                       "task_id": task_id, "outcome": outcome or "partial"}, store_path=store_path)
    console.print(f"[green]Feedback saved: {path.name}[/green]")


@trial_group.command("summary")
def trial_summary(
    store: str = typer.Option("data/local/trials", "--store"),
) -> None:
    """Produce a trial session summary for the current session."""
    from workflow_dataset.feedback.session_store import get_current_session
    from workflow_dataset.feedback.feedback_store import load_feedback_entries, save_session_summary
    from workflow_dataset.feedback.feedback_models import TrialSessionSummary
    from workflow_dataset.feedback.feedback_summary import aggregate_feedback
    from datetime import datetime, timezone
    store_path = Path(store)
    sess = get_current_session(store_path)
    session_id = sess.get("session_id", "")
    if not session_id:
        console.print(
            "[yellow]No active session. Run 'workflow-dataset trial start' first.[/yellow]")
        raise typer.Exit(1)
    entries = [e for e in load_feedback_entries(
        store_path) if e.session_id == session_id]
    completed = sum(1 for e in entries if (
        e.outcome_rating or "").lower() == "completed")
    confusion = [e.confusion_points for e in entries if e.confusion_points]
    failure = [e.failure_points for e in entries if e.failure_points]
    freeform = [e.freeform_feedback for e in entries if e.freeform_feedback]
    summary = TrialSessionSummary(
        user_id_or_alias=sess.get("user_alias", ""),
        session_id=session_id,
        tasks_attempted=len(entries),
        tasks_completed=completed,
        top_praise_points="; ".join(freeform[:3]) if freeform else "",
        top_failure_points="; ".join(failure[:3]) if failure else "",
        top_requested_features="",
        created_utc=datetime.now(timezone.utc).isoformat(),
    )
    path = save_session_summary(summary, store_path)
    console.print(f"[green]Session summary: {path.name}[/green]")
    console.print(
        f"  tasks_attempted={summary.tasks_attempted}  tasks_completed={summary.tasks_completed}")
    if confusion:
        console.print("  confusion (sample):", confusion[0][:100])


@trial_group.command("aggregate-feedback")
def trial_aggregate_feedback(
    store: str = typer.Option("data/local/trials", "--store"),
    report_path: str = typer.Option(
        "data/local/trials/latest_feedback_report.md", "--report"),
) -> None:
    """Summarize feedback across trial sessions and write report."""
    from workflow_dataset.feedback.feedback_summary import write_feedback_report
    store_path = Path(store)
    path = write_feedback_report(
        output_path=report_path, store_path=store_path)
    console.print(f"[green]Feedback report: {path}[/green]")


# ----- M18 First narrow release -----
release_group = typer.Typer(
    help="First narrow release: ops reporting assistant. Verify, demo, run, package, report.")
app.add_typer(release_group, name="release")


def _load_release_config(release_config_path: str = "configs/release_narrow.yaml") -> dict:
    """Load release preset; return release dict or empty."""
    path = Path(release_config_path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("release", {})


@release_group.command("verify")
def release_verify(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
    llm_config: str = typer.Option(
        "", "--llm-config", help="LLM config path (e.g. configs/llm_training_full.yaml); resolved from project root if relative."),
) -> None:
    """Verify release readiness: setup, graph, LLM adapter, trials. Uses release preset if present."""
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    rel = _load_release_config(release_config)
    llm_path = llm_config or rel.get(
        "default_llm_config", "configs/llm_training_full.yaml")
    if llm_path:
        r_llm = _resolve_path(llm_path)
        if r_llm is not None:
            llm_path = str(r_llm)
    settings = load_settings(config)
    setup = getattr(settings, "setup", None)
    paths = getattr(settings, "paths", None)
    graph_path = Path(getattr(paths, "graph_store_path",
                      "data/local/work_graph.sqlite"))
    console.print(
        f"[bold]Release scope:[/bold] {rel.get('scope_label', 'Operations reporting assistant')}")
    ok = True
    if not graph_path.exists():
        console.print(
            "[yellow]Graph not found (run setup init + setup run).[/yellow]")
        ok = False
    else:
        console.print("[green]Graph: OK[/green]")
    if setup:
        for name, dir_key in [("Setup dir", "setup_dir"), ("Parsed artifacts", "parsed_artifacts_dir"), ("Style signals", "style_signals_dir")]:
            p = Path(getattr(setup, dir_key, ""))
            if p and p.exists():
                console.print(f"  [green]{name}: OK[/green]")
            else:
                console.print(f"  [yellow]{name}: missing or empty[/yellow]")
    else:
        console.print("[yellow]Setup config missing.[/yellow]")
        ok = False
    from workflow_dataset.llm.verify import verify_llm_pipeline
    llm_cfg = _load_llm_config(llm_path) if Path(llm_path).exists() else {}
    if llm_cfg:
        res = verify_llm_pipeline(llm_path)
        if res.demo_can_load_adapter:
            console.print("[green]LLM adapter: OK[/green]")
        else:
            console.print(
                "[yellow]LLM adapter: missing (demo will use baseline)[/yellow]")
    else:
        console.print("[yellow]LLM config not found.[/yellow]")
    _trials_ensure_registered()
    from workflow_dataset.trials.trial_registry import list_trials
    trials = list_trials(domain=rel.get("trial_domain", "ops"))
    console.print(f"  [green]Trials (ops): {len(trials)}[/green]")
    if not ok:
        console.print("[dim]Run setup and LLM train for full demo.[/dim]")
        console.print(
            "[red]Blocking: release not ready. Fix the issues above and re-run verify.[/red]")
        raise typer.Exit(1)


@release_group.command("run")
def release_run(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
    llm_config: str = typer.Option(
        "", "--llm-config", help="LLM config path (e.g. configs/llm_training_full.yaml); resolved from project root if relative."),
    role: str = typer.Option(
        "", "--role", "-r", help="Role for pack-driven resolution (e.g. ops). Uses active pack role if set."),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Run narrow-release flow: suggest + ops trials in adapter mode. Pack-aware: use --role ops when ops_reporting_pack is installed."""
    from workflow_dataset.feedback.trial_events import record_trial_event
    from workflow_dataset.packs import resolve_active_capabilities
    from workflow_dataset.packs.pack_state import get_active_role
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    rel = _load_release_config(release_config)
    store_path = Path(rel.get("trials_output_dir", "data/local/trials"))
    record_trial_event("release_command_used", {
                       "command": "release run"}, store_path=store_path)
    llm_path = llm_config or rel.get(
        "default_llm_config", "configs/llm_training_full.yaml")
    if llm_path:
        r_llm = _resolve_path(llm_path)
        if r_llm is not None:
            llm_path = str(r_llm)
    _trials_ensure_registered()
    from workflow_dataset.trials.trial_registry import get_trial
    from workflow_dataset.trials.trial_runner import run_trial
    from workflow_dataset.trials.trial_models import TrialMode
    # Pack-driven: resolve by role (CLI or active_role); use pack templates as trial_ids when pack active
    resolved_role = role or get_active_role(packs_dir)
    trial_ids = rel.get("trial_ids", [
                        "ops_summarize_reporting", "ops_scaffold_status", "ops_next_steps"])
    retrieval_top_k = 5
    active_pack_ids: list[str] = []
    if resolved_role:
        cap = resolve_active_capabilities(
            role=resolved_role, packs_dir=packs_dir)
        if cap.active_packs and cap.templates:
            trial_ids = cap.templates
            retrieval_top_k = cap.retrieval_profile.get("top_k", 5) or 5
            active_pack_ids = [m.pack_id for m in cap.active_packs]
    if active_pack_ids:
        console.print(
            f"[dim]Active pack(s): {', '.join(active_pack_ids)}[/dim]")
    context = _trials_build_context(config)
    llm_cfg = _load_llm_config(llm_path) if Path(llm_path).exists() else {}
    adapter_path = None
    if llm_cfg:
        from workflow_dataset.llm.run_summary import find_latest_successful_adapter
        runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
        adapter_path, _ = find_latest_successful_adapter(runs_dir)
    corpus_path = (llm_cfg or {}).get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    output_dir = Path(rel.get("trials_output_dir", "data/local/trials"))
    mode = TrialMode(rel.get("default_model_mode", "adapter"))
    if not adapter_path and mode != TrialMode.BASELINE:
        console.print(
            "[yellow]Degraded mode: no adapter found; running with base model. Run LLM train for adapter.[/yellow]")
    for tid in trial_ids:
        record_trial_event("task_selected", {
                           "task_id": tid}, store_path=store_path)
        t = get_trial(tid)
        if not t:
            continue
        result = run_trial(t, mode, context_bundle=context, llm_config=llm_cfg, adapter_path=adapter_path,
                           corpus_path=corpus_path, retrieval_top_k=retrieval_top_k, output_dir=output_dir)
        record_trial_event("generation_succeeded" if result.completion_status == "completed" else "generation_partial", {
                           "task_id": tid, "completion_status": result.completion_status}, store_path=store_path)
        console.print(
            f"  [green]{tid}[/green] -> {result.completion_status}  task={result.task_completion_score:.2f}")
    console.print(f"[green]Release run done. Results in {output_dir}[/green]")


@release_group.command("demo")
def release_demo(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
    llm_config: str = typer.Option(
        "",
        "--llm-config",
        help="LLM config path (e.g. configs/llm_training_full.yaml or configs/llm_training.yaml). Required for demo; resolved from project root if relative.",
    ),
    retrieval: bool = typer.Option(False, "--retrieval"),
) -> None:
    """Founder demo: run demo-suite with release preset. Requires LLM config with base_model. See docs/FOUNDER_DEMO_FLOW.md."""
    from workflow_dataset.feedback.trial_events import record_trial_event
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    rel = _load_release_config(release_config)
    store_path = Path(rel.get("trials_output_dir", "data/local/trials"))
    record_trial_event("release_command_used", {
                       "command": "release demo"}, store_path=store_path)
    record_trial_event("task_selected", {
                       "task_id": "release_demo"}, store_path=store_path)
    llm_path = llm_config or rel.get(
        "default_llm_config", "configs/llm_training_full.yaml")
    if llm_path:
        r_llm = _resolve_path(llm_path)
        if r_llm is not None:
            llm_path = str(r_llm)
    from workflow_dataset.llm.train_backend import get_backend
    llm_cfg = _load_llm_config(llm_path) if Path(llm_path).exists() else {}
    use_retrieval = retrieval or rel.get("use_retrieval_by_default", False)
    corpus_path = (llm_cfg or {}).get(
        "corpus_path", "data/local/llm/corpus/corpus.jsonl")
    corpus_exists = corpus_path and Path(corpus_path).exists()
    grounded = use_retrieval and corpus_exists
    console.print("[bold]Founder demo — Operations reporting assistant[/bold]")
    if grounded:
        console.print("[green][Grounded: retrieval context used][/green]")
    else:
        console.print(
            "[yellow][Ungrounded: no retrieval context; outputs may be generic][/yellow]")
        console.print(
            "[dim]For context-grounded answers: run setup, ensure corpus exists, use --retrieval. See docs/FOUNDER_DEMO_FLOW.md.[/dim]")
    console.print(
        "[dim]Running demo-suite (first 3 prompts).[/dim]")
    if not llm_cfg or not llm_cfg.get("base_model"):
        root = _repo_root()
        console.print(
            "[yellow]LLM config missing or invalid (no base_model).[/yellow]")
        console.print(
            f"[dim]Provide a path, e.g.: --llm-config configs/llm_training_full.yaml[/dim]")
        console.print(f"[dim]Project root (for relative paths): {root}[/dim]")
        raise typer.Exit(1)
    from workflow_dataset.llm.run_summary import find_latest_successful_adapter
    runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
    adapter_path, _ = find_latest_successful_adapter(runs_dir)
    if not adapter_path:
        console.print(
            "[yellow]Degraded mode: no adapter found; using base model. Run LLM train for adapter.[/yellow]")
    backend = get_backend(llm_cfg.get("backend", "mlx"))
    base_model = llm_cfg["base_model"]
    prompts = [
        "Summarize this user's workflow style.",
        "What recurring work patterns are visible?",
        "Summarize this user's recurring reporting workflow and suggest a weekly status structure.",
    ]
    for i, prompt in enumerate(prompts[:3], 1):
        console.print(f"\n[bold]{i}. {prompt}[/bold]")
        user_prompt = prompt
        if use_retrieval and corpus_path and Path(corpus_path).exists():
            from workflow_dataset.llm.retrieval_context import retrieve, format_context_for_prompt
            docs = retrieve(corpus_path, prompt, top_k=3)
            ctx = format_context_for_prompt(docs, max_chars=1500)
            if ctx:
                user_prompt = (
                    "Context (retrieved):\n" + ctx + "\n\n"
                    "If the context above does not clearly describe this user's ops/reporting workflow, say so and keep the answer cautious.\n\n"
                    "User: " + prompt
                )
        try:
            out = backend.run_inference(base_model, user_prompt, max_tokens=200, adapter_path=adapter_path) if adapter_path else backend.run_inference(
                base_model, user_prompt, max_tokens=200)
            if out and out.startswith("[inference error"):
                console.print(f"[red]{out[:150]}[/red]")
            else:
                console.print(
                    out[:400] + ("..." if len(out or "") > 400 else "") or "[no output]")
        except Exception as e:
            console.print(f"[red]{e}[/red]")
    record_trial_event("generation_succeeded", {
                       "task_id": "release_demo"}, store_path=store_path)
    console.print(
        "\n[dim]Demo done. See docs/FOUNDER_DEMO_FLOW.md for full flow.[/dim]")


@release_group.command("package")
def release_package(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
) -> None:
    """Generate release readiness report. Does not create bundles; use assist bundle-create for that."""
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    rel = _load_release_config(release_config)
    report_dir = Path(rel.get("release_report_dir", "data/local/release"))
    report_dir.mkdir(parents=True, exist_ok=True)
    from workflow_dataset.release.report import write_release_readiness_report
    path = write_release_readiness_report(
        config_path=config, release_config_path=release_config, output_dir=report_dir)
    console.print(f"[green]Release report: {path}[/green]")


@release_group.command("report")
def release_report(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
    output_dir: str = typer.Option("", "--output-dir"),
) -> None:
    """Generate release-readiness report to data/local/release/release_readiness_report.md."""
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    rel = _load_release_config(release_config)
    out = Path(output_dir) if output_dir else Path(
        rel.get("release_report_dir", "data/local/release"))
    out.mkdir(parents=True, exist_ok=True)
    from workflow_dataset.release.report import write_release_readiness_report
    path = write_release_readiness_report(
        config_path=config, release_config_path=release_config, output_dir=out)
    console.print(f"[green]Report written: {path}[/green]")


# ----- M20 Narrow private pilot -----
pilot_group = typer.Typer(
    help="Narrow private pilot: verify, status, sessions, feedback, aggregate.")
app.add_typer(pilot_group, name="pilot")


@pilot_group.command("start-session")
def pilot_start_session(
    operator: str = typer.Option("", "--operator", "-o"),
    scope: str = typer.Option("ops", "--scope", "-s"),
    task_type: str = typer.Option("", "--task-type"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
) -> None:
    """Start a new pilot session; records context and mode. Run verify first to capture degraded state."""
    from workflow_dataset.pilot.session_log import start_session
    from workflow_dataset.pilot.health import pilot_verify_result
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    result = pilot_verify_result(
        config_path=config, release_config_path=release_config)
    degraded = not result.get("details", {}).get(
        "adapter_ok", False) and result.get("details", {}).get("llm_config_present")
    record = start_session(
        operator=operator,
        pilot_scope=scope,
        task_type=task_type,
        config_path=config,
        release_config_path=release_config,
        degraded_mode=degraded,
        pilot_dir=pilot_dir,
    )
    console.print(f"[green]Session started: {record.session_id}[/green]")
    if degraded:
        console.print(
            "[yellow]Degraded mode (no adapter) recorded for this session.[/yellow]")
    console.print(
        "[dim]Run pilot end-session when done; use pilot capture-feedback to record structured feedback.[/dim]")


@pilot_group.command("end-session")
def pilot_end_session(
    session_id: str = typer.Option("", "--session-id", "-s"),
    notes: str = typer.Option("", "--notes", "-n"),
    disposition: str = typer.Option(
        "", "--disposition", "-d", help="continue | fix | pause"),
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
) -> None:
    """Finalize the current (or given) pilot session with notes and disposition."""
    from workflow_dataset.pilot.session_log import end_session, get_current_session_id
    sid = session_id or get_current_session_id(pilot_dir)
    if not sid:
        console.print(
            "[red]No session to end. Run pilot start-session first, or pass --session-id.[/red]")
        raise typer.Exit(1)
    record = end_session(session_id=sid, operator_notes=notes,
                         disposition=disposition, pilot_dir=pilot_dir)
    if record:
        console.print(f"[green]Session ended: {record.session_id}[/green]")
        if record.disposition:
            console.print(f"  Disposition: {record.disposition}")
    else:
        console.print(f"[red]Session not found: {sid}[/red]")
        raise typer.Exit(1)


@pilot_group.command("capture-feedback")
def pilot_capture_feedback(
    usefulness: int = typer.Option(
        0, "--usefulness", "-u", help="1-5 how useful was the output"),
    trust: int = typer.Option(
        0, "--trust", "-t", help="1-5 how much user trusted the system"),
    clarity: int = typer.Option(
        0, "--clarity", "-c", help="1-5 clarity of prompts and next steps"),
    adoption: int = typer.Option(
        0, "--adoption", "-a", help="1-5 would use again"),
    blocker: bool = typer.Option(False, "--blocker/--no-blocker"),
    failure_reason: str = typer.Option("", "--failure-reason", "-f"),
    friction: str = typer.Option(
        "",
        "--friction",
        help="Operator friction e.g. report location unclear, next steps not specific enough",
    ),
    user_quote: str = typer.Option(
        "",
        "--user-quote",
        "-q",
        help="One verbatim user quote (improves evidence quality for aggregate)",
    ),
    notes: str = typer.Option(
        "",
        "--notes",
        "-n",
        help="Freeform notes (not parsed as structured evidence; use --user-quote and --friction for counts)",
    ),
    next_steps_specific: str = typer.Option(
        "",
        "--next-steps-specific",
        help="Were next steps specific enough? yes / no (appended to notes for aggregate)",
    ),
    report_location_clear: str = typer.Option(
        "",
        "--report-location-clear",
        help="Was output/report location clear? yes / no (appended to notes for aggregate)",
    ),
    session_id: str = typer.Option("", "--session-id", "-s"),
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
) -> None:
    """Capture structured feedback for the current (or given) pilot session. Use --user-quote and --friction for first-class evidence counts."""
    from workflow_dataset.pilot.feedback_capture import capture_feedback
    extra_parts: list[str] = []
    if next_steps_specific and next_steps_specific.strip().lower() in ("yes", "no"):
        extra_parts.append(f"Next steps specific enough: {next_steps_specific.strip().lower()}.")
    if report_location_clear and report_location_clear.strip().lower() in ("yes", "no"):
        extra_parts.append(f"Report location clear: {report_location_clear.strip().lower()}.")
    combined_notes = " ".join(extra_parts + [notes]).strip() if extra_parts else notes
    try:
        path = capture_feedback(
            session_id=session_id or None,
            usefulness_score=usefulness,
            trust_score=trust,
            clarity_score=clarity,
            adoption_likelihood=adoption,
            blocker_encountered=blocker,
            top_failure_reason=failure_reason,
            operator_friction_notes=friction,
            user_quote=user_quote,
            freeform_notes=combined_notes,
            pilot_dir=pilot_dir,
        )
        console.print(f"[green]Feedback saved: {path}[/green]")
        if not user_quote or not friction:
            console.print(
                "[dim]Structured evidence: use --user-quote and --friction (aggregate counts these only). Optional: --next-steps-specific and --report-location-clear yes/no.[/dim]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@pilot_group.command("aggregate")
def pilot_aggregate(
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
    limit: int = typer.Option(100, "--limit", "-l"),
) -> None:
    """Generate aggregate report from all/recent pilot sessions and feedback."""
    from workflow_dataset.pilot.aggregate import write_aggregate_report
    json_path, md_path = write_aggregate_report(
        pilot_dir=pilot_dir, session_limit=limit)
    console.print(f"[green]Aggregate report (JSON): {json_path}[/green]")
    console.print(f"[green]Aggregate report (MD):  {md_path}[/green]")


@pilot_group.command("latest-summary")
def pilot_latest_summary(
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
) -> None:
    """Print the latest pilot session summary (id, timestamps, degraded, blocking, disposition)."""
    from workflow_dataset.pilot.session_log import get_latest_session
    from workflow_dataset.pilot.feedback_capture import load_feedback
    record = get_latest_session(pilot_dir)
    if not record:
        console.print(
            "[dim]No pilot sessions found. Run pilot start-session first.[/dim]")
        return
    console.print(f"[bold]Latest session[/bold]  {record.session_id}")
    console.print(f"  Started: {record.timestamp_start}")
    console.print(f"  Ended:   {record.timestamp_end or '(active)'}")
    console.print(f"  Degraded: {record.degraded_mode}")
    console.print(f"  Blocking: {len(record.blocking_issues)}")
    for b in record.blocking_issues[:5]:
        console.print(f"    - {b}")
    console.print(f"  Warnings: {len(record.warnings)}")
    if record.disposition:
        console.print(f"  Disposition: {record.disposition}")
    fb = load_feedback(record.session_id, pilot_dir)
    if fb:
        console.print(
            f"  Feedback: usefulness={fb.usefulness_score} trust={fb.trust_score}")


@pilot_group.command("verify")
def pilot_verify(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
) -> None:
    """Verify pilot readiness: config, graph, setup, adapter, trials. Exit 1 if blocking issues."""
    from workflow_dataset.pilot.health import pilot_verify_result
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    result = pilot_verify_result(
        config_path=config, release_config_path=release_config)
    console.print(f"[bold]Pilot scope:[/bold] Operations reporting assistant")
    console.print(f"[bold]Ready:[/bold] {result['ready']}")
    for b in result.get("blocking", []):
        console.print(f"  [red]Blocking: {b}[/red]")
    for w in result.get("warnings", []):
        console.print(f"  [yellow]Warning: {w}[/yellow]")
    details = result.get("details", {})
    if details.get("graph_ok"):
        console.print("  [green]Graph: OK[/green]")
    if details.get("adapter_ok"):
        console.print(
            f"  [green]Adapter: OK ({details.get('adapter_path', '')})[/green]")
    if not result["ready"]:
        raise typer.Exit(1)


@pilot_group.command("status")
def pilot_status(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show pilot status: ready, degraded, safe-to-demo, latest adapter, feedback report."""
    from workflow_dataset.pilot.health import pilot_status_dict
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    status = pilot_status_dict(
        config_path=config, release_config_path=release_config)
    if json_output:
        import json
        console.print(json.dumps(status, indent=2))
        return
    console.print(f"[bold]Ready:[/bold] {status['ready']}")
    console.print(f"[bold]Safe to demo:[/bold] {status['safe_to_demo']}")
    console.print(f"[bold]Degraded (no adapter):[/bold] {status['degraded']}")
    if status.get("adapter_ok"):
        console.print("  Adapter: OK")
    elif status.get("degraded"):
        console.print("  Adapter: missing (degraded; base model only)")
    else:
        console.print("  Adapter: missing (LLM config missing or no adapter)")
    if status.get("latest_run_dir"):
        console.print(f"  Latest run: {status['latest_run_dir']}")
    if status.get("latest_feedback_report"):
        console.print(f"  Feedback report: {status['latest_feedback_report']}")


@pilot_group.command("latest-report")
def pilot_latest_report(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    release_config: str = typer.Option(
        "configs/release_narrow.yaml", "--release-config"),
    output_dir: str = typer.Option("data/local/pilot", "--output-dir"),
) -> None:
    """Generate pilot_readiness_report.md with scope, status, evidence, recommendation."""
    from workflow_dataset.pilot.health import write_pilot_readiness_report
    r_cfg = _resolve_path(config)
    r_rel = _resolve_path(release_config)
    config = str(r_cfg) if r_cfg is not None else config
    release_config = str(r_rel) if r_rel is not None else release_config
    out = Path(output_dir)
    path = write_pilot_readiness_report(
        config_path=config, release_config_path=release_config, pilot_dir=out)
    console.print(f"[green]Pilot report: {path}[/green]")


# ----- M21 Capability intake -----
sources_group = typer.Typer(
    help="Open-source capability intake: list sources, show, report, classify.")
app.add_typer(sources_group, name="sources")

packs_group = typer.Typer(
    help="Capability packs: list, show, install, uninstall, validate, resolve.")
app.add_typer(packs_group, name="packs")


@sources_group.command("list")
def sources_list(
    registry: str = typer.Option(
        "data/local/capability_intake/source_registry.json", "--registry"),
    adoption: str = typer.Option(
        "", "--adoption", help="Filter by adoption_recommendation"),
) -> None:
    """List registered capability intake sources."""
    from workflow_dataset.capability_intake.source_registry import list_sources
    sources = list_sources(registry_path=registry,
                           adoption_filter=adoption or None)
    for s in sources:
        console.print(
            f"  [bold]{s.source_id}[/bold]  {s.adoption_recommendation}  {s.recommended_role}  — {s.name}")


@sources_group.command("show")
def sources_show(
    source_id: str = typer.Argument(...,
                                    help="Source id (e.g. openclaw, mirofish)"),
    registry: str = typer.Option(
        "data/local/capability_intake/source_registry.json", "--registry"),
) -> None:
    """Show details for one registered source."""
    from workflow_dataset.capability_intake.source_registry import get_source
    s = get_source(source_id, registry_path=registry)
    if not s:
        console.print(f"[red]Source not found: {source_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{s.source_id}[/bold] — {s.name}")
    console.print(f"  Type: {s.source_type}  Kind: {s.source_kind}")
    console.print(f"  URL: {s.canonical_url or '(none)'}")
    console.print(f"  Role: {s.recommended_role}  Risk: {s.safety_risk_level}")
    console.print(
        f"  Local fit: {s.local_runtime_fit}  Cloud pack fit: {s.cloud_pack_fit}")
    console.print(f"  Adoption: {s.adoption_recommendation}")
    if s.unresolved_reason:
        console.print(f"  [yellow]Unresolved: {s.unresolved_reason}[/yellow]")
    if s.notes:
        console.print(f"  Notes: {s.notes[:300]}")


@sources_group.command("report")
def sources_report(
    registry: str = typer.Option(
        "data/local/capability_intake/source_registry.json", "--registry"),
    output: str = typer.Option(
        "data/local/capability_intake/source_report.md", "--output"),
) -> None:
    """Generate capability intake source report (markdown)."""
    from workflow_dataset.capability_intake.source_report import write_source_report
    path = write_source_report(output_path=output, registry_path=registry)
    console.print(f"[green]Source report: {path}[/green]")


@sources_group.command("rank")
def sources_rank(
    role: str = typer.Option(
        "", "--role", "-r", help="Job role e.g. ops, analyst"),
    industry: str = typer.Option(
        "", "--industry", "-i", help="Industry vertical"),
    workflow_type: str = typer.Option(
        "", "--workflow", "-w", help="Workflow type e.g. reporting"),
    task_type: str = typer.Option(
        "", "--task", "-t", help="Task type e.g. summarize, scaffold"),
    registry: str = typer.Option(
        "data/local/capability_intake/source_registry.json", "--registry"),
    top: int = typer.Option(10, "--top", "-n"),
) -> None:
    """Rank registered sources by fit to role/industry/workflow/task. Offline; uses registry only."""
    from workflow_dataset.capability_intake.repo_ranker import RepoTaskFitQuery, rank_sources_for_query
    query = RepoTaskFitQuery(role=role, industry=industry,
                             workflow_type=workflow_type, task_type=task_type)
    results = rank_sources_for_query(query, registry_path=registry, top_k=top)
    for r in results:
        console.print(
            f"  [bold]{r.source_id}[/bold]  fit={r.fit_score:.2f}  safety={r.safety_score:.2f}  adoption={r.adoption_recommendation}")
        if r.rationale:
            console.print(f"    [dim]{r.rationale}[/dim]")


@sources_group.command("unresolved")
def sources_unresolved(
    registry: str = typer.Option(
        "data/local/capability_intake/source_registry.json", "--registry"),
) -> None:
    """List sources marked unresolved (no canonical URL or ambiguous identity)."""
    from workflow_dataset.capability_intake.source_registry import list_sources
    sources = list_sources(registry_path=registry, unresolved_only=True)
    for s in sources:
        console.print(
            f"  [bold]{s.source_id}[/bold]  — {(s.unresolved_reason or '')[:80]}...")


@sources_group.command("classify")
def sources_classify(
    path_or_manifest: str = typer.Argument(
        ..., help="Path to manifest JSON or inline source_id"),
    registry: str = typer.Option(
        "data/local/capability_intake/source_registry.json", "--registry"),
) -> None:
    """Classify a manifest file and print role/risk/fit/recommendation."""
    from pathlib import Path
    from workflow_dataset.capability_intake.repo_parser import parse_local_manifest
    from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate
    p = Path(path_or_manifest)
    if p.exists():
        c = parse_local_manifest(p)
        if not c:
            console.print("[red]Failed to parse manifest.[/red]")
            raise typer.Exit(1)
    else:
        from workflow_dataset.capability_intake.source_registry import get_source
        c = get_source(path_or_manifest,
                       registry_path=registry) if path_or_manifest else None
        if not c:
            console.print(
                f"[red]Not a file and not found in registry: {path_or_manifest}[/red]")
            raise typer.Exit(1)
    console.print(f"  source_id: {c.source_id}")
    console.print(f"  recommended_role: {c.recommended_role}")
    console.print(f"  safety_risk_level: {c.safety_risk_level}")
    console.print(
        f"  local_runtime_fit: {c.local_runtime_fit}  cloud_pack_fit: {c.cloud_pack_fit}")
    console.print(f"  adoption_recommendation: {c.adoption_recommendation}")


@packs_group.command("list")
def packs_list(
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
    show_activation: bool = typer.Option(
        False, "--all", "-a", help="Show activation state (primary, pinned, suspended)"),
) -> None:
    """List installed capability packs. Use --all to show primary, pinned, suspended."""
    from workflow_dataset.packs import list_installed_packs
    from workflow_dataset.packs.pack_activation import get_primary_pack_id, get_pinned, get_suspended_pack_ids
    installed = list_installed_packs(packs_dir)
    if not installed:
        console.print(
            "[dim]No packs installed. Use 'packs install <manifest_path>' to install.[/dim]")
        raise typer.Exit(0)
    primary = get_primary_pack_id(packs_dir) if show_activation else ""
    pinned = get_pinned(packs_dir) if show_activation else {}
    suspended = set(get_suspended_pack_ids(packs_dir)
                    ) if show_activation else set()
    for rec in installed:
        pack_id = rec.get("pack_id", "")
        version = rec.get("version", "")
        suffix = []
        if pack_id == primary:
            suffix.append("primary")
        for sc, pid in pinned.items():
            if pid == pack_id:
                suffix.append(f"pinned({sc})")
        if pack_id in suspended:
            suffix.append("suspended")
        line = f"  {pack_id}  {version}"
        if suffix:
            line += "  [" + ", ".join(suffix) + "]"
        console.print(line)


@packs_group.command("show")
def packs_show(
    pack_id: str = typer.Argument(..., help="Installed pack id"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Show installed pack manifest summary."""
    from workflow_dataset.packs import get_installed_manifest
    manifest = get_installed_manifest(pack_id, packs_dir)
    if not manifest:
        console.print(f"[red]Pack not installed: {pack_id}[/red]")
        raise typer.Exit(1)
    console.print(f"pack_id: {manifest.pack_id}")
    console.print(f"name: {manifest.name}")
    console.print(f"version: {manifest.version}")
    console.print(f"role_tags: {manifest.role_tags}")
    console.print(f"industry_tags: {manifest.industry_tags}")
    console.print(f"workflow_tags: {manifest.workflow_tags}")
    console.print(f"task_tags: {manifest.task_tags}")
    console.print(f"recommended_models: {manifest.recommended_models}")


@packs_group.command("install")
def packs_install(
    manifest_path: str = typer.Argument(...,
                                        help="Path to pack manifest JSON"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Install a capability pack from a manifest file (local-only; declarative recipes only)."""
    from workflow_dataset.packs import install_pack
    ok, msg = install_pack(manifest_path, packs_dir)
    if ok:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)


@packs_group.command("uninstall")
def packs_uninstall(
    pack_id: str = typer.Argument(..., help="Pack id to uninstall"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Uninstall a capability pack (removes from installed state)."""
    from workflow_dataset.packs import uninstall_pack
    ok, msg = uninstall_pack(pack_id, packs_dir)
    if ok:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)


@packs_group.command("activate")
def packs_activate(
    pack_id: str = typer.Argument(
        ..., help="Pack id to activate (sets as primary pack for release run)"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Activate a pack: set as primary so release run uses it when --role is omitted."""
    from workflow_dataset.packs import get_installed_manifest
    from workflow_dataset.packs.pack_activation import set_primary_pack
    from workflow_dataset.packs.pack_state import set_active_role
    manifest = get_installed_manifest(pack_id, packs_dir)
    if not manifest:
        console.print(
            f"[red]Pack not installed: {pack_id}. Install it first.[/red]")
        raise typer.Exit(1)
    role = (manifest.role_tags or [""])[0]
    if not role:
        console.print(f"[red]Pack has no role_tags; cannot activate.[/red]")
        raise typer.Exit(1)
    set_primary_pack(pack_id, packs_dir)
    set_active_role(role, packs_dir)
    console.print(
        f"[green]Activated {pack_id} (primary, role={role}).[/green]")


@packs_group.command("deactivate")
def packs_deactivate(
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Clear primary pack and active role."""
    from workflow_dataset.packs.pack_activation import clear_primary_pack
    from workflow_dataset.packs.pack_state import clear_active_role
    clear_primary_pack(packs_dir)
    clear_active_role(packs_dir)
    console.print(
        "[green]Deactivated. No primary pack or active role.[/green]")


@packs_group.command("pin")
def packs_pin(
    pack_id: str = typer.Argument(..., help="Pack id to pin"),
    scope: str = typer.Option("session", "--scope",
                              "-s", help="Scope: session, project, or task"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Pin a pack for the given scope (it wins over primary for that scope)."""
    from workflow_dataset.packs.pack_activation import pin_pack
    pin_pack(pack_id, scope, packs_dir)
    console.print(f"[green]Pinned {pack_id} for scope={scope}.[/green]")


@packs_group.command("unpin")
def packs_unpin(
    pack_id: str = typer.Argument(
        None, help="Pack id to unpin (omit to clear by scope only)"),
    scope: str = typer.Option(None, "--scope", "-s",
                              help="Scope to clear (session, project, task)"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Unpin: use --scope to clear that scope, or pack_id to remove all pins for that pack."""
    from workflow_dataset.packs.pack_activation import unpin_pack
    unpin_pack(pack_id, scope, packs_dir)
    console.print("[green]Unpinned.[/green]")


@packs_group.command("conflicts")
def packs_conflicts(
    role: str = typer.Option("", "--role", "-r"),
    workflow: str = typer.Option("", "--workflow", "-w"),
    task: str = typer.Option("", "--task", "-t"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """List detected conflicts between installed packs (optionally for role/workflow/task)."""
    from workflow_dataset.packs import list_installed_packs, get_installed_manifest
    from workflow_dataset.packs.pack_conflicts import detect_conflicts
    installed = list_installed_packs(packs_dir)
    manifests = []
    for rec in installed:
        m = get_installed_manifest(rec["pack_id"], packs_dir)
        if m:
            manifests.append(m)
    conflicts = detect_conflicts(
        manifests, role=role or None, workflow=workflow or None, task=task or None)
    if not conflicts:
        console.print("[dim]No conflicts detected.[/dim]")
        return
    for c in conflicts:
        console.print(
            f"  [{c.conflict_class.value}] {c.capability}: {c.description}")
        console.print(f"    packs: {c.pack_ids}  -> {c.resolution}")


@packs_group.command("explain")
def packs_explain(
    task_or_scope: str = typer.Argument(
        "", help="Optional task or scope to explain"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Explain why current capabilities resolve as they do (primary, pinned, conflicts)."""
    from workflow_dataset.packs.pack_resolution_graph import resolve_with_priority
    from workflow_dataset.packs.pack_activation import get_current_context
    ctx = get_current_context(packs_dir)
    cap, expl = resolve_with_priority(
        role=ctx.get("current_role") or None,
        workflow_type=ctx.get("current_workflow") or None,
        task_type=ctx.get("current_task") or task_or_scope or None,
        packs_dir=packs_dir,
    )
    console.print("Resolution:", expl.summary)
    console.print("Primary:", expl.primary_pack_id or "(none)")
    console.print("Pinned:", expl.pinned_packs or "(none)")
    console.print("Secondary:", expl.secondary_pack_ids or "(none)")
    console.print("Excluded:", expl.excluded_pack_ids or "(none)")
    if expl.conflicts:
        console.print("Conflicts:", len(expl.conflicts))
        for c in expl.conflicts:
            console.print(f"  - {c.conflict_class.value}: {c.capability}")
    console.print("Active packs:", [m.pack_id for m in cap.active_packs])
    console.print("Templates:", cap.templates)


@packs_group.command("validate")
@packs_group.command("validate-manifest")
def packs_validate(
    path: str = typer.Argument(..., help="Path to pack manifest JSON"),
) -> None:
    """Validate a capability pack manifest against schema and safety policy."""
    from pathlib import Path
    import json
    from workflow_dataset.packs.pack_validator import validate_pack_manifest_and_recipes
    p = Path(path)
    if not p.exists():
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(1)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)
    valid, errors = validate_pack_manifest_and_recipes(data)
    if valid:
        console.print("[green]Manifest valid.[/green]")
    else:
        for e in errors:
            console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@packs_group.command("multi-pack-report")
def packs_multi_pack_report(
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
    output: str = typer.Option(
        "", "--output", "-o", help="Output path (default: data/local/packs/multi_pack_status_report.md)"),
) -> None:
    """Write multi-pack status report (installed, primary, pinned, resolution)."""
    from workflow_dataset.packs.pack_reporting import write_multi_pack_status_report
    path = write_multi_pack_status_report(
        packs_dir=packs_dir, output_path=output or None)
    console.print(f"[green]Report written: {path}[/green]")


@packs_group.command("conflict-report")
def packs_conflict_report(
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
    role: str = typer.Option("", "--role", "-r"),
    workflow: str = typer.Option("", "--workflow", "-w"),
    task: str = typer.Option("", "--task", "-t"),
    output: str = typer.Option("", "--output", "-o"),
) -> None:
    """Write conflict report for installed packs."""
    from workflow_dataset.packs.pack_reporting import write_conflict_report
    path = write_conflict_report(packs_dir=packs_dir, role=role or None,
                                 workflow=workflow or None, task=task or None, output_path=output or None)
    console.print(f"[green]Report written: {path}[/green]")


@packs_group.command("report")
def packs_report(
    pack_id: str = typer.Argument(...,
                                  help="Pack id to generate evaluation report for"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
    trials_dir: str = typer.Option("data/local/trials", "--trials-dir"),
) -> None:
    """Generate a short evaluation report for an installed pack (data/local/packs/<pack_id>/report.md)."""
    from workflow_dataset.packs.pack_report import write_pack_report
    try:
        path = write_pack_report(
            pack_id, packs_dir=packs_dir, trials_dir=trials_dir)
        console.print(f"[green]Report written: {path}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@packs_group.command("resolve")
def packs_resolve(
    role: str = typer.Option(
        "", "--role", "-r", help="Filter by role e.g. ops"),
    industry: str = typer.Option(
        "", "--industry", "-i", help="Filter by industry"),
    task: str = typer.Option("", "--task", "-t", help="Filter by task type"),
    workflow: str = typer.Option(
        "", "--workflow", "-w", help="Filter by workflow type"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Resolve active packs by role/industry/workflow/task."""
    from workflow_dataset.packs import resolve_active_capabilities
    cap = resolve_active_capabilities(
        role=role or None,
        industry=industry or None,
        workflow_type=workflow or None,
        task_type=task or None,
        packs_dir=packs_dir,
    )
    console.print("Active packs:")
    for m in cap.active_packs:
        console.print(f"  {m.pack_id}  {m.version}")
    console.print("Recommended models:", cap.recommended_models)
    console.print("Output adapters:", cap.output_adapters)


# ----- M22 Runtime -----
runtime_group = typer.Typer(
    help="Runtime status and active capability resolution.")
app.add_typer(runtime_group, name="runtime")


@runtime_group.command("status")
def runtime_status(
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Show current runtime status: installed packs, primary/pinned/suspended, resolution summary."""
    from workflow_dataset.packs import list_installed_packs, resolve_active_capabilities
    from workflow_dataset.packs.pack_state import get_active_role
    from workflow_dataset.packs.pack_activation import get_primary_pack_id, get_pinned, get_suspended_pack_ids, get_current_context
    installed = list_installed_packs(packs_dir)
    console.print("[bold]Installed packs[/bold]")
    if not installed:
        console.print("  (none)")
    else:
        for rec in installed:
            console.print(f"  {rec.get('pack_id')}  {rec.get('version')}")
    primary = get_primary_pack_id(packs_dir)
    pinned = get_pinned(packs_dir)
    suspended = get_suspended_pack_ids(packs_dir)
    ctx = get_current_context(packs_dir)
    if primary:
        console.print(f"[bold]Primary pack[/bold]  {primary}")
    if pinned:
        console.print("[bold]Pinned[/bold]", pinned)
    if suspended:
        console.print("[bold]Suspended[/bold]", suspended)
    if ctx.get("current_role"):
        console.print(f"[bold]Current role[/bold]  {ctx['current_role']}")
    elif get_active_role(packs_dir):
        console.print(
            f"[bold]Active role[/bold]  {get_active_role(packs_dir)}")
    cap = resolve_active_capabilities(
        role=ctx.get("current_role") or get_active_role(packs_dir) or None,
        workflow_type=ctx.get("current_workflow") or None,
        task_type=ctx.get("current_task") or None,
        packs_dir=packs_dir,
    )
    console.print("[bold]Active capabilities[/bold]")
    console.print("  packs:", [m.pack_id for m in cap.active_packs])
    console.print("  templates:", cap.templates[:10] if len(
        cap.templates) > 10 else cap.templates)
    console.print("  recommended_models:", cap.recommended_models)
    console.print("  output_adapters:", cap.output_adapters)


@runtime_group.command("show-active-capabilities")
def runtime_show_active(
    role: str = typer.Option("", "--role", "-r"),
    industry: str = typer.Option("", "--industry", "-i"),
    task: str = typer.Option("", "--task", "-t"),
    workflow: str = typer.Option("", "--workflow", "-w"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Show active capabilities for given role/industry/workflow/task."""
    from workflow_dataset.packs import resolve_active_capabilities
    cap = resolve_active_capabilities(
        role=role or None,
        industry=industry or None,
        workflow_type=workflow or None,
        task_type=task or None,
        packs_dir=packs_dir,
    )
    console.print("Active packs:", [m.pack_id for m in cap.active_packs])
    console.print("Prompts:", len(cap.prompts))
    console.print("Templates:", cap.templates)
    console.print("Output adapters:", cap.output_adapters)
    console.print("Parser profiles:", cap.parser_profiles)
    console.print("Recommended models:", cap.recommended_models)
    console.print("Retrieval profile:", cap.retrieval_profile)
    console.print("Safety restrictions:", cap.safety_restrictions)


@runtime_group.command("explain-resolution")
def runtime_explain(
    role: str = typer.Option("", "--role", "-r"),
    industry: str = typer.Option("", "--industry", "-i"),
    task: str = typer.Option("", "--task", "-t"),
    workflow: str = typer.Option("", "--workflow", "-w"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Explain why capabilities resolve as they do for given filters."""
    from workflow_dataset.packs import list_installed_packs, resolve_active_capabilities
    filters = []
    if role:
        filters.append(f"role={role}")
    if industry:
        filters.append(f"industry={industry}")
    if task:
        filters.append(f"task={task}")
    if workflow:
        filters.append(f"workflow={workflow}")
    console.print(
        "Filters:", filters if filters else "(none — all installed packs active)")
    installed = list_installed_packs(packs_dir)
    console.print("Installed:", [r.get("pack_id") for r in installed])
    cap = resolve_active_capabilities(
        role=role or None,
        industry=industry or None,
        workflow_type=workflow or None,
        task_type=task or None,
        packs_dir=packs_dir,
    )
    console.print("Active after resolution:", [
                  m.pack_id for m in cap.active_packs])
    for m in cap.active_packs:
        console.print(
            f"  {m.pack_id}: role_tags={m.role_tags} industry={m.industry_tags} workflow={m.workflow_tags} task={m.task_tags}")


@runtime_group.command("switch-role")
def runtime_switch_role(
    role_tag: str = typer.Argument(...,
                                   help="Role to switch to (e.g. ops, founder)"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Set current role for resolution (primary pack unchanged; resolution filters by this role)."""
    from workflow_dataset.packs.pack_activation import set_current_role
    set_current_role(role_tag, packs_dir)
    from workflow_dataset.packs.pack_state import set_active_role
    set_active_role(role_tag, packs_dir)
    console.print(f"[green]Current role set to: {role_tag}[/green]")


@runtime_group.command("switch-context")
def runtime_switch_context(
    workflow: str = typer.Option("", "--workflow", "-w"),
    task: str = typer.Option("", "--task", "-t"),
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Set current workflow and/or task for resolution."""
    from workflow_dataset.packs.pack_activation import set_current_context
    if not workflow and not task:
        console.print("[yellow]Provide --workflow and/or --task[/yellow]")
        raise typer.Exit(1)
    set_current_context(workflow=workflow or None,
                        task=task or None, packs_dir=packs_dir)
    console.print(
        f"[green]Context set: workflow={workflow or '(unchanged)'} task={task or '(unchanged)'}[/green]")


@runtime_group.command("clear-context")
def runtime_clear_context(
    packs_dir: str = typer.Option("data/local/packs", "--packs-dir"),
) -> None:
    """Clear current role/workflow/task and all pins (primary pack unchanged)."""
    from workflow_dataset.packs.pack_activation import clear_context
    from workflow_dataset.packs.pack_state import clear_active_role
    clear_context(packs_dir)
    clear_active_role(packs_dir)
    console.print(
        "[green]Context cleared (role, workflow, task, pins). Primary pack unchanged.[/green]")
