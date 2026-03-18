"""
M23A: Internal Agent Chain Lab — operator-controlled local workflow chaining.
All under data/local/chain_lab; no auto-merge, no hidden cloud, no uncontrolled autonomy.
"""

from workflow_dataset.chain_lab.config import get_chain_lab_root, get_chains_dir, get_runs_dir
from workflow_dataset.chain_lab.definition import load_chain, save_chain, list_chains, get_step_by_id_or_index
from workflow_dataset.chain_lab.manifest import load_run_manifest, save_run_manifest, get_latest_run_id
from workflow_dataset.chain_lab.runner import run_chain, resume_chain, retry_step
from workflow_dataset.chain_lab.report import chain_run_report, chain_artifact_tree, resolve_run_id
from workflow_dataset.chain_lab.compare import compare_chain_runs
from workflow_dataset.chain_lab.eval_bridge import list_chain_runs_for_eval, get_chain_run_for_eval

__all__ = [
    "get_chain_lab_root",
    "get_chains_dir",
    "get_runs_dir",
    "load_chain",
    "save_chain",
    "list_chains",
    "get_step_by_id_or_index",
    "load_run_manifest",
    "save_run_manifest",
    "get_latest_run_id",
    "run_chain",
    "resume_chain",
    "retry_step",
    "chain_run_report",
    "chain_artifact_tree",
    "resolve_run_id",
    "compare_chain_runs",
    "list_chain_runs_for_eval",
    "get_chain_run_for_eval",
]
