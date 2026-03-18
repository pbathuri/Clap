"""
M28I–M28L: CLI for human policy engine — show, evaluate, override, revoke, board.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.human_policy.store import load_policy_config, get_policy_dir
from workflow_dataset.human_policy.evaluate import evaluate
from workflow_dataset.human_policy.board import (
    list_active_effects,
    list_overrides,
    apply_override,
    revoke_override,
    explain_why_blocked,
    explain_why_allowed,
)


def _root(repo_root: str):
    return Path(repo_root).resolve() if repo_root else None


def cmd_show(repo_root: str = "") -> None:
    from rich.console import Console
    from rich.syntax import Syntax
    console = Console()
    root = _root(repo_root)
    config = load_policy_config(root)
    d = config.to_dict()
    import json
    console.print("[bold]Human policy config[/bold]")
    console.print(f"  path: {get_policy_dir(root) / 'policy_config.json'}")
    console.print(Syntax(json.dumps(d, indent=2), "json"))


def cmd_evaluate(
    action: str = "",
    project: str = "",
    pack: str = "",
    repo_root: str = "",
) -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    result = evaluate(action_class=action, project_id=project, pack_id=pack, repo_root=root)
    console.print("[bold]Policy evaluation[/bold]")
    console.print(f"  action_class: {action}  project: {project or '—'}  pack: {pack or '—'}")
    console.print(f"  is_always_manual: {result.is_always_manual}  may_batch: {result.may_batch}  may_delegate: {result.may_delegate}")
    console.print(f"  may_use_worker_lanes: {result.may_use_worker_lanes}  pack_may_override: {result.pack_may_override_defaults}  simulate_only: {result.simulate_only}")
    console.print(f"  blocked: {result.blocked}")
    for line in result.explanation:
        console.print(f"  [dim]{line}[/dim]")


def cmd_override(
    scope: str,
    id_: str,
    rule: str,
    value: str = "",
    reason: str = "",
    expires: str = "",
    repo_root: str = "",
) -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    val = value.lower() in ("true", "1", "yes") if value else False
    record = apply_override(scope=scope, scope_id=id_, rule_key=rule, rule_value=val, reason=reason, expires_at=expires, repo_root=root)
    console.print(f"[green]Override applied[/green] {record.override_id}")
    console.print(f"  scope={scope} scope_id={id_} rule_key={rule} rule_value={val}")


def cmd_revoke(override_id: str, repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    record = revoke_override(override_id, root)
    if record:
        console.print(f"[yellow]Revoked[/yellow] {override_id}")
    else:
        console.print(f"[red]Override not found: {override_id}[/red]")


def cmd_board(project: str = "", pack: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    root = _root(repo_root)
    effects = list_active_effects(project_id=project, pack_id=pack, repo_root=root)
    overrides = list_overrides(active_only=True, repo_root=root)
    console.print("[bold]Human policy board[/bold]")
    console.print(f"  project: {project or '—'}  pack: {pack or '—'}")
    t = Table("scope", "scope_id", "effect_key", "effect_value", "source")
    for e in effects:
        t.add_row(e.scope, e.scope_id, e.effect_key, str(e.effect_value), e.source)
    console.print(t)
    console.print("[bold]Active overrides[/bold]")
    for ov in overrides:
        console.print(f"  {ov.override_id}  scope={ov.scope} scope_id={ov.scope_id}  {ov.rule_key}={ov.rule_value}  [dim]revoke: workflow-dataset policy revoke {ov.override_id}[/dim]")
    if not overrides:
        console.print("  (none)")
    console.print("[dim]Explain blocked: workflow-dataset policy explain-blocked --action <action_class> --project <id>[/dim]")


def cmd_explain_blocked(action: str, project: str = "", pack: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    lines = explain_why_blocked(action_class=action, project_id=project, pack_id=pack, repo_root=root)
    if not lines:
        console.print(f"[green]Not blocked[/green] (or no reason). Use explain-allowed to see why allowed.")
        return
    console.print("[bold]Why blocked[/bold]")
    for line in lines:
        console.print(f"  {line}")


def cmd_explain_allowed(action: str, project: str = "", pack: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    console = Console()
    root = _root(repo_root)
    lines = explain_why_allowed(action_class=action, project_id=project, pack_id=pack, repo_root=root)
    console.print("[bold]Why allowed[/bold]")
    for line in lines:
        console.print(f"  {line}")


# M28L.1 Presets + trust mode
def cmd_presets(repo_root: str = "") -> None:
    from rich.console import Console
    from workflow_dataset.human_policy.presets import list_presets
    console = Console()
    presets = list_presets()
    console.print("[bold]Policy presets (trust modes)[/bold]")
    for p in presets:
        console.print(f"  [cyan]{p['id']}[/cyan]  {p['description']}")
    console.print("[dim]Apply: workflow-dataset policy apply-preset --name <id>[/dim]")


def cmd_apply_preset(name: str, repo_root: str = "") -> None:
    from rich.console import Console
    from workflow_dataset.human_policy.presets import apply_preset, PRESET_NAMES
    console = Console()
    root = _root(repo_root)
    if name not in PRESET_NAMES:
        console.print(f"[red]Unknown preset: {name}[/red]. Use: {', '.join(PRESET_NAMES)}")
        return
    config = apply_preset(name, root)
    if config:
        console.print(f"[green]Applied preset[/green] {name}")
        console.print(f"  active_preset: {config.active_preset}")
    else:
        console.print(f"[red]Failed to apply preset: {name}[/red]")


def cmd_trust_mode(preset: str = "", repo_root: str = "") -> None:
    from rich.console import Console
    from workflow_dataset.human_policy.presets import get_trust_mode_explanation, PRESET_NAMES
    console = Console()
    root = _root(repo_root)
    preset_name = preset.strip() or None
    if preset_name and preset_name not in PRESET_NAMES:
        console.print(f"[red]Unknown preset: {preset_name}[/red]. Omit --preset to explain current config.")
        return
    lines = get_trust_mode_explanation(preset_name=preset_name, repo_root=root)
    console.print("[bold]Trust mode explanation[/bold]")
    for line in lines:
        console.print(f"  {line}")
