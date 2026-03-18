"""
M50L.1: Post-v1 watch-state summary — what to monitor after stable-v1 approval; experimental/deferred remains.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from workflow_dataset.stable_v1_gate.models import PostV1WatchStateSummary

if TYPE_CHECKING:
    from workflow_dataset.stable_v1_gate.models import StableV1Report


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_post_v1_watch_state_summary(
    report: StableV1Report | None = None,
    repo_root: Path | str | None = None,
) -> PostV1WatchStateSummary:
    """
    Build post-v1 watch-state summary from the stable-v1 report (or build report when not provided).
    Summarizes: recommendation, narrow conditions in effect, gate warnings, experimental/deferred remains, next review.
    """
    now = datetime.now(timezone.utc)
    at_iso = now.isoformat()[:19] + "Z"

    if report is None:
        from workflow_dataset.stable_v1_gate.report import build_stable_v1_report
        root = _root(repo_root)
        report = build_stable_v1_report(root)

    decision = report.decision
    gate = report.gate
    evidence = report.evidence

    stable_v1_recommendation = decision.recommendation
    narrow_conditions_in_effect: list[str] = []
    if decision.narrow_condition:
        narrow_conditions_in_effect = [s.strip() for s in decision.narrow_condition.split(";") if s.strip()]

    gate_warnings_summary = ""
    if gate.warnings:
        gate_warnings_summary = f"{len(gate.warnings)} gate warning(s): " + "; ".join(w.summary[:60] for w in gate.warnings[:5])
        if len(gate.warnings) > 5:
            gate_warnings_summary += " ..."
    else:
        gate_warnings_summary = "None."

    experimental_summary = ""
    deferred_summary = ""
    try:
        root = _root(repo_root)
        from workflow_dataset.production_cut import get_active_cut
        from workflow_dataset.production_cut.labels import build_operator_surface_explanations
        cut = get_active_cut(root)
        if cut and (getattr(cut, "quarantined_surface_ids", None) or getattr(cut, "excluded_surface_ids", None)):
            expl = build_operator_surface_explanations(cut, root)
            experimental_summary = (expl.get("experimental_only_summary") or "")[:300]
            if not experimental_summary and getattr(cut, "quarantined_surface_ids", None):
                q = cut.quarantined_surface_ids
                experimental_summary = f"{len(q)} surface(s) experimental (quarantined); not production-default."
        if not experimental_summary:
            experimental_summary = "No experimental surfaces in current cut."
    except Exception:
        experimental_summary = "Unknown (run workflow-dataset production-cut scope-report)."

    if gate.warnings:
        deferred_summary = "Gate warnings represent conditions to revisit: " + "; ".join(w.summary[:50] for w in gate.warnings[:3])
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        root = _root(repo_root)
        rr = build_release_readiness(root)
        lims = getattr(rr, "known_limitations", []) or []
        if lims:
            deferred_summary = (deferred_summary + " " if deferred_summary else "") + "Known limitations (deferred): " + "; ".join(getattr(l, "summary", str(l))[:40] for l in lims[:3])
    except Exception:
        pass
    if not deferred_summary:
        deferred_summary = "None beyond gate warnings."

    next_review_action = decision.next_required_action or "workflow-dataset stable-v1 report"

    return PostV1WatchStateSummary(
        stable_v1_recommendation=stable_v1_recommendation,
        narrow_conditions_in_effect=narrow_conditions_in_effect,
        gate_warnings_summary=gate_warnings_summary,
        experimental_summary=experimental_summary,
        deferred_summary=deferred_summary,
        next_review_action=next_review_action,
        generated_at_iso=at_iso,
    )
