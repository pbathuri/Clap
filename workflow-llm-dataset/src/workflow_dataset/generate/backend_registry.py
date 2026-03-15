"""
Registry and abstraction for local generation backends (document, image demo, mock).

M10: mock only. M11: real document + image-demo backends with metadata and execution records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    GenerationManifest,
    GenerationStatus,
    PromptPack,
    AssetPlan,
    StylePack,
    BackendExecutionRecord,
)


class BackendCapability(str, Enum):
    """What a backend can do."""

    IMAGE = "image"
    VIDEO = "video"
    DESIGN = "design"
    DOCUMENT = "document"
    MOCK = "mock"


class ExecutionMode(str, Enum):
    """How the backend runs."""

    SYNC = "sync"
    ASYNC = "async"
    MOCK = "mock"


@dataclass
class BackendMeta:
    """Metadata for a registered backend."""

    backend_name: str
    backend_type: str  # document | image_demo | mock
    capabilities: list[BackendCapability]
    supported_families: list[str]  # prompt_family values, e.g. image, report_narrative
    supported_artifact_types: list[str]  # e.g. markdown, html, image
    required_dependencies: list[str] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SYNC
    version: str = "1.0"


# (success, message, output_paths, execution_record)
ExecuteResult = tuple[bool, str, list[str], BackendExecutionRecord | None]

_backends: dict[str, dict[str, Any]] = {}


def register_backend(
    name: str,
    execute_fn: Callable[..., ExecuteResult],
    meta: BackendMeta | None = None,
    capabilities: list[BackendCapability] | None = None,
) -> None:
    """Register a generation backend by name with optional metadata."""
    _backends[name] = {
        "execute": execute_fn,
        "meta": meta or BackendMeta(
            backend_name=name,
            backend_type="mock",
            capabilities=capabilities or [BackendCapability.MOCK],
            supported_families=[],
            supported_artifact_types=[],
        ),
        "capabilities": capabilities or (meta.capabilities if meta else [BackendCapability.MOCK]),
    }


def get_backend(name: str) -> dict[str, Any] | None:
    """Get backend by name. Returns None if not registered."""
    return _backends.get(name)


def list_backends() -> list[BackendMeta]:
    """List all registered backends with their metadata."""
    return [b["meta"] for b in _backends.values() if b.get("meta")]


def execute_generation(
    backend_name: str,
    request: GenerationRequest,
    manifest: GenerationManifest,
    workspace_path: Path | str,
    prompt_packs: list[PromptPack] | None = None,
    asset_plans: list[AssetPlan] | None = None,
    style_packs: list[StylePack] | None = None,
    use_llm: bool = False,
    allow_fallback: bool = True,
) -> ExecuteResult:
    """
    Execute generation via named backend. Sandbox-only.
    Returns (success, message, output_paths, execution_record).
    """
    backend = get_backend(backend_name)
    if not backend:
        rec = BackendExecutionRecord(
            backend_name=backend_name,
            execution_status="failed",
            error_message=f"Backend not registered: {backend_name}",
        )
        return False, rec.error_message, [], rec
    execute_fn = backend.get("execute")
    if not execute_fn:
        rec = BackendExecutionRecord(
            backend_name=backend_name,
            execution_status="failed",
            error_message="Backend has no execute function",
        )
        return False, rec.error_message, [], rec
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    prompt_packs = prompt_packs or []
    asset_plans = asset_plans or []
    style_packs = style_packs or []
    try:
        return execute_fn(
            request=request,
            manifest=manifest,
            workspace_path=workspace_path,
            prompt_packs=prompt_packs,
            asset_plans=asset_plans,
            style_packs=style_packs,
            use_llm=use_llm,
            allow_fallback=allow_fallback,
        )
    except MissingDependencyError as e:
        rec = BackendExecutionRecord(
            backend_name=backend_name,
            execution_status="failed",
            error_message=str(e),
            execution_log=[f"Missing dependency: {e}"],
        )
        return False, str(e), [], rec
    except UnsupportedFamilyError as e:
        rec = BackendExecutionRecord(
            backend_name=backend_name,
            execution_status="failed",
            error_message=str(e),
        )
        return False, str(e), [], rec
    except Exception as e:
        rec = BackendExecutionRecord(
            backend_name=backend_name,
            execution_status="failed",
            error_message=str(e),
            execution_log=[repr(e)],
        )
        return False, str(e), [], rec


class MissingDependencyError(Exception):
    """Raised when a required local dependency is missing."""

    pass


class UnsupportedFamilyError(Exception):
    """Raised when generation family is not supported by the backend."""

    pass


def _mock_execute(
    request: GenerationRequest,
    manifest: GenerationManifest,
    workspace_path: Path,
    prompt_packs: list[PromptPack],
    asset_plans: list[AssetPlan],
    style_packs: list[Any] | None = None,
    use_llm: bool = False,
    allow_fallback: bool = True,
) -> ExecuteResult:
    """Mock backend: write a placeholder file. For demo/tests."""
    from workflow_dataset.utils.dates import utc_now_iso

    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    placeholder = workspace_path / "MOCK_GENERATION_PLACEHOLDER.txt"
    placeholder.write_text(
        f"Mock generation for {request.generation_id}\n"
        f"Prompt packs: {len(prompt_packs)}\n"
        f"Asset plans: {len(asset_plans)}\n",
        encoding="utf-8",
    )
    rec = BackendExecutionRecord(
        backend_name="mock",
        backend_version="1.0",
        execution_status="success",
        generated_output_paths=[str(placeholder)],
        used_llm=False,
        used_fallback=False,
        executed_utc=utc_now_iso(),
    )
    return True, f"Mock executed; placeholder written to {placeholder}", [str(placeholder)], rec


# Register mock backend by default
register_backend(
    "mock",
    _mock_execute,
    meta=BackendMeta(
        backend_name="mock",
        backend_type="mock",
        capabilities=[BackendCapability.MOCK],
        supported_families=[],
        supported_artifact_types=["text"],
        execution_mode=ExecutionMode.MOCK,
    ),
)
