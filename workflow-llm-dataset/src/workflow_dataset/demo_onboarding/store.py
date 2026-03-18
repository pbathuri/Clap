"""
M51E–M51H: Persist demo onboarding session and bootstrap summary under data/local/demo_onboarding/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.demo_onboarding.models import DemoOnboardingSession

DEMO_DIR = "data/local/demo_onboarding"
SESSION_FILE = "demo_session.json"
BOOTSTRAP_SUMMARY_FILE = "memory_bootstrap_summary.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _dir(root: Path) -> Path:
    d = root / DEMO_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_session(session: DemoOnboardingSession, repo_root: Path | str | None = None) -> Path:
    path = _dir(_repo_root(repo_root)) / SESSION_FILE
    path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
    return path


def load_session(repo_root: Path | str | None = None) -> DemoOnboardingSession | None:
    path = _repo_root(repo_root) / DEMO_DIR / SESSION_FILE
    if not path.exists():
        return None
    try:
        return DemoOnboardingSession.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def save_bootstrap_summary(data: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    path = _dir(_repo_root(repo_root)) / BOOTSTRAP_SUMMARY_FILE
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_bootstrap_summary(repo_root: Path | str | None = None) -> dict[str, Any]:
    path = _repo_root(repo_root) / DEMO_DIR / BOOTSTRAP_SUMMARY_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
