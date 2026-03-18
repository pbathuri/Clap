"""
M42I–M42L: Built-in benchmark slices — map to eval suites and reliability paths.
"""

from __future__ import annotations

from workflow_dataset.benchmark_board.models import BenchmarkSlice

BUILTIN_SLICES: list[BenchmarkSlice] = [
    BenchmarkSlice(
        slice_id="ops_reporting",
        name="Ops reporting",
        description="Eval suite for ops/reporting workflows (weekly status, blockers).",
        eval_suite="ops_reporting",
        label="Ops reporting",
    ),
    BenchmarkSlice(
        slice_id="golden_path",
        name="Golden path",
        description="Reliability golden path; core install and first-value flow.",
        reliability_path_id="golden_first_run",
        label="Golden path",
    ),
    BenchmarkSlice(
        slice_id="single",
        name="Single case",
        description="Single-case eval run.",
        eval_suite="single",
        label="Single",
    ),
]


def get_slice(slice_id: str) -> BenchmarkSlice | None:
    for s in BUILTIN_SLICES:
        if s.slice_id == slice_id:
            return s
    return None


def list_slice_ids() -> list[str]:
    return [s.slice_id for s in BUILTIN_SLICES]
