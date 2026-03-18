"""
M22E: Workflow Composer + Template Studio. Local templates for ops/reporting; explicit composition.
M22E-F2: Template versioning, validation, and validation reports.
M22E-F3: Template import/export and typed parameters.
M22E-F5: Template testing harness (artifact inventory/order, manifest shape).
"""

from workflow_dataset.templates.registry import (
    TEMPLATES_DIR,
    get_template,
    list_templates,
    load_template,
)
from workflow_dataset.templates.validation import (
    get_template_status,
    resolve_template_params,
    template_validation_report,
    validate_template,
)
from workflow_dataset.templates.export_import import (
    export_template,
    import_template,
)
from workflow_dataset.templates.harness import (
    expected_artifact_list_for_template,
    run_template_harness,
    validate_workspace_against_template,
)

__all__ = [
    "TEMPLATES_DIR",
    "load_template",
    "get_template",
    "list_templates",
    "validate_template",
    "template_validation_report",
    "get_template_status",
    "resolve_template_params",
    "export_template",
    "import_template",
    "expected_artifact_list_for_template",
    "run_template_harness",
    "validate_workspace_against_template",
]
