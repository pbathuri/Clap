"""
M21X: Local evaluation harness and benchmark board for ops/reporting workflows.
Define cases, run suites, score outputs, compare runs, surface benchmark board. All local; no auto-apply.
"""

from workflow_dataset.eval.config import get_cases_dir, get_eval_root, get_runs_dir

__all__ = ["get_eval_root", "get_cases_dir", "get_runs_dir"]
