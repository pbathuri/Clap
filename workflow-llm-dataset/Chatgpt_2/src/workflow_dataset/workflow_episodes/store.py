"""
M33A–M33D: Workflow episode persistence — current episode, recent list, transitions.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.workflow_episodes.models import WorkflowEpisode, EpisodeTransitionEvent

EPISODES_DIR = "data/local/workflow_episodes"
CURRENT_FILE = "current.json"
RECENT_FILE = "recent_episodes.json"
TRANSITIONS_FILE = "transitions.jsonl"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_episodes_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / EPISODES_DIR


def get_current_episode(repo_root: Path | str | None = None) -> WorkflowEpisode | None:
    path = get_episodes_dir(repo_root) / CURRENT_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return WorkflowEpisode.from_dict(data)
    except Exception:
        return None


def save_current_episode(episode: WorkflowEpisode | None, repo_root: Path | str | None = None) -> Path:
    dir_path = get_episodes_dir(repo_root)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / CURRENT_FILE
    if episode is None:
        if path.exists():
            path.unlink()
        return path
    path.write_text(json.dumps(episode.to_dict(), indent=2), encoding="utf-8")
    return path


def list_recent_episodes(
    repo_root: Path | str | None = None,
    limit: int = 20,
    active_only: bool = False,
) -> list[WorkflowEpisode]:
    path = get_episodes_dir(repo_root) / RECENT_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("episodes", [])
        out = [WorkflowEpisode.from_dict(d) for d in items]
        if active_only:
            out = [e for e in out if e.is_active]
        return out[:limit]
    except Exception:
        return []


def append_to_recent(episode: WorkflowEpisode, repo_root: Path | str | None = None, max_recent: int = 50) -> None:
    dir_path = get_episodes_dir(repo_root)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / RECENT_FILE
    existing = list_recent_episodes(repo_root, limit=max_recent + 10, active_only=False)
    existing = [e for e in existing if e.episode_id != episode.episode_id]
    updated = [episode] + existing[: max_recent - 1]
    data = {"episodes": [e.to_dict() for e in updated]}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_episode_transition(transition: EpisodeTransitionEvent, repo_root: Path | str | None = None) -> Path:
    dir_path = get_episodes_dir(repo_root)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / TRANSITIONS_FILE
    line = transition.model_dump_json() + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    return path


def load_recent_transitions(
    repo_root: Path | str | None = None,
    limit: int = 30,
) -> list[EpisodeTransitionEvent]:
    path = get_episodes_dir(repo_root) / TRANSITIONS_FILE
    if not path.exists():
        return []
    out: list[EpisodeTransitionEvent] = []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines[-limit:]):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(EpisodeTransitionEvent.model_validate_json(line))
        except Exception:
            continue
    return out[:limit]
