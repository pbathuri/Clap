"""
M51E–M51H: Bounded memory bootstrap from a small demo workspace. No whole-disk crawl.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from workflow_dataset.demo_onboarding.models import BootstrapConfidence, MemoryBootstrapPlan

# Bounded scan limits (investor-demo safe)
MAX_FILES = 15
MAX_DEPTH = 4
MAX_BYTES_PER_FILE = 8192
ALLOWED_SUFFIXES = {".md", ".txt", ".markdown"}

_STOP = frozenset(
    "the a an and or to of in for on with is are was were be been being it this that these those at by from as if"
    .split()
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def default_bundled_sample_path(repo_root: Path | str | None = None) -> Path:
    """Path to shipped demo sample workspace (docs/samples/...)."""
    root = _repo_root(repo_root)
    p = root / "docs" / "samples" / "demo_onboarding_workspace"
    return p


def _collect_files(root: Path, max_files: int) -> list[Path]:
    out: list[Path] = []
    root = root.resolve()
    if not root.is_dir():
        return out

    def walk(d: Path, depth: int) -> None:
        if len(out) >= max_files or depth > MAX_DEPTH:
            return
        try:
            entries = sorted(d.iterdir(), key=lambda x: x.name)
        except OSError:
            return
        for p in entries:
            if len(out) >= max_files:
                break
            if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES:
                out.append(p)
            elif p.is_dir() and not p.name.startswith("."):
                walk(p, depth + 1)

    walk(root, 0)
    return out[:max_files]


def _rel_or_name(f: Path, root: Path) -> str:
    try:
        return str(f.resolve().relative_to(root.resolve()))
    except ValueError:
        return f.name


def _read_snippet(path: Path) -> str:
    try:
        raw = path.read_bytes()[:MAX_BYTES_PER_FILE]
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _project_hints(files: list[Path], workspace_root: Path) -> list[str]:
    hints: set[str] = set()
    try:
        wr = workspace_root.resolve()
        for f in files:
            try:
                rel = f.resolve().relative_to(wr)
                if rel.parts:
                    hints.add(rel.parts[0])
            except ValueError:
                hints.add(f.parent.name)
    except Exception:
        for f in files:
            hints.add(f.parent.name)
    return sorted(hints)[:8]


def _themes_from_text(texts: list[str], top_n: int = 8) -> list[str]:
    freq: dict[str, int] = {}
    for t in texts:
        for w in re.findall(r"[a-zA-Z]{4,}", t.lower()):
            if w in _STOP:
                continue
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:top_n]]


def _priorities_from_text(texts: list[str]) -> list[str]:
    prios: list[str] = []
    for t in texts:
        for line in t.splitlines():
            low = line.lower().strip()
            if any(k in low for k in ("priority", "todo", "deadline", "due:", "next:", "goal:")):
                s = line.strip()[:120]
                if s and s not in prios:
                    prios.append(s)
    return prios[:10]


def _work_style_hints(files: list[str], themes: list[str]) -> list[str]:
    hints = []
    if any("meeting" in f.lower() for f in files):
        hints.append("References to meetings in sample filenames or paths.")
    if any("report" in f.lower() for f in files):
        hints.append("Report-style documents present.")
    if "weekly" in themes or "status" in themes:
        hints.append("Possible recurring status / weekly rhythm (from sample text).")
    if not hints:
        hints.append("Limited sample; work-style hints are minimal.")
    return hints[:5]


def run_bounded_memory_bootstrap(
    workspace_root: Path | str,
    repo_root: Path | str | None = None,
    *,
    plan: MemoryBootstrapPlan | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    """
    Scan workspace_root with hard caps; extract hints; ingest MemoryItems; optional graph ingest.
    Returns summary dict for ready-state and persistence.
    """
    root = Path(workspace_root).resolve()
    rr = _repo_root(repo_root)
    files = _collect_files(root, plan.max_files if plan else MAX_FILES)
    texts = [_read_snippet(f) for f in files]

    project_hints = _project_hints(files, root)
    themes = _themes_from_text(texts)
    priorities = _priorities_from_text(texts)
    work_style = _work_style_hints([f.name for f in files], themes)

    memory_units_created = 0
    errors: list[str] = []

    if plan is None or plan.ingest_to_memory_substrate:
        try:
            from workflow_dataset.memory_substrate.models import MemoryItem
            from workflow_dataset.memory_substrate.store import ingest
            try:
                from workflow_dataset.utils.dates import utc_now_iso
            except Exception:
                from datetime import datetime, timezone
                def utc_now_iso() -> str:
                    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            items: list[MemoryItem] = []
            for f, snippet in zip(files, texts):
                preview = (snippet[:400] + "…") if len(snippet) > 400 else snippet
                body = f"Demo sample file: {f.name}\nPath relative to demo root.\nExcerpt:\n{preview}"
                items.append(
                    MemoryItem(
                        item_id="",
                        content=body,
                        source="demo_onboarding",
                        source_ref=_rel_or_name(f, root),
                        timestamp_utc=utc_now_iso(),
                        session_id=session_id or "demo_onboarding",
                        metadata={"demo_bootstrap": True, "filename": f.name},
                    )
                )
            if items:
                units = ingest(items, repo_root=rr, synthesize=len(items) > 1)
                memory_units_created = len(units)
        except Exception as e:
            errors.append(f"memory_ingest: {e}")

    graph_nodes = 0
    if (plan is None or plan.ingest_to_personal_graph) and files:
        try:
            from workflow_dataset.personal.graph_builder import ingest_events
            from workflow_dataset.utils.dates import utc_now_iso
            events = []
            for f in files:
                events.append({
                    "source": "file",
                    "payload": {
                        "path": str(f.resolve()),
                        "filename": f.name,
                        "is_dir": False,
                        "event_kind": "demo_bootstrap",
                    },
                })
            store_path = rr / "data" / "local" / "personal" / "work_graph.sqlite"
            store_path.parent.mkdir(parents=True, exist_ok=True)
            r = ingest_events(store_path, events, root_paths=[root])
            graph_nodes = r.get("nodes_created_or_updated", 0)
        except Exception as e:
            errors.append(f"graph_ingest: {e}")

    if not files:
        confidence = BootstrapConfidence(
            level="insufficient",
            rationale="No readable .md/.txt files in demo workspace.",
            files_scanned=0,
            memory_units_created=0,
        )
    elif len(files) < 2 and not any(len(t.strip()) > 50 for t in texts):
        confidence = BootstrapConfidence(
            level="low",
            rationale="Very few files or minimal text; inferred context is thin.",
            files_scanned=len(files),
            memory_units_created=memory_units_created,
        )
    elif len(files) >= 3 and themes:
        confidence = BootstrapConfidence(
            level="medium",
            rationale="Multiple sample files ingested; themes are heuristic word counts only.",
            files_scanned=len(files),
            memory_units_created=memory_units_created,
        )
    else:
        confidence = BootstrapConfidence(
            level="low",
            rationale="Bounded bootstrap complete; claims are limited to sample content.",
            files_scanned=len(files),
            memory_units_created=memory_units_created,
        )

    summary = {
        "workspace_root": str(root),
        "files_scanned": len(files),
        "file_names": [f.name for f in files],
        "project_hints": project_hints,
        "recurring_themes": themes,
        "work_style_hints": work_style,
        "likely_priorities": priorities,
        "memory_units_created": memory_units_created,
        "graph_nodes_touched": graph_nodes,
        "confidence": confidence.to_dict(),
        "errors": errors,
        "disclaimer": "Inferences are from a small bounded sample only, not full-device learning.",
    }
    return summary
