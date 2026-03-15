"""
Local generation backends: document, image-demo, mock.

M11: real document + image-demo backends; mock remains fallback.
"""

from __future__ import annotations

from workflow_dataset.generate.backend_registry import (
    register_backend,
    BackendMeta,
    BackendCapability,
    ExecutionMode,
)
from workflow_dataset.generate.backends.document_backend import execute_document_backend
from workflow_dataset.generate.backends.image_demo_backend import execute_image_demo_backend


def _register_real_backends() -> None:
    """Register document and image-demo backends with the registry."""
    register_backend(
        "document",
        execute_document_backend,
        meta=BackendMeta(
            backend_name="document",
            backend_type="document",
            capabilities=[BackendCapability.DOCUMENT],
            supported_families=[
                "report_narrative",
                "storyboard",
                "creative_brief",
                "design_brief",
                "presentation_narrative",
                "architecture_narrative",
            ],
            supported_artifact_types=["markdown"],
            execution_mode=ExecutionMode.SYNC,
            version="1.0",
        ),
    )
    register_backend(
        "image_demo",
        execute_image_demo_backend,
        meta=BackendMeta(
            backend_name="image_demo",
            backend_type="image_demo",
            capabilities=[BackendCapability.IMAGE, BackendCapability.DESIGN],
            supported_families=["image", "keyframe", "storyboard", "design_variant"],
            supported_artifact_types=["markdown", "html"],
            execution_mode=ExecutionMode.SYNC,
            version="1.0",
        ),
    )


_register_real_backends()
