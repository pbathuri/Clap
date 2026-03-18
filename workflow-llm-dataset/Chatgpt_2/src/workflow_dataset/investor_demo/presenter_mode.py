"""
M51L.1: Presenter mode — compact cues, 5-minute script alignment, degraded bridge.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from workflow_dataset.investor_demo.models import PresenterModeConfig, PresenterModeView
from workflow_dataset.investor_demo.session_store import load_demo_session
from workflow_dataset.investor_demo.degraded import collect_degraded_warnings
from workflow_dataset.investor_demo.degraded_narrative import degraded_narrative_bridge
from workflow_dataset.investor_demo.five_minute_script import beat_for_stage, build_five_minute_demo_script
from workflow_dataset.investor_demo.models import DemoNarrativeStage


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def presenter_config_path(repo_root: Path | str | None = None) -> Path:
    return _root(repo_root) / "data" / "local" / "investor_demo" / "presenter_mode.json"


def load_presenter_config(repo_root: Path | str | None = None) -> PresenterModeConfig:
    p = presenter_config_path(repo_root)
    if not p.exists():
        return PresenterModeConfig()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return PresenterModeConfig(
            enabled=bool(d.get("enabled", False)),
            five_minute_script_active=bool(d.get("five_minute_script_active", True)),
            updated_at_iso=d.get("updated_at_iso", ""),
        )
    except Exception:
        return PresenterModeConfig()


def save_presenter_config(cfg: PresenterModeConfig, repo_root: Path | str | None = None) -> None:
    root = _root(repo_root)
    p = presenter_config_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    cfg.updated_at_iso = datetime.now(timezone.utc).isoformat()[:19] + "Z"
    p.write_text(json.dumps(cfg.to_dict(), indent=2), encoding="utf-8")


def set_presenter_mode(enabled: bool, repo_root: Path | str | None = None) -> PresenterModeConfig:
    cfg = load_presenter_config(repo_root)
    cfg.enabled = enabled
    save_presenter_config(cfg, repo_root)
    sess = load_demo_session(repo_root)
    if sess:
        sess.presenter_mode_enabled = enabled
        from workflow_dataset.investor_demo.session_store import _save_session
        _save_session(_root(repo_root), sess)
    return cfg


def build_presenter_mode_view(repo_root: Path | str | None = None) -> PresenterModeView:
    root = _root(repo_root)
    cfg = load_presenter_config(root)
    sess = load_demo_session(root)
    warnings = collect_degraded_warnings(root)
    if sess and sess.degraded_warnings and not warnings:
        warnings = sess.degraded_warnings
    bridge = degraded_narrative_bridge(warnings)
    is_deg = len(warnings) > 0
    stage_id = sess.current_stage if sess else DemoNarrativeStage.STARTUP_READINESS.value
    beat = beat_for_stage(stage_id)
    headline = f"Stage: {stage_id}"
    if beat:
        headline = f"Beat {beat.beat_index}/{len(build_five_minute_demo_script().beats)} — {beat.stage_id.replace('_', ' ')}"

    hints = [
        "workflow-dataset investor-demo cue",
        "workflow-dataset investor-demo script",
        "workflow-dataset investor-demo session stage",
    ]
    if beat:
        hints.insert(0, beat.click_or_run.split("&&")[0].strip())

    return PresenterModeView(
        presenter_mode_enabled=cfg.enabled,
        degraded_bridge=bridge,
        is_degraded_demo=is_deg,
        current_stage_id=stage_id,
        current_beat=beat,
        headline=headline,
        next_cli_hints=hints[:5],
    )


def format_presenter_mode_text(view: PresenterModeView) -> str:
    lines = [
        "=== Presenter mode ===",
        f"Presenter mode: {'ON' if view.presenter_mode_enabled else 'OFF'}",
        f"{view.headline}",
        "",
    ]
    if view.is_degraded_demo and view.degraded_bridge:
        lines.append("[Degraded — narrative continues]")
        lines.append(view.degraded_bridge)
        lines.append("")
    if view.current_beat:
        b = view.current_beat
        lines.append("— Current beat —")
        lines.append(f"  SHOW:  {b.show}")
        lines.append(f"  RUN:   {b.click_or_run}")
        lines.append(f"  SAY:   {b.say}")
        if view.is_degraded_demo and b.if_degraded_say:
            lines.append(f"  IF DEGRADED SAY: {b.if_degraded_say}")
        lines.append("")
    lines.append("Next commands:")
    for h in view.next_cli_hints:
        lines.append(f"  • {h}")
    return "\n".join(lines)
