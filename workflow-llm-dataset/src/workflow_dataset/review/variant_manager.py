"""
M12: Variant management — multiple generated variants, lineage, compare, select preferred.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.review.review_models import VariantRecord
from workflow_dataset.review.version_store import (
    save_variant_record,
    load_variant_record,
    list_variants_for_generation,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def create_variant_record(
    base_artifact_id: str,
    generation_id: str,
    output_paths: list[str],
    variant_type: str = "refined",
    revision_note: str = "",
    used_llm_refinement: bool = False,
) -> VariantRecord:
    """Create and return a new variant record (caller should save via version_store)."""
    ts = utc_now_iso()
    variant_id = stable_id("var", base_artifact_id, generation_id, variant_type, ts, prefix="var")
    return VariantRecord(
        variant_id=variant_id,
        base_artifact_id=base_artifact_id,
        generation_id=generation_id,
        variant_type=variant_type,
        revision_note=revision_note,
        created_utc=ts,
        output_paths=list(output_paths),
        used_llm_refinement=used_llm_refinement,
    )


def register_variant(
    record: VariantRecord,
    store_path: Path | str,
) -> Path:
    """Persist variant record. Returns path to saved file."""
    return save_variant_record(record, store_path)


def get_variants_for_generation(generation_id: str, store_path: Path | str) -> list[VariantRecord]:
    """List all variants for a generation, newest first."""
    return list_variants_for_generation(generation_id, store_path)


def compare_variants(
    path_a: str | Path,
    path_b: str | Path,
    max_lines: int = 50,
) -> dict[str, Any]:
    """
    Compare two artifact files. Returns summary dict: size_a, size_b, line_count_a, line_count_b,
    same_content, preview_a, preview_b.
    """
    pa = Path(path_a)
    pb = Path(path_b)
    out: dict[str, Any] = {
        "path_a": str(pa),
        "path_b": str(pb),
        "size_a": pa.stat().st_size if pa.exists() else 0,
        "size_b": pb.stat().st_size if pb.exists() else 0,
        "line_count_a": 0,
        "line_count_b": 0,
        "same_content": False,
        "preview_a": "",
        "preview_b": "",
    }
    try:
        text_a = pa.read_text(encoding="utf-8", errors="replace") if pa.exists() else ""
        text_b = pb.read_text(encoding="utf-8", errors="replace") if pb.exists() else ""
        lines_a = text_a.splitlines()
        lines_b = text_b.splitlines()
        out["line_count_a"] = len(lines_a)
        out["line_count_b"] = len(lines_b)
        out["same_content"] = text_a.strip() == text_b.strip()
        out["preview_a"] = "\n".join(lines_a[:max_lines]) + ("\n..." if len(lines_a) > max_lines else "")
        out["preview_b"] = "\n".join(lines_b[:max_lines]) + ("\n..." if len(lines_b) > max_lines else "")
    except Exception as e:
        out["error"] = str(e)
    return out


def set_preferred_variant(
    variant_id: str,
    generation_id: str,
    store_path: Path | str,
) -> bool:
    """
    Mark a variant as preferred by setting variant_type to 'preferred' and others to 'refined'.
    Returns True if updated.
    """
    variants = list_variants_for_generation(generation_id, store_path)
    target = None
    for v in variants:
        if v.variant_id == variant_id:
            target = v
            break
    if not target:
        return False
    # Persist preferred: update target to preferred, others to refined (optional: store preferred_id in a small index)
    target.variant_type = "preferred"
    save_variant_record(target, store_path)
    for v in variants:
        if v.variant_id != variant_id and v.variant_type == "preferred":
            v.variant_type = "refined"
            save_variant_record(v, store_path)
    return True
