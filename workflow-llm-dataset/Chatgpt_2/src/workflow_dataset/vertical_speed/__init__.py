"""
M47E–M47H: High-frequency workflow speed and friction reduction for the chosen vertical.
"""

from workflow_dataset.vertical_speed.models import (
    FrequentWorkflow,
    FrictionCluster,
    RepeatedHandoff,
    SlowTransition,
    UnnecessaryBranch,
    RepeatValueBottleneck,
    SpeedUpCandidate,
    FastPath,
    CommonLoopBundle,
    WorkflowKind,
    FrictionKind,
)
from workflow_dataset.vertical_speed.identification import (
    list_frequent_workflows,
    get_top_workflows,
)
from workflow_dataset.vertical_speed.friction import (
    build_friction_clusters,
    get_speed_up_candidates,
    get_repeat_value_bottlenecks,
)
from workflow_dataset.vertical_speed.action_route import (
    route_item_to_action,
    get_grouped_review_recommendation,
)
from workflow_dataset.vertical_speed.repeat_value import (
    get_morning_first_action_prefill,
    get_blocked_recovery_suggestion,
    repeat_value_report,
)
from workflow_dataset.vertical_speed.fast_paths import (
    list_fast_paths,
    get_fast_path_by_workflow_id,
    get_fast_path_by_path_id,
)
from workflow_dataset.vertical_speed.common_loop_bundles import (
    list_common_loop_bundles,
    get_common_loop_bundle,
    get_bundles_for_workflow,
)
from workflow_dataset.vertical_speed.compression_report import build_compression_report
from workflow_dataset.vertical_speed.mission_control import vertical_speed_slice

__all__ = [
    "FrequentWorkflow",
    "FrictionCluster",
    "RepeatedHandoff",
    "SlowTransition",
    "UnnecessaryBranch",
    "RepeatValueBottleneck",
    "SpeedUpCandidate",
    "FastPath",
    "CommonLoopBundle",
    "WorkflowKind",
    "FrictionKind",
    "list_frequent_workflows",
    "get_top_workflows",
    "build_friction_clusters",
    "get_speed_up_candidates",
    "get_repeat_value_bottlenecks",
    "route_item_to_action",
    "get_grouped_review_recommendation",
    "get_morning_first_action_prefill",
    "get_blocked_recovery_suggestion",
    "repeat_value_report",
    "list_fast_paths",
    "get_fast_path_by_workflow_id",
    "get_fast_path_by_path_id",
    "list_common_loop_bundles",
    "get_common_loop_bundle",
    "get_bundles_for_workflow",
    "build_compression_report",
    "vertical_speed_slice",
]
