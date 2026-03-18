"""
M23R: Packaged local deployment — profile, install-check, first-run. Local-only; no cloud.
"""

from workflow_dataset.local_deployment.profile import (
    build_local_deployment_profile,
    get_deployment_dir,
    write_deployment_profile,
)
from workflow_dataset.local_deployment.install_check import run_install_check
from workflow_dataset.local_deployment.first_run import run_first_run

__all__ = [
    "build_local_deployment_profile",
    "get_deployment_dir",
    "write_deployment_profile",
    "run_install_check",
    "run_first_run",
]
