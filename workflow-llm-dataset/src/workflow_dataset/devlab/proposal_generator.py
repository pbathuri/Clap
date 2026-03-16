"""
D3: Proposal generator from repo intake reports + model compare results.
Advisory only; no code modification; local-only artifacts.
Produces: devlab_proposal.md, cursor_prompt.txt, rfc_skeleton.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.devlab.config import (
    get_devlab_root,
    get_reports_dir,
    get_model_compare_dir,
    get_proposals_dir,
)

import hashlib
from datetime import datetime, timezone


def _short_id(prefix: str = "d3") -> str:
    """Stable short id for proposal_id (no external utils dependency)."""
    raw = f"{prefix}_{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def load_intake_reports(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Load all repo_intake_report_*.json from devlab/reports. Returns list of report dicts."""
    reports_dir = get_reports_dir(root)
    out: list[dict[str, Any]] = []
    for p in sorted(reports_dir.glob("repo_intake_report_*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("repo_id"):
                data["_path"] = str(p)
                out.append(data)
        except Exception:
            pass
    return out


def load_model_compare_report(root: Path | str | None = None) -> dict[str, Any] | None:
    """Load model_compare_report.json from devlab/model_compare if present."""
    compare_dir = get_model_compare_dir(root)
    path = compare_dir / "model_compare_report.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _section_intake(reports: list[dict[str, Any]]) -> list[str]:
    """Build markdown lines for repo intake section."""
    lines = ["## Repo intake summary", ""]
    if not reports:
        lines.append("No repo intake reports found. Run `devlab repo-report <repo_id>` after adding repos.")
        return lines
    lines.append(f"**{len(reports)}** intake report(s) in devlab/reports.")
    lines.append("")
    for r in reports:
        repo_id = r.get("repo_id", "?")
        summary = (r.get("summary") or "")[:200]
        d2 = r.get("d2_recommendation", "")
        composite = r.get("composite_score")
        score_str = f" (composite: {composite:.2f})" if isinstance(composite, (int, float)) else ""
        use_as = r.get("reuse_or_inspiration") or r.get("license_triage", {}).get("use_as", "")
        lines.append(f"- **{repo_id}**{score_str}")
        lines.append(f"  - {summary}")
        if d2:
            lines.append(f"  - D2 recommendation: {d2}")
        if use_as:
            lines.append(f"  - Use: {use_as}")
        lines.append("")
    return lines


def _section_model_compare(mc: dict[str, Any] | None) -> list[str]:
    """Build markdown lines for model comparison section."""
    lines = ["## Model comparison summary", ""]
    if not mc:
        lines.append("No model comparison report found. Run `devlab compare-models --workflow <workflow> --providers ollama`.")
        return lines
    workflow = mc.get("workflow", "?")
    results = mc.get("results", [])
    lines.append(f"**Workflow:** {workflow}")
    lines.append(f"**Providers/models compared:** {len(results)}")
    lines.append("")
    for r in results:
        prov = r.get("provider", "?")
        model = r.get("model", "?")
        out_preview = (r.get("output") or "")[:150].replace("\n", " ")
        lines.append(f"- **{prov}** / {model}")
        lines.append(f"  - Output preview: {out_preview}...")
        lines.append("")
    lines.append("Use this to decide which provider/model to use for ops/reporting workflows. No auto-switch.")
    lines.append("")
    return lines


def _build_devlab_proposal_md(
    reports: list[dict[str, Any]],
    model_compare: dict[str, Any] | None,
    proposal_id: str,
) -> str:
    """Build full devlab_proposal.md content."""
    lines = [
        "# Devlab proposal (advisory)",
        "",
        f"**Proposal ID:** {proposal_id}",
        f"**Generated:** {_utc_now_iso()}",
        "",
        "This document is advisory only. No code has been modified. Review and apply changes explicitly.",
        "",
        "---",
        "",
    ]
    lines.extend(_section_intake(reports))
    lines.append("---")
    lines.append("")
    lines.extend(_section_model_compare(model_compare))
    lines.extend([
        "---",
        "",
        "## Next steps",
        "",
        "1. Review repo intake reports; decide which repos (if any) to adopt patterns or code from.",
        "2. Review model comparison; decide which provider/model to use for workflows.",
        "3. Use cursor_prompt.txt in this proposal for a Cursor/operator prompt to suggest concrete edits.",
        "4. Use rfc_skeleton.md to draft an RFC; complete and approve before implementation.",
        "",
        "---",
        "*Advisory only. Local-only artifacts. No automatic code changes.*",
    ])
    return "\n".join(lines)


def _build_cursor_prompt_txt(
    reports: list[dict[str, Any]],
    model_compare: dict[str, Any] | None,
    proposal_id: str,
) -> str:
    """Build cursor_prompt.txt: prompt for operator/Cursor to suggest edits."""
    parts = [
        f"Devlab proposal {proposal_id} (advisory). Do not modify code automatically.",
        "",
        "Context:",
    ]
    if reports:
        parts.append(f"- {len(reports)} repo intake report(s) in data/local/devlab/reports/. Review repo_intake_report_*.json for summary, D2 recommendation, and reuse vs inspiration.")
        top = [r.get("repo_id") for r in reports[:5]]
        parts.append(f"  Repo IDs: {', '.join(top)}")
    else:
        parts.append("- No repo intake reports. Run devlab add-repo, ingest-repo, repo-report to generate.")
    if model_compare:
        workflow = model_compare.get("workflow", "?")
        parts.append(f"- Model comparison in data/local/devlab/model_compare/model_compare_report.json (workflow: {workflow}). Use it to recommend which provider/model to use; do not auto-switch.")
    else:
        parts.append("- No model comparison. Run devlab compare-models to generate.")
    parts.extend([
        "",
        "Task: Suggest concrete, minimal changes (config, prompts, or code) that would:",
        "1. Incorporate useful patterns or modules from one intake repo (if any), with attribution.",
        "2. Align provider/model choice with the model comparison (if present).",
        "Output a list of suggested edits for operator review. Do not apply changes.",
    ])
    return "\n".join(parts)


def _build_rfc_skeleton_md(
    reports: list[dict[str, Any]],
    model_compare: dict[str, Any] | None,
    proposal_id: str,
) -> str:
    """Build rfc_skeleton.md: RFC skeleton for operator to complete."""
    lines = [
        "# RFC skeleton: Devlab adoption",
        "",
        f"**Proposal ID:** {proposal_id}",
        "",
        "## Summary",
        "",
        "Adopt findings from devlab repo intake and/or model comparison. Scope and details to be filled by operator.",
        "",
        "## Motivation",
        "",
    ]
    if reports:
        lines.append(f"- {len(reports)} repo intake report(s) available; D2 recommendations and license triage inform reuse vs inspiration.")
    if model_compare:
        lines.append(f"- Model comparison available for workflow: {model_compare.get('workflow', '?')}; informs provider/model choice.")
    if not reports and not model_compare:
        lines.append("- Generate repo reports and/or model compare, then re-run proposal generator.")
    lines.extend([
        "",
        "## Proposed changes",
        "",
        "- [ ] Select repo(s) or patterns to adopt (from intake reports).",
        "- [ ] Select provider/model for ops workflows (from model compare).",
        "- [ ] Document attribution and license for any adopted code.",
        "- [ ] No automatic code changes; all edits applied by operator.",
        "",
        "## Acceptance criteria",
        "",
        "- [ ] Intake and/or model compare reviewed.",
        "- [ ] Changes applied only after operator approval.",
        "- [ ] Local-first preserved; no silent provider switch.",
        "",
        "---",
        "*Draft. Operator completes and approves.*",
    ])
    return "\n".join(lines)


def generate_proposal(root: Path | str | None = None) -> dict[str, Any]:
    """
    D3: Generate devlab proposal from repo intake reports + model compare.
    Writes to proposals/<proposal_id>/: devlab_proposal.md, cursor_prompt.txt, rfc_skeleton.md, manifest.json.
    Returns {proposal_id, proposal_path, devlab_proposal_md, cursor_prompt_txt, rfc_skeleton_md, intake_count, model_compare_present}.
    """
    root = get_devlab_root(root)
    reports = load_intake_reports(root)
    model_compare = load_model_compare_report(root)

    proposal_id = _short_id("d3")
    proposals_dir = get_proposals_dir(root)
    prop_dir = proposals_dir / proposal_id
    prop_dir.mkdir(parents=True, exist_ok=True)

    # Write artifacts
    (prop_dir / "devlab_proposal.md").write_text(
        _build_devlab_proposal_md(reports, model_compare, proposal_id),
        encoding="utf-8",
    )
    (prop_dir / "cursor_prompt.txt").write_text(
        _build_cursor_prompt_txt(reports, model_compare, proposal_id),
        encoding="utf-8",
    )
    (prop_dir / "rfc_skeleton.md").write_text(
        _build_rfc_skeleton_md(reports, model_compare, proposal_id),
        encoding="utf-8",
    )

    manifest = {
        "proposal_id": proposal_id,
        "source": "proposal_generator",
        "status": "pending",
        "created_at": _utc_now_iso(),
        "operator_notes": "",
        "intake_count": len(reports),
        "model_compare_present": model_compare is not None,
    }
    (prop_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "proposal_id": proposal_id,
        "proposal_path": str(prop_dir),
        "devlab_proposal_md": str(prop_dir / "devlab_proposal.md"),
        "cursor_prompt_txt": str(prop_dir / "cursor_prompt.txt"),
        "rfc_skeleton_md": str(prop_dir / "rfc_skeleton.md"),
        "intake_count": len(reports),
        "model_compare_present": model_compare is not None,
    }
