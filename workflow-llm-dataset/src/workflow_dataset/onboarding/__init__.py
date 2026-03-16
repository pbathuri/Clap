"""
M23N: First-run onboarding and capability/approval bootstrap.
Local-first, no hidden scans, no auto-grant. Guided wizard and inspectable profile.
"""

from workflow_dataset.onboarding.bootstrap_profile import (
    BootstrapProfile,
    build_bootstrap_profile,
    load_bootstrap_profile,
    save_bootstrap_profile,
    get_bootstrap_profile_path,
)
from workflow_dataset.onboarding.onboarding_flow import (
    get_onboarding_status,
    run_onboarding_flow,
    format_onboarding_status,
)
from workflow_dataset.onboarding.product_summary import (
    build_first_run_summary,
    format_first_run_summary,
)
from workflow_dataset.onboarding.approval_bootstrap import (
    collect_approval_requests,
    format_approval_bootstrap_summary,
    apply_approval_choices,
)

__all__ = [
    "BootstrapProfile",
    "build_bootstrap_profile",
    "load_bootstrap_profile",
    "save_bootstrap_profile",
    "get_bootstrap_profile_path",
    "get_onboarding_status",
    "run_onboarding_flow",
    "format_onboarding_status",
    "build_first_run_summary",
    "format_first_run_summary",
    "collect_approval_requests",
    "format_approval_bootstrap_summary",
    "apply_approval_choices",
]
