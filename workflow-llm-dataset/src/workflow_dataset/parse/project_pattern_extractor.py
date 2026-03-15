"""
Project structure and deliverable-bundle pattern extraction.

Detects: project naming schemes, repeated file-bundle shapes, recurring project structures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProjectPattern(BaseModel):
    """A detected project-level pattern."""
    pattern_type: str = Field(..., description="e.g. project_naming_scheme, deliverable_bundle")
    value: str | list[str] | dict[str, Any] = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    project_paths: list[str] = Field(default_factory=list)
    description: str = Field(default="")


def extract_project_naming_scheme(project_roots: list[Path]) -> list[ProjectPattern]:
    """Infer project naming schemes (e.g. Client_ProjectName_YYYY)."""
    patterns: list[ProjectPattern] = []
    names = [p.name for p in project_roots if p.is_dir()]
    if len(names) < 2:
        return patterns
    # Check for common delimiters
    with_underscore = sum(1 for n in names if "_" in n)
    with_dash = sum(1 for n in names if "-" in n)
    with_space = sum(1 for n in names if " " in n)
    if with_underscore >= len(names) // 2:
        patterns.append(ProjectPattern(
            pattern_type="project_naming_scheme",
            value="underscore_separated",
            confidence=0.6,
            project_paths=[str(p) for p in project_roots[:10]],
            description="Projects often use underscore-separated names",
        ))
    if with_dash >= len(names) // 2:
        patterns.append(ProjectPattern(
            pattern_type="project_naming_scheme",
            value="dash_separated",
            confidence=0.6,
            project_paths=[str(p) for p in project_roots[:10]],
            description="Projects often use dash-separated names",
        ))
    return patterns


def extract_deliverable_bundle(project_path: Path, max_files: int = 200) -> list[ProjectPattern]:
    """
    Detect repeated deliverable shapes: e.g. same set of extensions or filenames
    appearing together (export set: .mp4 + .png + .pdf).
    """
    patterns: list[ProjectPattern] = []
    exts: list[str] = []
    try:
        for i, f in enumerate(project_path.rglob("*")):
            if i >= max_files:
                break
            if f.is_file():
                exts.append(f.suffix.lstrip(".").lower())
    except OSError:
        return patterns
    from collections import Counter
    c = Counter(exts)
    common = c.most_common(5)
    if common:
        patterns.append(ProjectPattern(
            pattern_type="deliverable_extensions",
            value=[e for e, _ in common],
            confidence=0.5,
            project_paths=[str(project_path)],
            description=f"Common extensions in project: {', '.join(e for e, _ in common)}",
        ))
    return patterns
