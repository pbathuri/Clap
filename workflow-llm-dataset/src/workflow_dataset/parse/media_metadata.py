"""
Media/image/video metadata extraction.

Lightweight: file metadata, naming patterns, version/revision hints.
Optional: image dimensions/EXIF-like, video/audio duration/codec when available (Pillow, ffprobe).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class MediaMetadata(BaseModel):
    """Extracted media metadata (local-only; no cloud)."""
    path: str = Field(default="")
    filename: str = Field(default="")
    extension: str = Field(default="")
    size_bytes: int = Field(default=0)
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)
    duration_seconds: float | None = Field(default=None)
    codec: str | None = Field(default=None)
    color_mode: str | None = Field(default=None, description="e.g. RGB, L")
    revision_hint: str | None = Field(default=None, description="e.g. v1, _20240301, _final")
    export_hint: bool = Field(default=False, description="Filename suggests export output")
    raw: dict[str, Any] = Field(default_factory=dict)


# Naming patterns that suggest revision/version/export
REVISION_PATTERNS = ("v1", "v2", "_final", "_export", "_master", "_comp", "_render", " copy", " (1)")


def extract_media_metadata(path: Path | str, include_pixel_metadata: bool = True) -> MediaMetadata:
    """
    Extract metadata from a media file. No network. Prefer fast path; optional EXIF/duration.
    """
    p = Path(path)
    if not p.exists() or p.is_dir():
        return MediaMetadata(path=str(p))
    name = p.name
    ext = p.suffix.lstrip(".").lower()
    size = 0
    try:
        size = p.stat().st_size
    except OSError:
        pass
    rev_hint = None
    for r in REVISION_PATTERNS:
        if r in name:
            rev_hint = r
            break
    export_hint = ext in ("mp4", "mov", "png", "jpg", "jpeg", "pdf", "wav", "mp3") and ("export" in name.lower() or "final" in name.lower() or "output" in name.lower())
    out = MediaMetadata(
        path=str(p.resolve()),
        filename=name,
        extension=ext,
        size_bytes=size,
        revision_hint=rev_hint,
        export_hint=export_hint,
    )
    if not include_pixel_metadata:
        return out
    # Image: dimensions, format, color mode, EXIF-like basics via Pillow
    if ext in ("png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff", "tif"):
        try:
            from PIL import Image
            with Image.open(p) as im:
                out.width, out.height = im.size
                out.raw["format"] = im.format
                if hasattr(im, "mode"):
                    out.color_mode = im.mode
                if hasattr(im, "info") and im.info:
                    out.raw["info_keys"] = list(im.info.keys())[:20]
                try:
                    exif = im.getexif()
                    if exif:
                        out.raw["exif_len"] = len(exif)
                except Exception:
                    pass
        except Exception:
            pass
    # Video/audio: duration and codec via ffprobe if available (no heavy deps)
    if ext in ("mp4", "mov", "avi", "mkv", "webm", "m4v", "wav", "mp3", "aac", "flac", "m4a"):
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration:format_name",
                    "-of", "default=noprint_wrappers=1", str(p),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().splitlines():
                    if line.startswith("duration="):
                        out.duration_seconds = float(line.split("=", 1)[1].strip())
                    elif line.startswith("format_name="):
                        out.codec = line.split("=", 1)[1].strip()
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
    return out
