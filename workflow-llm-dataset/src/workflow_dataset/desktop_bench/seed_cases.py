"""
M23I: Seed default benchmark cases and suite. Writes to data/local/desktop_bench/cases and suites.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.desktop_bench.config import get_cases_dir, get_suites_dir

INSPECT_FOLDER_BASIC = """benchmark_id: inspect_folder_basic
title: Inspect local folder and summarize contents
task_category: inspect_folder
required_adapters: [file_ops]
required_approvals: []
simulation_expected_outcome: success
real_mode_eligibility: true
expected_artifacts: []
safety_notes: Read-only; path should be under approved_paths for real mode.
scoring_notes: Pass if inspect_path and list_directory succeed.
steps:
  - adapter_id: file_ops
    action_id: inspect_path
    params:
      path: data/local
  - adapter_id: file_ops
    action_id: list_directory
    params:
      path: data/local
task_id: ""
"""

SNAPSHOT_NOTES_SAFE = """benchmark_id: snapshot_notes_safe
title: Snapshot notes into sandbox and produce structured summary
task_category: snapshot_notes
required_adapters: [file_ops, notes_document]
required_approvals: [path_scope, action_scope]
simulation_expected_outcome: success
real_mode_eligibility: true
expected_artifacts: [output]
safety_notes: Snapshot copies to sandbox only; read_text is read-only.
scoring_notes: Pass if snapshot_to_sandbox and read_text succeed.
steps:
  - adapter_id: file_ops
    action_id: snapshot_to_sandbox
    params:
      path: data/local
  - adapter_id: notes_document
    action_id: read_text
    params:
      path: data/local/desktop_bench/cases/inspect_folder_basic.yaml
task_id: ""
"""

SIMULATE_BROWSER = """benchmark_id: simulate_browser_open
title: Simulate browser open for approved URL
task_category: simulate_browser
required_adapters: [browser_open]
required_approvals: []
simulation_expected_outcome: success
real_mode_eligibility: false
expected_artifacts: []
safety_notes: Simulate only; no real browser open.
scoring_notes: Pass if simulate returns success and URL validation ok.
steps:
  - adapter_id: browser_open
    action_id: open_url
    params:
      url: https://example.com
task_id: ""
"""

REPLAY_TASK_SIMULATE = """benchmark_id: replay_task_simulate
title: Replay a simple demonstrated task in simulate mode
task_category: replay_task
required_adapters: [file_ops]
required_approvals: []
simulation_expected_outcome: success
real_mode_eligibility: false
expected_artifacts: []
safety_notes: Task replay is simulate-only.
scoring_notes: Pass if task exists and all steps simulate success.
task_id: cli_demo
steps: []
"""

SUITE_DESKTOP_BRIDGE_CORE = """suite: desktop_bridge_core
cases:
  - inspect_folder_basic
  - simulate_browser_open
"""


def seed_default_cases(repo_root: Path | str | None = None) -> list[Path]:
    """Write default benchmark cases to cases dir. Returns list of paths written."""
    cases_dir = get_cases_dir(repo_root)
    written = []
    for name, content in [
        ("inspect_folder_basic.yaml", INSPECT_FOLDER_BASIC),
        ("snapshot_notes_safe.yaml", SNAPSHOT_NOTES_SAFE),
        ("simulate_browser_open.yaml", SIMULATE_BROWSER),
        ("replay_task_simulate.yaml", REPLAY_TASK_SIMULATE),
    ]:
        p = cases_dir / name
        p.write_text(content, encoding="utf-8")
        written.append(p)
    return written


def seed_default_suite(repo_root: Path | str | None = None) -> Path:
    """Write desktop_bridge_core suite to suites dir."""
    suites_dir = get_suites_dir(repo_root)
    p = suites_dir / "desktop_bridge_core.yaml"
    p.write_text(SUITE_DESKTOP_BRIDGE_CORE, encoding="utf-8")
    return p
