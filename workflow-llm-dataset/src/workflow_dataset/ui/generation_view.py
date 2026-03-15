"""
Generation view: browse generations, create plan, inspect manifest.

M10 scaffolding: style pack, prompt pack, asset plan. Sandbox-only.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from workflow_dataset.settings import Settings
from workflow_dataset.ui.models import Screen
from workflow_dataset.ui.state_store import ConsoleState
from workflow_dataset.ui.services import (
    get_generation_requests,
    get_generation_manifest_preview,
    run_generation_plan_from_console,
    get_available_generation_backends,
    run_generation_backend_from_console,
    get_generation_review_preview,
    run_generation_refine_from_console,
    create_adoption_candidate_from_console,
    create_bundle_from_console,
    list_bundles_for_console,
    adopt_bundle_for_console,
)


def render_generation(console: Console, state: ConsoleState, settings: Settings) -> Screen:
    """Generation flow: list generations, create plan, preview manifest. Returns next screen."""
    gen = getattr(settings, "generation", None)
    if not gen or not getattr(gen, "generation_enabled", True):
        console.print(Panel("[yellow]Generation is disabled.[/yellow] Enable in config.", title="Generation", border_style="yellow"))
        Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")
        return Screen.HOME

    console.print(Panel(
        "[bold]Generation scaffolding[/bold]\n[dim]Style packs, prompt packs, asset plans. Sandbox-only; no uncontrolled execution.[/dim]",
        title="Generation",
        border_style="blue",
    ))

    items = get_generation_requests(
        settings,
        session_id=state.selected_session_id or "",
        project_id=state.selected_project_id,
        limit=25,
    )

    if items:
        table = Table(title="Generation requests")
        table.add_column("#", style="dim", width=4)
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Session", style="dim")
        table.add_column("Project", style="dim")
        for i, g in enumerate(items[:20], 1):
            table.add_row(
                str(i),
                (g.get("generation_id") or "")[:24],
                g.get("generation_type", ""),
                (g.get("session_id") or "")[:12],
                (g.get("project_id") or "")[:16],
            )
        console.print(table)

    backends = get_available_generation_backends(settings)
    console.print("\n[bold]Actions[/bold]")
    console.print("  [cyan]1[/cyan] Create new generation plan")
    console.print("  [cyan]2[/cyan] Preview manifest by ID (plan + execution results)")
    console.print("  [cyan]3[/cyan] Run backend in sandbox (choose generation + backend)")
    console.print("  [cyan]4[/cyan] Review generated outputs (preview + metadata)")
    console.print("  [cyan]5[/cyan] Refine a document artifact")
    console.print("  [cyan]6[/cyan] Mark outputs for adoption → Apply flow")
    console.print("  [cyan]7[/cyan] Create output bundle (toolchain-native)")
    console.print("  [cyan]8[/cyan] List bundles / Adopt bundle → Apply flow")
    console.print("  [cyan]Enter[/cyan] Return to home")

    action = Prompt.ask("Choice", default="").strip() or "0"
    if action == "0" or not action:
        return Screen.HOME

    if action == "1":
        gen_type = Prompt.ask("Generation type", default="image_pack").strip() or "image_pack"
        try:
            gen_id, ws_path = run_generation_plan_from_console(
                settings,
                session_id=state.selected_session_id or None,
                project_id=state.selected_project_id,
                generation_type=gen_type,
                source_ref=state.selected_draft_type or state.selected_suggestion_id or "",
                source_type="draft" if state.selected_draft_type else ("suggestion" if state.selected_suggestion_id else "project"),
            )
            console.print(f"[green]Plan created: {gen_id}[/green]")
            console.print(f"  workspace: {ws_path}")
        except Exception as e:
            console.print(f"[red]{e}[/red]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    if action == "2":
        manifest_id = Prompt.ask("Manifest ID (e.g. gm_...)", default="").strip()
        if not manifest_id:
            return Screen.GENERATION
        preview = get_generation_manifest_preview(settings, manifest_id)
        if not preview:
            console.print("[red]Manifest not found.[/red]")
        else:
            status = preview.get("status", "")
            backend_exec = preview.get("backend_executed") or "(none)"
            body = (
                f"generation_id: {preview.get('generation_id')}\n"
                f"workspace: {preview.get('workspace_path')}\n"
                f"status: {status}  backend_executed: {backend_exec}\n"
                f"style_pack_refs: {preview.get('style_pack_refs')}\n"
                f"prompt_pack_refs: {preview.get('prompt_pack_refs')}\n"
                f"asset_plan_refs: {preview.get('asset_plan_refs')}\n"
            )
            if preview.get("execution_records"):
                body += "\n[Execution records]\n"
                for rec in preview["execution_records"]:
                    body += f"  {rec.get('backend_name')} status={rec.get('execution_status')} llm={rec.get('used_llm')} fallback={rec.get('used_fallback')}\n"
                    for p in (rec.get("generated_output_paths") or [])[:5]:
                        body += f"    -> {p}\n"
                    if rec.get("error_message"):
                        body += f"    error: {rec['error_message']}\n"
            if preview.get("generated_output_paths"):
                body += "\n[Generated outputs]\n"
                for p in preview["generated_output_paths"][:15]:
                    body += f"  {p}\n"
            console.print(Panel(body, title=f"Manifest {manifest_id}", border_style="dim"))
            for pp in preview.get("prompt_packs") or []:
                console.print(f"  [cyan]{pp.get('prompt_family')}[/cyan]: {pp.get('prompt_text', '')[:100]}...")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    if action == "3":
        if not backends:
            console.print("[yellow]No backends enabled. Enable generation_enable_document_backend or generation_enable_image_demo_backend (or generation_enable_demo_backend for mock).[/yellow]")
        else:
            gen_id = Prompt.ask("Generation ID", default="").strip()
            if not gen_id:
                return Screen.GENERATION
            backend_names = [b["name"] for b in backends]
            backend = Prompt.ask(f"Backend ({', '.join(backend_names)})", default=backend_names[0] if backend_names else "").strip()
            if backend not in backend_names:
                console.print(f"[red]Unknown or disabled backend: {backend}[/red]")
            else:
                try:
                    ok, msg, paths = run_generation_backend_from_console(settings, gen_id, backend)
                    if ok:
                        console.print(f"[green]{msg}[/green]")
                        for p in (paths or [])[:10]:
                            console.print(f"  [dim]{p}[/dim]")
                    else:
                        console.print(f"[red]{msg}[/red]")
                except Exception as e:
                    console.print(f"[red]{e}[/red]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    if action == "4":
        gen_id = Prompt.ask("Generation ID", default="").strip()
        if not gen_id:
            return Screen.GENERATION
        previews = get_generation_review_preview(settings, gen_id)
        if not previews:
            console.print("[dim]No generated outputs to review.[/dim]")
        else:
            for review, body in previews:
                console.print(Panel(body[:2000] + ("..." if len(body) > 2000 else ""), title=review.summary, border_style="dim"))
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    if action == "5":
        gen_id = Prompt.ask("Generation ID", default="").strip()
        if not gen_id:
            return Screen.GENERATION
        art_path = Prompt.ask("Artifact path (relative to workspace, e.g. creative_brief_generated.md)", default="").strip()
        if not art_path:
            return Screen.GENERATION
        use_llm = Prompt.ask("Use LLM refinement? (y/N)", default="n").strip().lower() == "y"
        instruction = Prompt.ask("Refinement instruction (optional)", default="").strip()
        ok, msg, paths = run_generation_refine_from_console(settings, gen_id, art_path, use_llm=use_llm, instruction=instruction)
        if ok:
            console.print(f"[green]{msg}[/green]")
            for p in (paths or [])[:10]:
                console.print(f"  [dim]{p}[/dim]")
        else:
            console.print(f"[red]{msg}[/red]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    if action == "6":
        gen_id = Prompt.ask("Generation ID", default="").strip()
        if not gen_id:
            return Screen.GENERATION
        paths_str = Prompt.ask("Comma-separated paths to adopt (e.g. creative_brief_generated.md)", default="").strip()
        if not paths_str:
            return Screen.GENERATION
        candidate_paths = [p.strip() for p in paths_str.split(",") if p.strip()]
        cand = create_adoption_candidate_from_console(settings, gen_id, candidate_paths)
        if cand:
            console.print(f"[green]Adoption candidate created: {cand['adoption_id']}[/green]")
            console.print("  workspace:", cand["workspace_path"])
            console.print("  paths:", cand["candidate_paths"])
            state.set_pending_adoption_candidate(cand)
            console.print("[bold]Go to Apply to preview and confirm copy to target.[/bold]")
        else:
            console.print("[red]Failed to create adoption candidate.[/red]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    if action == "7":
        oa = getattr(settings, "output_adapters", None)
        if not oa or not getattr(oa, "output_adapters_enabled", True):
            console.print("[yellow]Output adapters are disabled.[/yellow]")
        else:
            from workflow_dataset.output_adapters import list_adapters
            adapter_types = [m.adapter_type for m in list_adapters()]
            adapter = Prompt.ask(f"Adapter type ({', '.join(adapter_types)})", default=adapter_types[0] if adapter_types else "").strip()
            if adapter in adapter_types:
                gen_id = Prompt.ask("Generation ID (optional)", default="").strip()
                art_path = Prompt.ask("Artifact path (optional)", default="").strip()
                result = create_bundle_from_console(settings, adapter, generation_id=gen_id, artifact_path=art_path)
                if result:
                    bid, paths, info = result
                    console.print(f"[green]Bundle created: {bid}[/green]")
                    pop_count = len(info.get("populated_paths") or [])
                    if pop_count:
                        console.print(f"  [dim]populated: {pop_count} paths from source[/dim]")
                    if info.get("xlsx_created"):
                        console.print("  [dim]XLSX workbook created[/dim]")
                    for p in (paths or [])[:8]:
                        console.print(f"  [dim]{p}[/dim]")
                else:
                    console.print("[red]Bundle creation failed.[/red]")
            else:
                console.print(f"[red]Unknown adapter: {adapter}[/red]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    if action == "8":
        bundles = list_bundles_for_console(settings, limit=15)
        if not bundles:
            console.print("[dim]No bundles yet. Create one with action 7.[/dim]")
        else:
            for i, b in enumerate(bundles[:10], 1):
                pop_count = len(b.get("populated_paths") or [])
                xlsx = " xlsx" if b.get("xlsx_created") else ""
                console.print(f"  [cyan]{i}[/cyan] {b['bundle_id']}  adapter={b['adapter_used']}  populated={pop_count}{xlsx}")
            bid = Prompt.ask("Bundle ID to adopt (or Enter to skip)", default="").strip()
            if bid:
                cand = adopt_bundle_for_console(settings, bid)
                if cand:
                    state.set_pending_adoption_candidate(cand)
                    console.print(f"[green]Adoption candidate created. Go to Apply to copy to target.[/green]")
                else:
                    console.print("[red]Bundle not found or adopt failed.[/red]")
        Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return Screen.GENERATION

    return Screen.HOME
