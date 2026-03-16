from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


# C2: Command center with workflow filter and drill-down subcommands
dashboard_group = typer.Typer(
    help="Local Reporting Command Center: readiness, workspaces, packages, cohort, next actions. Use --workflow to filter.",
)


@dashboard_group.callback(invoke_without_command=True)
def dashboard_cmd(
    ctx: typer.Context,
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    workflow: str | None = typer.Option(None, "--workflow", "-w", help="Filter views by workflow (e.g. weekly_status, ops_reporting_workspace)."),
) -> None:
    """Local Reporting Command Center. Add subcommand for drill-downs: workspace, package, cohort, apply-plan."""
    if ctx.invoked_subcommand is not None:
        return
    from workflow_dataset.ui.dashboard_view import print_dashboard_cli
    print_dashboard_cli(console, config_path=config, workflow_filter=workflow)


@dashboard_group.command("workspace")
def dashboard_workspace(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    workflow: str | None = typer.Option(None, "--workflow", "-w", help="Filter by workflow."),
) -> None:
    """Show latest workspace detail (path, artifacts, approved, next-step commands)."""
    from workflow_dataset.ui.dashboard_view import print_drilldown_cli
    print_drilldown_cli(console, drill="workspace", config_path=config, workflow_filter=workflow)


@dashboard_group.command("package")
def dashboard_package(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Show latest package detail (path, files, open command)."""
    from workflow_dataset.ui.dashboard_view import print_drilldown_cli
    print_drilldown_cli(console, drill="package", config_path=config)


@dashboard_group.command("cohort")
def dashboard_cohort(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Show latest cohort report (path, excerpt, open command)."""
    from workflow_dataset.ui.dashboard_view import print_drilldown_cli
    print_drilldown_cli(console, drill="cohort", config_path=config)


@dashboard_group.command("apply-plan")
def dashboard_apply_plan(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Show latest apply-plan preview (path, excerpt, open command)."""
    from workflow_dataset.ui.dashboard_view import print_drilldown_cli
    print_drilldown_cli(console, drill="apply_plan", config_path=config)


# C4: Action runner stubs — run macro command by id (no hidden automation)
@dashboard_group.command("action")
def dashboard_action(
    macro_id: str = typer.Argument(
        ...,
        help="inspect-workspace | open-package | open-cohort-report | staging-board | benchmark-board",
    ),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Run an action shortcut: runs the underlying command and prints output."""
    import subprocess
    from workflow_dataset.release.dashboard_data import get_dashboard_data
    from workflow_dataset.path_utils import get_repo_root
    repo_root = Path(get_repo_root())
    data = get_dashboard_data(config_path=config, repo_root=repo_root)
    macros = data.get("action_macros") or []
    macro = next((m for m in macros if m.get("id") == macro_id), None)
    if not macro:
        console.print(f"[yellow]No macro for id: {macro_id!r}. Available: {[m.get('id') for m in macros]}[/yellow]")
        raise typer.Exit(0)
    cmd = macro.get("command", "")
    if not cmd:
        console.print(f"[yellow]No command for macro: {macro_id}[/yellow]")
        raise typer.Exit(0)
    console.print(f"[dim]Running: {cmd}[/dim]\n")
    result = subprocess.run(cmd, shell=True, cwd=str(repo_root), timeout=60)
    raise typer.Exit(result.returncode if result.returncode is not None else 0)


app.add_typer(dashboard_group, name="dashboard")


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

# ----- M23U User work profile and bootstrap -----
profile_group = typer.Typer(
    help="User work profile: bootstrap, show, operator-summary. Local-only; explicit and editable.")
app.add_typer(profile_group, name="profile")


@profile_group.command("bootstrap")
def profile_bootstrap(
    repo_root: str = typer.Option("", "--repo-root"),
    field: str = typer.Option("", "--field", "-f", help="e.g. operations, founder_ops"),
    job_family: str = typer.Option("", "--job-family", "-j", help="e.g. office_admin, analyst"),
) -> None:
    """Create or update user work profile (field, job family, etc.). Saves to data/local/onboarding/user_work_profile.yaml."""
    from workflow_dataset.onboarding.user_work_profile import bootstrap_user_work_profile
    root = Path(repo_root).resolve() if repo_root else None
    profile = bootstrap_user_work_profile(repo_root=root, field=field, job_family=job_family)
    console.print("[green]User work profile saved.[/green]")
    console.print(f"  field: {profile.field or '(not set)'}")
    console.print(f"  job_family: {profile.job_family or '(not set)'}")
    console.print(f"  path: data/local/onboarding/user_work_profile.yaml")


@profile_group.command("show")
def profile_show(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Show current user work profile and bootstrap profile summary."""
    from workflow_dataset.onboarding.user_work_profile import load_user_work_profile, get_user_work_profile_path
    from workflow_dataset.onboarding.bootstrap_profile import load_bootstrap_profile
    root = Path(repo_root).resolve() if repo_root else None
    user = load_user_work_profile(root)
    if not user:
        console.print("[yellow]No user work profile found. Run 'profile bootstrap' to create.[/yellow]")
        path = get_user_work_profile_path(root)
        console.print(f"  path: {path}")
    else:
        console.print("[bold]User work profile[/bold]")
        console.print(f"  field: {user.field or '(not set)'}")
        console.print(f"  vertical: {user.vertical or '(not set)'}")
        console.print(f"  job_family: {user.job_family or '(not set)'}")
        console.print(f"  daily_task_style: {user.daily_task_style or '(not set)'}")
        console.print(f"  risk_safety_posture: {user.risk_safety_posture}")
        console.print(f"  preferred_automation_degree: {user.preferred_automation_degree}")
        console.print(f"  preferred_edge_tier: {user.preferred_edge_tier or '(not set)'}")
    boot = load_bootstrap_profile(root)
    if boot:
        console.print("[bold]Bootstrap profile (machine)[/bold]")
        console.print(f"  machine_id: {boot.machine_id}")
        console.print(f"  ready_for_real: {boot.ready_for_real}")
        console.print(f"  recommended_job_packs: {boot.recommended_job_packs[:5]}..." if len(boot.recommended_job_packs) > 5 else f"  recommended_job_packs: {boot.recommended_job_packs}")


@profile_group.command("operator-summary")
def profile_operator_summary(
    repo_root: str = typer.Option("", "--repo-root"),
    output: str = typer.Option("", "--output", "-o", help="Write markdown to file"),
) -> None:
    """Generate operator-facing summary: recommended domain pack(s), model/tool classes, specialization route, data usage, simulate-only scope."""
    from workflow_dataset.onboarding.user_work_profile import load_user_work_profile
    from workflow_dataset.onboarding.bootstrap_profile import load_bootstrap_profile
    from workflow_dataset.onboarding.operator_summary import build_operator_summary, format_operator_summary_md
    root = Path(repo_root).resolve() if repo_root else None
    user = load_user_work_profile(root)
    boot = load_bootstrap_profile(root)
    summary = build_operator_summary(
        user_profile=user,
        bootstrap_profile=boot,
        catalog_entries=None,
        repo_root=root,
    )
    md = format_operator_summary_md(summary)
    if output:
        Path(output).write_text(md, encoding="utf-8")
        console.print(f"[green]Summary written to {output}[/green]")
    else:
        console.print(md)


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


# ----- M23N First-run onboarding + capability/approval bootstrap -----
onboard_group = typer.Typer(
    help="First-run onboarding: local setup, capability summary, approval bootstrap, product summary. No auto-grant.")
app.add_typer(onboard_group, name="onboard")


@onboard_group.callback(invoke_without_command=True)
def onboard_cmd(
    ctx: typer.Context,
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """First-run onboarding: show status and run guided flow. Use subcommands: status, bootstrap, approve."""
    if ctx.invoked_subcommand is not None:
        return
    from workflow_dataset.onboarding.onboarding_flow import get_onboarding_status, format_onboarding_status
    status = get_onboarding_status(config_path=config)
    console.print(Panel(format_onboarding_status(status), title="Onboarding status", border_style="cyan"))
    console.print("[dim]Commands: workflow-dataset onboard status | onboard bootstrap | onboard approve[/dim]")


@onboard_group.command("status")
def onboard_status(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Show onboarding status: profile, env readiness, capabilities, approvals, blocked, next steps."""
    from workflow_dataset.onboarding.onboarding_flow import get_onboarding_status, format_onboarding_status
    status = get_onboarding_status(config_path=config)
    console.print(format_onboarding_status(status))


@onboard_group.command("bootstrap")
def onboard_bootstrap(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
) -> None:
    """Create or refresh bootstrap profile and first-run summary. Persists to data/local/onboarding/."""
    from workflow_dataset.onboarding import run_onboarding_flow, build_first_run_summary, format_first_run_summary
    status = run_onboarding_flow(config_path=config, persist_profile=True)
    console.print("[green]Bootstrap profile saved.[/green]")
    summary = build_first_run_summary(config_path=config)
    console.print(Panel(format_first_run_summary(summary=summary), title="First-run product summary", border_style="green"))


@onboard_group.command("approve")
def onboard_approve(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    paths: str = typer.Option("", "--paths", help="Comma-separated paths to approve (optional)"),
    refuse_paths: str = typer.Option("", "--refuse-paths", help="Comma-separated paths to refuse (omit from registry)"),
    approve_all_suggested: bool = typer.Option(False, "--approve-all-suggested", help="Approve all suggested paths and trusted scopes (no apps)"),
) -> None:
    """Review and apply approval choices. No auto-grant; only explicitly approved items are added."""
    from workflow_dataset.onboarding.approval_bootstrap import (
        collect_approval_requests,
        format_approval_bootstrap_summary,
        apply_approval_choices,
    )
    requests = collect_approval_requests()
    console.print(Panel(format_approval_bootstrap_summary(requests), title="Approval bootstrap — review", border_style="yellow"))
    approve_paths_list = [p.strip() for p in paths.split(",") if p.strip()] if paths else []
    refuse_paths_list = [p.strip() for p in refuse_paths.split(",") if p.strip()] if refuse_paths else []
    if approve_all_suggested:
        approve_paths_list = list(requests.get("suggested_paths", []))
        approve_scopes = [{"adapter_id": s["adapter_id"], "action_id": s["action_id"]} for s in requests.get("suggested_action_scopes", []) if s.get("executable")]
    else:
        approve_scopes = []
    if approve_paths_list or approve_scopes:
        path_written = apply_approval_choices(
            approve_paths=approve_paths_list,
            refuse_paths=refuse_paths_list,
            approve_scopes=approve_scopes,
            merge_with_existing=True,
        )
        console.print(f"[green]Approval registry updated: {path_written}[/green]")
    else:
        console.print("[dim]No approvals applied. Use --paths or --approve-all-suggested to add approvals.[/dim]")


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

# ----- M22D Local Knowledge Intake Center -----
intake_group = typer.Typer(
    help="Local intake: register paths, snapshot into sandbox, report. User-owned inputs only; no cloud.")
app.add_typer(intake_group, name="intake")

# ----- M22E Workflow Composer + Template Studio -----
templates_group = typer.Typer(
    help="Workflow templates: list, show, use with release demo --template. Local YAML in data/local/templates/.")
app.add_typer(templates_group, name="templates")

# ----- M23B Edge / Hardware Readiness Layer -----
edge_group = typer.Typer(
    help="Edge readiness: profile, checks, workflow matrix, missing deps. Local deployment only; no hardware specs.")
app.add_typer(edge_group, name="edge")

# ----- M23C-F1/F2 Desktop Action Adapters (simulate-first; F2 read-only + sandbox run) -----
adapters_group = typer.Typer(
    help="Desktop action adapters: list, show, simulate, run. Local-only; run = read-only or copy to sandbox only.")
app.add_typer(adapters_group, name="adapters")


@adapters_group.command("list")
def adapters_list() -> None:
    """List registered desktop action adapters (file_ops, notes_document, browser_open, app_launch)."""
    from workflow_dataset.desktop_adapters import list_adapters
    items = list_adapters()
    console.print("[bold]Desktop action adapters[/bold] (simulate-first; local-only)")
    for a in items:
        console.print(f"  [bold]{a.adapter_id}[/bold]  {a.adapter_type}")
        console.print(f"    {a.capability_description[:70]}{'...' if len(a.capability_description) > 70 else ''}")
        console.print(f"    simulate={a.supports_simulate}  real_execution={a.supports_real_execution}")


@adapters_group.command("show")
def adapters_show(
    id: str = typer.Option(..., "--id", "-i", help="Adapter id (e.g. file_ops, browser_open)"),
) -> None:
    """Show adapter contract: capability, actions, required approvals, failure modes."""
    from workflow_dataset.desktop_adapters import get_adapter
    a = get_adapter(id.strip())
    if not a:
        console.print(f"[red]Adapter not found: {id}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]Adapter: {a.adapter_id}[/bold]")
    console.print(f"  type: {a.adapter_type}")
    console.print(f"  capability: {a.capability_description}")
    console.print(f"  supports_simulate: {a.supports_simulate}  supports_real_execution: {a.supports_real_execution}")
    console.print("  required_approvals:")
    for ap in a.required_approvals:
        console.print(f"    - {ap}")
    console.print("  supported_actions:")
    for act in a.supported_actions:
        console.print(f"    - {act.action_id}: {act.description} (simulate={act.supports_simulate}, real={act.supports_real})")
    console.print("  failure_modes:")
    for fm in a.failure_modes:
        console.print(f"    - {fm}")


@adapters_group.command("simulate")
def adapters_simulate(
    id: str = typer.Option(..., "--id", "-i", help="Adapter id"),
    action: str = typer.Option(..., "--action", "-a", help="Action id (e.g. open_url, read_file)"),
    param: list[str] = typer.Option([], "--param", "-p", help="Param key=value (e.g. url=https://example.com)"),
) -> None:
    """Run adapter action in simulate mode. Dry-run only; no real execution."""
    from workflow_dataset.desktop_adapters import run_simulate
    params: dict[str, str] = {}
    for kv in param:
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.strip()] = v.strip()
    result = run_simulate(id.strip(), action.strip(), params)
    if result.success:
        console.print("[green]Simulate OK[/green]")
        console.print(result.preview)
        if not result.real_execution_supported:
            console.print("[dim]Real execution not implemented for this adapter/action.[/dim]")
    else:
        console.print(f"[red]{result.message}[/red]")
        raise typer.Exit(1)


@adapters_group.command("run")
def adapters_run(
    id: str = typer.Option(..., "--id", "-i", help="Adapter id (file_ops or notes_document for F2 run)"),
    action: str = typer.Option(..., "--action", "-a", help="Action id (e.g. inspect_path, read_text, snapshot_to_sandbox)"),
    param: list[str] = typer.Option([], "--param", "-p", help="Param key=value (e.g. path=/some/path)"),
    sandbox: str = typer.Option("", "--sandbox", "-s", help="Sandbox root for snapshot_to_sandbox (default: data/local/desktop_adapters/sandbox)"),
    repo_root: str = typer.Option("", "--repo-root", help="Repo root for sandbox resolution"),
) -> None:
    """Run adapter action (read-only or copy to sandbox only). No mutation of originals."""
    from workflow_dataset.desktop_adapters import run_execute, get_sandbox_root
    params: dict[str, str] = {}
    for kv in param:
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.strip()] = v.strip()
    sandbox_path = Path(sandbox).resolve() if sandbox else None
    repo_root_path = Path(repo_root).resolve() if repo_root else None
    if sandbox_path is None and repo_root_path:
        sandbox_path = get_sandbox_root(repo_root_path)
    elif sandbox_path is None:
        sandbox_path = get_sandbox_root()
    result = run_execute(
        id.strip(),
        action.strip(),
        params,
        sandbox_root=sandbox_path,
        repo_root=repo_root_path,
    )
    if result.success:
        console.print("[green]Run OK[/green]")
        for k, v in result.output.items():
            if k == "content" and isinstance(v, str) and len(v) > 500:
                console.print(f"  {k}: {v[:500]}...")
            elif k == "entries" and isinstance(v, list):
                console.print(f"  {k}: {len(v)} entries")
                for i, e in enumerate(v[:15]):
                    console.print(f"    {e}")
                if len(v) > 15:
                    console.print(f"    ... and {len(v) - 15} more")
            else:
                console.print(f"  {k}: {v}")
        if result.provenance:
            console.print("[dim]Provenance:[/dim]")
            for p in result.provenance:
                console.print(f"  {p.adapter_id}/{p.action_id} {p.outcome} {p.path_or_param}")
    else:
        console.print(f"[red]{result.message}[/red]")
        if result.provenance:
            for p in result.provenance:
                console.print(f"  [dim]{p.detail}[/dim]")
        raise typer.Exit(1)


# ----- M23D-F1 Capability discovery + approval registry -----
capabilities_group = typer.Typer(
    help="Capability discovery: scan adapters, approved paths/apps, action scopes. Local-only.")
app.add_typer(capabilities_group, name="capabilities")


@capabilities_group.command("scan")
def capabilities_scan(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Scan capability: adapters, approval registry. No heavy filesystem scan."""
    from workflow_dataset.capability_discovery import run_scan
    root = Path(repo_root).resolve() if repo_root else None
    profile = run_scan(repo_root=root)
    console.print("[bold]Capability scan[/bold]")
    console.print(f"  adapters: {len(profile.adapters_available)}")
    console.print(f"  approved_paths: {len(profile.approved_paths)}")
    console.print(f"  approved_apps: {len(profile.approved_apps)}")
    console.print(f"  action_scopes: {len(profile.action_scopes)}")
    for a in profile.adapters_available:
        ex = "real" if a.supports_real_execution else "simulate_only"
        console.print(f"  [dim]{a.adapter_id}[/dim] {ex}")


@capabilities_group.command("report")
def capabilities_report(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to path (optional)"),
) -> None:
    """Print capability profile report (adapters, approved paths/apps, action scopes)."""
    from workflow_dataset.capability_discovery import run_scan, format_profile_report
    root = Path(repo_root).resolve() if repo_root else None
    profile = run_scan(repo_root=root)
    report = format_profile_report(profile)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]Report written: {output}[/green]")
    else:
        console.print(report)


@capabilities_group.command("approvals")
def capabilities_approvals_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List approval registry (same as workflow-dataset approvals list)."""
    _approvals_list_impl(repo_root)


approvals_group = typer.Typer(help="Approval registry: list approved paths, apps, action scopes. Local file only.")
app.add_typer(approvals_group, name="approvals")


@approvals_group.command("list")
def approvals_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List approval registry: approved paths, approved apps, approved action scopes."""
    _approvals_list_impl(repo_root)


def _approvals_list_impl(repo_root: str) -> None:
    from workflow_dataset.capability_discovery import load_approval_registry, get_registry_path
    root = Path(repo_root).resolve() if repo_root else None
    path = get_registry_path(root)
    registry = load_approval_registry(root)
    console.print("[bold]Approval registry[/bold]")
    console.print(f"  [dim]Source: {path}[/dim]")
    console.print("  approved_paths:")
    for p in registry.approved_paths:
        console.print(f"    - {p}")
    if not registry.approved_paths:
        console.print("    (none)")
    console.print("  approved_apps:")
    for app in registry.approved_apps:
        console.print(f"    - {app}")
    if not registry.approved_apps:
        console.print("    (none; report uses built-in list)")
    console.print("  approved_action_scopes:")
    for s in registry.approved_action_scopes:
        console.print(f"    - {s}")
    if not registry.approved_action_scopes:
        console.print("    (none; scopes from adapter contracts)")


# ----- M23E-F1 Task demonstration capture + replay (simulate only) -----
tasks_group = typer.Typer(help="Task demonstrations: define, replay in simulate mode only. Local persistence.")
app.add_typer(tasks_group, name="tasks")


@tasks_group.command("define")
def tasks_define(
    from_file: str = typer.Option("", "--from-file", "-f", help="Load task from YAML file and save to store"),
    task_id: str = typer.Option("", "--task-id", "-t", help="Task id (required if not using --from-file)"),
    step: list[str] = typer.Option([], "--step", "-s", help="Step: adapter_id action_id param1=val1 param2=val2 (repeat for multiple steps)"),
    notes: str = typer.Option("", "--notes", "-n", help="Task-level notes"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Define a task (from file or from --task-id + --step). Saves to data/local/task_demonstrations."""
    from workflow_dataset.task_demos import TaskDefinition, TaskStep, save_task
    root = Path(repo_root).resolve() if repo_root else None
    if from_file:
        path = Path(from_file)
        if not path.exists():
            console.print(f"[red]File not found: {from_file}[/red]")
            raise typer.Exit(1)
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        steps = []
        for s in data.get("steps") or []:
            steps.append(TaskStep(
                adapter_id=str(s.get("adapter_id", "")),
                action_id=str(s.get("action_id", "")),
                params=dict(s.get("params") or {}),
                notes=str(s.get("notes") or ""),
            ))
        task = TaskDefinition(
            task_id=str(data.get("task_id", path.stem)),
            steps=steps,
            notes=str(data.get("notes") or ""),
        )
    else:
        if not task_id.strip():
            console.print("[red]Provide --task-id or --from-file[/red]")
            raise typer.Exit(1)
        steps = []
        for raw in step:
            parts = raw.split()
            if len(parts) < 2:
                continue
            adapter_id, action_id = parts[0], parts[1]
            params = {}
            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    params[k.strip()] = v.strip()
            steps.append(TaskStep(adapter_id=adapter_id, action_id=action_id, params=params))
        task = TaskDefinition(task_id=task_id.strip(), steps=steps, notes=notes)
    out_path = save_task(task, root)
    console.print(f"[green]Task saved: {task.task_id}[/green]")
    console.print(f"  [dim]{out_path}[/dim]")


@tasks_group.command("replay")
def tasks_replay(
    task_id: str = typer.Option(..., "--task-id", "-t", help="Task id to replay"),
    simulate: bool = typer.Option(True, "--simulate/--no-simulate", help="Run in simulate mode only (default: True)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Replay a task. F1: --simulate only; no real execution."""
    if not simulate:
        console.print("[red]F1: only simulate mode is supported. Use --simulate.[/red]")
        raise typer.Exit(1)
    from workflow_dataset.task_demos import replay_task_simulate, format_replay_report, get_task
    root = Path(repo_root).resolve() if repo_root else None
    task, results = replay_task_simulate(task_id, root)
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)
    console.print(format_replay_report(task, results))
    failed = sum(1 for r in results if not r.success)
    if failed:
        raise typer.Exit(1)


@tasks_group.command("list")
def tasks_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List defined task ids."""
    from workflow_dataset.task_demos import list_tasks
    root = Path(repo_root).resolve() if repo_root else None
    ids = list_tasks(root)
    console.print("[bold]Tasks[/bold]")
    for tid in ids:
        console.print(f"  - {tid}")
    if not ids:
        console.print("  (none)")


@tasks_group.command("show")
def tasks_show(
    task_id: str = typer.Option(..., "--task-id", "-t", help="Task id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show task definition (manifest)."""
    from workflow_dataset.task_demos import get_task, format_task_manifest
    root = Path(repo_root).resolve() if repo_root else None
    task = get_task(task_id, root)
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)
    console.print(format_task_manifest(task))


# ----- M23F-F1 Cross-app coordination graph (advisory only) -----
graph_group = typer.Typer(help="Coordination graph: from-task, summary, export. Advisory only; no execution.")
app.add_typer(graph_group, name="graph")


@graph_group.command("from-task")
def graph_from_task(
    task_id: str = typer.Option(..., "--task-id", "-t", help="Task id to build graph from"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    artifacts: bool = typer.Option(False, "--artifacts", help="Include advisory artifact nodes between steps"),
) -> None:
    """Build coordination graph from a task definition. Prints summary (advisory only)."""
    from workflow_dataset.task_demos import get_task
    from workflow_dataset.coordination_graph import task_definition_to_graph, format_graph_summary
    root = Path(repo_root).resolve() if repo_root else None
    task = get_task(task_id, root)
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)
    graph = task_definition_to_graph(task, include_artifact_nodes=artifacts)
    console.print(format_graph_summary(graph))


@graph_group.command("summary")
def graph_summary(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Summarize coordination graphs for all stored tasks (nodes/edges counts per task)."""
    from workflow_dataset.task_demos import list_tasks, get_task
    from workflow_dataset.coordination_graph import task_definition_to_graph
    root = Path(repo_root).resolve() if repo_root else None
    ids = list_tasks(root)
    console.print("[bold]Coordination graph summary[/bold] (advisory)")
    if not ids:
        console.print("  No tasks defined.")
        return
    for tid in ids:
        task = get_task(tid, root)
        if task:
            graph = task_definition_to_graph(task)
            console.print(f"  {tid}: nodes={len(graph.nodes)} edges={len(graph.edges)}")


@graph_group.command("export")
def graph_export(
    task_id: str = typer.Option(..., "--task-id", "-t", help="Task id"),
    output: str = typer.Option(..., "--output", "-o", help="Output path (JSON)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    artifacts: bool = typer.Option(False, "--artifacts", help="Include advisory artifact nodes"),
) -> None:
    """Export coordination graph for a task to JSON file."""
    import json
    from workflow_dataset.task_demos import get_task
    from workflow_dataset.coordination_graph import task_definition_to_graph, graph_to_dict
    root = Path(repo_root).resolve() if repo_root else None
    task = get_task(task_id, root)
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)
    graph = task_definition_to_graph(task, include_artifact_nodes=artifacts)
    data = graph_to_dict(graph)
    Path(output).write_text(json.dumps(data, indent=2), encoding="utf-8")
    console.print(f"[green]Exported: {output}[/green]")


@graph_group.command("inspect")
def graph_inspect(
    task_id: str = typer.Option(..., "--task-id", "-t", help="Task id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Inspect coordination graph for a task (same as graph from-task, default options)."""
    from workflow_dataset.task_demos import get_task
    from workflow_dataset.coordination_graph import task_definition_to_graph, format_graph_summary
    root = Path(repo_root).resolve() if repo_root else None
    task = get_task(task_id, root)
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)
    graph = task_definition_to_graph(task)
    console.print(format_graph_summary(graph))


# ----- M23I Desktop benchmark + trusted automation harness -----
desktop_bench_group = typer.Typer(
    help="Desktop task benchmark: list, run, run-suite, trusted-actions, board, compare, report, smoke.",
)
app.add_typer(desktop_bench_group, name="desktop-bench")


@desktop_bench_group.command("list")
def desktop_bench_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List benchmark case ids."""
    from workflow_dataset.desktop_bench import list_cases
    root = Path(repo_root).resolve() if repo_root else None
    ids = list_cases(root)
    console.print("[bold]Desktop benchmark cases[/bold]")
    for i in ids:
        console.print(f"  {i}")


@desktop_bench_group.command("run")
def desktop_bench_run(
    id: str = typer.Option(..., "--id", "-i", help="Benchmark case id"),
    mode: str = typer.Option("simulate", "--mode", "-m", help="simulate | real"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Run one benchmark case. Mode must be simulate or real (no silent fallback)."""
    from workflow_dataset.desktop_bench import run_benchmark
    root = Path(repo_root).resolve() if repo_root else None
    result = run_benchmark(id, mode, repo_root=root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Run {result.get('run_id')} outcome={result.get('outcome')} mode={result.get('mode')}[/green]")
    console.print(f"  run_path: {result.get('run_path')}")
    if result.get("errors"):
        for e in result["errors"]:
            console.print(f"  [red]{e}[/red]")


@desktop_bench_group.command("run-suite")
def desktop_bench_run_suite(
    suite: str = typer.Option(..., "--suite", "-s", help="Suite name (e.g. desktop_bridge_core)"),
    mode: str = typer.Option("simulate", "--mode", "-m", help="simulate | real"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Run a benchmark suite."""
    from workflow_dataset.desktop_bench import run_suite
    root = Path(repo_root).resolve() if repo_root else None
    result = run_suite(suite, mode, repo_root=root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Suite {result.get('suite')} run_id={result.get('run_id')} aggregate={result.get('aggregate_outcome')}[/green]")
    console.print(f"  run_path: {result.get('run_path')}")


@desktop_bench_group.command("trusted-actions")
def desktop_bench_trusted_actions(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List actions currently approved for real execution (narrow safe subset)."""
    from workflow_dataset.desktop_bench import list_trusted_actions_report
    root = Path(repo_root).resolve() if repo_root else None
    console.print(list_trusted_actions_report(root))


@desktop_bench_group.command("board")
def desktop_bench_board(
    suite: str = typer.Option("", "--suite", "-s", help="Filter by suite name"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show desktop benchmark board (latest run, pass/fail, trust status, next action)."""
    from workflow_dataset.desktop_bench import board_report, format_board_report
    root = Path(repo_root).resolve() if repo_root else None
    report = board_report(suite_name=suite or "", limit_runs=10, root=root)
    console.print(format_board_report(report))


@desktop_bench_group.command("compare")
def desktop_bench_compare(
    run: list[str] = typer.Option(..., "--run", "-r", help="Two run ids (e.g. --run latest --run previous)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Compare two runs (regression, outcome, trust status)."""
    from workflow_dataset.desktop_bench import compare_runs, list_runs as db_list_runs
    root = Path(repo_root).resolve() if repo_root else None
    if len(run) < 2:
        console.print("[red]Provide two --run ids (e.g. --run latest --run previous)[/red]")
        raise typer.Exit(1)
    run_a, run_b = run[0], run[1]
    runs = db_list_runs(limit=2, root=root)
    if run_a == "latest" and runs:
        run_a = runs[0].get("run_id", run_a)
    elif run_a == "previous" and len(runs) >= 2:
        run_a = runs[1].get("run_id", run_a)
    if run_b == "latest" and runs:
        run_b = runs[0].get("run_id", run_b)
    elif run_b == "previous" and len(runs) >= 2:
        run_b = runs[1].get("run_id", run_b)
    comp = compare_runs(run_a, run_b, root=root)
    if comp.get("error"):
        console.print(f"[red]{comp['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"Run A: {comp['run_a']} outcome={comp['outcome_a']} trust={comp['trust_status_a']}")
    console.print(f"Run B: {comp['run_b']} outcome={comp['outcome_b']} trust={comp['trust_status_b']}")
    console.print(f"Regression: {comp.get('regression_detected')}  Recommendation: {comp.get('recommendation')}")


@desktop_bench_group.command("report")
def desktop_bench_report(
    suite: str = typer.Option(..., "--suite", "-s", help="Suite name"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Report for a suite (latest run summary)."""
    from workflow_dataset.desktop_bench import board_report, format_board_report
    root = Path(repo_root).resolve() if repo_root else None
    report = board_report(suite_name=suite, limit_runs=5, root=root)
    console.print(format_board_report(report))


@desktop_bench_group.command("smoke")
def desktop_bench_smoke(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Smoke check: adapters available, approvals configured, harness healthy, trusted subset ready."""
    from workflow_dataset.desktop_adapters import list_adapters
    from workflow_dataset.desktop_bench import get_trusted_real_actions, list_cases, run_benchmark
    from workflow_dataset.capability_discovery.approval_registry import get_registry_path
    root = Path(repo_root).resolve() if repo_root else None
    console.print("[bold]Desktop benchmark smoke[/bold]")
    adapters = list_adapters()
    console.print(f"  adapters: {len(adapters)}")
    reg_path = get_registry_path(root)
    console.print(f"  approvals file: {'present' if reg_path.exists() else 'missing'}")
    cases = list_cases(root)
    console.print(f"  benchmark cases: {len(cases)}")
    trusted = get_trusted_real_actions(root)
    console.print(f"  trusted real actions: {len(trusted.get('trusted_actions', []))}  ready_for_real: {trusted.get('ready_for_real')}")
    if cases:
        r = run_benchmark(cases[0], "simulate", repo_root=root)
        if r.get("error"):
            console.print(f"  [red]harness: error — {r['error']}[/red]")
        else:
            console.print(f"  harness: ok (run {r.get('run_id')} outcome={r.get('outcome')})")
    console.print("[green]Smoke complete.[/green]")


@desktop_bench_group.command("seed")
def desktop_bench_seed(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Seed default benchmark cases and desktop_bridge_core suite."""
    from workflow_dataset.desktop_bench.seed_cases import seed_default_cases, seed_default_suite
    root = Path(repo_root).resolve() if repo_root else None
    paths = seed_default_cases(root)
    suite_path = seed_default_suite(root)
    console.print(f"[green]Seeded {len(paths)} cases and suite {suite_path.name}[/green]")


# ----- M23J Personal job packs + specialization memory -----
jobs_group = typer.Typer(
    help="Personal job packs: list, show, run (simulate/real), report, diagnostics, specialization.",
)
app.add_typer(jobs_group, name="jobs")


@jobs_group.command("list")
def jobs_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List job pack ids."""
    from workflow_dataset.job_packs import list_job_packs
    root = Path(repo_root).resolve() if repo_root else None
    ids = list_job_packs(root)
    console.print("[bold]Job packs[/bold]")
    for i in ids:
        console.print(f"  {i}")


@jobs_group.command("show")
def jobs_show(
    id: str = typer.Option(..., "--id", "-i", help="Job pack id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show job pack details, specialization summary, and last run status."""
    from workflow_dataset.job_packs import get_job_pack, load_specialization
    root = Path(repo_root).resolve() if repo_root else None
    job = get_job_pack(id, root)
    if not job:
        console.print(f"[red]Job pack not found: {id}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{job.title}[/bold] ({job.job_pack_id})")
    console.print(f"  description: {job.description or '—'}")
    console.print(f"  category: {job.category or '—'}")
    console.print(f"  source: {job.source.kind}={job.source.ref}" if job.source else "  source: —")
    console.print(f"  trust_level: {job.trust_level}  real_mode_eligibility: {job.real_mode_eligibility}")
    spec = load_specialization(id, root)
    console.print("  specialization: preferred_params=" + str(list(spec.preferred_params.keys()) or "[]"))
    if spec.last_successful_run:
        console.print(f"  last_successful_run: {spec.last_successful_run.get('run_id')} {spec.last_successful_run.get('timestamp')}")


@jobs_group.command("run")
def jobs_run(
    id: str = typer.Option(..., "--id", "-i", help="Job pack id"),
    mode: str = typer.Option("simulate", "--mode", "-m", help="simulate | real"),
    param: list[str] = typer.Option([], "--param", "-p", help="Param key=value (e.g. path=data/local)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    update_specialization: bool = typer.Option(False, "--update-specialization", help="On success, update specialization from this run"),
) -> None:
    """Run job pack. Preview is shown before execution; no hidden auto-run."""
    from workflow_dataset.job_packs import run_job, preview_job
    root = Path(repo_root).resolve() if repo_root else None
    params = {}
    for kv in param:
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.strip()] = v.strip()
    preview = preview_job(id, mode, params, root)
    if preview.get("error"):
        console.print(f"[red]{preview['error']}[/red]")
        raise typer.Exit(1)
    console.print("[dim]Resolved params: " + str(preview.get("resolved_params", {})) + "[/dim]")
    console.print("[dim]Policy: " + ("allowed" if preview.get("policy_allowed") else preview.get("policy_message", "")) + "[/dim]")
    if not preview.get("policy_allowed"):
        console.print(f"[red]{preview.get('policy_message')}[/red]")
        raise typer.Exit(1)
    result = run_job(id, mode, params, root, update_specialization_on_success=update_specialization)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Job {result.get('job_pack_id')} outcome={result.get('outcome')} run_id={result.get('run_id')}[/green]")
    if result.get("errors"):
        for e in result["errors"]:
            console.print(f"  [red]{e}[/red]")


@jobs_group.command("report")
def jobs_report(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Job packs summary: total, simulate-only, trusted, approval-blocked, recent successful."""
    from workflow_dataset.job_packs import job_packs_report, format_job_packs_report
    root = Path(repo_root).resolve() if repo_root else None
    report = job_packs_report(root)
    console.print(format_job_packs_report(report))


@jobs_group.command("diagnostics")
def jobs_diagnostics(
    id: str = typer.Option(..., "--id", "-i", help="Job pack id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Per-job diagnostics: trust level, policy for simulate/real, specialization summary."""
    from workflow_dataset.job_packs import job_diagnostics
    root = Path(repo_root).resolve() if repo_root else None
    d = job_diagnostics(id, root)
    if d.get("error"):
        console.print(f"[red]{d['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{d.get('title')}[/bold] ({d.get('job_pack_id')})")
    console.print(f"  trust_level: {d.get('trust_level')}  real_mode_eligibility: {d.get('real_mode_eligibility')}")
    console.print(f"  policy_simulate: allowed={d.get('policy_simulate', {}).get('allowed')}  {d.get('policy_simulate', {}).get('message')}")
    console.print(f"  policy_real: allowed={d.get('policy_real', {}).get('allowed')}  {d.get('policy_real', {}).get('message')}")


@jobs_group.command("specialization-show")
def jobs_specialization_show(
    id: str = typer.Option(..., "--id", "-i", help="Job pack id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show specialization memory for a job pack."""
    from workflow_dataset.job_packs import load_specialization
    root = Path(repo_root).resolve() if repo_root else None
    spec = load_specialization(id, root)
    console.print(f"[bold]Specialization[/bold] ({id})")
    console.print("  preferred_params: " + str(spec.preferred_params))
    console.print("  last_successful_run: " + str(spec.last_successful_run))
    console.print("  operator_notes: " + (spec.operator_notes or "—"))
    console.print("  updated_at: " + (spec.updated_at or "—"))


@jobs_group.command("save-as-preferred")
def jobs_save_as_preferred(
    id: str = typer.Option(..., "--id", "-i", help="Job pack id"),
    param: list[str] = typer.Option(..., "--param", "-p", help="Param key=value to save as preferred"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Save current params as preferred for this job (explicit operator action)."""
    from workflow_dataset.job_packs import save_as_preferred
    root = Path(repo_root).resolve() if repo_root else None
    params = {}
    for kv in param:
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.strip()] = v.strip()
    save_as_preferred(id, params, root)
    console.print(f"[green]Saved preferred params for {id}[/green]")


@jobs_group.command("seed")
def jobs_seed(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Seed example job packs (weekly_status_from_notes, replay_cli_demo)."""
    from workflow_dataset.job_packs.seed_jobs import seed_example_job_pack, seed_task_demo_job_pack
    from workflow_dataset.desktop_bench.seed_cases import seed_default_cases
    root = Path(repo_root).resolve() if repo_root else None
    seed_default_cases(root)  # ensure benchmark case exists
    p1 = seed_example_job_pack(root)
    p2 = seed_task_demo_job_pack(root)
    console.print(f"[green]Seeded job packs: {p1.name}, {p2.name}[/green]")


# ----- M23K Workday copilot -----
copilot_group = typer.Typer(
    help="Operator-approved workday copilot: recommend, plan, run, reminders, report.",
)
app.add_typer(copilot_group, name="copilot")


@copilot_group.command("recommend")
def copilot_recommend(
    limit: int = typer.Option(15, "--limit", "-n", help="Max recommendations"),
    context: str = typer.Option("", "--context", "-c", help="Use context snapshot: 'latest' for context-aware why-now"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show recommended jobs (recent success, trusted, blocked). Use --context latest for why-now evidence."""
    from workflow_dataset.copilot.recommendations import recommend_jobs
    root = Path(repo_root).resolve() if repo_root else None
    context_snapshot = context if context == "latest" else None
    recs = recommend_jobs(root, limit=limit, context_snapshot=context_snapshot)
    console.print("[bold]Copilot recommendations[/bold]")
    for r in recs:
        mode = r.get("mode_allowed", "")
        block = " [red]blocked[/red]" if r.get("blocking_issues") else ""
        console.print(f"  {r.get('job_pack_id')}  reason={r.get('reason')}  mode={mode}{block}")
        if r.get("why_now_evidence"):
            for e in r["why_now_evidence"][:3]:
                console.print(f"    [dim]why now: {e}[/dim]")
        if r.get("blocking_issues"):
            for b in r["blocking_issues"]:
                console.print(f"    [dim]{b}[/dim]")


@copilot_group.command("plan")
def copilot_plan(
    job: str = typer.Option("", "--job", "-j", help="Job pack id for plan"),
    routine: str = typer.Option("", "--routine", "-r", help="Routine id for plan"),
    mode: str = typer.Option("simulate", "--mode", "-m", help="simulate | real"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Preview plan (jobs, order, mode, approvals, blocked). No execution."""
    from workflow_dataset.copilot.plan import build_plan_for_job, build_plan_for_routine
    root = Path(repo_root).resolve() if repo_root else None
    if job and routine:
        console.print("[red]Use --job or --routine, not both.[/red]")
        raise typer.Exit(1)
    if job:
        plan = build_plan_for_job(job, mode, {}, root)
    elif routine:
        plan = build_plan_for_routine(routine, mode, root)
    else:
        console.print("[red]Provide --job or --routine.[/red]")
        raise typer.Exit(1)
    if not plan:
        console.print("[red]Plan not found (job or routine missing).[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]Plan {plan.plan_id}[/bold]  mode={plan.mode}")
    console.print("  job_pack_ids: " + str(plan.job_pack_ids))
    console.print("  blocked: " + str(plan.blocked))
    if plan.blocked_reasons:
        for k, v in plan.blocked_reasons.items():
            console.print(f"    [red]{k}: {v}[/red]")
    console.print("[dim]Run with: copilot run --job ... or --routine ... --mode " + mode + "[/dim]")


@copilot_group.command("run")
def copilot_run(
    job: str = typer.Option("", "--job", "-j", help="Job pack id"),
    routine: str = typer.Option("", "--routine", "-r", help="Routine id"),
    mode: str = typer.Option("simulate", "--mode", "-m", help="simulate | real"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Run plan for job or routine. Builds plan then executes; records plan run."""
    from workflow_dataset.copilot.plan import build_plan_for_job, build_plan_for_routine
    from workflow_dataset.copilot.run import run_plan
    root = Path(repo_root).resolve() if repo_root else None
    if job and routine:
        console.print("[red]Use --job or --routine, not both.[/red]")
        raise typer.Exit(1)
    if job:
        plan = build_plan_for_job(job, mode, {}, root)
    elif routine:
        plan = build_plan_for_routine(routine, mode, root)
    else:
        console.print("[red]Provide --job or --routine.[/red]")
        raise typer.Exit(1)
    if not plan:
        console.print("[red]Plan not found.[/red]")
        raise typer.Exit(1)
    result = run_plan(plan, root, stop_on_first_blocked=True, continue_on_blocked=False)
    if result.get("errors"):
        for e in result["errors"]:
            console.print(f"[red]{e}[/red]")
    console.print(f"[green]Plan run {result.get('plan_run_id')}  executed={result.get('executed_count')}  blocked={result.get('blocked_count')}[/green]")
    console.print("  run_path: " + str(result.get("run_path", "")))


@copilot_group.command("reminders")
def copilot_reminders(
    action: str = typer.Argument("list", help="list | add | due"),
    routine: str = typer.Option("", "--routine", "-r", help="Routine id (for add)"),
    job: str = typer.Option("", "--job", "-j", help="Job pack id (for add)"),
    due_at: str = typer.Option("", "--due-at", help="Due time/context (for add)"),
    title: str = typer.Option("", "--title", "-t", help="Reminder title (for add)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List reminders, add reminder, or show due. No auto-run."""
    from workflow_dataset.copilot.reminders import list_reminders, add_reminder, reminders_due
    root = Path(repo_root).resolve() if repo_root else None
    if action == "list":
        rems = list_reminders(root)
        console.print("[bold]Reminders[/bold]")
        for r in rems:
            console.print(f"  {r.get('reminder_id')}  {r.get('title')}  due={r.get('due_at')}  routine={r.get('routine_id')} job={r.get('job_pack_id')}")
    elif action == "add":
        if not routine and not job:
            console.print("[red]Provide --routine or --job.[/red]")
            raise typer.Exit(1)
        entry = add_reminder(routine_id=routine or None, job_pack_id=job or None, due_at=due_at, title=title, repo_root=root)
        console.print(f"[green]Added reminder {entry.get('reminder_id')}[/green]")
    elif action == "due":
        rems = reminders_due(root)
        console.print("[bold]Reminders (due / upcoming)[/bold]")
        for r in rems:
            console.print(f"  {r.get('title')}  due={r.get('due_at')}  routine={r.get('routine_id')} job={r.get('job_pack_id')}")
    else:
        console.print("[red]Use list, add, or due.[/red]")
        raise typer.Exit(1)


@copilot_group.command("explain-recommendation")
def copilot_explain_recommendation(
    id: str = typer.Option("", "--id", "-i", help="Recommendation id (e.g. rec_weekly_status_0)"),
    job: str = typer.Option("", "--job", "-j", help="Or explain by job pack id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Explain why a recommendation is relevant now (context + triggers)."""
    from workflow_dataset.context.recommendation_explain import explain_recommendation, explain_recommendation_by_job
    root = Path(repo_root).resolve() if repo_root else None
    if job:
        out = explain_recommendation_by_job(job, root)
    elif id:
        out = explain_recommendation(id, root)
    else:
        console.print("[red]Provide --id or --job.[/red]")
        raise typer.Exit(1)
    if out.get("error"):
        console.print(f"[red]{out['error']}[/red]")
        raise typer.Exit(1)
    console.print(out.get("explanation_md", ""))


@copilot_group.command("report")
def copilot_report_cmd(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Copilot report: recommendations, routines, plan runs, reminders."""
    from workflow_dataset.copilot.report import copilot_report, format_copilot_report
    root = Path(repo_root).resolve() if repo_root else None
    report = copilot_report(root)
    console.print(format_copilot_report(report))


# ----- M23L Context / work state -----
context_group = typer.Typer(
    help="Work state and context: refresh, show, compare. No background monitoring.",
)
app.add_typer(context_group, name="context")


@context_group.command("refresh")
def context_refresh(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Build and persist current work-state snapshot. Explicit; no daemon."""
    from workflow_dataset.context.work_state import build_work_state
    from workflow_dataset.context.snapshot import save_snapshot
    root = Path(repo_root).resolve() if repo_root else None
    state = build_work_state(root)
    path = save_snapshot(state, root)
    console.print(f"[green]Context snapshot saved: {state.snapshot_id}[/green]")
    console.print(f"  path: {path}")


@context_group.command("show")
def context_show(
    snapshot: str = typer.Option("latest", "--snapshot", "-s", help="Snapshot id or 'latest'"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show work-state summary for a snapshot."""
    from workflow_dataset.context.snapshot import load_snapshot
    from workflow_dataset.context.work_state import work_state_summary_md
    root = Path(repo_root).resolve() if repo_root else None
    ws = load_snapshot(snapshot, root)
    if not ws:
        console.print(f"[red]Snapshot not found: {snapshot}[/red]")
        raise typer.Exit(1)
    console.print(work_state_summary_md(ws))


@context_group.command("compare")
def context_compare(
    latest: bool = typer.Option(True, "--latest/--no-latest", help="Use latest as current"),
    previous: bool = typer.Option(True, "--previous/--no-previous", help="Use previous as baseline"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Compare latest vs previous snapshot (drift)."""
    from workflow_dataset.context.drift import load_latest_and_previous, compare_snapshots
    root = Path(repo_root).resolve() if repo_root else None
    latest_ws, previous_ws = load_latest_and_previous(root)
    if not latest_ws:
        console.print("[red]No latest snapshot. Run context refresh first.[/red]")
        raise typer.Exit(1)
    if not previous_ws:
        console.print("[yellow]No previous snapshot; showing latest summary only.[/yellow]")
        from workflow_dataset.context.work_state import work_state_summary_md
        console.print(work_state_summary_md(latest_ws))
        return
    drift = compare_snapshots(previous_ws, latest_ws)
    console.print("[bold]Context drift (previous → latest)[/bold]")
    for line in drift.summary:
        console.print(f"  {line}")


# ----- M23M Corrections -----
corrections_group = typer.Typer(
    help="Operator correction loop: add, list, propose-updates, preview/apply/reject, report.",
)
app.add_typer(corrections_group, name="corrections")


@corrections_group.command("add")
def corrections_add(
    source: str = typer.Option(..., "--source", "-s", help="recommendation | job | plan | routine | artifact | benchmark_result"),
    id: str = typer.Option(..., "--id", help="Source reference id (e.g. rec_xxx, job_pack_id, plan_id)"),
    category: str = typer.Option(..., "--category", "-c", help="e.g. bad_job_parameter_default, output_style_correction"),
    action: str = typer.Option("corrected", "--action", "-a", help="rejected | corrected | accepted_with_note | skipped | deferred"),
    original: str = typer.Option("", "--original", help="Original value (JSON or text)"),
    corrected: str = typer.Option("", "--corrected", help="Corrected value (JSON or text)"),
    reason: str = typer.Option("", "--reason", "-r", help="Correction reason"),
    severity: str = typer.Option("medium", "--severity", help="low | medium | high"),
    notes: str = typer.Option("", "--notes", "-n"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Record an operator correction. Use corrections propose-updates to derive learning updates."""
    import json
    from workflow_dataset.corrections.capture import add_correction
    root = Path(repo_root).resolve() if repo_root else None
    orig_val = original
    corr_val = corrected
    if original.strip().startswith("{") or original.strip().startswith("["):
        try:
            orig_val = json.loads(original)
        except Exception:
            pass
    if corrected.strip().startswith("{") or corrected.strip().startswith("["):
        try:
            corr_val = json.loads(corrected)
        except Exception:
            pass
    ev = add_correction(
        source_type=source,
        source_reference_id=id,
        correction_category=category,
        operator_action=action,
        original_value=orig_val,
        corrected_value=corr_val,
        correction_reason=reason,
        severity=severity,
        notes=notes,
        repo_root=root,
    )
    console.print(f"[green]Correction recorded: {ev.correction_id}[/green]")


@corrections_group.command("list")
def corrections_list(
    limit: int = typer.Option(20, "--limit", "-n"),
    source: str = typer.Option("", "--source", help="Filter by source type"),
    category: str = typer.Option("", "--category", help="Filter by category"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """List correction events."""
    from workflow_dataset.corrections.store import list_corrections
    root = Path(repo_root).resolve() if repo_root else None
    corrections = list_corrections(limit=limit, repo_root=root, source_type=source or None, category=category or None)
    console.print("[bold]Corrections[/bold]")
    for c in corrections:
        console.print(f"  {c.correction_id}  source={c.source_type}  ref={c.source_reference_id}  category={c.correction_category}  eligible={c.eligible_for_memory_update}")


@corrections_group.command("show")
def corrections_show(
    id: str = typer.Option(..., "--id", "-i", help="Correction id"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Show a single correction event."""
    from workflow_dataset.corrections.store import get_correction
    root = Path(repo_root).resolve() if repo_root else None
    c = get_correction(id, root)
    if not c:
        console.print(f"[red]Correction not found: {id}[/red]")
        raise typer.Exit(1)
    console.print(c.to_dict())


@corrections_group.command("propose-updates")
def corrections_propose_updates(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Propose learning updates from eligible corrections. Does not apply."""
    from workflow_dataset.corrections.updates import list_proposed_updates
    root = Path(repo_root).resolve() if repo_root else None
    proposed = list_proposed_updates(root)
    console.print(f"[bold]Proposed updates: {len(proposed)}[/bold]")
    for p in proposed:
        console.print(f"  {p.update_id}  {p.target_type}:{p.target_id}  risk={p.risk_level}")


@corrections_group.command("preview-update")
def corrections_preview_update(
    id: str = typer.Option(..., "--id", "-i", help="Update id"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Preview what would change if update is applied."""
    from workflow_dataset.corrections.updates import preview_update
    root = Path(repo_root).resolve() if repo_root else None
    out = preview_update(id, root)
    if out.get("error"):
        console.print(f"[red]{out['error']}[/red]")
        raise typer.Exit(1)
    console.print("[bold]Update preview[/bold]")
    console.print(f"  target: {out.get('target_type')}:{out.get('target_id')}")
    console.print(f"  before: {out.get('before_value')}")
    console.print(f"  after:  {out.get('after_value')}")
    console.print(f"  risk: {out.get('risk_level')}  reversible: {out.get('reversible')}")


@corrections_group.command("apply-update")
def corrections_apply_update(
    id: str = typer.Option(..., "--id", "-i", help="Update id"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Apply a proposed update. Records update for revert."""
    from workflow_dataset.corrections.updates import apply_update
    root = Path(repo_root).resolve() if repo_root else None
    out = apply_update(id, root)
    if out.get("error"):
        console.print(f"[red]{out['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Applied: {out.get('applied')}  target: {out.get('target')}[/green]")


@corrections_group.command("reject-update")
def corrections_reject_update(
    id: str = typer.Option(..., "--id", "-i", help="Update id (record only; no state change)"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Reject a proposed update (no apply). Optionally remove from proposed list."""
    from workflow_dataset.corrections.config import get_proposed_dir
    root = Path(repo_root).resolve() if repo_root else None
    path = get_proposed_dir(root) / f"{id}.json"
    if path.exists():
        path.unlink()
        console.print(f"[yellow]Removed proposed update: {id}[/yellow]")
    else:
        console.print(f"[dim]No proposed update file for {id}[/dim]")


@corrections_group.command("revert-update")
def corrections_revert_update(
    id: str = typer.Option(..., "--id", "-i", help="Update id (must be applied)"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Revert an applied update. Restores before state."""
    from workflow_dataset.corrections.updates import revert_update
    root = Path(repo_root).resolve() if repo_root else None
    out = revert_update(id, root)
    if out.get("error"):
        console.print(f"[red]{out['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Reverted: {out.get('reverted')}  target: {out.get('target')}[/green]")


@corrections_group.command("report")
def corrections_report_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Corrections impact report: recent, proposed, applied, reverted, most corrected."""
    from workflow_dataset.corrections.report import corrections_report, format_corrections_report
    root = Path(repo_root).resolve() if repo_root else None
    report = corrections_report(root)
    console.print(format_corrections_report(report))


@edge_group.command("readiness")
def edge_readiness(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    output: str = typer.Option("", "--output", "-o", help="Write full report to path (optional)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Run readiness checks and print summary. Use --output to write full edge readiness report."""
    from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
    from workflow_dataset.edge.report import generate_edge_readiness_report
    root = Path(repo_root) if repo_root else None
    checks = run_readiness_checks(repo_root=root, config_path=config)
    summary = checks_summary(checks)
    console.print("[bold]Edge readiness[/bold]")
    console.print(f"  ready: {summary.get('ready')}  passed: {summary.get('passed')}/{len(checks)}  failed_required: {summary.get('failed_required')}  optional_disabled: {summary.get('optional_disabled')}")
    for c in checks:
        status = "[green]ok[/green]" if c.get("passed") else "[red]FAIL[/red]"
        opt = " (optional)" if c.get("optional") else ""
        console.print(f"  {c.get('check_id')}: {status}{opt} — {c.get('message')}")
    if output:
        path = generate_edge_readiness_report(output_path=Path(output), repo_root=root, config_path=config)
        console.print(f"[green]Report: {path}[/green]")


@edge_group.command("report")
def edge_report(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge/edge_readiness_report.md)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Generate full edge readiness report (profile, checks, failure modes, missing deps, workflow matrix)."""
    from workflow_dataset.edge.report import generate_edge_readiness_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    path = generate_edge_readiness_report(output_path=out_path, repo_root=root, config_path=config)
    console.print(f"[green]Edge readiness report: {path}[/green]")


@edge_group.command("missing-deps")
def edge_missing_deps(
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge/missing_dependency_report.md)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Generate missing dependency report (required/optional ref, path status)."""
    from workflow_dataset.edge.report import generate_missing_dependency_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    path = generate_missing_dependency_report(output_path=out_path, repo_root=root)
    console.print(f"[green]Missing dependency report: {path}[/green]")


@edge_group.command("workflow-matrix")
def edge_workflow_matrix(
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge/supported_workflow_matrix.md)"),
    format: str = typer.Option("markdown", "--format", "-f", help="markdown | json"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Generate supported workflow matrix (workflow, description, required/optional files)."""
    from workflow_dataset.edge.report import generate_workflow_matrix_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    path = generate_workflow_matrix_report(output_path=out_path, repo_root=root, format=format)
    console.print(f"[green]Workflow matrix: {path}[/green]")


@edge_group.command("profile")
def edge_profile_cmd(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    tier: str = typer.Option("", "--tier", "-t", help="Tier: dev_full, local_standard, constrained_edge, minimal_eval"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Print edge profile summary (runtime, storage, model assumptions, workflows). Use --tier for tier-scoped profile."""
    from workflow_dataset.edge.profile import build_edge_profile
    root = Path(repo_root) if repo_root else None
    tier_opt = tier.strip() or None
    profile = build_edge_profile(repo_root=root, config_path=config, tier=tier_opt)
    console.print("[bold]Edge profile summary[/bold]")
    if profile.get("tier"):
        console.print(f"  Tier: {profile.get('tier')} — {profile.get('tier_description', '')}")
        console.print(f"  LLM requirement: {profile.get('tier_llm_requirement', '')}")
    console.print(f"  Repo root: {profile.get('repo_root')}")
    console.print(f"  Python: {profile.get('runtime_requirements', {}).get('python_version_min')} (recommended: {profile.get('runtime_requirements', {}).get('python_version_recommended')})")
    console.print(f"  Supported workflows: {', '.join(profile.get('supported_workflows', []))}")
    console.print(f"  Sandbox paths: {len(profile.get('sandbox_path_assumptions', {}).get('paths', []))}")
    if profile.get("workflow_availability"):
        console.print("[bold]Workflow availability[/bold]")
        for wa in profile["workflow_availability"]:
            console.print(f"  {wa.get('workflow')}: {wa.get('status')} — {wa.get('reason', '')[:50]}")


@edge_group.command("matrix")
def edge_matrix(
    tier: str = typer.Option("", "--tier", "-t", help="Tier (dev_full, local_standard, constrained_edge, minimal_eval); omit for all tiers"),
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge)"),
    format: str = typer.Option("markdown", "--format", "-f", help="markdown | json"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Generate workflow support matrix by tier (supported/degraded/unavailable, reason, fallback)."""
    from workflow_dataset.edge.report import generate_tier_matrix_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    tier_opt = tier.strip() or None
    path = generate_tier_matrix_report(output_path=out_path, repo_root=root, tier=tier_opt, format=format)
    console.print(f"[green]Workflow matrix: {path}[/green]")


@edge_group.command("compare")
def edge_compare(
    tier: str = typer.Option("local_standard", "--tier", "-t", help="First tier"),
    tier_b: str = typer.Option("constrained_edge", "--tier-b", help="Second tier"),
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge/tier_compare.md)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Compare two edge tiers (workflow status diff, paths diff, LLM requirement)."""
    from workflow_dataset.edge.report import generate_compare_report, compare_tiers
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    path = generate_compare_report(output_path=out_path, repo_root=root, tier_a=tier.strip(), tier_b=tier_b.strip())
    diff = compare_tiers(tier.strip(), tier_b.strip(), repo_root=root)
    if diff.get("error"):
        console.print(f"[red]{diff['error']}[/red]")
    else:
        console.print(f"[green]Tier compare: {path}[/green]")
        ta, tb = diff.get("tier_a", ""), diff.get("tier_b", "")
        for w in diff.get("workflow_status_diff", [])[:5]:
            console.print(f"  {w.get('workflow')}: {ta}={w.get(ta)} → {tb}={w.get(tb)}")


@edge_group.command("smoke-check")
def edge_smoke_check(
    tier: str = typer.Option("local_standard", "--tier", "-t", help="Tier to smoke-check"),
    workflow: list[str] = typer.Option([], "--workflow", "-w", help="Workflow(s) to test (default: weekly_status, status_action_bundle)"),
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    output: str = typer.Option("", "--output", "-o", help="Report path (default: data/local/edge/smoke_check_report.md)"),
    no_demo: bool = typer.Option(False, "--no-demo", help="Only run readiness checks, skip workflow demo runs"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Run lightweight smoke check for a tier: readiness + optional workflow demo runs. Reports pass/fail/skipped."""
    from workflow_dataset.edge.smoke import run_smoke_check
    from workflow_dataset.edge.report import generate_smoke_check_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    workflows = [w.strip() for w in workflow if w.strip()] or None
    result = run_smoke_check(
        tier=tier.strip(),
        workflows=workflows,
        repo_root=root,
        config_path=config,
        run_demo=not no_demo,
    )
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    path = generate_smoke_check_report(smoke_result=result, output_path=out_path, repo_root=root)
    console.print(f"[green]Smoke check report: {path}[/green]")
    console.print(f"  Overall: {'PASS' if result.get('overall_pass') else 'FAIL'}  passed={result.get('passed')}  failed={result.get('failed')}  skipped={result.get('skipped')}")
    for r in result.get("workflow_results") or []:
        st = r.get("status", "?")
        color = "green" if st == "pass" else "red" if st == "fail" else "dim"
        console.print(f"  [bold]{r.get('workflow')}[/bold]: [{color}]{st}[/{color}] — {r.get('message', '')[:50]}")


@edge_group.command("degraded-report")
def edge_degraded_report(
    tier: str = typer.Option("", "--tier", "-t", help="Tier (omit for all tiers with degraded workflows)"),
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge/degraded_workflows_report.md)"),
    format: str = typer.Option("markdown", "--format", "-f", help="markdown | json"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Report degraded workflows by tier: why partial, what is missing, what fallback is available."""
    from workflow_dataset.edge.report import generate_degraded_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    tier_opt = tier.strip() or None
    path = generate_degraded_report(output_path=out_path, repo_root=root, tier=tier_opt, format=format)
    console.print(f"[green]Degraded report: {path}[/green]")


@edge_group.command("package-report")
def edge_package_report(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    tier: str = typer.Option("", "--tier", "-t", help="Tier for tier-scoped packaging metadata (e.g. local_standard)"),
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge/edge_package_report.md or _<tier>.md)"),
    format: str = typer.Option("markdown", "--format", "-f", help="markdown | json"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Generate edge packaging/readiness metadata for deployment or appliance. Use --tier for tier-scoped report."""
    from workflow_dataset.edge.report import generate_package_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    tier_opt = tier.strip() or None
    path = generate_package_report(output_path=out_path, repo_root=root, config_path=config, tier=tier_opt, format=format)
    console.print(f"[green]Edge package report: {path}[/green]")


@edge_group.command("check-now")
def edge_check_now(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Run readiness checks, record a snapshot to history, and optionally suggest drift-report. Operator-started; no daemon."""
    from workflow_dataset.edge.history import record_readiness_snapshot
    root = Path(repo_root) if repo_root else None
    snapshot = record_readiness_snapshot(repo_root=root, config_path=config)
    path = snapshot.get("_path") or snapshot.get("_latest_path", "")
    console.print(f"[green]Snapshot recorded: {path}[/green]")
    console.print(f"  ready: {snapshot.get('ready')}  passed: {snapshot.get('summary', {}).get('passed')}  failed_required: {snapshot.get('summary', {}).get('failed_required')}")
    console.print("  Next: run [bold]workflow-dataset edge drift-report[/bold] to compare with previous run.")


@edge_group.command("drift-report")
def edge_drift_report(
    config: str = typer.Option("configs/settings.yaml", "--config", "-c"),
    output: str = typer.Option("", "--output", "-o", help="Output path (default: data/local/edge/readiness_drift_report.md)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Compare current readiness to last recorded snapshot; write drift report (what got worse, improved, next command)."""
    from workflow_dataset.edge.drift import generate_drift_report
    root = Path(repo_root) if repo_root else None
    out_path = Path(output) if output else None
    path = generate_drift_report(output_path=out_path, repo_root=root, config_path=config)
    console.print(f"[green]Drift report: {path}[/green]")


@edge_group.command("schedule-checks")
def edge_schedule_checks(
    interval_hours: float = typer.Option(24.0, "--interval-hours", help="Suggested interval in hours (e.g. 24); no daemon — use cron to run check-now"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Write a schedule marker (data/local/edge/schedule.json) with interval and instructions. No daemon; use cron to run 'workflow-dataset edge check-now'."""
    import json
    root = Path(repo_root) if repo_root else None
    if root is None:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root())
        except Exception:
            root = Path.cwd()
    out_dir = root / "data" / "local" / "edge"
    out_dir.mkdir(parents=True, exist_ok=True)
    schedule_path = out_dir / "schedule.json"
    payload = {
        "interval_hours": interval_hours,
        "note": "Operator-controlled. No daemon. Run: workflow-dataset edge check-now (e.g. via cron).",
    }
    schedule_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    console.print(f"[green]Schedule marker: {schedule_path}[/green]")
    console.print(f"  interval_hours: {interval_hours}  — run [bold]workflow-dataset edge check-now[/bold] from cron at this interval.")


@templates_group.command("list")
def templates_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    show_status: bool = typer.Option(False, "--show-status", help="Show validation status per template (valid / valid_with_warning / deprecated / invalid)"),
) -> None:
    """List workflow templates (id, name, workflow_id, artifacts). Use --show-status to include validation status."""
    from workflow_dataset.templates.registry import list_templates
    from workflow_dataset.templates.validation import get_template_status, STATUS_VALID, STATUS_VALID_WITH_WARNING, STATUS_DEPRECATED, STATUS_INVALID
    root = Path(repo_root) if repo_root else None
    items = list_templates(repo_root=root)
    if not items:
        console.print("[dim]No templates found. Add YAML to data/local/templates/ (e.g. ops_reporting_core.yaml).[/dim]")
        raise typer.Exit(0)
    console.print("[bold]Templates[/bold]")
    for t in items:
        name = t.get("name") or t.get("id")
        console.print(f"  [bold]{t.get('id')}[/bold]  {name}")
        if show_status:
            status = get_template_status(t, repo_root=root)
            if status == STATUS_VALID:
                console.print(f"    [green]{status}[/green]")
            elif status == STATUS_VALID_WITH_WARNING:
                console.print(f"    [yellow]{status}[/yellow]")
            elif status == STATUS_DEPRECATED:
                console.print(f"    [yellow]{status}[/yellow]")
            else:
                console.print(f"    [red]{status}[/red]")
        console.print(f"    workflow={t.get('workflow_id')}  artifacts={t.get('artifacts', [])}")
        if t.get("description"):
            console.print(f"    [dim]{t['description']}[/dim]")


@templates_group.command("show")
def templates_show(
    id: str = typer.Option(..., "--id", "-i", help="Template id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show template definition (workflow_id, artifacts, optional wording, version/deprecated if set)."""
    from workflow_dataset.templates.registry import load_template
    root = Path(repo_root) if repo_root else None
    try:
        t = load_template(id.strip(), repo_root=root)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]Template: {t.get('id')}[/bold]")
    console.print(f"  name: {t.get('name')}")
    console.print(f"  workflow_id: {t.get('workflow_id')}")
    console.print(f"  artifacts: {t.get('artifacts')}")
    if t.get("version") is not None:
        console.print(f"  version: {t.get('version')}")
    if t.get("deprecated"):
        console.print("  deprecated: true")
    if t.get("compatibility_note"):
        console.print(f"  compatibility_note: {t.get('compatibility_note')}")
    if t.get("description"):
        console.print(f"  description: {t.get('description')}")
    if t.get("wording_hints"):
        console.print(f"  wording_hints: {t.get('wording_hints')}")
    if t.get("migration_hints"):
        console.print(f"  migration_hints: {t.get('migration_hints')}")
    console.print("[dim]Run: workflow-dataset release demo --template " + str(t.get("id")) + " --save-artifact[/dim]")


@templates_group.command("validate")
def templates_validate(
    id: str = typer.Option(..., "--id", "-i", help="Template id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Validate template compatibility (workflow, artifacts, export contract). Exit 0 if valid/valid_with_warning, non-zero if deprecated/invalid."""
    from workflow_dataset.templates.validation import validate_template, STATUS_VALID, STATUS_VALID_WITH_WARNING
    root = Path(repo_root) if repo_root else None
    result = validate_template(id.strip(), repo_root=root)
    status = result.get("status", "invalid")
    if result.get("errors"):
        for e in result["errors"]:
            console.print(f"[red]{e}[/red]")
    if result.get("warnings"):
        for w in result["warnings"]:
            console.print(f"[yellow]{w}[/yellow]")
    if status == STATUS_VALID:
        console.print("[green]valid[/green]")
        raise typer.Exit(0)
    if status == STATUS_VALID_WITH_WARNING:
        console.print("[yellow]valid_with_warning[/yellow]")
        raise typer.Exit(0)
    if result.get("migration_hints"):
        for h in result["migration_hints"]:
            console.print(f"[dim]{h}[/dim]")
    raise typer.Exit(1)


@templates_group.command("report")
def templates_report(
    id: str = typer.Option(..., "--id", "-i", help="Template id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to file (default: stdout)"),
) -> None:
    """Generate template validation report (checks, status, migration hints)."""
    from workflow_dataset.templates.validation import template_validation_report
    root = Path(repo_root) if repo_root else None
    report = template_validation_report(id.strip(), repo_root=root)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]Report written: {output}[/green]")
    else:
        console.print(report)


@templates_group.command("export")
def templates_export(
    id: str = typer.Option(..., "--id", "-i", help="Template id to export"),
    out: str = typer.Option(..., "--out", "-o", help="Output path (.tmpl.json or .tmpl.yaml)"),
    format: str = typer.Option("json", "--format", "-f", help="json | yaml"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Export a registered template to a portable file (.tmpl.json or .tmpl.yaml)."""
    from workflow_dataset.templates.export_import import export_template
    root = Path(repo_root) if repo_root else None
    path = export_template(id.strip(), out, repo_root=root, format=format)
    console.print(f"[green]Exported: {path}[/green]")


@templates_group.command("import")
def templates_import(
    file: str = typer.Option(..., "--file", "-f", help="Path to .tmpl.json or .tmpl.yaml (or .json/.yaml)"),
    id: str = typer.Option("", "--id", "-i", help="Override template id (default: use id from file)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Replace existing template with same id"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Import a template from file. Validates before registration; use --overwrite to replace existing."""
    from workflow_dataset.templates.export_import import import_template
    root = Path(repo_root) if repo_root else None
    try:
        summary = import_template(file, repo_root=root, template_id=id.strip() or None, overwrite=overwrite)
        console.print(f"[green]Imported: {summary.get('id')}[/green]  {summary.get('path')}")
    except FileExistsError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@templates_group.command("usage")
def templates_usage(
    workspaces_root: str = typer.Option("data/local/workspaces", "--workspaces", "-w", help="Workspaces root to scan"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    limit: int = typer.Option(100, "--limit", "-n", help="Max workspaces to scan"),
) -> None:
    """Show template usage: most-used templates and recent template-driven runs (from workspace manifests)."""
    from workflow_dataset.templates.usage import template_usage_summary
    root = Path(repo_root) if repo_root else None
    data = template_usage_summary(workspaces_root=workspaces_root, repo_root=root, limit=limit)
    counts = data.get("counts_by_template") or {}
    recent = data.get("recent_runs") or []
    console.print("[bold]Template usage[/bold]")
    console.print(f"  Total runs scanned: {data.get('total_runs', 0)}")
    console.print(f"  Template-driven runs: {data.get('total_template_runs', 0)}")
    if counts:
        console.print("\n[bold]Most-used templates[/bold]")
        for tid, count in list(counts.items())[:15]:
            console.print(f"  {tid}: {count} run(s)")
    if recent:
        console.print("\n[bold]Recent template-driven runs[/bold] (up to 10)")
        for r in recent[:10]:
            console.print(f"  [dim]{r.get('timestamp') or '—'}[/dim]  {r.get('template_id')}  {r.get('run_id')}  {r.get('workspace_path', '')}")
    if not counts and not recent:
        console.print("[dim]No template-driven workspaces found. Use release demo --template <id> --save-artifact to create runs.[/dim]")


@templates_group.command("test")
def templates_test(
    id: str = typer.Option(..., "--id", "-i", help="Template id to run harness for"),
    workspace: str = typer.Option("", "--workspace", "-w", help="Path to workspace dir to validate (optional)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Run template harness: validate expected artifact inventory/order and manifest. Use --workspace to validate a dir."""
    from workflow_dataset.templates.harness import run_template_harness
    root = Path(repo_root) if repo_root else None
    ws = workspace.strip() or None
    result = run_template_harness(id.strip(), workspace_path=ws, repo_root=root)
    if result.passed:
        console.print(f"[green]PASS[/green]  {result.template_id}")
        console.print(f"  Expected artifacts: {result.expected_artifacts}")
        raise typer.Exit(0)
    console.print(f"[red]FAIL[/red]  {result.template_id}")
    for e in result.errors:
        console.print(f"  [red]{e}[/red]")
    for e in result.manifest_errors:
        console.print(f"  [yellow]{e}[/yellow]")
    console.print(result.to_message())
    raise typer.Exit(1)


@intake_group.command("add")
def intake_add(
    path: str = typer.Option(..., "--path", "-p", help="Local file or directory to snapshot"),
    label: str = typer.Option(..., "--label", "-l", help="Label for this intake set (e.g. sprint_notes)"),
    input_type: str = typer.Option(
        "mixed",
        "--type",
        "-t",
        help="Type: notes, docs, spreadsheets, exported_repos, meeting_fragments, mixed",
    ),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Register path(s) and snapshot into data/local/intake/<label>/. Never mutates originals."""
    from workflow_dataset.intake.registry import add_intake, INPUT_TYPES
    root = Path(repo_root) if repo_root else None
    p = Path(path).resolve()
    if not p.exists():
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)
    if input_type not in INPUT_TYPES:
        input_type = "mixed"
    try:
        entry = add_intake(label.strip(), [p], input_type=input_type, repo_root=root)
        console.print(f"[green]Intake registered: {entry.get('label')}[/green]")
        console.print(f"  Snapshot: {entry.get('snapshot_dir')}")
        console.print(f"  Files: {entry.get('file_count', 0)}")
        console.print("[dim]Use: workflow-dataset release demo --intake " + (entry.get("label") or label) + " --save-artifact[/dim]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@intake_group.command("list")
def intake_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List registered intake sets (label, type, file count, created_at)."""
    from workflow_dataset.intake.registry import list_intakes
    root = Path(repo_root) if repo_root else None
    items = list_intakes(repo_root=root)
    if not items:
        console.print("[dim]No intake sets. Add with: workflow-dataset intake add --path <dir> --label <name>[/dim]")
        raise typer.Exit(0)
    console.print("[bold]Intake sets[/bold]")
    for it in items:
        console.print(f"  [bold]{it.get('label')}[/bold]  type={it.get('input_type')}  files={it.get('file_count', 0)}  {it.get('created_at', '')}")
        console.print(f"    [dim]{it.get('snapshot_dir', '')}[/dim]")


@intake_group.command("report")
def intake_report_cmd(
    label: str = typer.Option(..., "--label", "-l", help="Intake set label"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to file"),
) -> None:
    """Show intake report: file inventory, parse summary, suggested workflows."""
    from workflow_dataset.intake.report import format_intake_report_text, intake_report
    root = Path(repo_root) if repo_root else None
    report = intake_report(label.strip(), repo_root=root)
    text = format_intake_report_text(report)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        console.print(f"[green]Wrote: {output}[/green]")
    else:
        console.print(text)


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


MAX_TASK_CONTEXT_CHARS = 2000

# Output-shaping for narrow ops/reporting demo: send-ready weekly status, tight blocker/risk phrasing, operational next steps.
OPS_WEEKLY_STATUS_INSTRUCTIONS = (
    "Produce a send-ready weekly status artifact (minimal editing to share). Use exactly these sections when evidence supports them: "
    "**Summary** (one headline sentence), **Wins** (concrete accomplishments), **Blockers**, **Risks**, **Next steps**. "
    "Add owner or timing only when the context clearly supports it; do not fabricate. "
    "Blockers: phrase each in operational form—e.g. 'Blocked by X', 'Waiting on Y', 'Needs decision on Z', 'Dependency unresolved: [what]'. Then one short line on what would unblock. No vague filler (avoid 'some blockers', 'a few issues'). "
    "Risks: phrase as short, concrete operational risks—e.g. schedule risk, dependency risk, approval risk, quality risk, resource risk—with one line each. Avoid generic 'there are risks' or filler. "
    "Next steps: operational, concrete actions (who does what by when, or next concrete milestone). Avoid generic-only 'continue monitoring' or 'follow up' unless nothing more specific is supported. "
    "Write so it reads like a real status update someone could send; tighten wording and avoid restating the prompt."
)
OPS_WEEKLY_STATUS_WEAK_CONTEXT_INSTRUCTIONS = (
    "If context is weak or mixed, fill only sections you can support and label clearly: "
    "'[Well-supported]' vs '[Uncertain—limited context]' or '[Inferred—low confidence]' for blockers/risks. Prefer a tighter partial artifact over a verbose generic one. Do not fabricate wins, blockers, or next steps; if blockers or risks are inferred, say so briefly."
)
OPS_CONCRETE_GENERAL_INSTRUCTIONS = (
    "Be concrete; avoid merely restating the question."
)
OPS_STATUS_BRIEF_INSTRUCTIONS = (
    "Produce a stakeholder-ready status brief. Use these sections when evidence supports them: "
    "**Headline summary** (one sentence), **Wins**, **Blockers**, **Risks**, **Next steps**. "
    "Keep wording short and send-ready. If context does not support a section, omit it or label clearly."
)
OPS_STATUS_BRIEF_WEAK_CONTEXT_INSTRUCTIONS = (
    "If context is weak or mixed, label sections: '[Well-supported]' vs '[Uncertain—limited context]' or '[Inferred—low confidence]'. "
    "Prefer a tighter partial brief over a generic one. Do not fabricate; if uncertain, say so briefly."
)
OPS_ACTION_REGISTER_INSTRUCTIONS = (
    "Produce an action register / follow-up list. For each item give: **Action**, **Why it matters**. "
    "Add **Owner** or **Timing/priority** only if clearly supported by context; do not fabricate owner or dates. "
    "Note **Blocker/dependency** where relevant. Use a simple list or table format."
)
OPS_ACTION_REGISTER_WEAK_CONTEXT_INSTRUCTIONS = (
    "If context is weak or mixed, include only actions you can support from context; label uncertain items. Do not invent owners or timing."
)
OPS_STAKEHOLDER_UPDATE_INSTRUCTIONS = (
    "Produce a concise, stakeholder-facing update. Use these sections when evidence supports them: "
    "**Headline summary** (one sentence), **Key progress / wins**, **Blockers / risks**, **Immediate asks / dependencies**. "
    "Keep wording short and safe to share with stakeholders. If context does not support a section, omit it or label clearly."
)
OPS_STAKEHOLDER_UPDATE_WEAK_CONTEXT_INSTRUCTIONS = (
    "If context is weak or mixed, label sections: '[Well-supported]' vs '[Uncertain—limited context]' or '[Inferred—low confidence]'. "
    "Prefer a useful partial update over a generic one. Do not fabricate; if uncertain, say so briefly."
)
OPS_DECISION_REQUESTS_INSTRUCTIONS = (
    "Produce a decision-requests list. For each item give: **Decision needed**, **Why it matters**, **Consequence if delayed**. "
    "Add **Owner** or **Timing** only if clearly supported by context; do not fabricate. Use a simple list or table format."
)
OPS_DECISION_REQUESTS_WEAK_CONTEXT_INSTRUCTIONS = (
    "If context is weak or mixed, include only decisions you can support from context; label uncertain items. Do not invent owners or timing."
)
OPS_MEETING_BRIEF_INSTRUCTIONS = (
    "Produce a concise meeting brief. Use these sections when evidence supports them: "
    "**Key outcomes** (what was decided or achieved), **Decisions**, **Takeaways**. "
    "Keep wording short and stakeholder-safe. If context does not support a section, omit it or label clearly."
)
OPS_MEETING_BRIEF_WEAK_CONTEXT_INSTRUCTIONS = (
    "If context is weak or mixed, label sections: '[Well-supported]' vs '[Uncertain—limited context]' or '[Inferred—low confidence]'. "
    "Prefer a useful partial brief over a generic one. Do not fabricate outcomes or decisions."
)
OPS_ACTION_ITEMS_INSTRUCTIONS = (
    "Produce an action-items list from the meeting/context. For each item give: **Action**, **Why it matters**. "
    "Add **Owner** or **Timing** only if clearly supported by context; do not fabricate. Use a simple list or table format."
)
OPS_ACTION_ITEMS_WEAK_CONTEXT_INSTRUCTIONS = (
    "If context is weak or mixed, include only actions you can support from context; label uncertain items. Do not invent owners or timing."
)


def _load_task_context(
    context_file: str | None,
    context_text: str | None,
    resolve_path: Any,
) -> str:
    """Load task-scoped context from file and/or inline text. Local-only; capped at MAX_TASK_CONTEXT_CHARS."""
    parts: list[str] = []
    if context_file:
        path = resolve_path(context_file)
        if path and Path(path).exists():
            raw = Path(path).read_text(encoding="utf-8", errors="replace").strip()
            if raw:
                parts.append(raw)
    if context_text and context_text.strip():
        parts.append(context_text.strip())
    combined = "\n\n".join(parts)
    if len(combined) > MAX_TASK_CONTEXT_CHARS:
        combined = combined[:MAX_TASK_CONTEXT_CHARS] + "\n[... truncated]"
    return combined


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
    context_file: str = typer.Option(
        "",
        "--context-file",
        help="Path to a local text file with task-scoped context (e.g. ops/reporting focus). Resolved from project root.",
    ),
    context_text: str = typer.Option(
        "",
        "--context-text",
        help="Inline task-scoped context (e.g. 'weekly ops reporting for project delivery'). Use with or without --context-file.",
    ),
    input_pack: str = typer.Option(
        "",
        "--input-pack",
        help="Named input pack: data/local/input_packs/<name>.json (manifest with paths) or data/local/input_packs/<name>/ (directory of .md/.txt). Local-only.",
    ),
    save_artifact: bool = typer.Option(
        False,
        "--save-artifact",
        help="Save output to sandbox (weekly_status or status_action_bundle per --workflow). No apply.",
    ),
    workflow: str = typer.Option(
        "weekly_status",
        "--workflow",
        "-w",
        help="Ops reporting suite: weekly_status | status_action_bundle | stakeholder_update_bundle | meeting_brief_bundle | ops_reporting_workspace.",
    ),
    rerun_from: str = typer.Option(
        "",
        "--rerun-from",
        help="Rerun from an existing workspace: use its manifest (context-file, input-pack, retrieval). New run saved to new dir; original unchanged. Local-only.",
    ),
    intake: str = typer.Option(
        "",
        "--intake",
        help="Named intake set (from workflow-dataset intake add). Local snapshot; feeds task context. Use with --save-artifact to write workspace.",
    ),
    template: str = typer.Option(
        "",
        "--template",
        "-t",
        help="Template id (e.g. ops_reporting_core). Overrides --workflow and controls artifact set/order when saving.",
    ),
    param: list[str] = typer.Option(
        [],
        "--param",
        "-p",
        help="Template parameter key=value (e.g. --param owner=Alex --param label=sprint_12). Only when template defines parameters.",
    ),
) -> None:
    """Ops reporting suite: run demo with release preset. --workflow: weekly_status (default), status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle, or ops_reporting_workspace (multi-artifact workspace). Use --retrieval and --context-file/--context-text for grounding; --save-artifact to write to sandbox. See docs/FOUNDER_DEMO_FLOW.md."""
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
    if rerun_from and rerun_from.strip():
        from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
        ws_path = _resolve_workspace_arg(rerun_from.strip())
        if not ws_path:
            console.print(f"[red]Workspace not found: {rerun_from}[/red]")
            raise typer.Exit(1)
        inv = get_workspace_inventory(ws_path)
        if not inv or not inv.get("manifest"):
            console.print("[red]Not a valid reporting workspace or no manifest.[/red]")
            raise typer.Exit(1)
        from workflow_dataset.release.workspace_rerun_diff import infer_rerun_args
        args = infer_rerun_args(inv["manifest"])
        context_file = args.get("context_file") or context_file
        input_pack = args.get("input_pack") or input_pack
        intake = args.get("intake") or intake
        retrieval = bool(args.get("retrieval")) or retrieval
        workflow = args.get("workflow") or workflow
        save_artifact = True
        console.print(f"[dim]Rerun from existing workspace (unchanged): {ws_path}[/dim]")
    template_def: dict[str, Any] | None = None
    template_params: dict[str, Any] = {}
    if template and template.strip():
        try:
            from workflow_dataset.templates.registry import load_template
            template_def = load_template(template.strip(), _repo_root())
            workflow = template_def.get("workflow_id") or workflow
            if param:
                from workflow_dataset.templates.validation import resolve_template_params
                template_params = resolve_template_params(template_def, param)
        except FileNotFoundError:
            console.print(f"[yellow]Template not found: {template}, using --workflow[/yellow]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
    elif param:
        console.print("[red]--param requires --template[/red]")
        raise typer.Exit(1)
    task_context = _load_task_context(
        context_file.strip() or None, context_text.strip() or None, _resolve_path
    )
    input_sources_used: list[dict[str, Any]] = []
    if context_file and context_file.strip():
        rp = _resolve_path(context_file.strip())
        if rp and Path(rp).exists():
            input_sources_used.append({"type": "context_file", "path_or_name": context_file.strip(), "resolved_path": str(rp)})
    if context_text and context_text.strip():
        input_sources_used.append({"type": "context_text", "path_or_name": "(inline)", "resolved_path": None})
    if input_pack and input_pack.strip():
        from workflow_dataset.release.input_packs import load_input_pack
        pack_content, pack_sources = load_input_pack(input_pack.strip(), _repo_root())
        for s in pack_sources:
            input_sources_used.append(s)
        if pack_content:
            task_context = (task_context + "\n\n" + pack_content).strip() if task_context else pack_content
    if intake and intake.strip():
        from workflow_dataset.intake.load import load_intake_content
        intake_content, intake_sources = load_intake_content(intake.strip(), _repo_root())
        for s in intake_sources:
            input_sources_used.append({"type": s.get("type", "intake"), "path_or_name": s.get("path_or_name", intake.strip())})
        if intake_content:
            task_context = (task_context + "\n\n" + intake_content).strip() if task_context else intake_content
    has_task_context = bool(task_context)
    grounded_by_retrieval = use_retrieval and corpus_exists
    grounded = has_task_context or grounded_by_retrieval
    console.print("[bold]Founder demo — Operations reporting assistant[/bold]")
    if grounded:
        if has_task_context and grounded_by_retrieval:
            console.print("[green][Grounded: task context + retrieval][/green]")
        elif has_task_context:
            console.print("[green][Grounded: task context used][/green]")
        else:
            console.print("[green][Grounded: retrieval context used][/green]")
    else:
        console.print(
            "[yellow][Ungrounded: no retrieval or task context; outputs may be generic][/yellow]")
        console.print(
            "[dim]Use --retrieval and/or --context-file/--context-text for grounded answers. See docs/FOUNDER_DEMO_FLOW.md.[/dim]")
    _prompt_count = 6 if workflow_type == "ops_reporting_workspace" else 3
    console.print(
        f"[dim]Running demo-suite (first {_prompt_count} prompts).[/dim]")
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
    workflow_type = (workflow or "weekly_status").strip().lower()
    if workflow_type not in ("status_action_bundle", "stakeholder_update_bundle", "meeting_brief_bundle", "ops_reporting_workspace"):
        workflow_type = "weekly_status"
    if workflow_type == "ops_reporting_workspace":
        prompts = [
            "Summarize this user's workflow style briefly.",
            "Produce a send-ready weekly status: **Summary**, **Wins**, **Blockers**, **Risks**, **Next steps**. Use honesty labels when evidence is partial or mixed.",
            "Produce a stakeholder-ready status brief: headline summary, wins, blockers, risks, next steps. Concise and send-ready.",
            "Produce an action register: action item, why it matters; owner/timing only if supported; note blocker/dependency where relevant. Do not fabricate.",
            "Produce a stakeholder-facing update: headline, key progress/wins, blockers/risks, immediate asks. Safe to share internally.",
            "Produce a decision-requests list: decision needed, why it matters, consequence if delayed; owner/timing only if supported. Do not fabricate.",
        ]
        prompt_kinds = ["general", "weekly_status", "status_brief", "action_register", "stakeholder_update", "decision_requests"]
    elif workflow_type == "status_action_bundle":
        prompts = [
            "Summarize this user's workflow style.",
            "Produce a stakeholder-ready status brief: headline summary, wins, blockers, risks, next steps. Use honesty labels when evidence is partial or mixed.",
            "Produce an action register / follow-up list: action item, why it matters; add owner or timing only if supported by context; note blocker/dependency where relevant. Do not fabricate owner or timing.",
        ]
        prompt_kinds: list[str] = ["general", "status_brief", "action_register"]
    elif workflow_type == "stakeholder_update_bundle":
        prompts = [
            "Summarize this user's workflow style.",
            "Produce a concise stakeholder-facing update: headline summary, key progress/wins, blockers/risks, immediate asks/dependencies. Use honesty labels when evidence is partial or mixed.",
            "Produce a decision-requests list: decision needed, why it matters, consequence if delayed; add owner or timing only if supported by context. Do not fabricate.",
        ]
        prompt_kinds = ["general", "stakeholder_update", "decision_requests"]
    elif workflow_type == "meeting_brief_bundle":
        prompts = [
            "Summarize this user's workflow style.",
            "Produce a concise meeting brief: key outcomes, decisions, takeaways. Stakeholder-safe. Use honesty labels when evidence is partial or mixed.",
            "Produce an action-items list from the meeting/context: action, why it matters; add owner or timing only if supported by context. Do not fabricate.",
        ]
        prompt_kinds = ["general", "meeting_brief", "action_items"]
    else:
        prompts = [
            "Summarize this user's workflow style.",
            "What recurring work patterns are visible?",
            "Summarize this user's recurring reporting workflow and suggest a weekly status structure.",
        ]
        prompt_kinds = ["general", "general", "weekly_status"]
    run_relevance: str | None = None
    relevance_order = ("weak", "mixed", "high")
    weekly_status_output: str | None = None
    status_brief_output: str | None = None
    action_register_output: str | None = None
    stakeholder_update_output: str | None = None
    decision_requests_output: str | None = None
    meeting_brief_output: str | None = None
    action_items_output: str | None = None

    max_demo_prompts = 6 if workflow_type == "ops_reporting_workspace" else 3
    for i, prompt in enumerate(prompts[:max_demo_prompts], 1):
        kind = prompt_kinds[i - 1] if i <= len(prompt_kinds) else "general"
        console.print(f"\n[bold]{i}. {prompt}[/bold]")
        user_prompt = prompt
        retrieval_ctx = ""
        relevance_hint_this = None
        if use_retrieval and corpus_path and Path(corpus_path).exists():
            from workflow_dataset.llm.retrieval_context import (
                retrieve_with_scores,
                relevance_hint_from_scores,
                format_context_for_prompt,
                OPS_REPORTING_PREFERRED_SOURCE_TYPES,
                OPS_REPORTING_QUERY_SUFFIX,
            )
            query_for_retrieval = prompt + OPS_REPORTING_QUERY_SUFFIX
            docs, scores = retrieve_with_scores(
                corpus_path,
                query_for_retrieval,
                top_k=3,
                prefer_source_types=OPS_REPORTING_PREFERRED_SOURCE_TYPES,
            )
            relevance_hint_this = relevance_hint_from_scores(scores)
            if run_relevance is None or relevance_order.index(relevance_hint_this) < relevance_order.index(run_relevance):
                run_relevance = relevance_hint_this
            console.print(f"[dim]Retrieval relevance: {relevance_hint_this}[/dim]")
            ctx = format_context_for_prompt(docs, max_chars=1500)
            if ctx:
                retrieval_ctx = f"Context (retrieved; relevance: {relevance_hint_this}):\n" + ctx

        parts: list[str] = []
        if task_context:
            parts.append("Task context (operator-provided):\n" + task_context)
            if has_task_context and (relevance_hint_this in ("weak", "mixed") or not retrieval_ctx):
                parts.append(
                    "Prioritize this task context. Do not make confident role or domain assumptions from weak or mixed retrieval; if retrieval is present but off-topic, say so and base the answer on task context only."
                )
        if retrieval_ctx:
            parts.append(retrieval_ctx)
            weak_or_mixed = relevance_hint_this in ("weak", "mixed")
            if not task_context:
                caveat = (
                    "The context above has weak or mixed relevance to ops/reporting. Say so clearly and give only a qualified, partial answer; do not overstate."
                    if weak_or_mixed
                    else "If the context does not clearly describe this user's ops/reporting workflow, say so and keep the answer cautious."
                )
                parts.append(caveat)
            elif weak_or_mixed:
                parts.append(
                    "Retrieval has weak or mixed relevance; prioritize the task context above and do not overstate from retrieved snippets."
                )
            else:
                parts.append(
                    "If the retrieved context does not clearly support the task context, say so and keep the answer cautious."
                )
        if parts:
            weak_or_mixed = relevance_hint_this in ("weak", "mixed") if relevance_hint_this else False
            if kind == "weekly_status":
                parts.append(OPS_WEEKLY_STATUS_INSTRUCTIONS)
                if weak_or_mixed:
                    parts.append(OPS_WEEKLY_STATUS_WEAK_CONTEXT_INSTRUCTIONS)
            elif kind == "status_brief":
                parts.append(OPS_STATUS_BRIEF_INSTRUCTIONS)
                if weak_or_mixed:
                    parts.append(OPS_STATUS_BRIEF_WEAK_CONTEXT_INSTRUCTIONS)
            elif kind == "action_register":
                parts.append(OPS_ACTION_REGISTER_INSTRUCTIONS)
                if weak_or_mixed:
                    parts.append(OPS_ACTION_REGISTER_WEAK_CONTEXT_INSTRUCTIONS)
            elif kind == "stakeholder_update":
                parts.append(OPS_STAKEHOLDER_UPDATE_INSTRUCTIONS)
                if weak_or_mixed:
                    parts.append(OPS_STAKEHOLDER_UPDATE_WEAK_CONTEXT_INSTRUCTIONS)
            elif kind == "decision_requests":
                parts.append(OPS_DECISION_REQUESTS_INSTRUCTIONS)
                if weak_or_mixed:
                    parts.append(OPS_DECISION_REQUESTS_WEAK_CONTEXT_INSTRUCTIONS)
            elif kind == "meeting_brief":
                parts.append(OPS_MEETING_BRIEF_INSTRUCTIONS)
                if weak_or_mixed:
                    parts.append(OPS_MEETING_BRIEF_WEAK_CONTEXT_INSTRUCTIONS)
            elif kind == "action_items":
                parts.append(OPS_ACTION_ITEMS_INSTRUCTIONS)
                if weak_or_mixed:
                    parts.append(OPS_ACTION_ITEMS_WEAK_CONTEXT_INSTRUCTIONS)
            else:
                parts.append(OPS_CONCRETE_GENERAL_INSTRUCTIONS)
            user_prompt = "\n\n".join(parts) + "\n\nUser: " + prompt
        else:
            if kind == "weekly_status":
                user_prompt = OPS_WEEKLY_STATUS_INSTRUCTIONS + "\n\nUser: " + prompt
            elif kind == "status_brief":
                user_prompt = OPS_STATUS_BRIEF_INSTRUCTIONS + "\n\nUser: " + prompt
            elif kind == "action_register":
                user_prompt = OPS_ACTION_REGISTER_INSTRUCTIONS + "\n\nUser: " + prompt
            elif kind == "stakeholder_update":
                user_prompt = OPS_STAKEHOLDER_UPDATE_INSTRUCTIONS + "\n\nUser: " + prompt
            elif kind == "decision_requests":
                user_prompt = OPS_DECISION_REQUESTS_INSTRUCTIONS + "\n\nUser: " + prompt
            elif kind == "meeting_brief":
                user_prompt = OPS_MEETING_BRIEF_INSTRUCTIONS + "\n\nUser: " + prompt
            elif kind == "action_items":
                user_prompt = OPS_ACTION_ITEMS_INSTRUCTIONS + "\n\nUser: " + prompt
            else:
                user_prompt = OPS_CONCRETE_GENERAL_INSTRUCTIONS + "\n\nUser: " + prompt
        try:
            out = backend.run_inference(base_model, user_prompt, max_tokens=200, adapter_path=adapter_path) if adapter_path else backend.run_inference(
                base_model, user_prompt, max_tokens=200)
            if out and out.startswith("[inference error"):
                console.print(f"[red]{out[:150]}[/red]")
            else:
                displayed = (out[:400] + ("..." if len(out or "") > 400 else "")) if out else "[no output]"
                console.print(displayed or "[no output]")
                if out and not out.startswith("[inference error]"):
                    if kind == "weekly_status":
                        weekly_status_output = out
                    elif kind == "status_brief":
                        status_brief_output = out
                    elif kind == "action_register":
                        action_register_output = out
                    elif kind == "stakeholder_update":
                        stakeholder_update_output = out
                    elif kind == "decision_requests":
                        decision_requests_output = out
                    elif kind == "meeting_brief":
                        meeting_brief_output = out
                    elif kind == "action_items":
                        action_items_output = out
        except Exception as e:
            console.print(f"[red]{e}[/red]")
    record_trial_event("generation_succeeded", {
                       "task_id": "release_demo"}, store_path=store_path)
    try:
        pilot_dir = Path("data/local/pilot")
        pilot_dir.mkdir(parents=True, exist_ok=True)
        if has_task_context and grounded_by_retrieval:
            grounding_mode = "task_context_and_retrieval"
        elif has_task_context:
            grounding_mode = "task_context_only"
        elif grounded_by_retrieval:
            grounding_mode = "retrieval_only"
        else:
            grounding_mode = "ungrounded"
        (pilot_dir / "last_demo_grounding.txt").write_text(
            grounding_mode + "\n" + (f"retrieval_relevance: {run_relevance}" if run_relevance else ""),
            encoding="utf-8",
        )
        if run_relevance is not None:
            (pilot_dir / "last_retrieval_relevance.txt").write_text(
                run_relevance, encoding="utf-8"
            )
    except Exception:
        pass
    saved_artifact_path: Path | None = None
    if save_artifact and workflow_type == "weekly_status" and weekly_status_output:
        try:
            from workflow_dataset.path_utils import get_repo_root
            from workflow_dataset.utils.dates import utc_now_iso
            from workflow_dataset.utils.hashes import stable_id
            root = get_repo_root() / "data/local/workspaces/weekly_status"
            root.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
            sid = stable_id("ws", ts, prefix="")[:8]
            dir_path = root / f"{ts}_{sid}"
            dir_path.mkdir(parents=True, exist_ok=True)
            md_path = dir_path / "weekly_status.md"
            md_path.write_text(weekly_status_output, encoding="utf-8")
            grounding = (
                "task_context_and_retrieval" if has_task_context and grounded_by_retrieval
                else "task_context_only" if has_task_context
                else "retrieval_only" if grounded_by_retrieval
                else "ungrounded"
            )
            manifest = {
                "artifact_type": "weekly_status",
                "grounding": grounding,
                "task_context_used": has_task_context,
                "retrieval_used": grounded_by_retrieval,
                "retrieval_relevance": run_relevance,
                "timestamp": utc_now_iso(),
            }
            (dir_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            saved_artifact_path = dir_path
            try:
                from workflow_dataset.pilot.session_log import record_workflow_artifact
                record_workflow_artifact("weekly_status", dir_path, pilot_dir=Path("data/local/pilot"))
            except Exception:
                pass
        except Exception:
            saved_artifact_path = None
    elif save_artifact and workflow_type == "status_action_bundle" and (status_brief_output or action_register_output):
        try:
            from workflow_dataset.path_utils import get_repo_root
            from workflow_dataset.utils.dates import utc_now_iso
            from workflow_dataset.utils.hashes import stable_id
            root = get_repo_root() / "data/local/workspaces/status_action_bundle"
            root.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
            sid = stable_id("sab", ts, prefix="")[:8]
            dir_path = root / f"{ts}_{sid}"
            dir_path.mkdir(parents=True, exist_ok=True)
            if status_brief_output:
                (dir_path / "status_brief.md").write_text(status_brief_output, encoding="utf-8")
            if action_register_output:
                (dir_path / "action_register.md").write_text(action_register_output, encoding="utf-8")
            grounding = (
                "task_context_and_retrieval" if has_task_context and grounded_by_retrieval
                else "task_context_only" if has_task_context
                else "retrieval_only" if grounded_by_retrieval
                else "ungrounded"
            )
            manifest = {
                "artifact_type": "status_action_bundle",
                "workflow": "status_action_bundle",
                "grounding": grounding,
                "task_context_used": has_task_context,
                "retrieval_used": grounded_by_retrieval,
                "retrieval_relevance": run_relevance,
                "timestamp": utc_now_iso(),
                "has_status_brief": bool(status_brief_output),
                "has_action_register": bool(action_register_output),
            }
            (dir_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            saved_artifact_path = dir_path
            try:
                from workflow_dataset.pilot.session_log import record_workflow_artifact
                record_workflow_artifact("status_action_bundle", dir_path, pilot_dir=Path("data/local/pilot"))
            except Exception:
                pass
        except Exception:
            saved_artifact_path = None
    elif save_artifact and workflow_type == "meeting_brief_bundle" and (meeting_brief_output or action_items_output):
        try:
            from workflow_dataset.path_utils import get_repo_root
            from workflow_dataset.utils.dates import utc_now_iso
            from workflow_dataset.utils.hashes import stable_id
            root = get_repo_root() / "data/local/workspaces/meeting_brief_bundle"
            root.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
            sid = stable_id("mbb", ts, prefix="")[:8]
            dir_path = root / f"{ts}_{sid}"
            dir_path.mkdir(parents=True, exist_ok=True)
            if meeting_brief_output:
                (dir_path / "meeting_brief.md").write_text(meeting_brief_output, encoding="utf-8")
            if action_items_output:
                (dir_path / "action_items.md").write_text(action_items_output, encoding="utf-8")
            grounding = (
                "task_context_and_retrieval" if has_task_context and grounded_by_retrieval
                else "task_context_only" if has_task_context
                else "retrieval_only" if grounded_by_retrieval
                else "ungrounded"
            )
            manifest = {
                "artifact_type": "meeting_brief_bundle",
                "workflow": "meeting_brief_bundle",
                "grounding": grounding,
                "task_context_used": has_task_context,
                "retrieval_used": grounded_by_retrieval,
                "retrieval_relevance": run_relevance,
                "timestamp": utc_now_iso(),
                "has_meeting_brief": bool(meeting_brief_output),
                "has_action_items": bool(action_items_output),
            }
            (dir_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            saved_artifact_path = dir_path
            try:
                from workflow_dataset.pilot.session_log import record_workflow_artifact
                record_workflow_artifact("meeting_brief_bundle", dir_path, pilot_dir=Path("data/local/pilot"))
            except Exception:
                pass
        except Exception:
            saved_artifact_path = None
    elif save_artifact and workflow_type == "stakeholder_update_bundle" and (stakeholder_update_output or decision_requests_output):
        try:
            from workflow_dataset.path_utils import get_repo_root
            from workflow_dataset.utils.dates import utc_now_iso
            from workflow_dataset.utils.hashes import stable_id
            root = get_repo_root() / "data/local/workspaces/stakeholder_update_bundle"
            root.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
            sid = stable_id("sub", ts, prefix="")[:8]
            dir_path = root / f"{ts}_{sid}"
            dir_path.mkdir(parents=True, exist_ok=True)
            if stakeholder_update_output:
                (dir_path / "stakeholder_update.md").write_text(stakeholder_update_output, encoding="utf-8")
            if decision_requests_output:
                (dir_path / "decision_requests.md").write_text(decision_requests_output, encoding="utf-8")
            grounding = (
                "task_context_and_retrieval" if has_task_context and grounded_by_retrieval
                else "task_context_only" if has_task_context
                else "retrieval_only" if grounded_by_retrieval
                else "ungrounded"
            )
            manifest = {
                "artifact_type": "stakeholder_update_bundle",
                "workflow": "stakeholder_update_bundle",
                "grounding": grounding,
                "task_context_used": has_task_context,
                "retrieval_used": grounded_by_retrieval,
                "retrieval_relevance": run_relevance,
                "timestamp": utc_now_iso(),
                "has_stakeholder_update": bool(stakeholder_update_output),
                "has_decision_requests": bool(decision_requests_output),
            }
            (dir_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            saved_artifact_path = dir_path
            try:
                from workflow_dataset.pilot.session_log import record_workflow_artifact
                record_workflow_artifact("stakeholder_update_bundle", dir_path, pilot_dir=Path("data/local/pilot"))
            except Exception:
                pass
        except Exception:
            saved_artifact_path = None
    elif save_artifact and workflow_type == "ops_reporting_workspace":
        try:
            from workflow_dataset.utils.dates import utc_now_iso
            from workflow_dataset.release.workspace_save import save_ops_reporting_workspace
            from workflow_dataset.release.artifact_schema import build_source_snapshot_md
            from workflow_dataset.templates.registry import template_artifact_order_and_filenames
            kind_to_output: dict[str, str | None] = {
                "weekly_status": weekly_status_output,
                "status_brief": status_brief_output,
                "action_register": action_register_output,
                "stakeholder_update": stakeholder_update_output,
                "decision_requests": decision_requests_output,
            }
            artifacts_dict: dict[str, str] = {}
            if template_def:
                for key, filename in template_artifact_order_and_filenames(template_def):
                    out = kind_to_output.get(key)
                    if out:
                        artifacts_dict[filename] = out
            else:
                if weekly_status_output:
                    artifacts_dict["weekly_status.md"] = weekly_status_output
                if status_brief_output:
                    artifacts_dict["status_brief.md"] = status_brief_output
                if action_register_output:
                    artifacts_dict["action_register.md"] = action_register_output
                if stakeholder_update_output:
                    artifacts_dict["stakeholder_update.md"] = stakeholder_update_output
                if decision_requests_output:
                    artifacts_dict["decision_requests.md"] = decision_requests_output
            saved_artifact_names = list(artifacts_dict.keys())
            retrieval_relevance_weak_or_mixed = run_relevance in ("weak", "mixed") if run_relevance else False
            context_file_path = (context_file.strip() if (context_file and context_file.strip()) else None) or None
            source_snapshot_content = build_source_snapshot_md(
                input_sources_used=input_sources_used,
                context_file_used=bool(context_file and context_file.strip()),
                context_file_path=context_file_path,
                input_pack_used=bool(input_pack and input_pack.strip()),
                input_pack_name=input_pack.strip() if (input_pack and input_pack.strip()) else None,
                retrieval_used=grounded_by_retrieval,
                retrieval_relevance=run_relevance,
                retrieval_relevance_weak_or_mixed=retrieval_relevance_weak_or_mixed,
                saved_artifact_paths=["source_snapshot.md"] + saved_artifact_names,
            )
            artifacts_dict["source_snapshot.md"] = source_snapshot_content
            grounding = (
                "task_context_and_retrieval" if has_task_context and grounded_by_retrieval
                else "task_context_only" if has_task_context
                else "retrieval_only" if grounded_by_retrieval
                else "ungrounded"
            )
            artifact_list = ["source_snapshot.md"] + saved_artifact_names
            from workflow_dataset.release.artifact_schema import validate_workspace_artifacts
            schema_validation = validate_workspace_artifacts(artifacts_dict)
            ws_manifest = {
                "workflow": "ops_reporting_workspace",
                "timestamp": utc_now_iso(),
                "grounding": grounding,
                "input_sources_used": [
                    {"type": s.get("type", "source"), "path_or_name": s.get("path_or_name") or s.get("path") or s.get("pack")}
                    for s in input_sources_used
                ],
                "artifact_list": artifact_list,
                "retrieval_used": grounded_by_retrieval,
                "explicit_context_used": has_task_context,
                "context_file_used": bool(context_file and context_file.strip()),
                "input_pack_used": bool(input_pack and input_pack.strip()),
                "intake_used": bool(intake and intake.strip()),
                "intake_name": intake.strip() if (intake and intake.strip()) else None,
                "template_id": template_def.get("id") if template_def else None,
                "template_version": template_def.get("version") if template_def else None,
                "template_params": template_params if template_params else None,
                "retrieval_relevance": run_relevance,
                "retrieval_relevance_weak_or_mixed": retrieval_relevance_weak_or_mixed,
                "schema_validation": {k: {"valid": v["valid"], "missing_required": v.get("missing_required", [])} for k, v in schema_validation.items()},
            }
            saved_artifact_path = save_ops_reporting_workspace(
                artifacts_dict,
                ws_manifest,
                pilot_dir=Path("data/local/pilot"),
            )
        except Exception:
            saved_artifact_path = None
    if saved_artifact_path:
        console.print(
            "\n[bold]Output location:[/bold] [green]Artifact(s) saved to sandbox:[/green]")
        console.print(f"  [bold]{saved_artifact_path.resolve()}[/bold]")
        if saved_artifact_path.is_dir():
            for f in sorted(saved_artifact_path.iterdir()):
                if f.is_file():
                    console.print(f"  — {f.name}")
        manifest_note = "workspace_manifest.json" if workflow_type == "ops_reporting_workspace" else "manifest.json"
        console.print(
            f"[dim]{manifest_note} in same dir has grounding/relevance. No apply performed; use existing apply flow to copy to project if desired.[/dim]")
        if workflow_type == "ops_reporting_workspace" and saved_artifact_path.is_dir():
            console.print("[dim]Which sources fed this run: see source_snapshot.md. Manifest: workspace_manifest.json (input_sources_used, retrieval_relevance_weak_or_mixed).[/dim]")
            preview_md = next((f for f in saved_artifact_path.iterdir() if f.suffix == ".md" and f.name != "source_snapshot.md"), None)
            if preview_md:
                console.print(f"[dim]Preview artifact: head \"{saved_artifact_path / preview_md.name}\"[/dim]")
    else:
        console.print(
            "\n[bold]Output location:[/bold] The text above is your artifact. "
            "No file written (use [bold]--save-artifact[/bold] to write to sandbox). "
            "Use [dim]pilot capture-feedback --notes[/dim] to record where you saved it or any output-location feedback.")
    console.print(
        "[dim]Demo done. See docs/FOUNDER_DEMO_FLOW.md for full flow.[/dim]")


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
    cohort: str = typer.Option("", "--cohort", help="Cohort/batch label for broader controlled pilot (e.g. broader_2026_q1)"),
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
        cohort_id=cohort or "",
        pilot_dir=pilot_dir,
    )
    console.print(f"[green]Session started: {record.session_id}[/green]")
    if record.cohort_id:
        console.print(f"[dim]Cohort: {record.cohort_id}[/dim]")
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
        help="Was output/report location clear? yes / no",
    ),
    status_brief_send_ready: str = typer.Option(
        "",
        "--status-brief-send-ready",
        help="For status_action_bundle: was status brief send-ready? yes / no",
    ),
    action_register_usable: str = typer.Option(
        "",
        "--action-register-usable",
        help="For status_action_bundle: was action register usable? yes / no",
    ),
    stakeholder_update_send_ready: str = typer.Option(
        "",
        "--stakeholder-update-send-ready",
        help="For stakeholder_update_bundle: was stakeholder update send-ready? yes / no",
    ),
    decision_requests_usable: str = typer.Option(
        "",
        "--decision-requests-usable",
        help="For stakeholder_update_bundle: were decision requests usable? yes / no",
    ),
    meeting_brief_send_ready: str = typer.Option(
        "",
        "--meeting-brief-send-ready",
        help="For meeting_brief_bundle: was meeting brief send-ready? yes / no",
    ),
    action_items_usable: str = typer.Option(
        "",
        "--action-items-usable",
        help="For meeting_brief_bundle: were action items usable? yes / no",
    ),
    session_id: str = typer.Option("", "--session-id", "-s"),
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
) -> None:
    """Capture structured feedback for the current (or given) pilot session. Use --user-quote and --friction for first-class evidence counts."""
    from workflow_dataset.pilot.feedback_capture import capture_feedback
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
            freeform_notes=notes,
            next_steps_specific=next_steps_specific or "",
            report_location_clear=report_location_clear or "",
            status_brief_send_ready=status_brief_send_ready or "",
            action_register_usable=action_register_usable or "",
            stakeholder_update_send_ready=stakeholder_update_send_ready or "",
            decision_requests_usable=decision_requests_usable or "",
            meeting_brief_send_ready=meeting_brief_send_ready or "",
            action_items_usable=action_items_usable or "",
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
    recent: int | None = typer.Option(None, "--recent", "-r", help="Include recent-cohort view and graduation readiness for last N sessions (default: 5 when enough sessions); with --cohort, last N sessions within that cohort"),
    cohort: str = typer.Option("", "--cohort", help="Generate report for a specific cohort only (e.g. broader_ops_q1). Use with optional --recent N for last N sessions in cohort."),
) -> None:
    """Generate aggregate report (all sessions) or cohort report (when --cohort is set)."""
    if cohort and cohort.strip():
        from workflow_dataset.pilot.aggregate import write_cohort_report
        try:
            json_path, md_path = write_cohort_report(
                pilot_dir=pilot_dir, cohort_id=cohort.strip(), session_limit=limit, recent_n=recent)
            console.print(f"[green]Cohort report (JSON): {json_path}[/green]")
            console.print(f"[green]Cohort report (MD):  {md_path}[/green]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
    else:
        from workflow_dataset.pilot.aggregate import write_aggregate_report
        json_path, md_path = write_aggregate_report(
            pilot_dir=pilot_dir, session_limit=limit, recent_n=recent)
        console.print(f"[green]Aggregate report (JSON): {json_path}[/green]")
        console.print(f"[green]Aggregate report (MD):  {md_path}[/green]")


@pilot_group.command("graduation-status")
def pilot_graduation_status(
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
    recent: int = typer.Option(5, "--recent", "-r", help="Evaluate last N sessions for graduation"),
) -> None:
    """Evaluate graduation readiness from the last N sessions; prints recommendation (continue / refine_once / graduate)."""
    from workflow_dataset.pilot.aggregate import aggregate_sessions, graduation_evaluate, DEFAULT_RECENT_COHORT_N
    use_n = recent if recent > 0 else DEFAULT_RECENT_COHORT_N
    data = aggregate_sessions(pilot_dir=pilot_dir, session_limit=100, recent_n=use_n)
    if data.get("sessions_count", 0) == 0:
        console.print("[dim]No sessions in cohort. Run pilot sessions and aggregate first.[/dim]")
        return
    result = graduation_evaluate(data)
    console.print(f"[bold]Graduation (last {use_n} sessions):[/bold] {result['recommendation_grade']}")
    console.print(result["summary"])
    for c in result.get("criteria_checks", []):
        status = "[green]✓[/green]" if c.get("passed") else "[red]✗[/red]"
        console.print(f"  {status} {c.get('criterion', '')}: {c.get('detail', '')}")
    console.print("[dim]Full report: pilot aggregate --recent {}[/dim]".format(use_n))


@pilot_group.command("cohort-status")
def pilot_cohort_status(
    cohort: str = typer.Option(..., "--cohort", help="Cohort/batch label (e.g. broader_2026_q1)"),
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
    limit: int = typer.Option(100, "--limit", "-l"),
) -> None:
    """Print outcome for a broader controlled pilot cohort (continue / expand_adjacent / hold_refine / rollback)."""
    from workflow_dataset.pilot.aggregate import aggregate_sessions, cohort_outcome
    data = aggregate_sessions(pilot_dir=pilot_dir, session_limit=limit, cohort_id=cohort)
    if data.get("sessions_count", 0) == 0:
        console.print(f"[dim]No sessions in cohort '{cohort}'. Start sessions with --cohort {cohort}[/dim]")
        return
    result = cohort_outcome(data)
    console.print(f"[bold]Cohort '{cohort}' ({result['cohort_size']} sessions):[/bold] {result['outcome']}")
    console.print(result["summary"])
    for c in result.get("criteria_checks", []):
        status = "[green]✓[/green]" if c.get("passed") else "[red]✗[/red]"
        console.print(f"  {status} {c.get('criterion', '')}: {c.get('detail', '')}")
    console.print("[dim]Full report: pilot cohort-report --cohort {}[/dim]".format(cohort))


@pilot_group.command("cohort-report")
def pilot_cohort_report(
    cohort: str = typer.Option(..., "--cohort", help="Cohort/batch label (e.g. broader_ops_q1)"),
    pilot_dir: str = typer.Option("data/local/pilot", "--pilot-dir"),
    limit: int = typer.Option(100, "--limit", "-l"),
    recent: int | None = typer.Option(None, "--recent", "-r", help="Last N sessions within cohort only"),
) -> None:
    """Generate cohort report for a broader controlled pilot batch. Sessions must have been started with --cohort."""
    from workflow_dataset.pilot.aggregate import write_cohort_report
    try:
        json_path, md_path = write_cohort_report(
            pilot_dir=pilot_dir, cohort_id=cohort, session_limit=limit, recent_n=recent)
        console.print(f"[green]Cohort report (JSON): {json_path}[/green]")
        console.print(f"[green]Cohort report (MD):  {md_path}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


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


# ----- M21T Operator review queue + publishable package -----
review_group = typer.Typer(
    help="Operator review queue: list workspaces, inspect, approve artifacts, build publishable package. Sandbox-only.")
app.add_typer(review_group, name="review")


# ----- M23A Internal chain lab (operator-controlled) -----
chain_group = typer.Typer(
    help="Internal chain lab: define and run local step chains, persist outputs, compare runs. Operator-controlled; no auto-apply.")
app.add_typer(chain_group, name="chain")


chain_examples_group = typer.Typer(help="Bundled example chains: list and install into chains dir.")
chain_group.add_typer(chain_examples_group, name="examples")


@chain_examples_group.command("list")
def chain_examples_list() -> None:
    """List bundled example chain definitions (id, description, step count)."""
    from workflow_dataset.chain_lab.examples import list_example_chains
    examples = list_example_chains()
    if not examples:
        console.print("[dim]No bundled examples found.[/dim]")
        raise typer.Exit(0)
    for ex in examples:
        console.print(f"  [bold]{ex.get('id', '')}[/bold]  steps={ex.get('step_count', 0)}")
        if ex.get("description"):
            console.print(f"    [dim]{ex['description'][:120]}[/dim]")
    console.print("[dim]Install: workflow-dataset chain examples install <id>[/dim]")


@chain_examples_group.command("install")
def chain_examples_install(
    id: str = typer.Argument(..., help="Example chain id to install"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Install a bundled example chain into data/local/chain_lab/chains/ (overwrites if present)."""
    from workflow_dataset.chain_lab.examples import install_example
    root = Path(repo_root) if repo_root else None
    try:
        path = install_example(id.strip(), repo_root=root)
        console.print(f"[green]Installed: {path}[/green]")
        console.print(f"[dim]Run: workflow-dataset chain run {id.strip()}[/dim]")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@chain_group.command("list")
def chain_list(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List chain definitions (id, description, step count, variant)."""
    from workflow_dataset.chain_lab.definition import list_chains
    root = Path(repo_root) if repo_root else None
    chains = list_chains(repo_root=root)
    if not chains:
        console.print("[dim]No chain definitions. Add one with: chain define --id <id> --file <path> or chain examples install <id>[/dim]")
        raise typer.Exit(0)
    for c in chains:
        console.print(f"  [bold]{c.get('id', '')}[/bold]  steps={c.get('step_count', 0)}  variant={c.get('variant_label', '') or '(none)'}")
        if c.get("description"):
            console.print(f"    [dim]{c['description'][:120]}[/dim]")


@chain_group.command("define")
def chain_define(
    id: str = typer.Option(..., "--id", "-i", help="Chain id"),
    file: str = typer.Option(..., "--file", "-f", help="Path to chain JSON definition"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Load a chain definition from JSON file and save under data/local/chain_lab/chains/."""
    from workflow_dataset.chain_lab.definition import save_chain
    rp = _resolve_path(file)
    if not rp or not rp.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)
    root = Path(repo_root) if repo_root else None
    data = json.loads(rp.read_text(encoding="utf-8"))
    data["id"] = id.strip() or data.get("id", "unnamed")
    path = save_chain(data, repo_root=root)
    console.print(f"[green]Chain saved: {path}[/green]")


@chain_group.command("run")
def chain_run(
    chain_id: str = typer.Argument(..., help="Chain id to run"),
    variant: str = typer.Option("", "--variant", "-v", help="Variant label for this run"),
    no_stop_on_failure: bool = typer.Option(False, "--no-stop-on-failure", help="Continue chain after step failure"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Run one chain. Steps run locally via CLI; outputs under data/local/chain_lab/runs/<run_id>/."""
    from workflow_dataset.chain_lab.runner import run_chain
    root = Path(repo_root) if repo_root else None
    result = run_chain(
        chain_id=chain_id,
        variant_label=variant or None,
        stop_on_first_failure=not no_stop_on_failure,
        repo_root=root,
    )
    run_id = result.get("run_id", "")
    status = result.get("status", "")
    console.print(f"[green]Run finished: {run_id}[/green]  status={status}")
    if result.get("failure_summary"):
        console.print(f"  [yellow]Failure: {result['failure_summary']}[/yellow]")
    console.print(f"[dim]Report: workflow-dataset chain report {run_id}[/dim]")


@chain_group.command("report")
def chain_report(
    run_id: str = typer.Argument("latest", help="Run id or 'latest' (default)"),
    run: str = typer.Option(None, "--run", "-r", help="Run id or 'latest' (overrides positional)"),
    repo_root: str = typer.Option("", "--repo-root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to file"),
) -> None:
    """Print per-step report and run summary. Use run id or 'latest'. Includes failure report when failed."""
    from workflow_dataset.chain_lab.report import chain_run_report
    root = Path(repo_root) if repo_root else None
    rid = (run or run_id).strip() or "latest"
    report = chain_run_report(rid, repo_root=root)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]Report written: {output}[/green]")
    else:
        console.print(report)


@chain_group.command("resume")
def chain_resume(
    run: str = typer.Option(..., "--run", "-r", help="Run id or 'latest' to resume"),
    from_step: int = typer.Option(0, "--from-step", help="Resume from this step index (0-based)"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Resume a chain run from a given step. Keeps prior step results; re-runs from step to end."""
    from workflow_dataset.chain_lab.report import resolve_run_id
    from workflow_dataset.chain_lab.runner import resume_chain
    root = Path(repo_root) if repo_root else None
    rid = resolve_run_id(run.strip() or "latest", root)
    if not rid:
        console.print(f"[red]Run not found: {run}[/red]")
        raise typer.Exit(1)
    result = resume_chain(run_id=rid, from_step_index=from_step, repo_root=root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Resumed run: {result.get('run_id')}[/green]  status={result.get('status')}")
    if result.get("failure_summary"):
        console.print(f"  [yellow]Failure: {result['failure_summary']}[/yellow]")


@chain_group.command("retry-step")
def chain_retry_step(
    run: str = typer.Option(..., "--run", "-r", help="Run id or 'latest'"),
    step: str = typer.Option(..., "--step", "-s", help="Step id or step index (0-based)"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Retry a single step of a chain run. Re-runs that step and updates the run manifest."""
    from workflow_dataset.chain_lab.report import resolve_run_id
    from workflow_dataset.chain_lab.runner import retry_step
    from workflow_dataset.chain_lab.definition import get_step_by_id_or_index
    root = Path(repo_root) if repo_root else None
    rid = resolve_run_id(run.strip() or "latest", root)
    if not rid:
        console.print(f"[red]Run not found: {run}[/red]")
        raise typer.Exit(1)
    step_arg = step.strip()
    if step_arg.isdigit():
        step_arg = int(step_arg)
    result = retry_step(run_id=rid, step_index_or_id=step_arg, repo_root=root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Retried step: {result.get('run_id')}[/green]  status={result.get('status')}")
    if result.get("failure_summary"):
        console.print(f"  [yellow]{result['failure_summary']}[/yellow]")


@chain_group.command("compare")
def chain_compare(
    run_id_a: str = typer.Argument(None, help="First run id (or use --run-a)"),
    run_id_b: str = typer.Argument(None, help="Second run id (or use --run-b)"),
    run_a: str = typer.Option(None, "--run-a", help="First run id or 'latest'"),
    run_b: str = typer.Option(None, "--run-b", help="Second run id or 'latest'"),
    repo_root: str = typer.Option("", "--repo-root"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    artifact_diff: bool = typer.Option(False, "--artifact-diff", help="Include output path diff (only_in_a, only_in_b)"),
    benchmark_view: bool = typer.Option(False, "--benchmark-view", help="Add benchmark-style summary (status, duration, artifact counts)"),
) -> None:
    """Compare two chain runs. Use: compare <id_a> <id_b> or compare --run-a A --run-b B. Use --benchmark-view for eval/review summary."""
    from workflow_dataset.chain_lab.compare import compare_chain_runs
    root = Path(repo_root) if repo_root else None
    a = (run_a or run_id_a or "").strip()
    b = (run_b or run_id_b or "").strip()
    if not a or not b:
        console.print("[red]Provide two runs: compare <id_a> <id_b> or --run-a A --run-b B[/red]")
        raise typer.Exit(1)
    diff = compare_chain_runs(a, b, repo_root=root, include_artifact_diff=artifact_diff, benchmark_view=benchmark_view)
    if json_out:
        console.print(json.dumps(diff, indent=2))
        return
    if benchmark_view and diff.get("benchmark_summary"):
        from workflow_dataset.chain_lab.compare import benchmark_summary_text
        text = benchmark_summary_text(diff)
        if text:
            console.print("[bold]Benchmark summary[/bold]")
            for line in text.strip().split("\n"):
                console.print(f"  {line}")
            console.print("")
        else:
            bs = diff["benchmark_summary"]
            console.print("[bold]Benchmark summary[/bold]")
            console.print(f"  {bs.get('summary_line', '')}")
            console.print("")
    ra, rb = diff.get("run_a"), diff.get("run_b")
    console.print(f"[bold]Run A:[/bold] {diff.get('run_id_a')}  {ra}")
    if isinstance(ra, dict) and (ra.get("started_at") or ra.get("ended_at")):
        console.print(f"  [dim]started: {ra.get('started_at') or '—'}  ended: {ra.get('ended_at') or '—'}[/dim]")
    console.print(f"[bold]Run B:[/bold] {diff.get('run_id_b')}  {rb}")
    if isinstance(rb, dict) and (rb.get("started_at") or rb.get("ended_at")):
        console.print(f"  [dim]started: {rb.get('started_at') or '—'}  ended: {rb.get('ended_at') or '—'}[/dim]")
    if diff.get("status_diff"):
        console.print(f"  Status diff: {diff['status_diff']}")
    if diff.get("step_count_diff") is not None:
        console.print(f"  Step count diff: {diff['step_count_diff']}")
    for s in diff.get("step_status_diff") or []:
        console.print(f"  Step {s.get('step_index')}: {s.get('status_a')} vs {s.get('status_b')}")
    if diff.get("failure_diff"):
        console.print(f"  Failure diff: A={diff['failure_diff'].get('a')}  B={diff['failure_diff'].get('b')}")
    if diff.get("output_inventory_a") or diff.get("output_inventory_b"):
        console.print("  [dim]Output inventories: output_inventory_a, output_inventory_b (use --json to see)[/dim]")
    if diff.get("artifact_diff"):
        ad = diff["artifact_diff"]
        console.print(f"  Artifact diff: only_in_a={len(ad.get('only_in_a') or [])}, only_in_b={len(ad.get('only_in_b') or [])}, common={ad.get('common_count', 0)}")


@chain_group.command("list-runs")
def chain_list_runs(
    limit: int = typer.Option(20, "--limit", "-n"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """List recent chain runs (run_id, chain, status, started). Newest first."""
    from workflow_dataset.chain_lab.cleanup import list_runs_with_meta
    root = Path(repo_root) if repo_root else None
    runs = list_runs_with_meta(repo_root=root, limit=limit)
    if not runs:
        console.print("[dim]No chain runs yet. Run: workflow-dataset chain run <chain_id>[/dim]")
        raise typer.Exit(0)
    for r in runs:
        rid = r.get("run_id", "")
        chain_id = r.get("chain_id", "") or "—"
        status = r.get("status", "") or "—"
        started = r.get("started_at", "") or "—"
        console.print(f"  [bold]{rid}[/bold]  chain={chain_id}  status={status}  started={started}")


@chain_group.command("artifact-tree")
def chain_artifact_tree_cmd(
    run_id: str = typer.Argument(..., help="Run id from chain run"),
    repo_root: str = typer.Option("", "--repo-root"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Print artifact tree for a chain run (run_dir, steps, output_paths)."""
    from workflow_dataset.chain_lab.report import chain_artifact_tree
    root = Path(repo_root) if repo_root else None
    tree = chain_artifact_tree(run_id, repo_root=root)
    if json_out:
        console.print(json.dumps(tree, indent=2))
        return
    console.print(f"[bold]Run:[/bold] {tree.get('run_id')}  [bold]Chain:[/bold] {tree.get('chain_id')}  [bold]Status:[/bold] {tree.get('status')}")
    console.print(f"  [dim]Run dir: {tree.get('run_dir', '')}[/dim]")
    for s in tree.get("steps") or []:
        console.print(f"  Step {s.get('step_index')} ({s.get('step_id')}): {s.get('status')}")
        for p in (s.get("output_paths") or [])[:5]:
            console.print(f"    — {p}")


chain_runs_group = typer.Typer(help="Run listing and archive.")
chain_group.add_typer(chain_runs_group, name="runs")


@chain_runs_group.command("archive")
def chain_runs_archive(
    run: str = typer.Option(..., "--run", "-r", help="Run id to archive"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Move a chain run to runs/archive/<run_id>. Safe local maintenance."""
    from workflow_dataset.chain_lab.cleanup import archive_run
    from workflow_dataset.chain_lab.report import resolve_run_id
    root = Path(repo_root) if repo_root else None
    rid = resolve_run_id(run.strip(), root) if run.strip().lower() != "latest" else run.strip()
    if not rid:
        rid = run.strip()
    try:
        path = archive_run(rid, repo_root=root)
        console.print(f"[green]Archived: {rid} → {path}[/green]")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@chain_group.command("cleanup")
def chain_cleanup(
    older_than: str = typer.Option("30d", "--older-than", help="Consider runs older than this (e.g. 30d, 7d)"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Only list runs (default); with --no-dry-run and --archive, archive them"),
    archive: bool = typer.Option(False, "--archive", help="Archive (move to runs/archive/) runs older than threshold"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """List or archive chain runs older than a given age. Default: dry-run, list only."""
    from workflow_dataset.chain_lab.cleanup import cleanup_older_runs
    root = Path(repo_root) if repo_root else None
    s = (older_than or "30d").strip().lower()
    days = 30.0
    if s.endswith("d"):
        try:
            days = float(s[:-1])
        except ValueError:
            days = 30.0
    else:
        try:
            days = float(s)
        except ValueError:
            days = 30.0
    result = cleanup_older_runs(repo_root=root, older_than_days=days, dry_run=dry_run, archive=archive)
    run_ids = result.get("run_ids") or []
    archived = result.get("archived") or []
    console.print(f"[bold]Runs older than {days} days:[/bold] {len(run_ids)}")
    if run_ids:
        for rid in run_ids[:30]:
            console.print(f"  {rid}")
        if len(run_ids) > 30:
            console.print(f"  ... and {len(run_ids) - 30} more")
    if result.get("dry_run"):
        console.print("[dim]Dry run. Use --no-dry-run --archive to archive these runs.[/dim]")
    elif archived:
        console.print(f"[green]Archived: {archived}[/green]")


def _review_workspaces_root() -> Path:
    from workflow_dataset.path_utils import get_repo_root
    return get_repo_root() / "data/local/workspaces"


def _resolve_workspace_arg(workspace: str) -> Path | None:
    """Resolve --workspace: path, workflow/run_id, or 'latest' (most recent) under data/local/workspaces."""
    from workflow_dataset.path_utils import get_repo_root
    from workflow_dataset.release.reporting_workspaces import list_reporting_workspaces
    root = _review_workspaces_root()
    if workspace.strip().lower() == "latest":
        items = list_reporting_workspaces(root, limit=1)
        if not items:
            return None
        path_str = items[0].get("workspace_path")
        return Path(path_str).resolve() if path_str else None
    p = Path(workspace)
    if p.exists() and p.is_dir():
        return p.resolve()
    if not p.is_absolute() and "/" in workspace:
        # e.g. weekly_status/2025-03-15_1432_abc
        candidate = root / workspace
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    candidate = root / workspace
    if candidate.exists() and candidate.is_dir():
        return candidate.resolve()
    for workflow_dir in root.iterdir():
        if workflow_dir.is_dir() and (workflow_dir / workspace).exists():
            return (workflow_dir / workspace).resolve()
    return None


@review_group.command("list-workspaces")
def review_list_workspaces(
    limit: int = typer.Option(20, "--limit", "-n", help="Max workspaces to list"),
) -> None:
    """List recent saved reporting workspaces (weekly_status, bundles, ops_reporting_workspace)."""
    from workflow_dataset.release.reporting_workspaces import list_reporting_workspaces
    root = _review_workspaces_root()
    items = list_reporting_workspaces(root, limit=limit)
    if not items:
        console.print("[dim]No reporting workspaces found under data/local/workspaces/[/dim]")
        raise typer.Exit(0)
    for inv in items:
        path = inv.get("workspace_path", "")
        workflow = inv.get("workflow", "?")
        ts = inv.get("timestamp") or "[no timestamp]"
        n = len(inv.get("artifacts") or [])
        console.print(f"  [bold]{workflow}[/bold]  {Path(path).name}  ({n} artifacts)  {ts}")
        console.print(f"    [dim]{path}[/dim]")


@review_group.command("show-workspace")
def review_show_workspace(
    workspace: str = typer.Argument(..., help="Workspace path or workflow/run_id (e.g. weekly_status/2025-03-15_1432_abc)"),
) -> None:
    """Show workspace inventory and current review state."""
    from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
    from workflow_dataset.release.review_state import load_review_state
    ws = _resolve_workspace_arg(workspace)
    if not ws:
        console.print(f"[red]Workspace not found: {workspace}[/red]")
        raise typer.Exit(1)
    inv = get_workspace_inventory(ws)
    if not inv:
        console.print(f"[red]Not a valid reporting workspace: {ws}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]Workspace:[/bold] {ws}")
    console.print(f"  Workflow: {inv.get('workflow', '?')}")
    console.print(f"  Timestamp: {inv.get('timestamp', '—')}")
    console.print(f"  Grounding: {inv.get('grounding', '—')}")
    console.print("[bold]Artifacts:[/bold]")
    state = load_review_state(ws)
    artifacts_state = state.get("artifacts") or {}
    for a in inv.get("artifacts") or []:
        meta = artifacts_state.get(a) or {}
        review_state = meta.get("state") or "—"
        console.print(f"  — {a}  [dim]review: {review_state}[/dim]")
    if state.get("last_package_path"):
        console.print(f"[bold]Last package:[/bold] {state['last_package_path']}")


@review_group.command("diff-workspaces")
def review_diff_workspaces(
    path_a: str = typer.Argument(..., help="First workspace path or workflow/run_id"),
    path_b: str = typer.Argument(..., help="Second workspace path or workflow/run_id"),
    no_diffs: bool = typer.Option(False, "--no-diffs", help="Skip artifact text diffs; show only inventory and manifest diff"),
) -> None:
    """Compare two workspace runs: inventory, manifest metadata, and artifact deltas. Does not mutate either workspace."""
    from workflow_dataset.release.workspace_rerun_diff import diff_workspaces
    pa = _resolve_workspace_arg(path_a)
    pb = _resolve_workspace_arg(path_b)
    if not pa:
        console.print(f"[red]Workspace not found: {path_a}[/red]")
        raise typer.Exit(1)
    if not pb:
        console.print(f"[red]Workspace not found: {path_b}[/red]")
        raise typer.Exit(1)
    result = diff_workspaces(pa, pb, include_artifact_diffs=not no_diffs)
    console.print("[bold]Workspace diff[/bold]")
    console.print(f"  A: {result['path_a']}")
    console.print(f"  B: {result['path_b']}")
    inv = result.get("inventory_diff") or {}
    console.print("[bold]Inventory[/bold]")
    console.print(f"  only in A: {inv.get('only_in_a', [])}")
    console.print(f"  only in B: {inv.get('only_in_b', [])}")
    console.print(f"  common: {inv.get('common', [])}")
    meta = result.get("manifest_metadata_diff") or {}
    if meta:
        console.print("[bold]Manifest metadata diff[/bold]")
        for k, v in meta.items():
            console.print(f"  {k}: A={v.get('a')}  B={v.get('b')}")
    else:
        console.print("[bold]Manifest metadata:[/bold] no differences")
    deltas = result.get("artifact_deltas") or {}
    if deltas:
        console.print("[bold]Artifact deltas[/bold]")
        for name, info in deltas.items():
            if "error" in info:
                console.print(f"  {name}: {info['error']}")
            else:
                console.print(f"  {name}: {info.get('diff_lines', 0)} diff lines")
                if info.get("preview"):
                    for line in (info["preview"] or "").strip().split("\n")[:15]:
                        console.print(f"    [dim]{line}[/dim]")
    else:
        console.print("[bold]Artifact deltas:[/bold] none")


@review_group.command("workspace-timeline")
def review_workspace_timeline(
    workflow: str = typer.Option("ops_reporting_workspace", "--workflow", "-w", help="Filter by workflow"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max runs to show"),
) -> None:
    """Show provenance timeline of workspace runs (newest first): timestamp, run_id, grounding, artifact count."""
    from workflow_dataset.release.workspace_rerun_diff import workspace_timeline
    root = _review_workspaces_root()
    items = workspace_timeline(root, workflow=workflow, limit=limit)
    if not items:
        console.print("[dim]No workspace runs found.[/dim]")
        raise typer.Exit(0)
    console.print(f"[bold]Workspace timeline[/bold] (workflow={workflow}, limit={limit})")
    for t in items:
        ts = t.get("timestamp") or "—"
        rid = t.get("run_id") or "—"
        gr = t.get("grounding") or "—"
        n = t.get("artifact_count") or 0
        console.print(f"  {ts}  {rid}  grounding={gr}  artifacts={n}")
        console.print(f"    [dim]{t.get('workspace_path', '')}[/dim]")


@review_group.command("validate-workspace")
def review_validate_workspace(
    workspace: str = typer.Argument(..., help="Workspace path or workflow/run_id to validate against export contract"),
) -> None:
    """Validate a workspace against the export contract (schema version, required/optional files, manifest compatibility)."""
    from workflow_dataset.release.workspace_export_contract import (
        WORKSPACE_EXPORT_SCHEMA_VERSION,
        validate_workspace_export,
    )
    ws = _resolve_workspace_arg(workspace)
    if not ws:
        console.print(f"[red]Workspace not found: {workspace}[/red]")
        raise typer.Exit(1)
    result = validate_workspace_export(ws, schema_version=WORKSPACE_EXPORT_SCHEMA_VERSION)
    console.print(f"[bold]Export contract validation[/bold] (schema version {result.get('contract_version', '?')})")
    console.print(f"  Workspace: {ws}")
    console.print(f"  Workflow: {result.get('workflow', '—')}")
    console.print(f"  Manifest compatible: {result.get('manifest_compatible', False)}")
    if result.get("valid"):
        console.print("[green]Valid: workspace meets export contract.[/green]")
    else:
        console.print("[red]Invalid:[/red]")
        for e in result.get("errors") or []:
            console.print(f"  — {e}")
    for w in result.get("warnings") or []:
        console.print(f"  [yellow]Warning:[/yellow] {w}")
    if not result.get("valid"):
        raise typer.Exit(1)


@review_group.command("export-contract")
def review_export_contract(
    workflow: str = typer.Option("ops_reporting_workspace", "--workflow", "-w", help="Workflow to show contract for"),
) -> None:
    """Print the export contract for a workflow (schema version, required/optional files, manifest keys)."""
    from workflow_dataset.release.workspace_export_contract import (
        WORKSPACE_EXPORT_SCHEMA_VERSION,
        EXPORT_CONTRACTS,
        get_export_contract,
    )
    contract = get_export_contract(workflow)
    console.print(f"[bold]Export contract[/bold] (schema version {WORKSPACE_EXPORT_SCHEMA_VERSION})")
    if not contract:
        console.print(f"[yellow]No contract defined for workflow: {workflow}[/yellow]")
        console.print("Known workflows: " + ", ".join(EXPORT_CONTRACTS.keys()))
        raise typer.Exit(0)
    console.print(f"  Workflow: {workflow}")
    console.print(f"  Description: {contract.get('description', '—')}")
    console.print(f"  Manifest file: {contract.get('manifest_file', '—')}")
    console.print(f"  Required manifest keys: {contract.get('required_manifest_keys', [])}")
    console.print(f"  Required files: {contract.get('required_files', [])}")
    console.print(f"  Optional files: {contract.get('optional_files', [])}")
    if contract.get("required_at_least_one_of"):
        console.print(f"  Required at least one of: {contract['required_at_least_one_of']}")


@review_group.command("approve-artifact")
def review_approve_artifact(
    workspace: str = typer.Argument(..., help="Workspace path or workflow/run_id"),
    artifact: str = typer.Option(..., "--artifact", "-a", help="Artifact filename (e.g. weekly_status.md)"),
    note: str = typer.Option("", "--note", help="Optional note"),
) -> None:
    """Mark an artifact as approved for packaging."""
    from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
    from workflow_dataset.release.review_state import set_artifact_state
    ws = _resolve_workspace_arg(workspace)
    if not ws:
        console.print(f"[red]Workspace not found: {workspace}[/red]")
        raise typer.Exit(1)
    inv = get_workspace_inventory(ws)
    artifacts = inv.get("artifacts") or [] if inv else []
    if artifact not in artifacts:
        console.print(f"[red]Unknown artifact: {artifact}. Known: {artifacts}[/red]")
        raise typer.Exit(1)
    set_artifact_state(ws, artifact, "approved", note=note)
    console.print(f"[green]Approved: {artifact}[/green]")


@review_group.command("set-artifact-state")
def review_set_artifact_state(
    workspace: str = typer.Argument(..., help="Workspace path or workflow/run_id"),
    artifact: str = typer.Option(..., "--artifact", "-a", help="Artifact filename"),
    state: str = typer.Option(..., "--state", "-s", help="approved | needs_revision | excluded"),
    note: str = typer.Option("", "--note"),
) -> None:
    """Set artifact review state: approved, needs_revision, or excluded."""
    from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
    from workflow_dataset.release.review_state import set_artifact_state, VALID_STATES
    ws = _resolve_workspace_arg(workspace)
    if not ws:
        console.print(f"[red]Workspace not found: {workspace}[/red]")
        raise typer.Exit(1)
    if state not in VALID_STATES:
        console.print(f"[red]state must be one of: {VALID_STATES}[/red]")
        raise typer.Exit(1)
    inv = get_workspace_inventory(ws)
    artifacts = inv.get("artifacts") or [] if inv else []
    if artifact not in artifacts:
        console.print(f"[red]Unknown artifact: {artifact}. Known: {artifacts}[/red]")
        raise typer.Exit(1)
    set_artifact_state(ws, artifact, state, note=note)
    console.print(f"[green]{artifact} -> {state}[/green]")


@review_group.command("build-package")
def review_build_package(
    workspace: str = typer.Argument(..., help="Workspace path or workflow/run_id"),
    profile: str = typer.Option(
        "",
        "--profile",
        "-p",
        help="Handoff profile: internal_team (all approved), stakeholder (stakeholder-facing only), operator_archive (all, audit). Omit for default (all approved).",
    ),
) -> None:
    """Build publishable package from approved artifacts. Writes to data/local/packages/. No apply. Use --profile for handoff type."""
    from workflow_dataset.release.package_builder import build_package
    from workflow_dataset.release.handoff_profiles import VALID_PROFILES
    ws = _resolve_workspace_arg(workspace)
    if not ws:
        console.print(f"[red]Workspace not found: {workspace}[/red]")
        raise typer.Exit(1)
    profile_arg = profile.strip() or None
    if profile and profile.strip() and profile.strip().lower() not in VALID_PROFILES:
        console.print(f"[red]Unknown profile: {profile}. Valid: {list(VALID_PROFILES)}[/red]")
        raise typer.Exit(1)
    try:
        package_dir = build_package(ws, profile=profile_arg)
        console.print(f"[green]Package built:[/green] {package_dir.resolve()}")
        if profile_arg:
            console.print(f"  [dim]Profile: {profile_arg}[/dim]")
        for f in sorted(package_dir.iterdir()):
            if f.is_file():
                console.print(f"  — {f.name}")
        console.print("[dim]To apply to a target: workflow-dataset assist apply-plan <package_dir> <target>[/dim]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@review_group.command("metrics")
def review_metrics_cmd(
    limit: int = typer.Option(200, "--limit", "-n", help="Max workspaces to include in metrics"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON (read-only metrics)."),
) -> None:
    """Review queue metrics: pending count, revision rate, avg approved per workspace/package, common revision reasons. Local, read-only."""
    from workflow_dataset.release.review_metrics import get_review_metrics
    root = _review_workspaces_root()
    metrics = get_review_metrics(root, limit_workspaces=limit)
    if json_output:
        import json
        console.print(json.dumps(metrics, indent=2))
        return
    console.print("[bold]Review queue metrics[/bold]")
    console.print(f"  Workspaces: {metrics['workspaces_total']} total, {metrics['workspaces_pending_review']} with pending review")
    console.print(f"  Artifacts: {metrics['artifacts_total']} total — {metrics['artifacts_reviewed']} reviewed, {metrics['artifacts_pending']} pending")
    console.print(f"  States: {metrics['artifacts_approved']} approved, {metrics['artifacts_needs_revision']} needs_revision, {metrics['artifacts_excluded']} excluded")
    rev_rate = metrics.get("revision_rate")
    if rev_rate is not None:
        console.print(f"  Revision rate: {rev_rate:.1%} (needs_revision / reviewed)")
    else:
        console.print("  Revision rate: — (no reviewed artifacts)")
    avg_ws = metrics.get("avg_approved_per_workspace")
    if avg_ws is not None:
        console.print(f"  Avg approved per workspace: {avg_ws:.1f}")
    avg_pkg = metrics.get("avg_approved_per_package")
    if avg_pkg is not None:
        console.print(f"  Avg approved per package: {avg_pkg:.1f} (over {metrics['workspaces_with_package']} workspace(s) with package)")
    reasons = metrics.get("revision_reasons") or []
    if reasons:
        console.print("[bold]Common revision reasons[/bold]")
        for r in reasons[:10]:
            console.print(f"  — {r['count']}× \"{r['reason'][:60]}{'…' if len(r['reason']) > 60 else ''}\"")
    else:
        console.print("[dim]No revision reasons recorded.[/dim]")


@review_group.command("list-profiles")
def review_list_profiles() -> None:
    """List handoff profiles for build-package (internal_team, stakeholder, operator_archive)."""
    from workflow_dataset.release.handoff_profiles import list_profiles
    for p in list_profiles():
        console.print(f"  [bold]{p['name']}[/bold] — {p['label']}")
        console.print(f"    [dim]{p['description']}[/dim]")


@review_group.command("package-status")
def review_package_status(
    workspace: str = typer.Argument(..., help="Workspace path or workflow/run_id"),
) -> None:
    """Show review state and last built package path for this workspace."""
    from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
    from workflow_dataset.release.review_state import load_review_state, get_approved_artifacts
    ws = _resolve_workspace_arg(workspace)
    if not ws:
        console.print(f"[red]Workspace not found: {workspace}[/red]")
        raise typer.Exit(1)
    inv = get_workspace_inventory(ws)
    if not inv:
        console.print(f"[red]Not a valid reporting workspace: {ws}[/red]")
        raise typer.Exit(1)
    state = load_review_state(ws)
    approved = get_approved_artifacts(ws)
    console.print(f"[bold]Workspace:[/bold] {ws.name}")
    console.print(f"  Lane: {state.get('lane') or '—'}")
    console.print(f"  Approved artifacts: {len(approved)} — {approved or 'none'}")
    console.print(f"  Last package: {state.get('last_package_path') or '—'}")


# ----- M22C Role-based review lanes -----
@review_group.command("lane-status")
def review_lane_status(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show role-lane summary: workspaces and packages per lane, pending counts, needs-revision. Local-only."""
    from workflow_dataset.release.lane_views import get_lane_status
    from workflow_dataset.release.review_state import LANES
    root = Path(repo_root) if repo_root else None
    status = get_lane_status(repo_root=root)
    console.print("[bold]Review lanes (local)[/bold]")
    for lane in LANES:
        s = status.get("summary_by_lane", {}).get(lane, {})
        console.print(f"  [bold]{lane}[/bold]: workspaces={s.get('count_workspaces', 0)}  packages={s.get('count_packages', 0)}  pending={s.get('pending_count', 0)}  needs_revision={s.get('needs_revision_count', 0)}")
    un = status.get("unlane", {})
    if un.get("count_workspaces") or un.get("count_packages"):
        console.print(f"  [dim]no lane[/dim]: workspaces={un.get('count_workspaces', 0)}  packages={un.get('count_packages', 0)}  pending={un.get('pending_count', 0)}")
    console.print("[dim]Assign lane: workflow-dataset review assign-lane --workspace <path> --lane <operator|reviewer|stakeholder-prep|approver>[/dim]")


@review_group.command("assign-lane")
def review_assign_lane(
    workspace: str = typer.Option("", "--workspace", "-w", help="Workspace path or workflow/run_id"),
    package: str = typer.Option("", "--package", "-p", help="Package directory path or name under data/local/packages"),
    lane: str = typer.Option(..., "--lane", "-l", help="Lane: operator, reviewer, stakeholder-prep, approver"),
) -> None:
    """Assign a role lane to a workspace or package. Local-only; no cloud sync."""
    from workflow_dataset.release.review_state import set_workspace_lane, LANES
    from workflow_dataset.release.lane_views import set_package_lane
    lane = (lane or "").strip().lower()
    if lane not in LANES:
        console.print(f"[red]lane must be one of: {', '.join(LANES)}[/red]")
        raise typer.Exit(1)
    if workspace and package:
        console.print("[red]Provide either --workspace or --package, not both.[/red]")
        raise typer.Exit(1)
    if workspace:
        ws = _resolve_workspace_arg(workspace)
        if not ws:
            console.print(f"[red]Workspace not found: {workspace}[/red]")
            raise typer.Exit(1)
        path = set_workspace_lane(ws, lane)
        console.print(f"[green]Lane set to {lane}[/green] for workspace {ws}")
        console.print(f"  [dim]{path}[/dim]")
    elif package:
        pkg = _resolve_package_arg(package)
        if not pkg:
            console.print(f"[red]Package not found: {package}[/red]")
            raise typer.Exit(1)
        path = set_package_lane(pkg, lane)
        console.print(f"[green]Lane set to {lane}[/green] for package {pkg}")
        console.print(f"  [dim]{path}[/dim]")
    else:
        console.print("[red]Provide --workspace or --package.[/red]")
        raise typer.Exit(1)


@review_group.command("list-lane")
def review_list_lane(
    lane: str = typer.Option(..., "--lane", "-l", help="Lane: operator, reviewer, stakeholder-prep, approver"),
    packages: bool = typer.Option(False, "--packages", help="List packages in lane instead of workspaces"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    limit: int = typer.Option(30, "--limit", "-n", help="Max items"),
) -> None:
    """List workspaces (or packages with --packages) in a role lane."""
    from workflow_dataset.release.lane_views import list_workspaces_in_lane, list_packages_in_lane
    from workflow_dataset.release.review_state import LANES
    lane = (lane or "").strip().lower()
    if lane not in LANES:
        console.print(f"[red]lane must be one of: {', '.join(LANES)}[/red]")
        raise typer.Exit(1)
    root = Path(repo_root) if repo_root else None
    if packages:
        items = list_packages_in_lane(lane, repo_root=root, limit=limit)
        if not items:
            console.print(f"[dim]No packages in lane '{lane}'.[/dim]")
            raise typer.Exit(0)
        console.print(f"[bold]Packages in lane: {lane}[/bold] ({len(items)})")
        for it in items:
            console.print(f"  {it.get('package_dir', '')}  workflow={it.get('workflow', '?')}  artifacts={it.get('artifact_count', 0)}")
            console.print(f"    [dim]{it.get('package_path', '')}[/dim]")
    else:
        items = list_workspaces_in_lane(lane, repo_root=root, limit=limit)
        if not items:
            console.print(f"[dim]No workspaces in lane '{lane}'.[/dim]")
            raise typer.Exit(0)
        console.print(f"[bold]Workspaces in lane: {lane}[/bold] ({len(items)})")
        for it in items:
            st = it.get("status", "?")
            rev = "  [yellow]needs_revision[/yellow]" if it.get("needs_revision") else ""
            console.print(f"  {it.get('run_id', '')}  {it.get('workflow', '?')}  status={st}{rev}")
            console.print(f"    [dim]{it.get('workspace_path', '')}[/dim]")


def _resolve_package_arg(package: str) -> Path | None:
    """Resolve package: path, packages/<run_id>, or 'latest' (newest dir under data/local/packages)."""
    from workflow_dataset.path_utils import get_repo_root
    root = Path(get_repo_root()) / "data/local/packages"
    if not root.exists():
        return None
    pkg_arg = (package or "").strip()
    if pkg_arg.lower() == "latest":
        dirs = sorted([d for d in root.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
        return dirs[0].resolve() if dirs else None
    p = Path(package)
    if p.exists() and p.is_dir():
        return p.resolve()
    candidate = root / package
    if candidate.exists() and candidate.is_dir():
        return candidate.resolve()
    if not p.is_absolute():
        for d in root.iterdir():
            if d.is_dir() and d.name == package:
                return d.resolve()
    return None


# ----- M21V Staging board -----
@review_group.command("queue-status")
def review_queue_status() -> None:
    """Show review queue and staging board summary: workspaces, packages, staged items."""
    from workflow_dataset.release.reporting_workspaces import list_reporting_workspaces
    from workflow_dataset.release.review_state import get_approved_artifacts, load_review_state
    from workflow_dataset.release.staging_board import load_staging_board
    root = _review_workspaces_root()
    workspaces = list_reporting_workspaces(root, limit=20)
    unreviewed = package_pending = 0
    for inv in workspaces:
        wp = inv.get("workspace_path")
        if not wp:
            continue
        state = load_review_state(Path(wp))
        approved = get_approved_artifacts(Path(wp))
        artifacts_count = len(inv.get("artifacts") or [])
        has_any = bool(state.get("artifacts"))
        if not has_any and artifacts_count > 0:
            unreviewed += 1
        elif approved and not state.get("last_package_path"):
            package_pending += 1
    board = load_staging_board()
    staged = board.get("items") or []
    console.print("[bold]Review queue[/bold]")
    console.print(f"  Workspaces awaiting review: {unreviewed}")
    console.print(f"  Approved, package not built: {package_pending}")
    console.print("[bold]Staging board[/bold]")
    console.print(f"  Staged items: {len(staged)}")
    if staged:
        for i in staged[:5]:
            console.print(f"    — {i.get('staged_id', '')}  {i.get('source_type', '')}  {i.get('workflow', '')}  {Path(i.get('source_path', '')).name}")
    if board.get("last_apply_plan_preview_path"):
        console.print(f"  Last apply-plan preview: {board['last_apply_plan_preview_path']}")


@review_group.command("stage-package")
def review_stage_package(
    package: str = typer.Argument(..., help="Package path, id, or 'latest' (e.g. latest or data/local/packages/2025-03-15_1500_abc)"),
) -> None:
    """Add a built package to the staging board. No apply."""
    from workflow_dataset.release.staging_board import add_staged_package
    pkg_path = _resolve_package_arg(package)
    if not pkg_path:
        console.print(f"[red]Package not found: {package}[/red]")
        raise typer.Exit(1)
    try:
        item = add_staged_package(pkg_path)
        console.print(f"[green]Staged package:[/green] {item.get('staged_id', '')}")
        console.print(f"  Source: {item.get('source_path', '')}")
        console.print(f"  Artifacts: {item.get('artifact_paths', [])}")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@review_group.command("stage-artifact")
def review_stage_artifact(
    workspace: str = typer.Argument(..., help="Workspace path or workflow/run_id"),
    artifact: str = typer.Option(..., "--artifact", "-a", help="Artifact filename to stage (e.g. weekly_status.md)"),
) -> None:
    """Add one approved artifact from a workspace to the staging board. No apply."""
    from workflow_dataset.release.staging_board import add_staged_artifact
    from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
    ws = _resolve_workspace_arg(workspace)
    if not ws:
        console.print(f"[red]Workspace not found: {workspace}[/red]")
        raise typer.Exit(1)
    inv = get_workspace_inventory(ws)
    if not inv or artifact not in (inv.get("artifacts") or []):
        console.print(f"[red]Artifact {artifact} not in workspace. Known: {inv.get('artifacts', []) if inv else []}[/red]")
        raise typer.Exit(1)
    try:
        item = add_staged_artifact(ws, artifact)
        console.print(f"[green]Staged artifact:[/green] {item.get('staged_id', '')}")
        console.print(f"  Workspace: {item.get('source_path', '')}  artifact: {artifact}")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@review_group.command("staging-board")
def review_staging_board() -> None:
    """List all items on the staging board with source and provenance."""
    from workflow_dataset.release.staging_board import list_staged_items
    items = list_staged_items()
    if not items:
        console.print("[dim]Staging board is empty. Use review stage-package or review stage-artifact.[/dim]")
        raise typer.Exit(0)
    for i in items:
        console.print(f"  [bold]{i.get('staged_id', '')}[/bold]  {i.get('source_type', '')}  {i.get('workflow', '')}")
        console.print(f"    Source: {i.get('source_path', '')}")
        console.print(f"    Artifacts: {i.get('artifact_paths', [])}")
        console.print(f"    Staged: {i.get('staged_at', '')}")


@review_group.command("unstage")
def review_unstage(
    item: str = typer.Option(..., "--item", "-i", help="Staged item id (from staging-board)"),
) -> None:
    """Remove one item from the staging board."""
    from workflow_dataset.release.staging_board import remove_staged_item
    if remove_staged_item(item):
        console.print(f"[green]Removed staged item: {item}[/green]")
    else:
        console.print(f"[red]No staged item with id: {item}[/red]")
        raise typer.Exit(1)


@review_group.command("clear-staging")
def review_clear_staging() -> None:
    """Clear all items from the staging board. No apply."""
    from workflow_dataset.release.staging_board import clear_staging
    clear_staging()
    console.print("[green]Staging board cleared.[/green]")


@review_group.command("build-apply-plan")
def review_build_apply_plan(
    target: str = typer.Argument(..., help="Target directory path for apply-plan preview"),
    item: str = typer.Option("", "--item", "-i", help="Staged item id (default: first item)"),
) -> None:
    """Build apply-plan preview from staging board. No apply; use assist apply with --confirm to apply."""
    from workflow_dataset.release.staging_board import build_apply_plan_from_staging
    from workflow_dataset.apply.diff_preview import render_diff_preview
    plan, err = build_apply_plan_from_staging(target, item_id=item or None, save_preview=True)
    if err and not plan:
        console.print(f"[red]{err}[/red]")
        raise typer.Exit(1)
    if plan:
        console.print(render_diff_preview(plan))
        from workflow_dataset.release.staging_board import get_last_apply_plan_preview_path
        path = get_last_apply_plan_preview_path()
        if path:
            console.print(f"[dim]Preview saved: {path}[/dim]")
        console.print("[dim]No apply performed. To apply: workflow-dataset assist apply <source_dir> <target> --confirm[/dim]")


@review_group.command("apply-plan-status")
def review_apply_plan_status() -> None:
    """Show staging board state, last apply-plan preview, and next command to proceed."""
    from workflow_dataset.release.staging_board import load_staging_board
    board = load_staging_board()
    items = board.get("items") or []
    console.print(f"[bold]Staged items:[/bold] {len(items)}")
    if items:
        latest = items[-1]
        console.print(f"[bold]Latest staged:[/bold] {latest.get('staged_id', '')}  {latest.get('source_type', '')}  {Path(latest.get('source_path', '')).name}")
    path = board.get("last_apply_plan_preview_path")
    if path:
        console.print(f"[bold]Last apply-plan preview:[/bold] {path}")
        console.print("[dim]View: cat " + path + "[/dim]")
    else:
        console.print("[dim]Last apply-plan preview: none[/dim]")
    console.print("[bold]Next:[/bold] ", end="")
    if not items:
        console.print("[dim]review stage-package <path|latest> or review stage-artifact <workspace> --artifact <name>[/dim]")
    elif not path:
        console.print("[dim]review build-apply-plan <target_path>[/dim]")
    else:
        console.print("[dim]review build-apply-plan <target_path> to refresh, or assist apply <source> <target> --confirm to apply[/dim]")


# ----- M21T-F2 Revision loop + package compare -----
@review_group.command("package-compare")
def review_package_compare(
    package_a: str = typer.Option(..., "--package-a", "-a", help="First package (path, id, or 'latest')"),
    package_b: str = typer.Option(..., "--package-b", "-b", help="Second package (path, id, or 'latest')"),
    no_diffs: bool = typer.Option(False, "--no-diffs", help="Skip artifact content diffs; show only inventory and manifest"),
) -> None:
    """Compare two packages: artifact inventory, manifest, revision state, and optional content deltas."""
    from workflow_dataset.release.package_compare import compare_packages, format_package_compare_for_console
    pa = _resolve_package_arg(package_a)
    pb = _resolve_package_arg(package_b)
    if not pa:
        console.print(f"[red]Package not found: {package_a}[/red]")
        raise typer.Exit(1)
    if not pb:
        console.print(f"[red]Package not found: {package_b}[/red]")
        raise typer.Exit(1)
    result = compare_packages(pa, pb, include_content_diff=not no_diffs)
    console.print(format_package_compare_for_console(result))


@review_group.command("mark-superseded")
def review_mark_superseded(
    package: str = typer.Option(..., "--package", "-p", help="Package that supersedes (B)"),
    supersedes: str = typer.Option(..., "--supersedes", "-s", help="Package that is superseded (A)"),
    reason: str = typer.Option("", "--reason", "-r", help="Revision reason"),
    note: str = typer.Option("", "--note", "-n", help="Operator note"),
) -> None:
    """Mark package B as superseding package A. Updates revision_meta in both; A status becomes superseded."""
    from workflow_dataset.release.package_revision import set_supersedes
    pkg_b = _resolve_package_arg(package)
    pkg_a = _resolve_package_arg(supersedes)
    if not pkg_b:
        console.print(f"[red]Package not found: {package}[/red]")
        raise typer.Exit(1)
    if not pkg_a:
        console.print(f"[red]Package not found: {supersedes}[/red]")
        raise typer.Exit(1)
    set_supersedes(pkg_b, pkg_a, reason=reason, note=note)
    console.print(f"[green]{pkg_b.name} supersedes {pkg_a.name}[/green]")
    if reason:
        console.print(f"  [dim]Reason: {reason}[/dim]")
    if note:
        console.print(f"  [dim]Note: {note}[/dim]")


@review_group.command("package-lineage")
def review_package_lineage(
    package: str = typer.Argument(..., help="Package path, id, or 'latest'"),
) -> None:
    """Show revision lineage for a package: status, supersedes, superseded_by, notes."""
    from workflow_dataset.release.package_revision import get_lineage
    pkg = _resolve_package_arg(package)
    if not pkg:
        console.print(f"[red]Package not found: {package}[/red]")
        raise typer.Exit(1)
    lineage = get_lineage(pkg)
    console.print(f"[bold]Package:[/bold] {lineage['name']}")
    console.print(f"  Path: {lineage['path']}")
    console.print(f"  Status: {lineage['status']}")
    if lineage.get("supersedes"):
        console.print(f"  Supersedes: {lineage['supersedes']}")
    if lineage.get("superseded_by"):
        console.print(f"  Superseded by: {lineage['superseded_by']}")
    if lineage.get("revision_reason"):
        console.print(f"  Reason: {lineage['revision_reason']}")
    if lineage.get("revision_note"):
        console.print(f"  Note: {lineage['revision_note']}")
    if lineage.get("updated_at"):
        console.print(f"  Updated: {lineage['updated_at']}")


@review_group.command("set-package-status")
def review_set_package_status(
    package: str = typer.Argument(..., help="Package path, id, or 'latest'"),
    status: str = typer.Option(..., "--status", "-s", help="approved | needs_revision | superseded | archived"),
    note: str = typer.Option("", "--note", "-n", help="Optional note"),
) -> None:
    """Set package revision status. Use mark-superseded to link B supersedes A."""
    from workflow_dataset.release.package_revision import set_package_status, PACKAGE_STATUSES
    if status not in PACKAGE_STATUSES:
        console.print(f"[red]status must be one of: {PACKAGE_STATUSES}[/red]")
        raise typer.Exit(1)
    pkg = _resolve_package_arg(package)
    if not pkg:
        console.print(f"[red]Package not found: {package}[/red]")
        raise typer.Exit(1)
    set_package_status(pkg, status, note=note)
    console.print(f"[green]{pkg.name} -> {status}[/green]")


# ----- M21 Capability intake -----
sources_group = typer.Typer(
    help="Open-source capability intake: list sources, show, report, classify.")
app.add_typer(sources_group, name="sources")

packs_group = typer.Typer(
    help="Capability packs: list, show, install, uninstall, validate, resolve.")
app.add_typer(packs_group, name="packs")

# M23U: Domain packs (vertical-specific: founder_ops, office_admin, etc.)
packs_domain_group = typer.Typer(help="Domain packs: list, recommend by field. M23U.")
packs_group.add_typer(packs_domain_group, name="domain")


@packs_domain_group.command("list")
def packs_domain_list() -> None:
    """List built-in domain pack IDs and names."""
    from workflow_dataset.domain_packs import list_domain_packs, get_domain_pack
    for did in list_domain_packs():
        pack = get_domain_pack(did)
        name = pack.name if pack else ""
        console.print(f"  [bold]{did}[/bold] — {name}")


@packs_domain_group.command("recommend")
def packs_domain_recommend(
    field: str = typer.Option("", "--field", "-f", help="User field e.g. operations, founder"),
    job_family: str = typer.Option("", "--job-family", "-j", help="Job family e.g. office_admin, analyst"),
) -> None:
    """Recommend domain packs for a field (and optional job family)."""
    from workflow_dataset.domain_packs import recommend_domain_packs
    recs = recommend_domain_packs(field=field, job_family=job_family)
    if not recs:
        console.print("[yellow]No domain packs.[/yellow]")
        return
    console.print(f"[bold]Recommended domain packs[/bold] (field={field or '(any)'}, job_family={job_family or '(any)'})")
    for pack, score in recs[:10]:
        console.print(f"  [bold]{pack.domain_id}[/bold] — {pack.name} (score: {score:.2f})")

# ----- M23U Specialization recipes (generation only; no auto-download/train) -----
recipe_group = typer.Typer(
    help="Specialization recipes: build for domain pack, explain by id. Recipe generation only.")
app.add_typer(recipe_group, name="recipe")


@recipe_group.command("build")
def recipe_build(
    pack: str = typer.Option(..., "--pack", "-p", help="Domain pack id e.g. founder_ops"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Build specialization recipe for a domain pack. Outputs recipe spec only; no download or training."""
    from workflow_dataset.specialization import build_recipe_for_domain_pack
    root = Path(repo_root).resolve() if repo_root else None
    recipe = build_recipe_for_domain_pack(pack, repo_root=root)
    if not recipe:
        console.print(f"[red]No recipe for pack '{pack}' or pack not found.[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{recipe.recipe_id}[/bold] — {recipe.name}")
    console.print(f"  mode: {recipe.mode}")
    console.print(f"  auto_download: {recipe.auto_download}  auto_train: {recipe.auto_train}")
    console.print("  steps_summary:")
    for s in recipe.steps_summary:
        console.print(f"    - {s}")


@recipe_group.command("explain")
def recipe_explain(
    id_arg: str = typer.Argument(..., help="Recipe id e.g. retrieval_only, adapter_finetune"),
) -> None:
    """Explain a specialization recipe: mode, data sources, licensing, steps. No side effects."""
    from workflow_dataset.specialization import explain_recipe
    out = explain_recipe(id_arg)
    if not out.get("found"):
        console.print(f"[red]{out.get('message', 'Recipe not found.')}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{out['recipe_id']}[/bold] — {out.get('name', '')}")
    console.print(f"  description: {out.get('description', '')}")
    console.print(f"  mode: {out.get('mode', '')}")
    console.print(f"  auto_download: {out.get('auto_download')}  auto_train: {out.get('auto_train')}")
    console.print("  steps_summary:")
    for s in out.get("steps_summary", []):
        console.print(f"    - {s}")

# ----- M21W Development lab -----
devlab_group = typer.Typer(
    help="Development lab: curated repo intake, model comparison, operator-controlled dev loop.")
app.add_typer(devlab_group, name="devlab")


@devlab_group.command("list")
def devlab_list(
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """List registered devlab repos."""
    from workflow_dataset.devlab.repo_intake import load_registry
    root = devlab_root or None
    entries = load_registry(root)
    if not entries:
        console.print("[dim]No repos registered. Use devlab add-repo --url ...[/dim]")
        return
    for e in entries:
        console.print(f"  [bold]{e.get('repo_id')}[/bold]  {e.get('category')}  {e.get('url')}")


@devlab_group.command("add-repo")
def devlab_add_repo(
    url: str = typer.Option(..., "--url", "-u", help="Repository URL (e.g. https://github.com/owner/repo)"),
    label: str = typer.Option("", "--label", "-l", help="Why useful / short label"),
    category: str = typer.Option(
        "other", "--category", "-c",
        help="Category: UI, retrieval, evaluation, agent tooling, workflow engine, packaging, local model tooling, other"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority: low, medium, high"),
    devlab_root: str = typer.Option("", "--devlab-root", help="Override devlab sandbox root"),
) -> None:
    """Register a candidate repo for research. Does not clone; use ingest-repo to clone and parse."""
    from workflow_dataset.devlab.repo_intake import register_repo
    root = devlab_root or None
    entry = register_repo(url=url, label=label, category=category, priority=priority, root=root)
    console.print(f"[green]Registered: {entry.get('repo_id')}  {url}[/green]")


@devlab_group.command("ingest-repo")
def devlab_ingest_repo(
    repo: str = typer.Argument(..., help="Repo id or URL (must be registered for URL)"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Clone repo into sandbox (if needed) and parse-only. No execution of external code."""
    from workflow_dataset.devlab.repo_intake import ingest_repo
    root = devlab_root or None
    try:
        data = ingest_repo(repo, root=root)
        console.print(f"[green]Ingested: {data.get('repo_id')} at {data.get('repo_path')}[/green]")
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@devlab_group.command("repo-report")
def devlab_repo_report(
    repo: str = typer.Argument(..., help="Repo id or URL"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Generate per-repo intake report (summary, risks, license, D2 scores and recommendation)."""
    from workflow_dataset.devlab.repo_intake import write_intake_report
    root = devlab_root or None
    try:
        path = write_intake_report(repo, root=root)
        console.print(f"[green]Report: {path}[/green]")
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@devlab_group.command("score-repo")
def devlab_score_repo(
    repo: str = typer.Option(..., "--repo", "-r", help="Repo id to score (must be registered)"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Score one repo: usefulness, license/risk triage, D2 recommendation. Writes or updates intake report."""
    from workflow_dataset.devlab.repo_intake import score_repo
    root = devlab_root or None
    try:
        data = score_repo(repo, root=root)
        console.print(f"[green]{data.get('repo_id')}[/green]  composite={data.get('composite_score', 0):.2f}  {data.get('d2_recommendation')}")
        console.print(f"  relevance={data.get('usefulness_scores', {}).get('relevance')}  risk={data.get('usefulness_scores', {}).get('risk')}")
        triage = data.get("license_triage") or {}
        console.print(f"  license_visible={triage.get('license_visible')}  use_as={triage.get('use_as')}")
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@devlab_group.command("score-repos")
def devlab_score_repos(
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Re-score all existing intake reports (parse-only). Updates reports with D2 usefulness and recommendation."""
    from workflow_dataset.devlab.repo_intake import score_all_reports
    root = devlab_root or None
    updated = score_all_reports(root)
    if not updated:
        console.print("[dim]No reports to score, or repo dirs missing. Run devlab ingest-repo and repo-report first.[/dim]")
        return
    for u in updated:
        console.print(f"  [green]{u['repo_id']}[/green]  {u['d2_recommendation']}")
    console.print(f"[green]Updated {len(updated)} report(s).[/green]")


@devlab_group.command("generate-proposal")
def devlab_generate_proposal(
    repo: str = typer.Option("", "--repo", "-r", help="Focus proposal on this repo id only (optional)"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Generate devlab proposal from repo intake + model compare. Writes devlab_proposal.md, cursor_prompt.txt, rfc_skeleton.md. Advisory only."""
    from workflow_dataset.devlab.proposal_generator import generate_proposal
    root = devlab_root or None
    repo_id = repo.strip() or None
    result = generate_proposal(root, repo_id=repo_id)
    console.print(f"[green]Proposal: {result['proposal_id']}[/green]  path: {result['proposal_path']}")
    console.print(f"  intake reports: {result['intake_count']}  model compare: {result['model_compare_present']}")
    if result.get("next_patch_ranked"):
        console.print("  [dim]Ranked next patch: " + ", ".join(f"{x.get('repo_id')}({x.get('d2_recommendation')})" for x in result["next_patch_ranked"][:3]) + "[/dim]")
    console.print(f"  devlab_proposal.md  cursor_prompt.txt  rfc_skeleton.md")


@devlab_group.command("shortlist")
def devlab_shortlist(
    category: str = typer.Option("", "--category", "-c", help="Filter to one category: UI, eval, packaging, workflow_engine, local_model_tooling, other"),
    output: str = typer.Option("", "--output", "-o", help="Write shortlist to file (json or .md)"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Produce ranked intake shortlist by category (UI, eval, workflow engine, packaging, local model tooling)."""
    from pathlib import Path
    from workflow_dataset.devlab.repo_intake import load_registry
    from workflow_dataset.devlab.config import get_reports_dir
    from workflow_dataset.devlab.shortlist import build_shortlist, write_shortlist_report
    root = devlab_root or None
    registry = load_registry(root)
    reports_dir = get_reports_dir(root)
    shortlist = build_shortlist(reports_dir, registry)
    cat_filter = (category or "").strip()
    if cat_filter:
        cat_normalized = cat_filter.lower().replace(" ", "_")
        if cat_normalized == "evaluation":
            cat_normalized = "eval"
        matched = {k: v for k, v in shortlist.items() if k.lower().replace(" ", "_") == cat_normalized or k == cat_filter}
        shortlist = matched if matched else {cat_filter: []}
    if output:
        p = Path(output)
        fmt = "md" if p.suffix.lower() == ".md" else "json"
        write_shortlist_report(shortlist, p, format=fmt)
        console.print(f"[green]Shortlist: {p}[/green]")
    for cat, entries in shortlist.items():
        if not entries:
            continue
        console.print(f"[bold]{cat}[/bold]")
        for e in entries[:5]:
            console.print(f"  {e.get('repo_id')}  score={e.get('composite_score', 0):.2f}  {e.get('d2_recommendation')}")
        if len(entries) > 5:
            console.print(f"  ... and {len(entries) - 5} more")
        console.print("")


@devlab_group.command("compare-models")
def devlab_compare_models(
    workflow: str = typer.Option(
        "weekly_status", "--workflow", "-w",
        help="Workflow prompt: weekly_status, status_action_bundle, stakeholder_update_bundle, ops_reporting_workspace"),
    providers: str = typer.Option(
        "ollama", "--providers", "-p",
        help="Comma-separated: ollama, openai, anthropic"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Compare providers on workflow prompt. Local Ollama first; API only if keys set."""
    from workflow_dataset.devlab.model_lab import compare_models, write_compare_report
    root = devlab_root or None
    plist = [p.strip() for p in providers.split(",") if p.strip()]
    results = compare_models(workflow, plist, root=root)
    path = write_compare_report(workflow, results, root=root)
    for r in results:
        out = r["output"]
        console.print(f"  [bold]{r['provider']}[/bold]: {(out[:120] + '...') if len(out) > 120 else out}")
    console.print(f"[green]Report: {path}[/green]")


@devlab_group.command("run-loop")
def devlab_run_loop(
    workflow: str = typer.Option("weekly_status", "--workflow", "-w"),
    providers: str = typer.Option("ollama", "--providers", "-p"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Run one-shot dev loop: evidence, repo reports, model compare, memo, tests; save artifacts."""
    from workflow_dataset.devlab.dev_loop import run_loop
    root = devlab_root or None
    plist = [p.strip() for p in providers.split(",") if p.strip()]
    try:
        status = run_loop(workflow=workflow, providers=plist, root=root)
        console.print(f"[green]Loop done. Report: {status.get('devlab_report')}[/green]")
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@devlab_group.command("loop-status")
def devlab_loop_status(
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Show dev loop status (last run, artifact paths)."""
    from workflow_dataset.devlab.dev_loop import loop_status
    root = devlab_root or None
    s = loop_status(root=root)
    if not s:
        console.print("[dim]No loop run yet. Use devlab run-loop.[/dim]")
        return
    console.print(f"  running: {s.get('running', False)}")
    console.print(f"  last_run: {s.get('last_run', '')}")
    console.print(f"  devlab_report: {s.get('devlab_report', '')}")
    console.print(f"  model_compare_report: {s.get('model_compare_report', '')}")


@devlab_group.command("stop-loop")
def devlab_stop_loop(
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Clear running flag (loop is one-shot; no background process by default)."""
    from workflow_dataset.devlab.dev_loop import stop_loop
    stop_loop(devlab_root or None)
    console.print("[green]Loop flag cleared.[/green]")


# ----- M21Z Experiment scheduler + patch proposal factory -----
@devlab_group.command("seed-experiment")
def devlab_seed_experiment(
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Create default experiment definition (ops_reporting_benchmark) if missing."""
    from workflow_dataset.devlab.experiments import seed_default_experiment
    d = seed_default_experiment(devlab_root or None)
    console.print(f"[green]Experiment: {d.get('id')}  goal={d.get('goal', '')[:50]}...[/green]")


@devlab_group.command("queue-experiment")
def devlab_queue_experiment(
    experiment_id: str = typer.Argument(..., help="Experiment id (must have experiments/<id>.json)"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Queue an experiment. Does not run it; use run-experiment to run."""
    from workflow_dataset.devlab.experiments import load_experiment, queue_experiment
    root = devlab_root or None
    if not load_experiment(experiment_id, root):
        console.print(f"[red]Experiment not found: {experiment_id}. Add experiments/<id>.json first.[/red]")
        raise typer.Exit(1)
    entry = queue_experiment(experiment_id, root)
    console.print(f"[green]Queued: {experiment_id}  status={entry.get('status')}[/green]")


@devlab_group.command("run-experiment")
def devlab_run_experiment(
    experiment_id: str = typer.Argument(..., help="Experiment id to run"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Run one experiment: benchmark suite, score, generate proposal. No auto-apply."""
    from workflow_dataset.devlab.experiment_runner import run_experiment
    root = devlab_root or None
    result = run_experiment(experiment_id, root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Done. proposal_id={result.get('proposal_id')}  path={result.get('proposal_path')}[/green]")


@devlab_group.command("experiment-status")
def devlab_experiment_status(
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Show experiment queue status: queued, running, done, failed, cancelled."""
    from workflow_dataset.devlab.experiments import get_queue_status
    root = devlab_root or None
    s = get_queue_status(root)
    console.print(f"  queued: {s.get('queued', 0)}  running: {s.get('running', 0)}  done: {s.get('done', 0)}  failed: {s.get('failed', 0)}  cancelled: {s.get('cancelled', 0)}")
    if s.get("last"):
        console.print(f"  last: {s['last'].get('experiment_id')}  {s['last'].get('status')}  proposal={s['last'].get('proposal_id')}")


@devlab_group.command("run-history")
def devlab_run_history(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of recent runs to list"),
    devlab_root: str = typer.Option("", "--devlab-root"),
    output: str = typer.Option("", "--output", "-o", help="Write to file (json or .md)"),
) -> None:
    """D4: List recent devlab runs (queue history) newest first. No perpetual behavior."""
    from workflow_dataset.devlab.experiments import list_recent_runs
    root = devlab_root or None
    runs = list_recent_runs(limit=limit, root=root)
    if not runs:
        console.print("[dim]No runs in history. Use devlab queue-experiment and run-experiment or run-next.[/dim]")
        return
    for r in runs:
        idx = r.get("_index", "")
        exp = r.get("experiment_id", "")
        st = r.get("status", "")
        qat = (r.get("queued_at") or "")[:19]
        rid = r.get("run_id") or ""
        pid = r.get("proposal_id") or ""
        console.print(f"  [{idx}]  {exp}  {st}  queued={qat}  run_id={rid}  proposal={pid}")
    if output:
        p = Path(output)
        p.parent.mkdir(parents=True, exist_ok=True)
        import json
        out = [{"index": x.get("_index"), "experiment_id": x.get("experiment_id"), "status": x.get("status"), "queued_at": x.get("queued_at"), "run_id": x.get("run_id"), "proposal_id": x.get("proposal_id"), "completed_at": x.get("completed_at")} for x in runs]
        if p.suffix.lower() == ".md":
            lines = ["# Devlab run history", "", f"Limit: {limit}", ""]
            for x in out:
                lines.append(f"- **{x['experiment_id']}**  {x['status']}  queued={x.get('queued_at', '')}  run_id={x.get('run_id') or '-'}  proposal={x.get('proposal_id') or '-'}")
            p.write_text("\n".join(lines), encoding="utf-8")
        else:
            p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        console.print(f"[green]Written: {p}[/green]")


@devlab_group.command("show-run")
def devlab_show_run(
    run_id_or_experiment_id_or_index: str = typer.Argument(..., help="run_id, experiment_id, or history index (0=most recent)"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """D4: Show status/history for one run (by run_id, experiment_id, or history index)."""
    from workflow_dataset.devlab.experiments import get_run_entry
    root = devlab_root or None
    run_id = experiment_id = None
    index = None
    if run_id_or_experiment_id_or_index.isdigit():
        index = int(run_id_or_experiment_id_or_index)
    else:
        if run_id_or_experiment_id_or_index.startswith("run_") or len(run_id_or_experiment_id_or_index) > 20:
            run_id = run_id_or_experiment_id_or_index
        else:
            experiment_id = run_id_or_experiment_id_or_index
    entry = get_run_entry(run_id=run_id, experiment_id=experiment_id, index=index, root=root)
    if not entry:
        console.print(f"[red]Run not found: {run_id_or_experiment_id_or_index}[/red]")
        raise typer.Exit(1)
    console.print(f"  experiment_id: {entry.get('experiment_id')}")
    console.print(f"  status: {entry.get('status')}")
    console.print(f"  queued_at: {entry.get('queued_at')}")
    console.print(f"  completed_at: {entry.get('completed_at')}")
    console.print(f"  run_id: {entry.get('run_id')}")
    console.print(f"  proposal_id: {entry.get('proposal_id')}")


@devlab_group.command("run-next")
def devlab_run_next(
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """D4: Run one experiment from the queue (oldest queued). Stops after one run; no perpetual loop."""
    from workflow_dataset.devlab.experiments import run_next_queued
    root = devlab_root or None
    out = run_next_queued(root)
    if not out.get("ran"):
        console.print(f"[dim]{out.get('reason', 'no_queued')}[/dim]")
        return
    result = out.get("result", {})
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Done. experiment_id={out.get('experiment_id')}  proposal_id={result.get('proposal_id')}  path={result.get('proposal_path')}[/green]")


@devlab_group.command("cancel-queued")
def devlab_cancel_queued(
    experiment_id_or_index: str = typer.Argument(..., help="Experiment id or history index (0=most recent) to cancel"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """D4: Cancel a queued run. Only queued entries can be cancelled; no effect on running/done/failed."""
    from workflow_dataset.devlab.experiments import cancel_queued, cancel_queued_by_index
    root = devlab_root or None
    if experiment_id_or_index.isdigit():
        ok = cancel_queued_by_index(int(experiment_id_or_index), root)
    else:
        ok = cancel_queued(experiment_id_or_index, root)
    if not ok:
        console.print(f"[red]No queued run found for: {experiment_id_or_index}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Cancelled: {experiment_id_or_index}[/green]")


@devlab_group.command("proposal-queue")
def devlab_proposal_queue(
    devlab_root: str = typer.Option("", "--devlab-root"),
    status_filter: str = typer.Option("", "--status", "-s", help="Filter: pending, reviewed, accepted, rejected"),
) -> None:
    """List patch proposals (pending, reviewed, accepted, rejected)."""
    from workflow_dataset.devlab.proposals import list_proposals, proposal_queue_summary
    root = devlab_root or None
    summary = proposal_queue_summary(root)
    console.print(f"  total: {summary['total']}  pending: {summary['pending']}  reviewed: {summary['reviewed']}  accepted: {summary['accepted']}  rejected: {summary['rejected']}")
    proposals = list_proposals(root)
    if status_filter:
        proposals = [p for p in proposals if p.get("status") == status_filter]
    for p in proposals[:20]:
        console.print(f"  [bold]{p.get('proposal_id')}[/bold]  {p.get('status')}  exp={p.get('experiment_id')}  run={p.get('run_id')}")


@devlab_group.command("show-proposal")
def devlab_show_proposal(
    proposal_id: str = typer.Argument("latest", help="Proposal id or 'latest' (default)"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Show proposal manifest and paths to devlab_proposal, cursor_prompt, rfc_skeleton. Use id or 'latest'."""
    from workflow_dataset.devlab.proposals import get_proposal
    root = devlab_root or None
    p = get_proposal(proposal_id or "latest", root)
    if not p:
        console.print(f"[red]Proposal not found: {proposal_id}[/red]")
        raise typer.Exit(1)
    console.print(f"  proposal_id: {p.get('proposal_id')}")
    console.print(f"  status: {p.get('status')}  created_at: {p.get('created_at')}")
    console.print(f"  path: {p.get('proposal_path')}")
    for k in ("devlab_proposal_md", "experiment_report_md", "patch_proposal_md", "cursor_prompt_txt", "rfc_skeleton_md"):
        if p.get(k):
            console.print(f"  {k}: {p[k]}")


@devlab_group.command("review-proposal")
def devlab_review_proposal(
    proposal_id: str = typer.Argument(..., help="Proposal id"),
    status: str = typer.Option(..., "--status", "-s", help="pending | reviewed | accepted | rejected"),
    notes: str = typer.Option("", "--notes", "-n", help="Operator notes"),
    devlab_root: str = typer.Option("", "--devlab-root"),
) -> None:
    """Update proposal status and optional operator notes. No code changes."""
    from workflow_dataset.devlab.proposals import update_proposal_status
    ok = update_proposal_status(proposal_id, status, operator_notes=notes, root=devlab_root or None)
    if not ok:
        console.print(f"[red]Proposal not found: {proposal_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Updated {proposal_id} -> {status}[/green]")


# ----- M21X Eval harness + benchmark board -----
eval_group = typer.Typer(
    help="Local evaluation harness and benchmark board for ops/reporting workflows.")
app.add_typer(eval_group, name="eval")


@eval_group.command("add-case")
def eval_add_case(
    case_id: str = typer.Argument(..., help="Case id"),
    workflow: str = typer.Option(..., "--workflow", "-w", help="Workflow: weekly_status, status_action_bundle, etc."),
    task_context: str = typer.Option(..., "--task-context", "-t", help="Task context text"),
    context_file: str = typer.Option("", "--context-file", help="Optional path to context file"),
    retrieval: bool = typer.Option(False, "--retrieval", help="Use retrieval for this case"),
    rubric: str = typer.Option("", "--rubric", help="Rubric hints"),
    eval_root: str = typer.Option("", "--eval-root"),
) -> None:
    """Add an evaluation case to the local case library."""
    from workflow_dataset.eval.case_format import add_case
    root = eval_root or None
    add_case(
        case_id=case_id,
        workflow=workflow,
        task_context=task_context,
        context_file=context_file,
        retrieval=retrieval,
        rubric_hints=rubric,
        root=root,
    )
    console.print(f"[green]Added case: {case_id}[/green]")


@eval_group.command("seed-defaults")
def eval_seed_defaults(
    eval_root: str = typer.Option("", "--eval-root"),
) -> None:
    """Seed default ops_reporting_core cases and suite if missing."""
    from workflow_dataset.eval.case_format import seed_default_cases
    cases = seed_default_cases(eval_root or None)
    console.print(f"[green]Seeded {len(cases)} cases and suite ops_reporting_core[/green]")


@eval_group.command("seed-expanded")
def eval_seed_expanded(
    eval_root: str = typer.Option("", "--eval-root"),
) -> None:
    """E2: Seed expanded case library (weekly_status, status_action_bundle, stakeholder_update_bundle, ops_reporting_workspace) and suite ops_reporting_expanded."""
    from workflow_dataset.eval.case_format import seed_expanded_cases
    cases = seed_expanded_cases(eval_root or None)
    console.print(f"[green]Seeded {len(cases)} expanded cases and suite ops_reporting_expanded[/green]")


@eval_group.command("run-suite")
def eval_run_suite(
    suite: str = typer.Argument(..., help="Suite name (e.g. ops_reporting_core)"),
    llm_config: str = typer.Option("", "--llm-config", help="LLM config path"),
    eval_root: str = typer.Option("", "--eval-root"),
) -> None:
    """Run benchmark suite through current workflows. Saves to data/local/eval/runs/<run_id>/."""
    from workflow_dataset.eval.harness import run_suite
    result = run_suite(suite_name=suite, llm_config_path=llm_config or None, root=eval_root or None)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Run: {result.get('run_id')}  path: {result.get('run_path')}[/green]")


@eval_group.command("run-case")
def eval_run_case(
    case_id: str = typer.Argument(..., help="Case id to run (e.g. weekly_status_project_delivery)"),
    llm_config: str = typer.Option("", "--llm-config", help="LLM config path"),
    eval_root: str = typer.Option("", "--eval-root"),
    case_path: str = typer.Option("", "--case-path", help="Optional path to case JSON file"),
) -> None:
    """Run a single benchmark case. Saves to data/local/eval/runs/<run_id>/."""
    from workflow_dataset.eval.harness import run_case
    result = run_case(
        case_id=case_id,
        case_path=case_path or None,
        llm_config_path=llm_config or None,
        root=eval_root or None,
    )
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Run: {result.get('run_id')}  path: {result.get('run_path')}[/green]")


@eval_group.command("compare-runs")
def eval_compare_runs(
    run_a: str | None = typer.Argument(None, help="First run id (baseline); or use --run"),
    run_b: str | None = typer.Argument(None, help="Second run id (newer); or use --run"),
    run: list[str] = typer.Option(
        [], "--run", "-r",
        help="Resolve by alias: e.g. --run previous --run latest (baseline first, then newer).",
    ),
    eval_root: str = typer.Option("", "--eval-root"),
) -> None:
    """Compare two eval runs: deltas, regressions, wins, thresholds, recommendation. Use --run previous --run latest to compare latest vs previous."""
    from workflow_dataset.eval.board import compare_runs, resolve_run_id
    root = eval_root or None
    if len(run) >= 2:
        run_a = resolve_run_id(run[0], root)
        run_b = resolve_run_id(run[1], root)
    if not run_a or not run_b:
        console.print("[red]Provide both run ids (e.g. run_a run_b) or --run <baseline> --run <newer> e.g. --run previous --run latest.[/red]")
        raise typer.Exit(1)
    out = compare_runs(run_a, run_b, root=root)
    if out.get("error"):
        console.print(f"[red]{out['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"  Run A (baseline): {out.get('run_a')}  {out.get('run_a_timestamp')}")
    console.print(f"  Run B (newer):    {out.get('run_b')}  {out.get('run_b_timestamp')}")
    console.print(f"  Regressions:  {out.get('regressions')}")
    console.print(f"  Improvements:  {out.get('improvements')}")
    console.print(f"  Thresholds passed: {out.get('thresholds_passed')}")
    console.print(f"  [bold]Recommendation: {out.get('recommendation')}[/bold]")


@eval_group.command("compare-latest")
def eval_compare_latest(
    suite: str = typer.Option("", "--suite", "-s", help="Filter by suite name"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max runs to consider"),
    eval_root: str = typer.Option("", "--eval-root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to .json or .md"),
) -> None:
    """E2: Compare latest run vs previous best. Show regressions and wins clearly."""
    from workflow_dataset.eval.board import compare_latest_vs_best
    out = compare_latest_vs_best(suite_name=suite, limit_runs=limit, root=eval_root or None)
    if out.get("error"):
        console.print(f"[red]{out['error']}[/red]")
        raise typer.Exit(1)
    console.print("[bold]Latest vs previous best[/bold]")
    console.print(f"  Baseline (best): {out.get('run_a')}  (newer run: {out.get('run_b')}  {out.get('run_b_timestamp')})")
    console.print(f"  Regressions:  {out.get('regressions')}")
    console.print(f"  Improvements: {out.get('improvements')}")
    console.print(f"  Thresholds passed: {out.get('thresholds_passed')}")
    console.print(f"  [bold]Recommendation: {out.get('recommendation')}[/bold]")
    if output:
        p = Path(output)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix.lower() == ".md":
            lines = [
                "# Compare latest vs best",
                "",
                f"- **Baseline (best):** {out.get('run_a')}",
                f"- **Latest run:** {out.get('run_b')}  {out.get('run_b_timestamp')}",
                f"- **Regressions:** {out.get('regressions')}",
                f"- **Improvements:** {out.get('improvements')}",
                f"- **Thresholds passed:** {out.get('thresholds_passed')}",
                f"- **Recommendation:** {out.get('recommendation')}",
            ]
            p.write_text("\n".join(lines), encoding="utf-8")
        else:
            import json
            p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        console.print(f"[green]Wrote: {p}[/green]")


@eval_group.command("trend")
def eval_trend(
    suite: str = typer.Option("", "--suite", "-s", help="Filter by suite name"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent runs for trend"),
    eval_root: str = typer.Option("", "--eval-root"),
    output: str = typer.Option("", "--output", "-o", help="Write trend report to file (json or .md)"),
) -> None:
    """E4: Benchmark trend view — trend over runs, best/worst workflows, top regression risk, top improvement opportunity."""
    from workflow_dataset.eval.trend import trend_report, write_trend_report
    out = trend_report(suite_name=suite, limit_runs=limit, root=eval_root or None)
    if out.get("trend_over_runs") == "no_runs":
        console.print("[dim]No runs in history. Use eval run-suite and score-run first.[/dim]")
        if output:
            p = Path(output)
            p.parent.mkdir(parents=True, exist_ok=True)
            import json
            p.write_text(json.dumps(out, indent=2), encoding="utf-8")
            console.print(f"[green]Trend report written: {p}[/green]")
        return
    console.print(f"[bold]Trend:[/bold] {out.get('trend_over_runs')}")
    console.print(f"  Latest: {out.get('latest_run_id')}  {out.get('latest_timestamp')}")
    console.print("[bold]Best workflows (latest run):[/bold]")
    for w in out.get("best_workflows", [])[:5]:
        console.print(f"  {w.get('workflow')}  {w.get('mean_score')}")
    console.print("[bold]Worst workflows (latest run):[/bold]")
    for w in out.get("worst_workflows", [])[:5]:
        console.print(f"  {w.get('workflow')}  {w.get('mean_score')}")
    rr = out.get("top_regression_risk")
    if rr:
        console.print(f"[bold]Top regression risk:[/bold] {rr.get('name')}  delta={rr.get('delta')}")
    else:
        console.print("[bold]Top regression risk:[/bold] —")
    io_ = out.get("top_improvement_opportunity")
    if io_:
        console.print(f"[bold]Top improvement opportunity:[/bold] {io_.get('name')}  delta={io_.get('delta')}")
    else:
        console.print("[bold]Top improvement opportunity:[/bold] —")
    if output:
        p = Path(output)
        fmt = "md" if p.suffix.lower() == ".md" else "json"
        write_trend_report(out, p, format=fmt)
        console.print(f"[green]Trend report written: {p}[/green]")


@eval_group.command("board")
def eval_board(
    suite: str = typer.Option("", "--suite", "-s", help="Filter by suite name"),
    limit: int = typer.Option(10, "--limit", "-n"),
    eval_root: str = typer.Option("", "--eval-root"),
    output: str = typer.Option("", "--output", "-o", help="Write board report to file (json or .md)"),
) -> None:
    """Show benchmark board: latest runs, best variant, recommendation."""
    from workflow_dataset.eval.board import board_report, write_board_report
    out = board_report(suite_name=suite, limit_runs=limit, root=eval_root or None)
    if output:
        p = Path(output)
        fmt = "md" if p.suffix.lower() == ".md" else "json"
        write_board_report(out, p, format=fmt)
        console.print(f"[green]Board report written: {p}[/green]")
    console.print(f"[bold]Suite: {out.get('suite')}[/bold]")
    console.print(f"  Latest run: {out.get('latest_run_id')}  {out.get('latest_timestamp')}")
    console.print(f"  Best run: {out.get('best_run_id')}")
    console.print(f"  Thresholds passed: {out.get('thresholds_passed')}")
    console.print(f"  [bold]Recommendation: {out.get('recommendation')}[/bold]")
    c = out.get("comparison_with_previous") or out.get("comparison_with_best")
    if c:
        console.print(f"  Regressions: {c.get('regressions')}")
        console.print(f"  Improvements: {c.get('improvements')}")


@eval_group.command("score-run")
def eval_score_run(
    run_id: str = typer.Argument(..., help="Run id to score"),
    eval_root: str = typer.Option("", "--eval-root"),
) -> None:
    """Compute heuristic scores for a run (and optionally attach operator rating)."""
    from workflow_dataset.eval.board import get_run
    from workflow_dataset.eval.config import get_runs_dir
    from workflow_dataset.eval.scoring import score_run
    manifest = get_run(run_id, eval_root or None)
    if not manifest:
        console.print(f"[red]Run not found: {run_id}[/red]")
        raise typer.Exit(1)
    path_str = manifest.get("run_path") or str(get_runs_dir(eval_root or None) / run_id)
    score_run(Path(path_str))
    console.print(f"[green]Scored run: {run_id}[/green]")


@eval_group.command("operator-rating")
def eval_operator_rating(
    run_id: str = typer.Argument(..., help="Run id"),
    case_id: str = typer.Argument(..., help="Case id within run"),
    rating: str = typer.Option(..., "--rating", "-r", help="JSON object: e.g. '{\"overall\": 4, \"notes\": \"good\"}'"),
    eval_root: str = typer.Option("", "--eval-root"),
) -> None:
    """Save operator rating for a case in a run."""
    import json
    from workflow_dataset.eval.scoring import save_operator_rating
    try:
        rating_dict = json.loads(rating)
    except Exception:
        console.print("[red]--rating must be valid JSON[/red]")
        raise typer.Exit(1)
    path = save_operator_rating(run_id, case_id, rating_dict, root=eval_root or None)
    console.print(f"[green]Saved: {path}[/green]")


@eval_group.command("reconcile")
def eval_reconcile(
    run_id: str = typer.Argument(..., help="Run id to reconcile"),
    compare_with: str = typer.Option("", "--compare-with", "-c", help="Optional previous run id for comparison"),
    eval_root: str = typer.Option("", "--eval-root"),
    output: str = typer.Option("", "--output", "-o", help="Write reconciliation to file (json or .md)"),
) -> None:
    """E3: Reconciliation output — heuristic vs operator vs model-judge scores and why promote/hold/refine/revert."""
    from workflow_dataset.eval.board import get_run, compare_runs
    from workflow_dataset.eval.scoring import score_run
    from workflow_dataset.eval.reconciliation import reconcile_run
    manifest = get_run(run_id, eval_root or None)
    if not manifest:
        console.print(f"[red]Run not found: {run_id}[/red]")
        raise typer.Exit(1)
    if not manifest.get("scored"):
        from workflow_dataset.eval.config import get_runs_dir
        path_str = manifest.get("run_path") or str(get_runs_dir(eval_root or None) / run_id)
        score_run(Path(path_str))
        manifest = get_run(run_id, eval_root or None) or manifest
    comparison = None
    if compare_with:
        comp = compare_runs(compare_with, run_id, root=eval_root or None)
        if not comp.get("error"):
            comparison = comp
    recon = reconcile_run(manifest, comparison=comparison)
    console.print(f"[bold]Run:[/bold] {recon.get('run_id')}")
    console.print(f"[bold]Verdict:[/bold] {recon.get('verdict')}")
    console.print(f"  heuristic_score: {recon.get('heuristic_score')}")
    console.print(f"  operator_score: {recon.get('operator_score')}")
    console.print(f"  model_judge_score: {recon.get('model_judge_score')}")
    console.print("[bold]Reasons:[/bold]")
    for r in recon.get("reasons", []):
        console.print(f"  {r}")
    if output:
        p = Path(output)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix.lower() == ".md":
            lines = [
                "# Reconciliation",
                "",
                f"- **Run:** {recon.get('run_id')}",
                f"- **Verdict:** {recon.get('verdict')}",
                "",
                "## Scores",
                f"- Heuristic: {recon.get('heuristic_score')}",
                f"- Operator: {recon.get('operator_score')}",
                f"- Model-judge: {recon.get('model_judge_score')}",
                "",
                "## Reasons",
            ]
            for r in recon.get("reasons", []):
                lines.append(f"- {r}")
            p.write_text("\n".join(lines), encoding="utf-8")
        else:
            import json
            out = {k: v for k, v in recon.items() if k != "comparison" or v is not None}
            if recon.get("comparison"):
                out["comparison"] = {k: v for k, v in recon["comparison"].items() if k != "aggregate_a" and k != "aggregate_b" and k != "deltas"}
            p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        console.print(f"[green]Reconciliation written: {p}[/green]")


# ----- M21Y Product evolution planner -----
planner_group = typer.Typer(
    help="Evidence-based milestone recommendations. Advisory only; no auto-execution.")
app.add_typer(planner_group, name="planner")


@planner_group.command("recommend-next")
def planner_recommend_next(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root for evidence"),
) -> None:
    """Output the single highest-priority next milestone (next best step)."""
    from workflow_dataset.planner.evidence import gather_evidence
    from workflow_dataset.planner.candidates import rank_candidates
    from workflow_dataset.planner.briefs import recommend_next
    root = Path(repo_root) if repo_root else None
    evidence = gather_evidence(root)
    candidates = rank_candidates(evidence)
    rec = recommend_next(candidates)
    if not rec:
        console.print("[dim]No candidates. Run planner shortlist for full list.[/dim]")
        return
    console.print(f"[bold]Next best step: {rec.get('title')}[/bold]")
    console.print(f"  ID: {rec.get('id')}")
    console.print(f"  Rationale: {rec.get('rationale', '')[:200]}...")
    console.print("[dim]Use: workflow-dataset planner build-brief --candidate " + rec.get("id", "") + "[/dim]")


@planner_group.command("shortlist")
def planner_shortlist(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Output ranked milestone shortlist (id, title, priority)."""
    from workflow_dataset.planner.evidence import gather_evidence
    from workflow_dataset.planner.candidates import rank_candidates
    root = Path(repo_root) if repo_root else None
    evidence = gather_evidence(root)
    candidates = rank_candidates(evidence)
    for c in candidates:
        console.print(f"  [bold]{c.get('priority', '?')}. {c.get('id')}[/bold]  — {c.get('title', '')[:60]}")


@planner_group.command("build-brief")
def planner_build_brief(
    candidate: str = typer.Option(..., "--candidate", "-c", help="Candidate id from shortlist"),
    repo_root: str = typer.Option("", "--repo-root"),
    output: str = typer.Option("", "--output", "-o", help="Write to file (default: stdout)"),
) -> None:
    """Generate full milestone brief for a candidate."""
    from workflow_dataset.planner.evidence import gather_evidence
    from workflow_dataset.planner.candidates import rank_candidates
    from workflow_dataset.planner.briefs import build_milestone_brief
    root = Path(repo_root) if repo_root else None
    evidence = gather_evidence(root)
    candidates = rank_candidates(evidence)
    text = build_milestone_brief(candidate, candidates, evidence)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        console.print(f"[green]Wrote: {output}[/green]")
    else:
        console.print(text)


@planner_group.command("build-rfc")
def planner_build_rfc(
    candidate: str = typer.Option(..., "--candidate", "-c", help="Candidate id from shortlist"),
    repo_root: str = typer.Option("", "--repo-root"),
    output: str = typer.Option("", "--output", "-o", help="Write to file (default: stdout)"),
) -> None:
    """Generate RFC skeleton for a candidate."""
    from workflow_dataset.planner.evidence import gather_evidence
    from workflow_dataset.planner.candidates import rank_candidates
    from workflow_dataset.planner.briefs import build_rfc_skeleton
    root = Path(repo_root) if repo_root else None
    evidence = gather_evidence(root)
    candidates = rank_candidates(evidence)
    text = build_rfc_skeleton(candidate, candidates, evidence)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        console.print(f"[green]Wrote: {output}[/green]")
    else:
        console.print(text)


# ----- M22A Workflow incubator -----
incubator_group = typer.Typer(
    help="Adjacent workflow incubator: track, gate, and promote experimental workflows. Operator-controlled.")
app.add_typer(incubator_group, name="incubator")


@incubator_group.command("add-candidate")
def incubator_add_candidate(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    description: str = typer.Option("", "--description", "-d"),
    target_user_value: str = typer.Option("", "--target-value", "-t"),
    stage: str = typer.Option("idea", "--stage", "-s", help="idea | prototype | benchmarked | cohort_tested | promoted | rejected"),
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """Add a workflow candidate to the incubator. Experimental only; distinct from validated suite."""
    from workflow_dataset.incubator.registry import add_candidate
    root = incubator_root or None
    try:
        add_candidate(candidate_id, description=description, target_user_value=target_user_value, stage=stage, root=root)
        console.print(f"[green]Added candidate: {candidate_id}  stage={stage}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@incubator_group.command("list")
def incubator_list(
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """List workflow candidates (stage, decision)."""
    from workflow_dataset.incubator.registry import list_candidates
    candidates = list_candidates(incubator_root or None)
    if not candidates:
        console.print("[dim]No candidates. Use incubator add-candidate.[/dim]")
        return
    for c in candidates:
        console.print(f"  [bold]{c.get('id')}[/bold]  {c.get('stage')}  {c.get('promotion_decision', 'none')}  — {(c.get('description') or '')[:50]}")


@incubator_group.command("show")
def incubator_show(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """Show candidate details and evidence."""
    from workflow_dataset.incubator.registry import get_candidate
    c = get_candidate(candidate_id, incubator_root or None)
    if not c:
        console.print(f"[red]Candidate not found: {candidate_id}[/red]")
        raise typer.Exit(1)
    console.print(f"  id: {c.get('id')}")
    console.print(f"  stage: {c.get('stage')}  promotion_decision: {c.get('promotion_decision', 'none')}")
    console.print(f"  description: {c.get('description', '')[:200]}")
    console.print(f"  target_user_value: {c.get('target_user_value', '')[:200]}")
    console.print(f"  evidence_refs: {c.get('evidence_refs', [])}")
    gr = c.get("gate_results")
    if gr and isinstance(gr, dict):
        gp, gt = gr.get("gates_passed"), gr.get("gates_total")
        if gp is not None and gt is not None:
            console.print(f"  gates_passed: {gp} / {gt}  recommendation: {gr.get('recommendation')}")


@incubator_group.command("evaluate")
def incubator_evaluate(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    incubator_root: str = typer.Option("", "--incubator-root"),
    attach: bool = typer.Option(True, "--attach/--no-attach", help="Save gate results to candidate"),
) -> None:
    """Run promotion gates and show recommendation. Does not promote."""
    from workflow_dataset.incubator.gates import evaluate_gates, promotion_report
    from workflow_dataset.incubator.registry import get_candidate, update_candidate
    root = incubator_root or None
    result = evaluate_gates(candidate_id, root)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(promotion_report(candidate_id, result, root))
    if attach:
        update_candidate(candidate_id, {"gate_results": result}, root)
    console.print(f"\n[dim]Recommendation: {result.get('recommendation')}. Use promote/reject/hold to set decision.[/dim]")


@incubator_group.command("promote")
def incubator_promote(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """Mark candidate as promoted. Does not modify validated workflow suite or product code."""
    from workflow_dataset.incubator.registry import set_promotion_decision
    c = set_promotion_decision(candidate_id, "promoted", root=incubator_root or None)
    if not c:
        console.print(f"[red]Candidate not found: {candidate_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Marked promoted: {candidate_id}. Add to product suite manually if desired.[/green]")


@incubator_group.command("reject")
def incubator_reject(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """Mark candidate as rejected."""
    from workflow_dataset.incubator.registry import set_promotion_decision
    c = set_promotion_decision(candidate_id, "rejected", root=incubator_root or None)
    if not c:
        console.print(f"[red]Candidate not found: {candidate_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Marked rejected: {candidate_id}[/green]")


@incubator_group.command("hold")
def incubator_hold(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """Mark candidate as hold (no promote/reject yet)."""
    from workflow_dataset.incubator.registry import set_promotion_decision
    c = set_promotion_decision(candidate_id, "hold", root=incubator_root or None)
    if not c:
        console.print(f"[red]Candidate not found: {candidate_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Marked hold: {candidate_id}[/green]")


@incubator_group.command("mark-stage")
def incubator_mark_stage(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    stage: str = typer.Argument(..., help="idea | prototype | benchmarked | cohort_tested | promoted | rejected"),
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """Set candidate stage."""
    from workflow_dataset.incubator.registry import mark_stage
    c = mark_stage(candidate_id, stage, root=incubator_root or None)
    if not c:
        console.print(f"[red]Candidate not found or invalid stage: {candidate_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Stage set: {candidate_id} -> {stage}[/green]")


@incubator_group.command("attach-evidence")
def incubator_attach_evidence(
    candidate_id: str = typer.Argument(..., help="Candidate id"),
    evidence_ref: str = typer.Argument(..., help="Path or run id to attach"),
    incubator_root: str = typer.Option("", "--incubator-root"),
) -> None:
    """Attach an evidence reference (eval run id, proposal id, or path)."""
    from workflow_dataset.incubator.registry import attach_evidence
    c = attach_evidence(candidate_id, evidence_ref, root=incubator_root or None)
    if not c:
        console.print(f"[red]Candidate not found: {candidate_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Attached evidence: {evidence_ref}[/green]")


# ----- M22B Mission control -----
@app.command("mission-control")
def mission_control_cmd(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root for state aggregation"),
    output: str = typer.Option("", "--output", "-o", help="Write report to file (default: stdout)"),
) -> None:
    """Unified mission-control dashboard: product, evaluation, development, incubator state and recommended next action."""
    from workflow_dataset.mission_control.report import format_mission_control_report
    from workflow_dataset.mission_control.state import get_mission_control_state
    root = Path(repo_root) if repo_root else None
    state = get_mission_control_state(root)
    report = format_mission_control_report(state=state)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]Wrote: {output}[/green]")
    else:
        console.print(report)


# ----- M23V / M23O Daily inbox -----
inbox_group = typer.Typer(
    help="Daily work inbox / context digest: what changed, what to do now, what is blocked, why.",
)
app.add_typer(inbox_group, name="inbox")


@inbox_group.callback(invoke_without_command=True)
def inbox_cmd(
    ctx: typer.Context,
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to file (default: stdout)"),
    explain: bool = typer.Option(False, "--explain", "-e", help="Include per-item reason, trust, mode, blockers, outcome"),
) -> None:
    """Daily inbox: work state summary, what changed, relevant jobs/routines, blocked, reminders, top next action."""
    if ctx.invoked_subcommand is not None:
        return
    from workflow_dataset.daily.inbox_report import format_inbox_report
    root = Path(repo_root) if repo_root else None
    report = format_inbox_report(repo_root=root, include_explain=explain)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]Wrote: {output}[/green]")
    else:
        console.print(report)


@inbox_group.command("explain")
def inbox_explain_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Explain why each inbox item is shown now: reason, trust level, mode, blockers, expected outcome."""
    from workflow_dataset.daily.inbox_report import format_explain_why_now
    console.print(format_explain_why_now(repo_root=Path(repo_root) if repo_root else None))


@inbox_group.command("compare")
def inbox_compare_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Compare latest vs previous digest snapshot: newly appeared, dropped, escalated."""
    from workflow_dataset.daily.digest_history import load_digest_snapshot, compare_digests
    root = Path(repo_root) if repo_root else None
    latest = load_digest_snapshot("latest", root)
    previous = load_digest_snapshot("previous", root)
    if not latest:
        console.print("[dim]No latest digest. Run 'workflow-dataset inbox snapshot' first.[/dim]")
        raise typer.Exit(0)
    if not previous:
        console.print("[dim]No previous digest. Run 'workflow-dataset inbox' twice (or inbox snapshot) to get a compare.[/dim]")
        console.print(Panel("\n".join([f"Latest: {latest.get('created_at', '')}", f"Top next: {latest.get('top_next_recommended', {}).get('label', '')}"]), title="Latest digest", border_style="cyan"))
        raise typer.Exit(0)
    result = compare_digests(previous, latest)
    lines = ["# Digest compare (previous → latest)", "", "## Newly appeared", ", ".join(result.newly_appeared) or "—", "", "## Dropped", ", ".join(result.dropped) or "—", "", "## No longer blocked (escalated)", ", ".join(result.escalated) or "—", "", "## Summary"]
    lines.extend(result.summary)
    console.print(Panel("\n".join(lines), title="Inbox compare", border_style="green"))


@inbox_group.command("snapshot")
def inbox_snapshot_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Build digest and persist as snapshot (latest + timestamped). Enables compare on next run."""
    from workflow_dataset.daily.inbox import build_daily_digest
    from workflow_dataset.daily.digest_history import save_digest_snapshot
    root = Path(repo_root) if repo_root else None
    digest = build_daily_digest(root)
    path = save_digest_snapshot(digest, root)
    console.print(f"[green]Digest snapshot saved: {path}[/green]")
    console.print(f"  created_at: {digest.created_at}")
    console.print(f"  top next: {digest.top_next_recommended.get('label', '')}")


# ----- M23V Macros -----
macro_group = typer.Typer(
    help="Macro (multi-step) runs: list, preview, run. Uses routines; checkpointed runs under copilot/runs.",
)
app.add_typer(macro_group, name="macro")


@macro_group.command("list")
def macro_list_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """List available macros (routines)."""
    from workflow_dataset.macros.runner import list_macros
    root = Path(repo_root) if repo_root else None
    macros = list_macros(root)
    if not macros:
        console.print("[dim]No macros (routines) defined. Add YAML under data/local/copilot/routines/.[/dim]")
        return
    for m in macros:
        console.print(f"  {m.macro_id}  {m.title or ''}  (mode={m.mode})")


@macro_group.command("preview")
def macro_preview_cmd(
    id: str = typer.Option(..., "--id", "-i", help="Macro (routine) id"),
    mode: str = typer.Option("simulate", "--mode", "-m", help="simulate | real"),
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Preview macro: jobs, order, step types, blocked steps. No execution."""
    from workflow_dataset.macros.runner import macro_preview
    from workflow_dataset.macros.report import format_macro_preview
    root = Path(repo_root) if repo_root else None
    plan = macro_preview(id, mode=mode, repo_root=root)
    console.print(format_macro_preview(plan, macro_id=id, mode=mode, repo_root=root))


@macro_group.command("run")
def macro_run_cmd(
    id: str = typer.Option(..., "--id", "-i", help="Macro (routine) id"),
    mode: str = typer.Option("simulate", "--mode", "-m", help="simulate | real"),
    repo_root: str = typer.Option("", "--repo-root"),
    continue_on_blocked: bool = typer.Option(False, "--continue-on-blocked", help="Continue past blocked steps"),
) -> None:
    """Run macro (checkpointed). Use --mode simulate for dry run."""
    from workflow_dataset.macros.runner import macro_run
    root = Path(repo_root) if repo_root else None
    result = macro_run(id, mode=mode, repo_root=root, continue_on_blocked=continue_on_blocked)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Run: {result.get('plan_run_id')}  executed={result.get('executed_count')}  blocked={result.get('blocked_count')}[/green]")
    if result.get("errors"):
        for e in result["errors"]:
            console.print(f"[yellow]{e}[/yellow]")


# ----- M23V Trust cockpit -----
trust_group = typer.Typer(
    help="Trust / evidence cockpit: benchmark trust, coverage, approval readiness, release gates.",
)
app.add_typer(trust_group, name="trust")


@trust_group.command("cockpit")
def trust_cockpit_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to file"),
) -> None:
    """Trust and evidence cockpit: benchmark, coverage, approvals, job/macro trust, corrections, release gates."""
    from workflow_dataset.trust.report import format_trust_cockpit
    report = format_trust_cockpit(repo_root=Path(repo_root) if repo_root else None)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]Wrote: {output}[/green]")
    else:
        console.print(report)


@trust_group.command("release-gates")
def trust_release_gates_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
) -> None:
    """Release gate status: unreviewed, package pending, staged, release report."""
    from workflow_dataset.trust.report import format_release_gates
    console.print(format_release_gates(repo_root=Path(repo_root) if repo_root else None))


# ----- M23V Package readiness -----
package_group = typer.Typer(
    help="Package / install readiness: machine and product readiness, first-install readiness report.",
)
app.add_typer(package_group, name="package")


@package_group.command("readiness-report")
def package_readiness_report_cmd(
    repo_root: str = typer.Option("", "--repo-root"),
    output: str = typer.Option("", "--output", "-o", help="Write report to file"),
) -> None:
    """Package/install readiness: machine readiness, missing prereqs, ready for first real-user install, experimental."""
    from workflow_dataset.package_readiness.report import format_readiness_report
    report = format_readiness_report(repo_root=Path(repo_root) if repo_root else None)
    if output:
        Path(output).write_text(report, encoding="utf-8")
        console.print(f"[green]Wrote: {output}[/green]")
    else:
        console.print(report)


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


# ----- M23T Runtime mesh: backends, catalog, integrations, recommend, profile, compatibility -----
@runtime_group.command("backends")
def runtime_backends(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List backend/runtime profiles and status (available, configured, missing, unsupported)."""
    from workflow_dataset.runtime_mesh.backend_registry import list_backend_profiles
    root = Path(repo_root) if repo_root else None
    profiles = list_backend_profiles(root)
    console.print("[bold]Runtime backends[/bold]")
    for p in profiles:
        console.print(f"  {p.backend_id}  family={p.backend_family}  status={p.status}  local={p.local}")
    if not profiles:
        console.print("  (none)")


@runtime_group.command("catalog")
def runtime_catalog(
    capability: str = typer.Option("", "--capability", "-c", help="Filter by capability class"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List model capability catalog (optionally filter by capability class)."""
    from workflow_dataset.runtime_mesh.model_catalog import load_model_catalog, list_models_by_capability
    root = Path(repo_root) if repo_root else None
    if capability:
        models = list_models_by_capability(capability, root)
    else:
        models = load_model_catalog(root)
    console.print("[bold]Model catalog[/bold]")
    for m in models:
        console.print(f"  {m.model_id}  backend={m.backend_family}  capabilities={m.capability_classes}")
    if not models:
        console.print("  (none)")


@runtime_group.command("integrations")
def runtime_integrations(
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """List integration manifests (OpenClaw, coding-agent, IDE, etc.) and enable state."""
    from workflow_dataset.runtime_mesh.integration_registry import list_integrations
    root = Path(repo_root) if repo_root else None
    integrations = list_integrations(root)
    console.print("[bold]Integrations[/bold]")
    for i in integrations:
        console.print(f"  {i.integration_id}  local={i.local}  enabled={i.enabled}  install={i.install_status}")
    if not integrations:
        console.print("  (none)")


@runtime_group.command("recommend")
def runtime_recommend(
    task_class: str = typer.Option(..., "--task-class", "-t", help="e.g. desktop_copilot, codebase_task, local_retrieval"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Recommend backend and model class for a task class."""
    from workflow_dataset.runtime_mesh.policy import recommend_for_task_class
    root = Path(repo_root) if repo_root else None
    rec = recommend_for_task_class(task_class, root)
    console.print(f"[bold]Task class[/bold]  {rec.get('task_class')}")
    console.print(f"  backend_id: {rec.get('backend_id')}  status: {rec.get('backend_status')}")
    console.print(f"  model_class: {rec.get('model_class')}")
    console.print(f"  model_ids: {rec.get('model_ids', [])}")
    console.print(f"  integrations_available: {rec.get('integrations_available', [])}")
    if rec.get("missing"):
        console.print("[yellow]  missing: " + "; ".join(rec["missing"]) + "[/yellow]")
    console.print(f"  [dim]{rec.get('reason', '')}[/dim]")


@runtime_group.command("profile")
def runtime_profile(
    backend: str = typer.Option(..., "--backend", "-b", help="Backend id (e.g. ollama, repo_local)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show full profile for a backend (capabilities, prerequisites, status)."""
    from workflow_dataset.runtime_mesh.backend_registry import get_backend_profile
    root = Path(repo_root) if repo_root else None
    prof = get_backend_profile(backend, root)
    if not prof:
        console.print(f"[red]Backend not found: {backend}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{prof.backend_id}[/bold]  family={prof.backend_family}  status={prof.status}")
    console.print("  local=", prof.local, "  optional_remote=", prof.optional_remote)
    console.print("  tool_calling=", prof.tool_calling, "  thinking=", prof.thinking_reasoning, "  vision=", prof.vision, "  embedding=", prof.embedding, "  ocr=", prof.ocr)
    console.print("  coding_agent_suitable=", prof.coding_agent_suitable, "  desktop_assistant_suitable=", prof.desktop_assistant_suitable)
    console.print("  install_prerequisites:", prof.install_prerequisites)
    if prof.notes:
        console.print("  notes:", prof.notes)
    if prof.risk_trust_notes:
        console.print("  risk_trust:", prof.risk_trust_notes)


@runtime_group.command("compatibility")
def runtime_compatibility(
    model: str = typer.Option(..., "--model", "-m", help="Model id (e.g. qwen3-coder-next)"),
    repo_root: str = typer.Option("", "--repo-root", help="Override repo root"),
) -> None:
    """Show compatibility report for a model (catalog, backend status, suitable task classes)."""
    from workflow_dataset.runtime_mesh.policy import compatibility_for_model
    root = Path(repo_root) if repo_root else None
    report = compatibility_for_model(model, root)
    console.print(f"[bold]Model[/bold]  {report.get('model_id')}  in_catalog={report.get('in_catalog')}")
    console.print("  backend_family:", report.get("backend_family"), "  backend_status:", report.get("backend_status"))
    console.print("  capability_classes:", report.get("capability_classes", []))
    console.print("  recommended_usage:", report.get("recommended_usage", []))
    console.print("  suitable_task_classes:", report.get("suitable_task_classes", []))
    console.print("  ", report.get("message", ""), style="dim")
