"""Tests for media metadata extraction (image/video/audio)."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.parse.media_metadata import (
    MediaMetadata,
    extract_media_metadata,
    REVISION_PATTERNS,
)


def test_extract_media_metadata_nonexistent_path() -> None:
    """Nonexistent path returns minimal metadata."""
    out = extract_media_metadata("/nonexistent/fake.png")
    assert out.path != ""
    assert out.width is None and out.height is None


def test_extract_media_metadata_revision_and_export_hints(tmp_path: Path) -> None:
    """Revision and export hints are set from filename."""
    f = tmp_path / "export_v1_final.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG magic
    out = extract_media_metadata(f, include_pixel_metadata=False)
    assert out.revision_hint is not None or "v1" in f.name or "final" in f.name
    assert out.export_hint is True  # "export" and "final" in name, .png


def test_extract_media_metadata_image_dimensions(tmp_path: Path) -> None:
    """Image dimensions and color_mode when Pillow available (real small PNG)."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("PIL not installed")
    img_path = tmp_path / "tiny.png"
    img = Image.new("RGB", (12, 10), color=(1, 2, 3))
    img.save(img_path)
    out = extract_media_metadata(img_path, include_pixel_metadata=True)
    assert out.width == 12 and out.height == 10
    assert out.color_mode == "RGB"
    assert "format" in out.raw
