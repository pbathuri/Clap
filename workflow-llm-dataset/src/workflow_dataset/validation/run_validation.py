"""
M23W: Full-surface validation — run pytest and categorize failures. No auto-fix; report only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

# Test path relative to repo
TESTS_DIR = "tests"


def run_pytest_and_categorize(
    repo_root: Path | str | None = None,
    tests_path: str = TESTS_DIR,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run pytest on tests_path; return collected, passed, failed, errors, skipped, and categorized failures.
    Categories: integration_issue, environment_issue, optional_dependency, stale_test (heuristic).
    Does not install anything.
    """
    root = Path(repo_root) if repo_root else Path.cwd()
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = get_repo_root() if not repo_root else Path(repo_root)
    except Exception:
        pass
    test_dir = root / tests_path
    if not test_dir.exists() or not test_dir.is_dir():
        return {
            "ran": False,
            "error": f"Tests dir not found: {test_dir}",
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "categories": {},
        }
    cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=no", "-q", "--no-header"]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {
            "ran": True,
            "error": "pytest timed out (300s)",
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "categories": {},
        }
    except FileNotFoundError:
        return {
            "ran": False,
            "error": "pytest not found; run in project env (pip install -e .[dev])",
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "categories": {},
        }
    out = result.stdout + "\n" + result.stderr
    passed = failed = errors = skipped = 0
    for line in out.splitlines():
        if " passed" in line and " failed" not in line and " error" not in line:
            try:
                passed = int(line.strip().split()[0])
            except (ValueError, IndexError):
                pass
        if " failed" in line:
            try:
                parts = line.replace(",", "").split()
                for i, p in enumerate(parts):
                    if p == "failed" and i > 0:
                        failed = int(parts[i - 1])
                        break
            except (ValueError, IndexError):
                pass
        if " error" in line and "errors" in line.lower():
            try:
                parts = line.replace(",", "").split()
                for i, p in enumerate(parts):
                    if p == "error" or p == "errors":
                        if i > 0 and parts[i - 1].isdigit():
                            errors = int(parts[i - 1])
                        break
            except (ValueError, IndexError):
                pass
        if " skipped" in line:
            try:
                parts = line.replace(",", "").split()
                for i, p in enumerate(parts):
                    if p == "skipped" and i > 0:
                        skipped = int(parts[i - 1])
                        break
            except (ValueError, IndexError):
                pass
    categories: dict[str, list[str]] = {
        "environment_issue": [],
        "integration_issue": [],
        "optional_dependency": [],
        "stale_test": [],
    }
    for line in out.splitlines():
        lower = line.lower()
        if "modulenotfounderror" in lower or "no module named" in lower:
            categories["environment_issue"].append(line.strip()[:120])
        elif "importerror" in lower:
            categories["optional_dependency"].append(line.strip()[:120])
        elif "failed" in lower and "FAILED" in line:
            categories["integration_issue"].append(line.strip()[:120])
    return {
        "ran": True,
        "returncode": result.returncode,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "categories": categories,
        "raw_tail": "\n".join(out.splitlines()[-30:]) if out else "",
    }
