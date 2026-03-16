"""
M22E: Workflow Composer + Template Studio. Local templates for ops/reporting; explicit composition.
M22E-F2: Template versioning, validation, and validation reports.
"""

from workflow_dataset.templates.registry import (
    TEMPLATES_DIR,
    get_template,
    list_templates,
    load_template,
)
from workflow_dataset.templates.validation import (
    get_template_status,
    template_validation_report,
    validate_template,
)

__all__ = [
    "TEMPLATES_DIR",
    "load_template",
    "get_template",
    "list_templates",
    "validate_template",
    "template_validation_report",
    "get_template_status",
]
