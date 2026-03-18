"""
Agent execution layer: observe, simulate, assist, automate.

Default mode is simulate (no changes to real system without approval).
See docs/schemas/EXECUTION_MODES.md.
"""

from workflow_dataset.agent.execution_modes import ExecutionMode

__all__ = ["ExecutionMode"]
