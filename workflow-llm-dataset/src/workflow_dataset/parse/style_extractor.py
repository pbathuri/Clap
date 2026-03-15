"""
Style-signature extraction: naming conventions, recurring templates, deliverable patterns.

Focus: asset organization, output naming, export/revision patterns, repeated project structures.
Deterministic and explainable; no artistic/visual imitation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class StylePattern(BaseModel):
    """A detected style pattern (e.g. naming convention, folder layout)."""
    pattern_type: str = Field(..., description="e.g. naming_convention, heading_template, export_naming")
    value: str | list[str] | dict[str, Any] = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_paths: list[str] = Field(default_factory=list)
    description: str = Field(default="")


# Common revision/version patterns in filenames
REVISION_PATTERNS = [
    re.compile(r"v\d+", re.I),
    re.compile(r"_\d{4}-\d{2}-\d{2}"),
    re.compile(r"_\d{8}"),
    re.compile(r"\(\d+\)"),
    re.compile(r"-\d+$"),
    re.compile(r" copy( \d+)?$", re.I),
    re.compile(r" final( \d+)?$", re.I),
    re.compile(r" rev\d+", re.I),
]


def extract_naming_conventions(paths: list[Path]) -> list[StylePattern]:
    """Infer naming conventions from a list of file/folder paths."""
    patterns: list[StylePattern] = []
    by_ext: dict[str, list[str]] = {}
    for p in paths:
        name = p.name
        ext = p.suffix.lstrip(".").lower()
        if ext:
            by_ext.setdefault(ext, []).append(name)
    for ext, names in by_ext.items():
        if len(names) < 2:
            continue
        rev_count = 0
        for n in names:
            if any(r.search(n) for r in REVISION_PATTERNS):
                rev_count += 1
        if rev_count >= len(names) // 2:
            patterns.append(StylePattern(
                pattern_type="revision_naming",
                value=f"revision_pattern_in_{ext}",
                confidence=0.7,
                evidence_paths=[str(p) for p in paths[:5]],
                description=f"Many {ext} files use version/revision suffixes",
            ))
    return patterns


def extract_folder_layout_style(dir_path: Path, max_depth: int = 3) -> list[StylePattern]:
    """Infer folder layout style from a directory tree (e.g. exports/, assets/, src/)."""
    patterns: list[StylePattern] = []
    top_dirs: list[str] = []
    try:
        for entry in dir_path.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                top_dirs.append(entry.name.lower())
    except OSError:
        return patterns
    if not top_dirs:
        return patterns
    # Common creative/design folder names
    creative_folders = {"exports", "export", "output", "outputs", "assets", "src", "source", "final", "draft", "raw", "renders", "comp"}
    matches = [d for d in top_dirs if d in creative_folders or "export" in d or "asset" in d]
    if matches:
        patterns.append(StylePattern(
            pattern_type="folder_layout",
            value=top_dirs,
            confidence=0.6,
            evidence_paths=[str(dir_path)],
            description=f"Top-level folders: {', '.join(top_dirs)}",
        ))
    return patterns


def extract_heading_templates(section_headings: list[str]) -> list[StylePattern]:
    """Detect recurring heading templates (e.g. '## Week of YYYY-MM-DD')."""
    if len(section_headings) < 2:
        return []
    patterns: list[StylePattern] = []
    # Simple heuristic: same prefix
    prefixes: dict[str, int] = {}
    for h in section_headings:
        parts = h.split()
        if len(parts) >= 1:
            prefix = parts[0][:20]
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
    for prefix, count in prefixes.items():
        if count >= 2 and len(prefix) >= 2:
            patterns.append(StylePattern(
                pattern_type="heading_template",
                value=prefix,
                confidence=min(0.9, 0.5 + count * 0.1),
                evidence_paths=[],
                description=f"Recurring heading prefix: '{prefix}' ({count}x)",
            ))
    return patterns


def extract_spreadsheet_schema_patterns(sheet_names: list[str], header_lists: list[list[str]]) -> list[StylePattern]:
    """Detect repeated spreadsheet schemas (same/similar headers across sheets or files)."""
    patterns: list[StylePattern] = []
    if len(header_lists) < 2:
        return patterns
    from collections import Counter
    header_tuples = [tuple(h) for h in header_lists if h]
    if not header_tuples:
        return patterns
    c = Counter(header_tuples)
    for headers, count in c.most_common(2):
        if count >= 2:
            patterns.append(StylePattern(
                pattern_type="spreadsheet_schema_repetition",
                value=list(headers),
                confidence=0.5 + 0.1 * count,
                evidence_paths=[],
                description=f"Same column set seen {count} times",
            ))
    return patterns
