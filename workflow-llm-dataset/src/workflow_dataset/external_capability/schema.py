"""
M24A: External capability source schema — unified entry for Ollama models, OpenClaw,
coding-agent, IDE, automation, optional model/dataset sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Source categories
SOURCE_CATEGORIES = (
    "ollama_model",
    "openclaw",
    "coding_agent",
    "ide_editor",
    "automation",
    "embeddings",
    "vision_ocr",
    "optional_model_dataset",
)

# Activation status (read from runtime / registry)
ACTIVATION_STATUSES = ("available", "configured", "not_installed", "optional", "blocked", "unknown")

# Lifecycle states for health reporting (M24G)
LIFECYCLE_STATES = ("installed", "configured", "active", "blocked", "failed", "unknown")


@dataclass
class ExternalCapabilitySource:
    """Single external capability source for activation planning."""

    source_id: str
    category: str  # one of SOURCE_CATEGORIES
    local: bool = True
    optional_remote: bool = False
    install_prerequisites: list[str] = field(default_factory=list)
    license_policy: str = ""  # e.g. "MIT", "Apache-2.0", "reference_only"
    usage_policy: str = ""  # e.g. "local_only", "optional_wrapper"
    security_notes: str = ""
    approval_notes: str = ""
    trust_notes: str = ""
    supported_task_classes: list[str] = field(default_factory=list)
    supported_domain_pack_ids: list[str] = field(default_factory=list)  # verticals
    supported_value_pack_ids: list[str] = field(default_factory=list)  # e.g. founder_ops_plus
    supported_tiers: list[str] = field(default_factory=list)  # dev_full, local_standard, etc.
    machine_requirements: list[str] = field(default_factory=list)  # e.g. ollama_running, 8gb_ram
    estimated_resource: str = ""  # e.g. "low", "medium", "high"
    activation_status: str = "unknown"  # one of ACTIVATION_STATUSES
    enabled: bool = False
    display_name: str = ""
    notes: str = ""
    rollback_notes: str = ""  # how to deactivate / rollback

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "category": self.category,
            "local": self.local,
            "optional_remote": self.optional_remote,
            "install_prerequisites": self.install_prerequisites,
            "license_policy": self.license_policy,
            "usage_policy": self.usage_policy,
            "security_notes": self.security_notes,
            "approval_notes": self.approval_notes,
            "trust_notes": self.trust_notes,
            "supported_task_classes": self.supported_task_classes,
            "supported_domain_pack_ids": self.supported_domain_pack_ids,
            "supported_value_pack_ids": self.supported_value_pack_ids,
            "supported_tiers": self.supported_tiers,
            "machine_requirements": self.machine_requirements,
            "estimated_resource": self.estimated_resource,
            "activation_status": self.activation_status,
            "enabled": self.enabled,
            "display_name": self.display_name,
            "notes": self.notes,
            "rollback_notes": self.rollback_notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExternalCapabilitySource:
        return cls(
            source_id=str(d.get("source_id", "")),
            category=str(d.get("category", "ollama_model")),
            local=bool(d.get("local", True)),
            optional_remote=bool(d.get("optional_remote", False)),
            install_prerequisites=list(d.get("install_prerequisites", [])),
            license_policy=str(d.get("license_policy", "")),
            usage_policy=str(d.get("usage_policy", "")),
            security_notes=str(d.get("security_notes", "")),
            approval_notes=str(d.get("approval_notes", "")),
            trust_notes=str(d.get("trust_notes", "")),
            supported_task_classes=list(d.get("supported_task_classes", [])),
            supported_domain_pack_ids=list(d.get("supported_domain_pack_ids", [])),
            supported_value_pack_ids=list(d.get("supported_value_pack_ids", [])),
            supported_tiers=list(d.get("supported_tiers", [])),
            machine_requirements=list(d.get("machine_requirements", [])),
            estimated_resource=str(d.get("estimated_resource", "")),
            activation_status=str(d.get("activation_status", "unknown")),
            enabled=bool(d.get("enabled", False)),
            display_name=str(d.get("display_name", "")),
            notes=str(d.get("notes", "")),
            rollback_notes=str(d.get("rollback_notes", "")),
        )
