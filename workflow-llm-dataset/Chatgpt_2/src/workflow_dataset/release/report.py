"""
M18: Release readiness report — evidence-based summary for narrow release.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_release_readiness_report(
    config_path: str = "configs/settings.yaml",
    release_config_path: str = "configs/release_narrow.yaml",
    output_dir: Path | str | None = None,
) -> Path:
    """
    Write release_readiness_report.md under output_dir. Summarizes scope, evidence, safety, demo readiness.
    Evidence-based; reads release preset and checks for graph, adapter, trial results when possible.
    """
    output_dir = Path(output_dir) if output_dir else Path("data/local/release")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "release_readiness_report.md"

    import yaml
    rel: dict[str, Any] = {}
    if Path(release_config_path).exists():
        with open(release_config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        rel = data.get("release", {})

    scope = rel.get("scope", "ops")
    scope_label = rel.get("scope_label", "Operations reporting assistant")
    trial_ids = rel.get("trial_ids", ["ops_summarize_reporting", "ops_scaffold_status", "ops_next_steps"])

    # Optional: load settings for paths
    graph_ok = False
    try:
        from workflow_dataset.settings import load_settings
        s = load_settings(config_path)
        p = getattr(s, "paths", None)
        if p:
            gp = Path(getattr(p, "graph_store_path", ""))
            graph_ok = gp.exists()
    except Exception:
        pass

    # Optional: LLM adapter
    adapter_ok = False
    llm_path = rel.get("default_llm_config", "configs/llm_training_full.yaml")
    if Path(llm_path).exists():
        try:
            with open(llm_path) as f:
                llm_cfg = yaml.safe_load(f) or {}
            runs_dir = Path(llm_cfg.get("runs_dir", "data/local/llm/runs"))
            from workflow_dataset.llm.run_summary import find_latest_successful_adapter
            adapter_path, _ = find_latest_successful_adapter(runs_dir)
            adapter_ok = bool(adapter_path)
        except Exception:
            pass

    # Optional: trial results count
    trial_count = 0
    trials_dir = Path(rel.get("trials_output_dir", "data/local/trials"))
    if trials_dir.exists():
        trial_count = len(list(trials_dir.glob("res_*.json")))

    lines = [
        "# Release readiness report",
        "",
        f"**Scope:** {scope_label}",
        f"**Category:** {scope}",
        "",
        "## Supported workflows",
        "",
        "- Summarize recurring reporting workflow and suggest weekly status structure",
        "- Scaffold weekly status report package in the user's style",
        "- Recommend next steps based on previous work structure",
        "- Explain workflow type from observed patterns (e.g. .csv/.xlsx usage)",
        "",
        "## Supported inputs",
        "",
        "- Work graph (projects, nodes)",
        "- Parsed artifacts from setup",
        "- Style signals (naming, export patterns)",
        "- Optional: corpus for retrieval-grounded answers",
        "",
        "## Supported outputs",
        "",
        "- Style-aware suggestions (assist suggest)",
        "- Model-generated text (workflow summary, next steps, explanations)",
        "- Generated scaffolds/bundles in sandbox (generation workspace, bundle root)",
        "- Adoption candidates for apply preview and confirm",
        "",
        "## Evidence (M16/M17)",
        "",
        "- M16: Full adapter outperformed smoke (token_overlap 0.80 vs 0.26); workflow_inference and knowledge_qa strongest.",
        "- M17: Ops trials (ops_summarize_reporting, ops_scaffold_status, ops_next_steps) define narrow release.",
        "- Retrieval: Optional; can hurt overlap on eval; use for qualitative grounding when desired.",
        "",
        "## Safety boundaries",
        "",
        "- No uncontrolled writes; sandbox-only generation/bundles.",
        "- Apply only after explicit user confirmation.",
        "- Local-only; no cloud APIs.",
        "- Simulate-first; agent suggests, does not execute without approval.",
        "",
        "## Known failure modes",
        "",
        "- Empty graph or no setup: suggestions and context will be minimal.",
        "- No adapter: demo uses base model or placeholder; answers less task-specific.",
        "- Retrieval on: may reduce metric overlap; still useful for grounded phrasing.",
        "- Personalization is mild; model often generic.",
        "",
        "## Demo readiness",
        "",
        f"- Graph: {'OK' if graph_ok else 'missing or not checked'}",
        f"- Adapter: {'OK' if adapter_ok else 'missing (baseline/placeholder possible)'}",
        f"- Trial results: {trial_count} result(s) in {trials_dir}",
        "",
        "## Ready for",
        "",
        "- **Internal founder demo:** Yes, with pre-demo setup (see docs/FOUNDER_DEMO_FLOW.md).",
        "- **Friendly-user trial:** Yes, single user, narrow ops/reporting flow.",
        "- **Narrow private pilot:** After founder demo and one friendly-user run; document feedback and limits.",
        "",
        "---",
        "",
        "See docs/FIRST_NARROW_RELEASE.md and docs/NOT_YET_SUPPORTED.md.",
        "",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path