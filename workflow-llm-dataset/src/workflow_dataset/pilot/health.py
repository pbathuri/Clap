"""
M20: Pilot health — verify result, status dict, pilot readiness report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def _load_release_config(release_config_path: str | Path = "configs/release_narrow.yaml") -> dict[str, Any]:
    path = Path(release_config_path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("release", {})


def _load_llm_config(llm_path: str | Path) -> dict[str, Any]:
    path = Path(llm_path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def pilot_verify_result(
    config_path: str = "configs/settings.yaml",
    release_config_path: str = "configs/release_narrow.yaml",
) -> dict[str, Any]:
    """
    Run checks needed for pilot: config, graph, setup dirs, LLM adapter, trials.
    Returns dict with ready: bool, blocking: list[str], warnings: list[str], details.
    Relative paths are resolved against project root (directory containing configs/settings.yaml).
    """
    from workflow_dataset.path_utils import resolve_config_path
    r_cfg = resolve_config_path(config_path)
    r_rel = resolve_config_path(release_config_path)
    config_path = str(r_cfg) if r_cfg is not None else config_path
    release_config_path = str(r_rel) if r_rel is not None else release_config_path
    rel = _load_release_config(release_config_path)
    llm_path = rel.get("default_llm_config", "configs/llm_training_full.yaml")
    if llm_path:
        r_llm = resolve_config_path(llm_path)
        if r_llm is not None:
            llm_path = str(r_llm)
    blocking: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    try:
        from workflow_dataset.settings import load_settings
        settings = load_settings(config_path)
    except Exception as e:
        blocking.append(f"Config load failed: {e}")
        return {"ready": False, "blocking": blocking, "warnings": warnings, "details": details}

    paths = getattr(settings, "paths", None)
    graph_path = Path(getattr(paths, "graph_store_path", "data/local/work_graph.sqlite")) if paths else Path("data/local/work_graph.sqlite")
    details["graph_path"] = str(graph_path)
    if not graph_path.exists():
        blocking.append("Graph missing (run setup init + setup run)")
    else:
        details["graph_ok"] = True

    setup = getattr(settings, "setup", None)
    if not setup:
        blocking.append("Setup config missing")
    else:
        for name, dir_key in [("setup_dir", "setup_dir"), ("parsed_artifacts_dir", "parsed_artifacts_dir"), ("style_signals_dir", "style_signals_dir")]:
            p = Path(getattr(setup, dir_key, ""))
            details[f"{name}_ok"] = bool(p and p.exists())
            if not p or not p.exists():
                blocking.append(f"Setup: {name} missing or empty")

    llm_cfg = _load_llm_config(llm_path)
    details["llm_config_path"] = llm_path
    details["llm_config_present"] = bool(llm_cfg)
    if not llm_cfg:
        warnings.append("LLM config not found; demo/run will use baseline if base_model set elsewhere")
    else:
        runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
        try:
            from workflow_dataset.llm.run_summary import find_latest_successful_adapter
            adapter_path, run_dir = find_latest_successful_adapter(runs_dir)
            details["adapter_ok"] = bool(adapter_path)
            details["adapter_path"] = adapter_path or ""
            details["latest_run_dir"] = run_dir or ""
            if not adapter_path:
                warnings.append("No successful adapter; demo/run will use base model (degraded)")
        except Exception as e:
            details["adapter_error"] = str(e)
            warnings.append(f"Adapter check failed: {e}")

    trials_dir = Path(rel.get("trials_output_dir", "data/local/trials"))
    details["trials_dir"] = str(trials_dir)
    feedback_report = trials_dir / "latest_feedback_report.md"
    details["feedback_report_present"] = feedback_report.exists()

    ready = len(blocking) == 0
    return {"ready": ready, "blocking": blocking, "warnings": warnings, "details": details}


def _pilot_feedback_excerpt(pilot_dir: Path | str, max_chars: int = 600) -> str:
    """Build a short excerpt from M21 pilot feedback (freeform_notes, user_quote) for the readiness report."""
    try:
        from workflow_dataset.pilot.feedback_capture import list_feedback_files, load_feedback
        from workflow_dataset.pilot.session_log import list_sessions
        root = Path(pilot_dir) if pilot_dir else Path("data/local/pilot")
        sessions = list_sessions(root, limit=5)
        if not sessions:
            return ""
        parts: list[str] = []
        seen = 0
        for s in sessions:
            if seen >= 2:
                break
            fb = load_feedback(s.session_id, root)
            if not fb:
                continue
            text_parts: list[str] = []
            if fb.freeform_notes and fb.freeform_notes.strip():
                text_parts.append(fb.freeform_notes.strip())
            if fb.user_quote and fb.user_quote.strip():
                text_parts.append(f'"{fb.user_quote.strip()}"')
            if text_parts:
                parts.append("- " + " ".join(text_parts)[:280])
                seen += 1
        return "\n".join(parts)[:max_chars] if parts else ""
    except Exception:
        return ""


def pilot_status_dict(
    config_path: str = "configs/settings.yaml",
    release_config_path: str = "configs/release_narrow.yaml",
    trials_dir: str | Path | None = None,
    packs_dir: str | Path | None = None,
) -> dict[str, Any]:
    """
    Summarize pilot status: interpreter, config validity, latest adapter, degraded, safe to demo, latest feedback.
    When packs_dir is set, resolves active pack for release scope (e.g. ops) and adds active_pack_ids.
    """
    rel = _load_release_config(release_config_path)
    trials_dir = Path(trials_dir) if trials_dir else Path(rel.get("trials_output_dir", "data/local/trials"))
    result = pilot_verify_result(config_path=config_path, release_config_path=release_config_path)
    status: dict[str, Any] = {
        "ready": result["ready"],
        "blocking": result["blocking"],
        "warnings": result["warnings"],
        "degraded": False,
        "safe_to_demo": result["ready"],
        "config_valid": len(result["blocking"]) == 0 or "Config load failed" not in result["blocking"],
    }
    details = result.get("details", {})
    status["graph_ok"] = details.get("graph_ok", False)
    status["adapter_ok"] = details.get("adapter_ok", False)
    status["adapter_path"] = details.get("adapter_path", "")
    status["latest_run_dir"] = details.get("latest_run_dir", "")
    if not details.get("adapter_ok") and details.get("llm_config_present"):
        status["degraded"] = True
        status["safe_to_demo"] = status["safe_to_demo"]  # can still demo with base model
    if not result["ready"]:
        status["safe_to_demo"] = False

    feedback_report = trials_dir / "latest_feedback_report.md"
    status["latest_feedback_report"] = str(feedback_report) if feedback_report.exists() else ""
    status["scope"] = rel.get("scope_label", "Operations reporting assistant")
    scope_role = rel.get("scope", "ops")
    try:
        from workflow_dataset.packs import resolve_active_capabilities
        cap = resolve_active_capabilities(role=scope_role, packs_dir=packs_dir or "data/local/packs")
        status["active_pack_ids"] = [m.pack_id for m in cap.active_packs]
    except Exception:
        status["active_pack_ids"] = []
    return status


def write_pilot_readiness_report(
    output_path: str | Path | None = None,
    config_path: str = "configs/settings.yaml",
    release_config_path: str = "configs/release_narrow.yaml",
    pilot_dir: Path | str | None = None,
) -> Path:
    """
    Write pilot_readiness_report.md summarizing scope, status, evidence, risks, recommendation.
    """
    rel = _load_release_config(release_config_path)
    pilot_dir = Path(pilot_dir) if pilot_dir else Path("data/local/pilot")
    pilot_dir.mkdir(parents=True, exist_ok=True)
    out = Path(output_path) if output_path else pilot_dir / "pilot_readiness_report.md"

    status = pilot_status_dict(config_path=config_path, release_config_path=release_config_path, trials_dir=rel.get("trials_output_dir", "data/local/trials"))
    trials_dir = Path(rel.get("trials_output_dir", "data/local/trials"))
    feedback_report = trials_dir / "latest_feedback_report.md"
    trial_feedback_summary = ""
    if feedback_report.exists():
        try:
            raw = feedback_report.read_text(encoding="utf-8")[:1500]
            if "Feedback entries: 0" not in raw and "No feedback yet" not in raw:
                trial_feedback_summary = raw
        except Exception:
            pass

    pilot_feedback_excerpt = _pilot_feedback_excerpt(pilot_dir)

    active_packs = status.get("active_pack_ids") or []
    lines = [
        "# Pilot readiness report",
        "",
        f"**Scope:** {status.get('scope', 'Operations reporting assistant')}",
        f"**Active pack(s):** {', '.join(active_packs) if active_packs else '(none)'}",
        f"**Ready:** {status.get('ready', False)}",
        f"**Safe to demo:** {status.get('safe_to_demo', False)}",
        f"**Degraded mode:** {status.get('degraded', False)}"
        + (
            " (no adapter; base model only)"
            if status.get("degraded")
            else " (adapter available)" if status.get("adapter_ok") else " (LLM config missing or no adapter)"
        ),
        "",
        "## Blocking issues",
        "",
    ]
    for b in status.get("blocking", []):
        lines.append(f"- {b}")
    if not status.get("blocking"):
        lines.append("- (none)")
    lines.extend(["", "## Warnings", ""])
    for w in status.get("warnings", []):
        lines.append(f"- {w}")
    if not status.get("warnings"):
        lines.append("- (none)")
    lines.extend([
        "",
        "## Supported user / task set",
        "",
        "- Pilot user: ops/reporting role; single device; local-first.",
        "- Tasks: ops_summarize_reporting, ops_scaffold_status, ops_next_steps, release_demo.",
        "- Excluded: spreadsheet, creative, finance, multi-user, cloud.",
        "",
        "## Evidence",
        "",
        f"- Graph: {'OK' if status.get('graph_ok') else 'missing'}",
        f"- Adapter: {'OK' if status.get('adapter_ok') else 'missing (degraded)'}",
        f"- Latest run: {status.get('latest_run_dir', '(none)')}",
        "",
        "## M21 pilot evidence",
        "",
    ])
    try:
        from workflow_dataset.pilot.session_log import list_sessions
        from workflow_dataset.pilot.feedback_capture import list_feedback_files
        sessions = list_sessions(pilot_dir)
        feedback_paths = list_feedback_files(pilot_dir)
        lines.append(f"- **Pilot sessions completed:** {len(sessions)}")
        lines.append(f"- **Structured feedback entries:** {len(feedback_paths)}")
        if len(sessions) == 0:
            lines.append("- Run `pilot start-session` → run/demo → `pilot capture-feedback` → `pilot end-session` → `pilot aggregate` to generate evidence.")
    except Exception:
        lines.append("- (M21 session/feedback modules not available)")
    lines.extend([
        "",
        "## Unresolved risks",
        "",
        "See docs/RELIABILITY_TRIAGE.md. Acceptable-with-warning items (no adapter, retrieval fail) are documented.",
        "",
        "## Recommendation",
        "",
    ])
    pilot_sessions_count = 0
    try:
        from workflow_dataset.pilot.session_log import list_sessions
        pilot_sessions_count = len(list_sessions(pilot_dir))
    except Exception:
        pass
    if not status.get("ready"):
        lines.append("- **Not ready.** Fix blocking issues (graph, setup) then re-run pilot verify.")
    elif pilot_sessions_count >= 3:
        lines.append("- **Continue narrow pilot expansion / evidence collection** within current scope. Initial 2–3 user threshold exceeded; proceed per docs/PILOT_OPERATOR_GUIDE.md.")
    elif status.get("degraded"):
        lines.append("- **Ready for 2–3 user narrow private pilot** with degraded mode (base model). Recommend training adapter for better outputs.")
    else:
        lines.append("- **Ready for 2–3 user narrow private pilot** with adapter. Proceed per docs/PILOT_OPERATOR_GUIDE.md.")
    lines.append("")
    if pilot_feedback_excerpt:
        lines.append("## Latest pilot feedback (excerpt)")
        lines.append("")
        lines.append("Evidence from M21 pilot session feedback (data/local/pilot/feedback/):")
        lines.append("")
        lines.append(pilot_feedback_excerpt)
        lines.append("")
    if trial_feedback_summary:
        lines.append("## Trial feedback (excerpt)")
        lines.append("")
        lines.append("From trial tasks (data/local/trials/latest_feedback_report.md):")
        lines.append("")
        lines.append(trial_feedback_summary[:800].strip())
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
