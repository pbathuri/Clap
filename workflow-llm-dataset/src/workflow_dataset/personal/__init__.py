"""
Personal work graph: private, device-local model of the user's work.

Includes profile, projects, routines, workflows, preferences, approval boundaries.
See docs/schemas/PERSONAL_WORK_GRAPH.md.
"""

from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode

__all__ = ["PersonalWorkGraphNode", "NodeType"]
