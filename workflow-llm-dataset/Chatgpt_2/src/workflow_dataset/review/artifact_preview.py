"""
M12: Richer preview of generated artifacts (markdown, text, html, json, csv).

Shows summary, provenance, backend, style/prompt refs, deterministic vs LLM.
Console/CLI compatible; no browser app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.review.review_models import GeneratedArtifactReview
from workflow_dataset.generate.generate_models import BackendExecutionRecord
from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.utils.dates import utc_now_iso

# Max chars to include in preview body
PREVIEW_HEAD_LINES = 30
PREVIEW_MAX_CHARS = 8000


def _detect_artifact_type(path: Path) -> str:
    suf = (path.suffix or "").lower()
    if suf in (".md", ".markdown"):
        return "markdown"
    if suf == ".html":
        return "html"
    if suf == ".json":
        return "json"
    if suf == ".csv":
        return "csv"
    return "text"


def _read_preview_content(path: Path, artifact_type: str) -> str:
    """Read leading content for preview; safe for binary."""
    if not path.exists() or not path.is_file():
        return ""
    try:
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            return "[binary or non-UTF-8 file]"
        if artifact_type == "json":
            return text[:PREVIEW_MAX_CHARS]
        if artifact_type == "html":
            return text[:PREVIEW_MAX_CHARS]
        lines = text.splitlines()
        head = lines[:PREVIEW_HEAD_LINES]
        return "\n".join(head) + ("\n..." if len(lines) > PREVIEW_HEAD_LINES else "")
    except Exception:
        return "[read error]"


def build_summary(path: Path, content_preview: str, artifact_type: str) -> str:
    """One-line or short summary from path and content."""
    name = path.name
    line_count = len(content_preview.splitlines()) if content_preview else 0
    return f"{name} ({artifact_type}, ~{line_count} lines)"


def preview_artifact(
    artifact_path: str | Path,
    generation_id: str = "",
    execution_record: BackendExecutionRecord | None = None,
    style_pack_refs: list[str] | None = None,
    prompt_pack_refs: list[str] | None = None,
) -> tuple[GeneratedArtifactReview, str]:
    """
    Build a GeneratedArtifactReview and a preview text string for console/CLI.
    Returns (review, preview_body).
    """
    path = Path(artifact_path)
    artifact_type = _detect_artifact_type(path)
    content = _read_preview_content(path, artifact_type)
    summary = build_summary(path, content, artifact_type)
    ts = utc_now_iso()
    review_id = stable_id("rev", str(path), generation_id or path.stem, ts, prefix="rev")
    used_llm = False
    used_fallback = True
    backend_used = ""
    if execution_record:
        used_llm = execution_record.used_llm
        used_fallback = execution_record.used_fallback
        backend_used = execution_record.backend_name or ""

    review = GeneratedArtifactReview(
        review_id=review_id,
        generation_id=generation_id,
        artifact_id=path.stem,
        artifact_type=artifact_type,
        preview_path=str(path.resolve()),
        summary=summary,
        provenance_refs=[],
        style_pack_refs=style_pack_refs or [],
        prompt_pack_refs=prompt_pack_refs or [],
        backend_used=backend_used,
        used_llm=used_llm,
        used_fallback=used_fallback,
        created_utc=ts,
    )
    body_parts = [
        f"Artifact: {path.name}",
        f"Type: {artifact_type}  Backend: {backend_used or '-'}",
        f"LLM used: {used_llm}  Deterministic fallback: {used_fallback}",
        f"Style refs: {style_pack_refs or []}",
        f"Prompt refs: {prompt_pack_refs or []}",
        "",
        "--- Preview ---",
        content[:PREVIEW_MAX_CHARS] or "(empty)",
    ]
    return review, "\n".join(body_parts)


def preview_artifacts_from_manifest(
    generated_output_paths: list[str],
    workspace_path: str | Path,
    generation_id: str = "",
    execution_records: list[BackendExecutionRecord] | None = None,
    style_pack_refs: list[str] | None = None,
    prompt_pack_refs: list[str] | None = None,
) -> list[tuple[GeneratedArtifactReview, str]]:
    """
    Build review + preview text for each generated output path.
    execution_records: last record applies to all if single; else match by path.
    """
    workspace_path = Path(workspace_path)
    rec_by_path: dict[str, BackendExecutionRecord] = {}
    if execution_records:
        for rec in execution_records:
            for p in rec.generated_output_paths:
                rec_by_path[p] = rec
    results = []
    for out_path in generated_output_paths:
        p = Path(out_path)
        if not p.is_absolute():
            p = workspace_path / out_path
        rec = rec_by_path.get(str(p)) or rec_by_path.get(out_path) or (execution_records[0] if execution_records else None)
        review, body = preview_artifact(
            p,
            generation_id=generation_id,
            execution_record=rec,
            style_pack_refs=style_pack_refs,
            prompt_pack_refs=prompt_pack_refs,
        )
        results.append((review, body))
    return results
