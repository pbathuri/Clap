"""
M41B–M41C: Create improvement experiments from issue cluster, repeated correction, accepted adaptation; compare; record outcome.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.learning_lab.models import (
    ImprovementExperiment,
    LocalLearningSlice,
    ExperimentEvidenceBundle,
    SOURCE_ISSUE_CLUSTER,
    SOURCE_REPEATED_CORRECTION,
    SOURCE_ACCEPTED_ADAPTATION,
    OUTCOME_PENDING,
    OUTCOME_REJECTED,
    OUTCOME_QUARANTINED,
    OUTCOME_PROMOTED,
)
from workflow_dataset.learning_lab.store import (
    save_experiment,
    get_experiment,
    list_experiments,
    set_active_experiment_id,
    get_current_profile_id,
)

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _apply_profile_and_template(
    exp: ImprovementExperiment,
    profile_id: str,
    template_id: str,
    repo_root: Path,
) -> None:
    """Set profile_id and template_id on experiment; use store default profile if profile_id empty."""
    exp.profile_id = profile_id or get_current_profile_id(repo_root)
    exp.template_id = template_id or ""


def create_experiment_from_issue_cluster(
    cluster_id: str,
    cohort_id: str = "",
    profile_id: str = "",
    template_id: str = "",
    repo_root: Path | str | None = None,
) -> ImprovementExperiment | None:
    """Create an improvement experiment from a triage issue cluster."""
    root = _root(repo_root)
    try:
        from workflow_dataset.triage.clusters import build_all_clusters
        from workflow_dataset.triage.store import list_evidence
        clusters = build_all_clusters(repo_root=root, cohort_id=cohort_id)
        cluster = next((c for c in clusters if c.cluster_id == cluster_id), None)
        if not cluster:
            return None
        evidence_ids = []
        try:
            evidence = list_evidence(repo_root=root, cohort_id=cohort_id, limit=200)
            for e in evidence:
                if e.issue_id and e.issue_id in cluster.issue_ids:
                    evidence_ids.append(e.evidence_id)
        except Exception:
            pass
        exp_id = stable_id("exp", "issue_cluster", cluster_id, utc_now_iso(), prefix="exp_")
        now = utc_now_iso()
        local_slice = LocalLearningSlice(
            slice_id=stable_id("slice", cluster_id, prefix="slice_"),
            description=f"Issue cluster {cluster_id}: {len(cluster.issue_ids)} issues",
            issue_ids=list(cluster.issue_ids),
            evidence_ids=evidence_ids[:50],
        )
        evidence_bundle = ExperimentEvidenceBundle(
            evidence_ids=evidence_ids[:30],
            correction_ids=[],
            session_ids=[],
            summary=f"Cluster {cluster_id}; {len(cluster.issue_ids)} issues",
        )
        exp = ImprovementExperiment(
            experiment_id=exp_id,
            source_type=SOURCE_ISSUE_CLUSTER,
            source_ref=cluster_id,
            label=f"Experiment from cluster {cluster_id}",
            created_at_utc=now,
            status=OUTCOME_PENDING,
            local_slice=local_slice,
            evidence_bundle=evidence_bundle,
            comparison_summary="",
        )
        _apply_profile_and_template(exp, profile_id, template_id, root)
        save_experiment(exp, root)
        set_active_experiment_id(exp_id, root)
        return exp
    except Exception:
        return None


def create_experiment_from_repeated_correction(
    target_type: str,
    target_id: str,
    min_corrections: int = 2,
    profile_id: str = "",
    template_id: str = "",
    repo_root: Path | str | None = None,
) -> ImprovementExperiment | None:
    """Create experiment from repeated corrections on same target (e.g. same job/routine)."""
    root = _root(repo_root)
    try:
        from workflow_dataset.corrections.store import list_corrections
        from workflow_dataset.corrections.propose import propose_updates
        corrections = list_corrections(limit=100, repo_root=root)
        proposed = propose_updates(repo_root=root, limit_corrections=100)
        same_target = [p for p in proposed if p.target_type == target_type and p.target_id == target_id]
        if not same_target:
            return None
        correction_ids = []
        for p in same_target:
            correction_ids.extend(getattr(p, "correction_ids", []) or [])
        correction_ids = list(dict.fromkeys(correction_ids))
        if len(correction_ids) < min_corrections:
            return None
        correction_ids = correction_ids[:20]
        exp_id = stable_id("exp", "repeated_correction", target_type, target_id, utc_now_iso(), prefix="exp_")
        now = utc_now_iso()
        evidence_bundle = ExperimentEvidenceBundle(
            evidence_ids=[],
            correction_ids=correction_ids,
            session_ids=[],
            summary=f"Repeated corrections on {target_type}/{target_id}",
        )
        local_slice = LocalLearningSlice(
            slice_id=stable_id("slice", target_type, target_id, prefix="slice_"),
            description=f"Corrections for {target_type} {target_id}",
            correction_ids=correction_ids,
        )
        exp = ImprovementExperiment(
            experiment_id=exp_id,
            source_type=SOURCE_REPEATED_CORRECTION,
            source_ref=f"{target_type}:{target_id}",
            label=f"Experiment from repeated corrections {target_type}/{target_id}",
            created_at_utc=now,
            status=OUTCOME_PENDING,
            local_slice=local_slice,
            evidence_bundle=evidence_bundle,
            comparison_summary="",
        )
        _apply_profile_and_template(exp, profile_id, template_id, root)
        save_experiment(exp, root)
        set_active_experiment_id(exp_id, root)
        return exp
    except Exception:
        return None


def create_experiment_from_accepted_adaptation(
    adaptation_id: str,
    profile_id: str = "",
    template_id: str = "",
    repo_root: Path | str | None = None,
) -> ImprovementExperiment | None:
    """Create experiment from an accepted adaptation candidate (evidence bundle already exists)."""
    root = _root(repo_root)
    try:
        from workflow_dataset.safe_adaptation.store import load_candidate
        cand = load_candidate(adaptation_id, root)
        ev = getattr(cand, "evidence", None) if cand else None
        evidence_ids = list(getattr(ev, "evidence_ids", []) or [])[:30] if ev else []
        correction_ids = list(getattr(ev, "correction_ids", []) or [])[:20] if ev else []
        session_ids = list(getattr(ev, "session_ids", []) or [])[:20] if ev else []
        summary_ev = getattr(ev, "summary", "") or f"Adaptation {adaptation_id}" if ev else f"Adaptation {adaptation_id}"
        exp_id = stable_id("exp", "accepted_adaptation", adaptation_id, utc_now_iso(), prefix="exp_")
        now = utc_now_iso()
        evidence_bundle = ExperimentEvidenceBundle(
            evidence_ids=evidence_ids,
            correction_ids=correction_ids,
            session_ids=session_ids,
            summary=summary_ev,
        )
        local_slice = LocalLearningSlice(
            slice_id=stable_id("slice", adaptation_id, prefix="slice_"),
            description=f"Adaptation {adaptation_id}",
            evidence_ids=evidence_ids[:20],
            correction_ids=correction_ids[:20],
        )
        exp = ImprovementExperiment(
            experiment_id=exp_id,
            source_type=SOURCE_ACCEPTED_ADAPTATION,
            source_ref=adaptation_id,
            label=f"Experiment from adaptation {adaptation_id}",
            created_at_utc=now,
            status=OUTCOME_PENDING,
            local_slice=local_slice,
            evidence_bundle=evidence_bundle,
            comparison_summary="",
        )
        _apply_profile_and_template(exp, profile_id, template_id, root)
        save_experiment(exp, root)
        set_active_experiment_id(exp_id, root)
        return exp
    except Exception:
        return None


def compare_before_after(
    experiment_id: str,
    run_before: str | None = None,
    run_after: str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Compare before/after using eval board if runs provided; else return summary from slice."""
    root = _root(repo_root)
    exp = get_experiment(experiment_id, root)
    if not exp:
        return {"error": f"Experiment not found: {experiment_id}"}
    if run_before and run_after:
        try:
            from workflow_dataset.eval.board import compare_runs
            comp = compare_runs(run_before, run_after, root=root)
            if comp.get("error"):
                return {"experiment_id": experiment_id, "comparison": comp, "comparison_summary": comp.get("error")}
            rec = comp.get("recommendation", "")
            summary = f"before={run_before} after={run_after} recommendation={rec}"
            return {
                "experiment_id": experiment_id,
                "comparison": comp,
                "comparison_summary": summary,
                "run_before": run_before,
                "run_after": run_after,
            }
        except Exception as e:
            return {"experiment_id": experiment_id, "comparison_summary": f"Compare failed: {e}"}
    # No runs: summarize slice
    sl = exp.local_slice
    eb = exp.evidence_bundle
    parts = []
    if sl:
        if sl.issue_ids:
            parts.append(f"{len(sl.issue_ids)} issues")
        if sl.correction_ids:
            parts.append(f"{len(sl.correction_ids)} corrections")
        if sl.evidence_ids:
            parts.append(f"{len(sl.evidence_ids)} evidence")
    if eb:
        parts.append(eb.summary or "")
    summary = "; ".join(parts) if parts else "No runs to compare; slice only."
    return {
        "experiment_id": experiment_id,
        "comparison_summary": summary,
        "run_before": None,
        "run_after": None,
    }


def record_outcome(
    experiment_id: str,
    outcome: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> ImprovementExperiment | None:
    """Record experiment outcome: rejected | quarantined | promoted. Appends updated experiment line."""
    if outcome not in (OUTCOME_REJECTED, OUTCOME_QUARANTINED, OUTCOME_PROMOTED):
        return None
    root = _root(repo_root)
    exp = get_experiment(experiment_id, root)
    if not exp:
        return None
    exp.status = outcome
    exp.status_reason = reason or outcome
    save_experiment(exp, root)
    return exp
