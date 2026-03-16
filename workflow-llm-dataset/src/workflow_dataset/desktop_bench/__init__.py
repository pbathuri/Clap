"""
M23I: Desktop task benchmark + trusted automation harness.
Narrow, measurable, approval-gated desktop automation.
"""

from workflow_dataset.desktop_bench.schema import (
    DesktopBenchmarkCase,
    load_case,
    list_cases,
    load_suite,
    get_case,
)
from workflow_dataset.desktop_bench.config import (
    get_desktop_bench_root,
    get_cases_dir,
    get_runs_dir,
    get_suites_dir,
)
from workflow_dataset.desktop_bench.harness import (
    run_benchmark,
    run_suite,
)
from workflow_dataset.desktop_bench.trusted_actions import (
    get_trusted_real_actions,
    list_trusted_actions_report,
)
from workflow_dataset.desktop_bench.scoring import (
    score_run,
    compute_trust_status,
)
from workflow_dataset.desktop_bench.board import (
    list_runs,
    get_run,
    board_report,
    compare_runs,
    format_board_report,
)

__all__ = [
    "DesktopBenchmarkCase",
    "load_case",
    "list_cases",
    "load_suite",
    "get_case",
    "get_desktop_bench_root",
    "get_cases_dir",
    "get_runs_dir",
    "get_suites_dir",
    "run_benchmark",
    "run_suite",
    "get_trusted_real_actions",
    "list_trusted_actions_report",
    "score_run",
    "compute_trust_status",
    "list_runs",
    "get_run",
    "board_report",
    "compare_runs",
    "format_board_report",
]
