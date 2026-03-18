"""
M24G: Capability health — lifecycle summary, prerequisite checks, failed diagnostics, deactivation path, health report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.registry import list_external_sources
from workflow_dataset.external_capability.lifecycle import source_lifecycle_state
from workflow_dataset.external_capability.activation_store import list_requests, load_history


@dataclass
class PrerequisiteCheck:
    source_id: str
    check: str
    passed: bool
    detail: str = ""


@dataclass
class CapabilityHealth:
    """Aggregate capability health for reporting."""

    by_lifecycle: dict[str, list[str]] = field(default_factory=dict)  # lifecycle_state -> [source_id]
    prerequisite_checks: list[PrerequisiteCheck] = field(default_factory=list)
    failed_activations: list[dict[str, Any]] = field(default_factory=list)
    deactivation_path_available: list[str] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    recommended_next: str = ""


def _check_ollama(source_id: str, root: Path) -> PrerequisiteCheck:
    if source_id != "backend_ollama":
        return PrerequisiteCheck(source_id=source_id, check="n/a", passed=True)
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as _:
            return PrerequisiteCheck(source_id=source_id, check="ollama_reachable", passed=True, detail="Ollama responding")
    except Exception as e:
        return PrerequisiteCheck(source_id=source_id, check="ollama_reachable", passed=False, detail=str(e))


def _check_integration_enabled(source_id: str, root: Path) -> PrerequisiteCheck:
    try:
        from workflow_dataset.runtime_mesh.integration_registry import get_integration
        m = get_integration(source_id, root)
        if not m:
            return PrerequisiteCheck(source_id=source_id, check="integration_manifest", passed=True, detail="Not an integration")
        return PrerequisiteCheck(
            source_id=source_id,
            check="integration_enabled",
            passed=m.enabled,
            detail="enabled" if m.enabled else "disabled",
        )
    except Exception as e:
        return PrerequisiteCheck(source_id=source_id, check="integration_manifest", passed=False, detail=str(e))


def build_capability_health(repo_root: Path | str | None = None) -> CapabilityHealth:
    """
    Build capability health: lifecycle counts, prerequisite checks, failed activations,
    deactivation path availability, summary, recommended next action.
    """
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    health = CapabilityHealth()
    sources = list_external_sources(root)
    by_lifecycle: dict[str, list[str]] = {}
    for s in sources:
        state = source_lifecycle_state(s.source_id, root)
        by_lifecycle.setdefault(state, []).append(s.source_id)
    health.by_lifecycle = by_lifecycle

    # Prerequisite checks for backends and key integrations
    checks: list[PrerequisiteCheck] = []
    for s in sources:
        if s.source_id == "backend_ollama":
            checks.append(_check_ollama(s.source_id, root))
        if s.source_id in ("openclaw", "coding_agent", "ide_editor", "notebook_rag"):
            checks.append(_check_integration_enabled(s.source_id, root))
    health.prerequisite_checks = checks

    # Failed activations from store and history
    failed_reqs = list_requests(root, status="failed")
    history = load_history(root, limit=30)
    failed_entries = [e for e in history if e.get("outcome") == "failed"]
    health.failed_activations = [
        {"activation_id": e.get("activation_id"), "details": e.get("details"), "recorded_at": e.get("recorded_at")}
        for e in failed_entries
    ]
    for r in failed_reqs:
        if not any(f.get("activation_id") == r.activation_id for f in health.failed_activations):
            health.failed_activations.append({
                "activation_id": r.activation_id,
                "source_id": r.source_id,
                "details": {},
                "recorded_at": r.updated_at or r.created_at,
            })

    # Deactivation path: integrations and sources with rollback_notes
    for s in sources:
        if s.source_id in ("openclaw", "coding_agent", "ide_editor", "notebook_rag") or s.rollback_notes:
            health.deactivation_path_available.append(s.source_id)

    # Summary counts
    health.summary = {
        "active": len(by_lifecycle.get("active", [])),
        "configured": len(by_lifecycle.get("configured", [])),
        "installed": len(by_lifecycle.get("installed", [])),
        "blocked": len(by_lifecycle.get("blocked", [])),
        "failed": len(by_lifecycle.get("failed", [])),
        "unknown": len(by_lifecycle.get("unknown", [])),
        "total_sources": len(sources),
        "prereq_passed": sum(1 for c in checks if c.passed),
        "prereq_failed": sum(1 for c in checks if not c.passed and c.check != "n/a"),
    }

    # Recommended next
    pending = list_requests(root, status="pending")
    if pending:
        health.recommended_next = f"Run: workflow-dataset capabilities external execute --id {pending[0].activation_id} [--approved]"
    elif health.summary.get("failed", 0) > 0:
        health.recommended_next = "Run: workflow-dataset capabilities external health (review failed activations)"
    elif health.summary.get("configured", 0) > 0:
        health.recommended_next = "Run: workflow-dataset capabilities external recommend (then request/preview/execute as needed)"
    else:
        health.recommended_next = "Run: workflow-dataset capabilities external list"

    return health


def format_health_report(health: CapabilityHealth) -> str:
    """Produce human-readable capability health report."""
    lines = [
        "=== Capability health report ===",
        "",
        "[Lifecycle summary]",
        f"  active: {health.summary.get('active', 0)}  configured: {health.summary.get('configured', 0)}  installed: {health.summary.get('installed', 0)}",
        f"  blocked: {health.summary.get('blocked', 0)}  failed: {health.summary.get('failed', 0)}  unknown: {health.summary.get('unknown', 0)}",
        f"  total_sources: {health.summary.get('total_sources', 0)}",
        "",
        "[Prerequisite checks]",
    ]
    for c in health.prerequisite_checks:
        status = "ok" if c.passed else "FAIL"
        lines.append(f"  {c.source_id}  {c.check}: {status}  {c.detail}")
    if not health.prerequisite_checks:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Failed activations]")
    for f in health.failed_activations[:10]:
        lines.append(f"  {f.get('activation_id', '')}  {f.get('details', {})}")
    if not health.failed_activations:
        lines.append("  (none)")
    lines.append("")
    lines.append("[Deactivation path available]")
    for sid in health.deactivation_path_available[:15]:
        lines.append(f"  {sid}")
    lines.append("")
    lines.append("[Recommended next]")
    lines.append(f"  {health.recommended_next}")
    return "\n".join(lines)
