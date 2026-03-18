"""
M12: Version/revision store for generated artifacts and refined variants.

Tracks original artifact, refined variants, preferred variant, revision notes, backend, LLM usage.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.review.review_models import VariantRecord, GeneratedArtifactReview
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _review_root(store_path: Path | str) -> Path:
    p = Path(store_path)
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p


def save_variant_record(record: VariantRecord, store_path: Path | str) -> Path:
    """Persist a variant record. Returns path to file."""
    root = _review_root(store_path)
    base = root / "variants"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{record.variant_id}.json"
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_variant_record(variant_id: str, store_path: Path | str) -> VariantRecord | None:
    """Load variant record by id."""
    root = _review_root(store_path)
    path = root / "variants" / f"{variant_id}.json"
    if not path.exists():
        return None
    return VariantRecord.model_validate_json(path.read_text(encoding="utf-8"))


def list_variants_for_generation(generation_id: str, store_path: Path | str) -> list[VariantRecord]:
    """List all variant records for a generation."""
    root = _review_root(store_path)
    base = root / "variants"
    if not base.exists():
        return []
    out = []
    for p in base.glob("*.json"):
        try:
            rec = VariantRecord.model_validate_json(p.read_text(encoding="utf-8"))
            if rec.generation_id == generation_id:
                out.append(rec)
        except Exception:
            continue
    return sorted(out, key=lambda r: r.created_utc, reverse=True)


def save_review(review: GeneratedArtifactReview, store_path: Path | str) -> Path:
    """Persist a generated artifact review. Returns path to file."""
    root = _review_root(store_path)
    base = root / "reviews"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{review.review_id}.json"
    path.write_text(review.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_review(review_id: str, store_path: Path | str) -> GeneratedArtifactReview | None:
    """Load review by id."""
    root = _review_root(store_path)
    path = root / "reviews" / f"{review_id}.json"
    if not path.exists():
        return None
    return GeneratedArtifactReview.model_validate_json(path.read_text(encoding="utf-8"))
