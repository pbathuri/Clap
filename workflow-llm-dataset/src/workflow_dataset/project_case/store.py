"""
M27B: Project/case store — create, load, save, list, archive; attach sessions, plans, runs, artifacts, skills.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.project_case.models import (
    Project,
    Goal,
    Subgoal,
    LinkedSession,
    LinkedPlan,
    LinkedRun,
    LinkedArtifact,
    LinkedSkill,
)

PROJECT_CASE_ROOT = "data/local/project_case"
PROJECTS_SUBDIR = "projects"
CURRENT_PROJECT_FILE = "current_project_id.json"
PROJECT_META_FILE = "project.json"
GOALS_FILE = "goals.json"
LINKS_FILE = "links.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_projects_dir(repo_root: Path | str | None = None) -> Path:
    """Base directory for project_case state: data/local/project_case."""
    return _repo_root(repo_root) / PROJECT_CASE_ROOT


def get_project_dir(project_id: str, repo_root: Path | str | None = None) -> Path:
    """Directory for one project: data/local/project_case/projects/<project_id>/."""
    return get_projects_dir(repo_root) / PROJECTS_SUBDIR / _safe_id(project_id)


def _safe_id(project_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (project_id or "").strip()) or "default"


def get_current_project_id_path(repo_root: Path | str | None = None) -> Path:
    return get_projects_dir(repo_root) / CURRENT_PROJECT_FILE


def create_project(
    project_id: str,
    title: str = "",
    description: str = "",
    repo_root: Path | str | None = None,
) -> Project:
    """Create a new project. Overwrites if project_id exists."""
    now = utc_now_iso()
    project = Project(
        project_id=project_id,
        title=title or project_id,
        description=description,
        state="active",
        created_at=now,
        updated_at=now,
    )
    save_project(project, repo_root)
    proj_dir = get_project_dir(project_id, repo_root)
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / GOALS_FILE).write_text(json.dumps({"goals": [], "subgoals": [], "goal_dependencies": []}, indent=2), encoding="utf-8")
    (proj_dir / LINKS_FILE).write_text(json.dumps({
        "sessions": [], "plans": [], "runs": [], "artifacts": [], "skills": [],
    }, indent=2), encoding="utf-8")
    return project


def load_project(project_id: str, repo_root: Path | str | None = None) -> Project | None:
    """Load project by id. Returns None if not found."""
    path = get_project_dir(project_id, repo_root) / PROJECT_META_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Project.from_dict(data)
    except Exception:
        return None


def save_project(project: Project, repo_root: Path | str | None = None) -> Path:
    """Persist project metadata to project.json."""
    root = get_project_dir(project.project_id, repo_root)
    root.mkdir(parents=True, exist_ok=True)
    project.updated_at = utc_now_iso()
    path = root / PROJECT_META_FILE
    path.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")
    return path


def list_projects(
    repo_root: Path | str | None = None,
    state_filter: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List projects (metadata). state_filter: optional 'active' | 'archived' | 'closed'."""
    root = get_projects_dir(repo_root) / PROJECTS_SUBDIR
    if not root.exists():
        return []
    current = get_current_project_id(repo_root)
    out = []
    for d in root.iterdir():
        if not d.is_dir():
            continue
        meta = d / PROJECT_META_FILE
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            state = data.get("state", "active")
            if state_filter and state != state_filter:
                continue
            out.append({
                "project_id": data.get("project_id", d.name),
                "title": data.get("title", ""),
                "state": state,
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "is_current": data.get("project_id", d.name) == current,
            })
        except Exception:
            continue
    out.sort(key=lambda x: x.get("updated_at", "") or x.get("created_at", ""), reverse=True)
    return out[:limit]


def set_current_project_id(project_id: str | None, repo_root: Path | str | None = None) -> Path:
    """Set or clear current project pointer."""
    root = get_projects_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = get_current_project_id_path(repo_root)
    path.write_text(json.dumps({"project_id": project_id}, indent=2), encoding="utf-8")
    return path


def get_current_project_id(repo_root: Path | str | None = None) -> str | None:
    """Return current project id if set; else None."""
    path = get_current_project_id_path(repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("project_id")
    except Exception:
        return None


def archive_project(project_id: str, repo_root: Path | str | None = None) -> bool:
    """Mark project as archived. Returns True if existed and was updated."""
    proj = load_project(project_id, repo_root)
    if not proj:
        return False
    proj.state = "archived"
    save_project(proj, repo_root)
    if get_current_project_id(repo_root) == project_id:
        set_current_project_id(None, repo_root)
    return True


def _load_links(project_id: str, repo_root: Path | str | None) -> dict[str, list[dict]]:
    path = get_project_dir(project_id, repo_root) / LINKS_FILE
    if not path.exists():
        return {"sessions": [], "plans": [], "runs": [], "artifacts": [], "skills": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"sessions": [], "plans": [], "runs": [], "artifacts": [], "skills": []}


def _save_links(project_id: str, links: dict[str, list[dict]], repo_root: Path | str | None) -> Path:
    root = get_project_dir(project_id, repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / LINKS_FILE
    path.write_text(json.dumps(links, indent=2), encoding="utf-8")
    return path


def attach_session(project_id: str, session_id: str, repo_root: Path | str | None = None) -> bool:
    """Attach a session to the project. Returns True if project exists."""
    if not load_project(project_id, repo_root):
        return False
    links = _load_links(project_id, repo_root)
    sessions = links.get("sessions", [])
    if any(s.get("session_id") == session_id for s in sessions):
        return True
    sessions.append({"session_id": session_id, "attached_at": utc_now_iso()})
    links["sessions"] = sessions
    _save_links(project_id, links, repo_root)
    return True


def attach_plan(project_id: str, plan_id: str = "", plan_path: str = "", repo_root: Path | str | None = None) -> bool:
    if not load_project(project_id, repo_root):
        return False
    links = _load_links(project_id, repo_root)
    plans = links.get("plans", [])
    plans.append({"plan_id": plan_id, "plan_path": plan_path, "attached_at": utc_now_iso()})
    links["plans"] = plans
    _save_links(project_id, links, repo_root)
    return True


def attach_run(project_id: str, run_id: str, repo_root: Path | str | None = None) -> bool:
    if not load_project(project_id, repo_root):
        return False
    links = _load_links(project_id, repo_root)
    runs = links.get("runs", [])
    if any(r.get("run_id") == run_id for r in runs):
        return True
    runs.append({"run_id": run_id, "attached_at": utc_now_iso()})
    links["runs"] = runs
    _save_links(project_id, links, repo_root)
    return True


def attach_artifact(project_id: str, path_or_label: str, repo_root: Path | str | None = None) -> bool:
    if not load_project(project_id, repo_root):
        return False
    links = _load_links(project_id, repo_root)
    artifacts = links.get("artifacts", [])
    artifacts.append({"path_or_label": path_or_label, "attached_at": utc_now_iso()})
    links["artifacts"] = artifacts
    _save_links(project_id, links, repo_root)
    return True


def attach_skill(project_id: str, skill_id: str, repo_root: Path | str | None = None) -> bool:
    if not load_project(project_id, repo_root):
        return False
    links = _load_links(project_id, repo_root)
    skills = links.get("skills", [])
    if any(s.get("skill_id") == skill_id for s in skills):
        return True
    skills.append({"skill_id": skill_id, "attached_at": utc_now_iso()})
    links["skills"] = skills
    _save_links(project_id, links, repo_root)
    return True


def get_linked_sessions(project_id: str, repo_root: Path | str | None = None) -> list[LinkedSession]:
    links = _load_links(project_id, repo_root)
    return [LinkedSession.from_dict(s) for s in links.get("sessions", [])]


def get_linked_plans(project_id: str, repo_root: Path | str | None = None) -> list[LinkedPlan]:
    links = _load_links(project_id, repo_root)
    return [LinkedPlan.from_dict(p) for p in links.get("plans", [])]


def get_linked_runs(project_id: str, repo_root: Path | str | None = None) -> list[LinkedRun]:
    links = _load_links(project_id, repo_root)
    return [LinkedRun.from_dict(r) for r in links.get("runs", [])]


def get_linked_artifacts(project_id: str, repo_root: Path | str | None = None) -> list[LinkedArtifact]:
    links = _load_links(project_id, repo_root)
    return [LinkedArtifact.from_dict(a) for a in links.get("artifacts", [])]


def get_linked_skills(project_id: str, repo_root: Path | str | None = None) -> list[LinkedSkill]:
    links = _load_links(project_id, repo_root)
    return [LinkedSkill.from_dict(s) for s in links.get("skills", [])]
