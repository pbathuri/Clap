"""
Classify file paths into artifact families (text, spreadsheet, project, media, etc.).

Deterministic, extension and path based; used by setup inventory stage.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.setup.setup_models import ArtifactFamily


# Extensions per family (lowercase, no dot)
TEXT_EXTENSIONS = {"txt", "md", "markdown", "rst", "tex", "log", "json", "xml", "yaml", "yml", "toml", "ini", "cfg"}
SPREADSHEET_EXTENSIONS = {"csv", "xlsx", "xls", "ods", "tsv"}
MEDIA_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v", "wav", "mp3", "aac", "flac", "m4a"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "tif", "heic", "svg", "psd", "ai"}
EXPORT_DELIVERABLE_EXTENSIONS = {"pdf", "zip", "mp4", "mov", "png", "jpg", "jpeg", "gif", "webm"}  # common export outputs


def classify_artifact(path: Path | str) -> ArtifactFamily:
    """
    Classify a file path into an artifact family. Directories are PROJECT_DIRECTORY.
    """
    p = Path(path)
    if p.is_dir():
        return ArtifactFamily.PROJECT_DIRECTORY
    ext = p.suffix.lstrip(".").lower()
    if ext in TEXT_EXTENSIONS:
        return ArtifactFamily.TEXT_DOCUMENT
    if ext in SPREADSHEET_EXTENSIONS:
        return ArtifactFamily.SPREADSHEET_TABLE
    if ext in IMAGE_EXTENSIONS:
        return ArtifactFamily.IMAGE_ASSET
    if ext in MEDIA_EXTENSIONS:
        return ArtifactFamily.MEDIA_ASSET
    if ext in EXPORT_DELIVERABLE_EXTENSIONS:
        return ArtifactFamily.EXPORTED_DELIVERABLE
    return ArtifactFamily.UNKNOWN


def is_supported_for_parsing(path: Path | str) -> bool:
    """True if we have a low-level parser for this path (v1: txt, md, csv, json, xlsx)."""
    p = Path(path)
    if p.is_dir():
        return False
    ext = p.suffix.lstrip(".").lower()
    return ext in {"txt", "md", "csv", "json", "xlsx"}
