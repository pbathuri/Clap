"""
M23I: Benchmark task schema for desktop/operator tasks.
Local and inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class DesktopBenchmarkCase:
    """One benchmark case: id, title, category, required adapters/approvals, expected outcomes, safety."""
    benchmark_id: str
    title: str
    task_category: str  # e.g. inspect_folder | snapshot_notes | simulate_browser | replay_task | approved_real
    required_adapters: list[str] = field(default_factory=list)  # adapter_ids
    required_approvals: list[str] = field(default_factory=list)  # e.g. path_scope, action_scope
    required_capability_profile: dict[str, Any] = field(default_factory=dict)  # optional constraints
    simulation_expected_outcome: str = "success"  # success | failure | any
    real_mode_eligibility: bool = False  # true only if safe, approved subset
    expected_artifacts: list[str] = field(default_factory=list)  # e.g. ["output.json", "preview"]
    expected_coordination_graph_shape: dict[str, Any] = field(default_factory=dict)  # optional: nodes_min, edges_min
    safety_notes: str = ""
    scoring_notes: str = ""
    # Steps: either inline steps (adapter_id, action_id, params) or task_id for replay
    steps: list[dict[str, Any]] = field(default_factory=list)  # [{"adapter_id","action_id","params"}]
    task_id: str = ""  # if set, replay this task (simulate only)


def _case_from_dict(d: dict[str, Any], case_id: str = "") -> DesktopBenchmarkCase:
    return DesktopBenchmarkCase(
        benchmark_id=str(d.get("benchmark_id", case_id)),
        title=str(d.get("title", "")),
        task_category=str(d.get("task_category", "inspect_folder")),
        required_adapters=list(d.get("required_adapters") or []),
        required_approvals=list(d.get("required_approvals") or []),
        required_capability_profile=dict(d.get("required_capability_profile") or {}),
        simulation_expected_outcome=str(d.get("simulation_expected_outcome", "success")),
        real_mode_eligibility=bool(d.get("real_mode_eligibility", False)),
        expected_artifacts=list(d.get("expected_artifacts") or []),
        expected_coordination_graph_shape=dict(d.get("expected_coordination_graph_shape") or {}),
        safety_notes=str(d.get("safety_notes", "")),
        scoring_notes=str(d.get("scoring_notes", "")),
        steps=list(d.get("steps") or []),
        task_id=str(d.get("task_id", "")),
    )


def load_case(path: Path | str, case_id: str = "") -> DesktopBenchmarkCase | None:
    """Load a single benchmark case from YAML or JSON file."""
    path = Path(path)
    if not path.exists() or not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in (".yaml", ".yml") and yaml:
            data = yaml.safe_load(raw) or {}
        else:
            import json
            data = json.loads(raw)
    except Exception:
        return None
    cid = case_id or data.get("benchmark_id") or path.stem
    return _case_from_dict(data, cid)


def _find_case_by_id(cases_dir: Path, benchmark_id: str) -> DesktopBenchmarkCase | None:
    """Find case by benchmark_id in cases dir (stem or benchmark_id field)."""
    for f in cases_dir.iterdir():
        if f.suffix.lower() not in (".yaml", ".yml", ".json") or not f.is_file():
            continue
        case = load_case(f, f.stem)
        if case and (case.benchmark_id == benchmark_id or f.stem == benchmark_id):
            return case
    return None


def get_case(benchmark_id: str, repo_root: Path | str | None = None) -> DesktopBenchmarkCase | None:
    """Load benchmark case by id from cases dir."""
    from workflow_dataset.desktop_bench.config import get_cases_dir
    return _find_case_by_id(get_cases_dir(repo_root), benchmark_id)


def list_cases(repo_root: Path | str | None = None) -> list[str]:
    """List benchmark case ids (from filenames)."""
    from workflow_dataset.desktop_bench.config import get_cases_dir
    cases_dir = get_cases_dir(repo_root)
    ids = []
    for f in cases_dir.iterdir():
        if f.is_file() and f.suffix.lower() in (".yaml", ".yml", ".json"):
            ids.append(f.stem)
    return sorted(ids)


def load_suite(suite_name: str, repo_root: Path | str | None = None) -> list[DesktopBenchmarkCase]:
    """Load a suite (list of case ids); return list of DesktopBenchmarkCase. Reads from suites/<suite_name>.yaml or .json."""
    from workflow_dataset.desktop_bench.config import get_suites_dir, get_cases_dir
    suites_dir = get_suites_dir(repo_root)
    cases_dir = get_cases_dir(repo_root)
    cases_dir = get_cases_dir(repo_root)
    for ext in (".yaml", ".yml", ".json"):
        path = suites_dir / f"{suite_name}{ext}"
        if path.exists() and path.is_file():
            raw = path.read_text(encoding="utf-8")
            try:
                if path.suffix.lower() in (".yaml", ".yml") and yaml:
                    data = yaml.safe_load(raw) or {}
                else:
                    import json
                    data = json.loads(raw) or {}
            except Exception:
                return []
            case_ids = data.get("cases", data.get("case_ids", []))
            if isinstance(case_ids, list):
                out = []
                for cid in case_ids:
                    c = _find_case_by_id(cases_dir, str(cid))
                    if c:
                        out.append(c)
                return out
            break
    return []
