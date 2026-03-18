"""
M36A–M36D: Daily operating surface and workday state machine. Local-first; explicit states and transitions.
"""

from workflow_dataset.workday.models import (
    WorkdayState,
    WorkdayStateRecord,
    StateTransition,
    ActiveDailyContext,
    DaySummarySnapshot,
    BlockedStateInfo,
)
from workflow_dataset.workday.store import (
    load_workday_state,
    save_workday_state,
    load_day_summary,
    save_day_summary,
    current_day_id,
    get_active_workday_preset_id,
    set_active_workday_preset_id,
)
from workflow_dataset.workday.presets import (
    WorkdayPreset,
    BUILTIN_WORKDAY_PRESETS,
    get_workday_preset,
    list_workday_presets,
)
from workflow_dataset.workday.state_machine import (
    VALID_TRANSITIONS,
    can_transition,
    apply_transition,
    gather_context,
)
from workflow_dataset.workday.surface import (
    DailyOperatingSurface,
    build_daily_operating_surface,
    format_daily_operating_surface,
)
from workflow_dataset.workday.cli import (
    cmd_day_status,
    cmd_day_start,
    cmd_day_mode,
    cmd_day_wrap_up,
    cmd_day_shutdown,
    cmd_day_resume,
)

__all__ = [
    "WorkdayState",
    "WorkdayStateRecord",
    "StateTransition",
    "ActiveDailyContext",
    "DaySummarySnapshot",
    "BlockedStateInfo",
    "load_workday_state",
    "save_workday_state",
    "load_day_summary",
    "save_day_summary",
    "current_day_id",
    "get_active_workday_preset_id",
    "set_active_workday_preset_id",
    "WorkdayPreset",
    "BUILTIN_WORKDAY_PRESETS",
    "get_workday_preset",
    "list_workday_presets",
    "VALID_TRANSITIONS",
    "can_transition",
    "apply_transition",
    "gather_context",
    "DailyOperatingSurface",
    "build_daily_operating_surface",
    "format_daily_operating_surface",
    "cmd_day_status",
    "cmd_day_start",
    "cmd_day_mode",
    "cmd_day_wrap_up",
    "cmd_day_shutdown",
    "cmd_day_resume",
]
