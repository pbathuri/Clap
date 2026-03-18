"""
M26A: Goal / Plan / Work graph schema. Explicit, inspectable; no execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Step classification (align with macros where applicable)
STEP_CLASS_REASONING = "reasoning_only"
STEP_CLASS_LOCAL_INSPECT = "local_inspect"
STEP_CLASS_SANDBOX_WRITE = "sandbox_write"
STEP_CLASS_TRUSTED_REAL_CANDIDATE = "trusted_real_candidate"
STEP_CLASS_HUMAN_REQUIRED = "human_required"
STEP_CLASS_BLOCKED = "blocked"


@dataclass
class GoalRequest:
    """Operator intent or live goal input."""
    goal_text: str
    context_session_id: str = ""
    context_pack_id: str = ""
    created_at: str = ""


@dataclass
class ProvenanceSource:
    """Where a plan step came from: job, macro, routine, task_demo, pack."""
    kind: str  # "job" | "macro" | "routine" | "task_demo" | "pack"
    ref: str   # job_pack_id, macro_id, routine_id, task_id, pack_id
    label: str = ""


@dataclass
class ExpectedArtifact:
    """Expected output or artifact from a step or the plan."""
    label: str
    path_or_type: str = ""
    step_index: int | None = None


@dataclass
class BlockedCondition:
    """Reason a step or the plan is blocked."""
    reason: str
    step_index: int | None = None
    approval_scope: str = ""


@dataclass
class Checkpoint:
    """Placeholder for human approval or review before proceeding."""
    step_index: int
    label: str = ""
    required_approval: str = ""


@dataclass
class DependencyEdge:
    """Directed edge: source step index -> target step index."""
    source_index: int
    target_index: int
    edge_type: str = "sequence"  # sequence | artifact | optional


@dataclass
class PlanStep:
    """Single step in a compiled plan with classification and provenance."""
    step_index: int
    label: str
    step_class: str = ""  # reasoning_only | local_inspect | sandbox_write | trusted_real_candidate | human_required | blocked
    trust_level: str = ""
    approval_required: bool = False
    checkpoint_before: bool = False
    expected_outputs: list[str] = field(default_factory=list)
    blocked_reason: str = ""
    provenance: ProvenanceSource | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "label": self.label,
            "step_class": self.step_class,
            "trust_level": self.trust_level,
            "approval_required": self.approval_required,
            "checkpoint_before": self.checkpoint_before,
            "expected_outputs": list(self.expected_outputs),
            "blocked_reason": self.blocked_reason,
            "provenance": {
                "kind": self.provenance.kind,
                "ref": self.provenance.ref,
                "label": self.provenance.label,
            } if self.provenance else None,
        }


@dataclass
class Plan:
    """Compiled work graph: steps, dependencies, checkpoints, blocked, expected outputs."""
    plan_id: str
    goal_text: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    expected_artifacts: list[ExpectedArtifact] = field(default_factory=list)
    blocked_conditions: list[BlockedCondition] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)  # e.g. ["job:weekly_report", "macro:ops_flow"]
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal_text": self.goal_text,
            "steps": [s.to_dict() for s in self.steps],
            "edges": [
                {"source_index": e.source_index, "target_index": e.target_index, "edge_type": e.edge_type}
                for e in self.edges
            ],
            "checkpoints": [
                {"step_index": c.step_index, "label": c.label, "required_approval": c.required_approval}
                for c in self.checkpoints
            ],
            "expected_artifacts": [
                {"label": a.label, "path_or_type": a.path_or_type, "step_index": a.step_index}
                for a in self.expected_artifacts
            ],
            "blocked_conditions": [
                {"reason": b.reason, "step_index": b.step_index, "approval_scope": b.approval_scope}
                for b in self.blocked_conditions
            ],
            "sources_used": list(self.sources_used),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Plan:
        steps = []
        for s in d.get("steps", []):
            prov = s.get("provenance")
            provenance = ProvenanceSource(
                kind=prov.get("kind", ""),
                ref=prov.get("ref", ""),
                label=prov.get("label", ""),
            ) if prov else None
            steps.append(PlanStep(
                step_index=s.get("step_index", 0),
                label=s.get("label", ""),
                step_class=s.get("step_class", ""),
                trust_level=s.get("trust_level", ""),
                approval_required=s.get("approval_required", False),
                checkpoint_before=s.get("checkpoint_before", False),
                expected_outputs=list(s.get("expected_outputs", [])),
                blocked_reason=s.get("blocked_reason", ""),
                provenance=provenance,
            ))
        edges = [
            DependencyEdge(
                source_index=e.get("source_index", 0),
                target_index=e.get("target_index", 0),
                edge_type=e.get("edge_type", "sequence"),
            )
            for e in d.get("edges", [])
        ]
        checkpoints = [
            Checkpoint(
                step_index=c.get("step_index", 0),
                label=c.get("label", ""),
                required_approval=c.get("required_approval", ""),
            )
            for c in d.get("checkpoints", [])
        ]
        expected_artifacts = [
            ExpectedArtifact(
                label=a.get("label", ""),
                path_or_type=a.get("path_or_type", ""),
                step_index=a.get("step_index"),
            )
            for a in d.get("expected_artifacts", [])
        ]
        blocked_conditions = [
            BlockedCondition(
                reason=b.get("reason", ""),
                step_index=b.get("step_index"),
                approval_scope=b.get("approval_scope", ""),
            )
            for b in d.get("blocked_conditions", [])
        ]
        return cls(
            plan_id=d.get("plan_id", ""),
            goal_text=d.get("goal_text", ""),
            steps=steps,
            edges=edges,
            checkpoints=checkpoints,
            expected_artifacts=expected_artifacts,
            blocked_conditions=blocked_conditions,
            sources_used=list(d.get("sources_used", [])),
            created_at=d.get("created_at", ""),
        )
