"""
Alias module for local operator state persistence.
"""

from workflow_dataset.local_operator.state_store import (
    get_operator_state_path,
    load_operator_state,
    save_operator_state,
)

__all__ = [
    "get_operator_state_path",
    "load_operator_state",
    "save_operator_state",
]
