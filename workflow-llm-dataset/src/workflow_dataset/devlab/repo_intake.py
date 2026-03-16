"""
M21W: Devlab curated repo intake — registry, parse-only, ingest, intake reports with D2 scoring.
Sandbox-only; no execution of external code.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from workflow_dataset.devlab.config import (
    get_devlab_root,
    get_registry_path,
    get_reports_dir,
    get_repos_dir,
)
from workflow_dataset.devlab.license_triage import triage_license_risk
from workflow_dataset.devlab.repo_scoring import (
    recommend_d2,
    score_repo_usefulness,
    usefulness_composite,
)


def _repo_id_from_url(url: str) -> str:
    """Derive repo_id from GitHub URL (owner_repo)."""
    url = (url or "").strip().rstrip("/")
    if "git@" in url and ":" in url:
        # git@github.com:owner/repo.git -> owner_repo
        try:
            _, rest = url.split(":", 1)
            owner, repo = rest.split("/", 1)
            return f"{owner}_{repo.replace('.git', '')}"
        except ValueError:
            pass
    if "/" in url:
        if "github.com" in url:
            parts = url.replace("https://", "").replace("http://", "").split("/")
            idx = next((i for i, p in enumerate(parts) if p == "github.com"), -1)
            if idx >= 0 and len(parts) > idx + 2:
                owner, repo = parts[idx + 1], parts[idx + 2].replace(".git", "")
                return f"{owner}_{repo}"
        return url.split("/")[-1].replace(".git", "")
    return url.replace(".git", "").replace("-", "_")


def load_registry(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Load devlab repo registry. Returns list of { repo_id, url, label, category, priority }."""
    path = get_registry_path(root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("repos") or data.get("entries") or []
    except Exception:
        return []


def register_repo(
    url: str,
    label: str = "",
    category: str = "other",
    priority: str = "medium",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Register a repo in the devlab registry. Returns the new entry."""
    path = get_registry_path(root)
    get_devlab_root(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    repo_id = _repo_id_from_url(url)
    entry = {"repo_id": repo_id, "url": url, "label": label, "category": category, "priority": priority}
    entries = load_registry(root)
    entries = [e for e in entries if (e.get("repo_id") or "") != repo_id]
    entries.append(entry)
    path.write_text(json.dumps({"repos": entries}, indent=2), encoding="utf-8")
    return entry


def parse_only(repo_dir: Path | str) -> dict[str, Any]:
    """
    Parse-only: read README, license, deps files; list file tree. No execution.
    Returns: readme_preview, license_note, deps (file -> content snippet), file_tree (list of {path, dir}).
    """
    repo_dir = Path(repo_dir)
    if not repo_dir.exists() or not repo_dir.is_dir():
        return {"readme_preview": "", "license_note": "", "deps": {}, "file_tree": []}

    readme_preview = ""
    for name in ("README.md", "README.rst", "README", "readme.md"):
        p = repo_dir / name
        if p.exists() and p.is_file():
            try:
                readme_preview = p.read_text(encoding="utf-8", errors="replace")[:4000]
            except Exception:
                pass
            break

    license_note = ""
    for name in ("LICENSE", "LICENSE.md", "LICENCE"):
        p = repo_dir / name
        if p.exists() and p.is_file():
            try:
                license_note = p.read_text(encoding="utf-8", errors="replace")[:2000]
            except Exception:
                pass
            break

    deps: dict[str, str] = {}
    for name in ("requirements.txt", "pyproject.toml", "package.json", "Pipfile", "setup.py"):
        p = repo_dir / name
        if p.exists() and p.is_file():
            try:
                deps[name] = p.read_text(encoding="utf-8", errors="replace")[:8000]
            except Exception:
                deps[name] = ""
    if not deps and (repo_dir / "requirements.txt").exists():
        try:
            deps["requirements.txt"] = (repo_dir / "requirements.txt").read_text(encoding="utf-8", errors="replace")[:8000]
        except Exception:
            pass

    file_tree: list[dict[str, Any]] = []
    try:
        for p in sorted(repo_dir.rglob("*"))[:200]:
            if p.name in (".git", "__pycache__", ".venv", "node_modules") or p.suffix in (".pyc",):
                continue
            try:
                rel = p.relative_to(repo_dir)
            except ValueError:
                continue
            file_tree.append({"path": str(rel), "dir": p.is_dir()})
    except Exception:
        pass

    return {
        "readme_preview": readme_preview,
        "license_note": license_note,
        "deps": deps,
        "file_tree": file_tree,
    }


def ingest_repo(repo: str, root: Path | str | None = None) -> dict[str, Any]:
    """
    Ingest repo: resolve repo_id, clone if needed into sandbox, then parse-only.
    Raises ValueError if repo not in registry (when repo is URL and not registered).
    """
    root = Path(root) if root else get_devlab_root()
    registry = load_registry(root)
    repo_id = None
    repo_path = None

    if repo in [e.get("repo_id") for e in registry]:
        repo_id = repo
        repo_path = get_repos_dir(root) / repo_id
    else:
        # might be URL
        rid = _repo_id_from_url(repo)
        if rid in [e.get("repo_id") for e in registry]:
            repo_id = rid
            repo_path = get_repos_dir(root) / repo_id
        else:
            raise ValueError(f"Repo {repo} not in registry; add with devlab add-repo --url ...")

    if not repo_path.exists():
        entry = next((e for e in registry if e.get("repo_id") == repo_id), {})
        url = entry.get("url", "")
        if url:
            get_repos_dir(root).mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", url, str(repo_path)],
                    check=True,
                    capture_output=True,
                    timeout=120,
                    cwd=str(get_repos_dir(root)),
                )
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                repo_path.mkdir(parents=True, exist_ok=True)
                (repo_path / "README.md").write_text(f"# Placeholder for {repo_id}\nClone failed or no git.", encoding="utf-8")

    parsed = parse_only(repo_path)
    return {
        "repo_id": repo_id,
        "repo_path": str(repo_path),
        **parsed,
    }


def write_intake_report(repo: str, root: Path | str | None = None) -> Path:
    """
    Generate per-repo intake report: parse + usefulness scores + license triage + D2 recommendation.
    If repo dir exists, uses it; else tries ingest (clone). Returns path to report JSON.
    """
    root = Path(root) if root else get_devlab_root()
    repos_dir = get_repos_dir(root)
    reports_dir = get_reports_dir(root)
    registry = load_registry(root)

    repo_id = None
    for e in registry:
        if e.get("repo_id") == repo or e.get("url", "").strip() == repo.strip():
            repo_id = e.get("repo_id")
            break
    if not repo_id:
        repo_id = _repo_id_from_url(repo) if "/" in repo or "github" in repo else repo
        if repo_id not in [e.get("repo_id") for e in registry]:
            try:
                data = ingest_repo(repo, root)
                repo_id = data["repo_id"]
            except ValueError:
                raise ValueError(f"Repo {repo} not in registry")

    repo_path = repos_dir / repo_id
    if not repo_path.exists():
        try:
            ingest_repo(repo_id, root)
        except Exception:
            pass
    parsed = parse_only(repo_path) if repo_path.exists() else {"readme_preview": "", "license_note": "", "deps": {}, "file_tree": []}
    entry = next((e for e in registry if e.get("repo_id") == repo_id), {"category": "other"})
    context = {"category": entry.get("category", "other")}

    usefulness_scores = score_repo_usefulness(parsed, context)
    license_triage = triage_license_risk(parsed)
    d2_recommendation = recommend_d2(usefulness_scores, license_triage)
    composite = usefulness_composite(usefulness_scores)

    parse_out = dict(parsed)
    parse_out["file_tree_count"] = len(parsed.get("file_tree") or [])
    parse_out["deps_files"] = list((parsed.get("deps") or {}).keys())

    report = {
        "repo_id": repo_id,
        "url": entry.get("url", ""),
        "summary": (parsed.get("readme_preview") or "")[:500],
        "parse": parse_out,
        "usefulness_scores": usefulness_scores,
        "license_triage": license_triage,
        "d2_recommendation": d2_recommendation,
        "composite_score": composite,
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"repo_intake_report_{repo_id}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def score_all_reports(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Re-score all existing intake reports (from repo dirs). Returns list of updated report summaries."""
    root = Path(root) if root else get_devlab_root()
    reports_dir = get_reports_dir(root)
    repos_dir = get_repos_dir(root)
    registry = load_registry(root)
    updated: list[dict[str, Any]] = []
    for p in reports_dir.glob("repo_intake_report_*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            repo_id = data.get("repo_id", p.stem.replace("repo_intake_report_", ""))
        except Exception:
            continue
        repo_path = repos_dir / repo_id
        parsed = parse_only(repo_path) if repo_path.exists() else data.get("parse") or {}
        if isinstance(parsed.get("file_tree"), list) and not parsed.get("deps_files"):
            parsed["deps_files"] = list((parsed.get("deps") or {}).keys())
        entry = next((e for e in registry if e.get("repo_id") == repo_id), {"category": "other"})
        context = {"category": entry.get("category", "other")}
        usefulness_scores = score_repo_usefulness(parsed, context)
        license_triage = triage_license_risk(parsed)
        d2_recommendation = recommend_d2(usefulness_scores, license_triage)
        composite = usefulness_composite(usefulness_scores)
        data["usefulness_scores"] = usefulness_scores
        data["license_triage"] = license_triage
        data["d2_recommendation"] = d2_recommendation
        data["composite_score"] = composite
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        updated.append({"repo_id": repo_id, "d2_recommendation": d2_recommendation})
    return updated


def score_repo(repo: str, root: Path | str | None = None) -> dict[str, Any]:
    """Score a single repo (by id). Writes or updates intake report; returns report dict."""
    path = write_intake_report(repo, root=root)
    return json.loads(path.read_text(encoding="utf-8"))
