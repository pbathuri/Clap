"""
M23F-F1: Graph summary report. Advisory only.
"""

from __future__ import annotations

from workflow_dataset.coordination_graph.models import CoordinationGraph


def format_graph_summary(graph: CoordinationGraph) -> str:
    """Format coordination graph as a short text summary."""
    lines: list[str] = []
    lines.append(f"# Coordination graph: {graph.task_id or '(unnamed)'}")
    lines.append("")
    lines.append(f"  nodes: {len(graph.nodes)}  edges: {len(graph.edges)}")
    lines.append("")
    lines.append("## Nodes (by type)")
    by_type: dict[str, list[str]] = {}
    for n in graph.nodes:
        by_type.setdefault(n.type, []).append(n.label)
    for t, labels in sorted(by_type.items()):
        lines.append(f"  {t}: {', '.join(labels)}")
    lines.append("")
    lines.append("## Edges (sequence)")
    for e in graph.edges:
        lines.append(f"  {e.source_id} -> {e.target_id} ({e.edge_type})")
    return "\n".join(lines)
