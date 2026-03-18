"""
M23C-F2: Notes/text document adapter execution. Read-only; no mutation of originals.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReadTextResult:
    content: str
    error: str | None = None


@dataclass
class SummarizeResult:
    summary: str
    error: str | None = None


@dataclass
class ProposeStatusResult:
    suggested_lines: list[str]
    error: str | None = None


def run_read_text(path: str | Path) -> ReadTextResult:
    """Read text file content (UTF-8). Read-only."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return ReadTextResult(content="", error="path_not_found")
    if not p.is_file():
        return ReadTextResult(content="", error="not_a_file")
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        return ReadTextResult(content=content)
    except OSError as e:
        return ReadTextResult(content="", error=f"read_failed: {e!s}")


def run_summarize_text_for_workflow(path: str | Path) -> SummarizeResult:
    """Summarize text for workflow context (first/last lines, length). Read-only."""
    r = run_read_text(path)
    if r.error:
        return SummarizeResult(summary="", error=r.error)
    text = r.content
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return SummarizeResult(summary="(empty file)")
    first = lines[0][:200] + ("..." if len(lines[0]) > 200 else "")
    last = lines[-1][:200] + ("..." if len(lines[-1]) > 200 else "") if lines else ""
    summary = f"Lines: {len(lines)}, chars: {len(text)}\nFirst: {first}\nLast: {last}"
    return SummarizeResult(summary=summary)


def run_propose_status_from_notes(path: str | Path) -> ProposeStatusResult:
    """Propose status lines from notes (bullet-style suggestions). Read-only; no write."""
    r = run_read_text(path)
    if r.error:
        return ProposeStatusResult(suggested_lines=[], error=r.error)
    lines = [ln.strip() for ln in r.content.splitlines() if ln.strip()]
    suggested: list[str] = []
    for ln in lines[:20]:
        if len(ln) > 3:
            suggested.append(f"- {ln[:200]}" + ("..." if len(ln) > 200 else ""))
    if not suggested and lines:
        suggested.append(f"- (1 line, {len(lines[0])} chars)")
    return ProposeStatusResult(suggested_lines=suggested)
