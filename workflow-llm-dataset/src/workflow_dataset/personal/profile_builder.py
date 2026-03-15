"""
Build or update user profile / role from observation and teaching.

Profile includes self-described role(s), industry/occupation hints for
matching against global work priors. All on-device.
"""

from __future__ import annotations

from workflow_dataset.personal.work_graph import PersonalWorkGraphNode, NodeType


def build_profile_from_observation(
    event_summary: dict,
) -> PersonalWorkGraphNode | None:
    """Infer profile hints from observation summary. TODO: implement."""
    return None


def update_profile_from_teaching(
    existing_node: PersonalWorkGraphNode | None,
    teaching_content: dict,
) -> PersonalWorkGraphNode:
    """Update profile from explicit user teaching. TODO: implement."""
    return PersonalWorkGraphNode(
        node_id="user_profile_placeholder",
        node_type=NodeType.USER_PROFILE,
        label="",
        attributes={},
    )
