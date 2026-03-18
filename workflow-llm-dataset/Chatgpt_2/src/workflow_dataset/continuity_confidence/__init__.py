"""
M49I–M49L: Device-aware runtime profiles and continuity confidence.
Post-restore confidence, downgraded/promoted capability, recommended operating posture.
"""

from workflow_dataset.continuity_confidence.models import (
    TargetDeviceProfile,
    PostRestoreRuntimeProfile,
    ContinuityConfidenceScore,
    ContinuityConfidenceClass,
    DowngradedCapabilityNote,
    PromotedCapabilityNote,
    ModelRouteAdjustment,
    OperatorModeSafetyAdjustment,
    RecommendedOperatingPosture,
    DeviceCapabilityClass,
    DeviceClass,
    PostRestoreOperatingPreset,
    PostRestoreSafeOperatingGuidance,
)
from workflow_dataset.continuity_confidence.device_classes import (
    list_device_classes,
    get_device_class,
    resolve_device_class,
)
from workflow_dataset.continuity_confidence.post_restore_presets import (
    list_post_restore_presets,
    get_post_restore_preset,
    get_recommended_preset_for,
)
from workflow_dataset.continuity_confidence.safe_operating_guidance import post_restore_safe_operating_guidance
from workflow_dataset.continuity_confidence.device_profile import (
    build_target_device_profile,
    compare_source_target,
)
from workflow_dataset.continuity_confidence.confidence import build_continuity_confidence
from workflow_dataset.continuity_confidence.adaptation import (
    build_post_restore_runtime_profile,
    get_downgraded_runtime_explanation,
)
from workflow_dataset.continuity_confidence.report import continuity_confidence_report
from workflow_dataset.continuity_confidence.mission_control import continuity_confidence_slice

__all__ = [
    "TargetDeviceProfile",
    "PostRestoreRuntimeProfile",
    "ContinuityConfidenceScore",
    "ContinuityConfidenceClass",
    "DowngradedCapabilityNote",
    "PromotedCapabilityNote",
    "ModelRouteAdjustment",
    "OperatorModeSafetyAdjustment",
    "RecommendedOperatingPosture",
    "DeviceCapabilityClass",
    "build_target_device_profile",
    "compare_source_target",
    "build_continuity_confidence",
    "build_post_restore_runtime_profile",
    "get_downgraded_runtime_explanation",
    "continuity_confidence_report",
    "continuity_confidence_slice",
    "DeviceClass",
    "PostRestoreOperatingPreset",
    "PostRestoreSafeOperatingGuidance",
    "list_device_classes",
    "get_device_class",
    "resolve_device_class",
    "list_post_restore_presets",
    "get_post_restore_preset",
    "get_recommended_preset_for",
    "post_restore_safe_operating_guidance",
]
