"""
M40A–M40D: Production cut — final vertical lock and production surface freeze.
"""

from workflow_dataset.production_cut.models import (
    ProductionCut,
    ChosenPrimaryVertical,
    IncludedSurface,
    ExcludedSurface,
    QuarantinedExperimentalSurface,
    SupportedWorkflowSet,
    RequiredTrustPosture,
    DefaultOperatingProfile,
    ProductionReadinessNote,
    ProductionDefaultProfile,
    ExperimentalQuarantineRule,
    ProductionSafeLabel,
)
from workflow_dataset.production_cut.store import get_active_cut, set_active_cut
from workflow_dataset.production_cut.lock import (
    choose_primary_from_evidence,
    build_production_cut_for_vertical,
    lock_production_cut,
    explain_production_cut,
)
from workflow_dataset.production_cut.freeze import (
    build_production_freeze,
    get_default_visible_surfaces,
    get_hidden_experimental_surfaces,
    get_blocked_unsupported_surfaces,
)
from workflow_dataset.production_cut.scope_report import (
    build_frozen_scope_report,
    build_surfaces_classification,
)
from workflow_dataset.production_cut.production_defaults import get_production_default_profile
from workflow_dataset.production_cut.quarantine_rules import (
    list_quarantine_rules,
    build_quarantine_rules_report,
)
from workflow_dataset.production_cut.labels import (
    build_production_safe_label_report,
    build_operator_surface_explanations,
)

__all__ = [
    "ProductionCut",
    "ChosenPrimaryVertical",
    "IncludedSurface",
    "ExcludedSurface",
    "QuarantinedExperimentalSurface",
    "SupportedWorkflowSet",
    "RequiredTrustPosture",
    "DefaultOperatingProfile",
    "ProductionReadinessNote",
    "get_active_cut",
    "set_active_cut",
    "choose_primary_from_evidence",
    "build_production_cut_for_vertical",
    "lock_production_cut",
    "explain_production_cut",
    "build_production_freeze",
    "get_default_visible_surfaces",
    "get_hidden_experimental_surfaces",
    "get_blocked_unsupported_surfaces",
    "build_frozen_scope_report",
    "build_surfaces_classification",
    "ProductionDefaultProfile",
    "ExperimentalQuarantineRule",
    "ProductionSafeLabel",
    "get_production_default_profile",
    "list_quarantine_rules",
    "build_quarantine_rules_report",
    "build_production_safe_label_report",
    "build_operator_surface_explanations",
]
