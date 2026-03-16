"""
M22E-F5: Template testing harness. Validates workspace output against template expectations.
Run built-in templates against fixture workspaces; check artifact inventory, order, manifest shape.
No LLM/cloud; local fixtures only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.templates.registry import (
    load_template,
    template_artifact_order_and_filenames,
)

# Manifest filename used by ops_reporting_workspace
WORKSPACE_MANIFEST_NAME = "workspace_manifest.json"
# First artifact in saved workspace (always present)
SOURCE_SNAPSHOT_FILENAME = "source_snapshot.md"

# Required keys in workspace manifest for template-driven runs
REQUIRED_MANIFEST_KEYS = ("workflow", "artifact_list")
OPTIONAL_MANIFEST_KEYS = ("template_id", "template_params", "grounding", "timestamp")


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root)
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def expected_artifact_list_for_template(template: dict[str, Any]) -> list[str]:
    """
    Return expected artifact filenames in order for a template-driven workspace.
    Convention: source_snapshot.md first, then template artifact order.
    """
    ordered = template_artifact_order_and_filenames(template)
    filenames = [SOURCE_SNAPSHOT_FILENAME] + [f for _k, f in ordered]
    return filenames


def required_manifest_keys_for_template(template: dict[str, Any]) -> tuple[str, ...]:
    """Return required manifest keys when workspace is from this template."""
    return REQUIRED_MANIFEST_KEYS + ("template_id",)


@dataclass
class HarnessResult:
    """Result of validating a workspace against a template."""
    passed: bool
    template_id: str
    expected_artifacts: list[str] = field(default_factory=list)
    actual_artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    manifest_errors: list[str] = field(default_factory=list)

    def to_message(self) -> str:
        """Human-readable failure message."""
        lines = [f"Template: {self.template_id}", f"Expected artifacts (order): {self.expected_artifacts}"]
        if self.actual_artifacts:
            lines.append(f"Actual artifacts: {self.actual_artifacts}")
        if self.errors:
            lines.append("Errors:")
            for e in self.errors:
                lines.append(f"  - {e}")
        if self.manifest_errors:
            lines.append("Manifest:")
            for e in self.manifest_errors:
                lines.append(f"  - {e}")
        return "\n".join(lines)


def validate_workspace_against_template(
    workspace_path: Path | str,
    template_id_or_dict: str | dict[str, Any],
    repo_root: Path | str | None = None,
) -> HarnessResult:
    """
    Validate a workspace dir against a template: artifact inventory, order, manifest structure.
    Returns HarnessResult with passed, errors, expected_artifacts, actual_artifacts.
    """
    ws = Path(workspace_path).resolve()
    if not ws.exists() or not ws.is_dir():
        return HarnessResult(
            passed=False,
            template_id=template_id_or_dict.get("id", "?") if isinstance(template_id_or_dict, dict) else str(template_id_or_dict),
            errors=[f"Workspace path is not a directory: {ws}"],
        )
    if isinstance(template_id_or_dict, dict):
        template = template_id_or_dict
    else:
        try:
            template = load_template(template_id_or_dict.strip(), repo_root=repo_root)
        except FileNotFoundError:
            return HarnessResult(
                passed=False,
                template_id=template_id_or_dict.strip(),
                errors=[f"Template not found: {template_id_or_dict}"],
            )
        except Exception as e:
            return HarnessResult(
                passed=False,
                template_id=template_id_or_dict.strip(),
                errors=[f"Failed to load template: {e}"],
            )

    tid = template.get("id", "?")
    expected = expected_artifact_list_for_template(template)
    errors: list[str] = []
    manifest_errors: list[str] = []

    # Load manifest
    manifest_path = ws / WORKSPACE_MANIFEST_NAME
    if not manifest_path.exists():
        manifest_path = ws / "manifest.json"
    manifest: dict[str, Any] | None = None
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            manifest_errors.append(f"Could not parse manifest: {e}")
    else:
        manifest_errors.append("Missing workspace_manifest.json (or manifest.json)")

    # Actual artifact list: from manifest or dir listing
    actual: list[str] = []
    if manifest:
        actual = list(manifest.get("artifact_list") or manifest.get("saved_artifact_paths") or [])
        # Normalize to filenames only
        actual = [p if "/" not in p else Path(p).name for p in actual if isinstance(p, str)]
        # Remove manifest file from list if present
        actual = [a for a in actual if a not in (WORKSPACE_MANIFEST_NAME, "manifest.json")]
    if not actual:
        for f in sorted(ws.iterdir()):
            if f.is_file() and f.suffix.lower() == ".md":
                actual.append(f.name)
        actual = sorted(actual)

    # Check required manifest keys
    required = required_manifest_keys_for_template(template)
    if manifest:
        for key in required:
            if key not in manifest:
                manifest_errors.append(f"Missing required manifest key: {key}")
        if manifest.get("workflow") != template.get("workflow_id"):
            manifest_errors.append(
                f"Manifest workflow '{manifest.get('workflow')}' != template workflow_id '{template.get('workflow_id')}'"
            )
        if manifest.get("template_id") != tid:
            manifest_errors.append(f"Manifest template_id '{manifest.get('template_id')}' != template id '{tid}'")

    # Inventory: same set (order checked separately)
    expected_set = set(expected)
    actual_set = set(actual)
    missing = expected_set - actual_set
    extra = actual_set - expected_set
    if missing:
        errors.append(f"Missing artifacts: {sorted(missing)}")
    if extra:
        errors.append(f"Unexpected artifacts: {sorted(extra)}")

    # Order: expected list must match actual when restricted to expected artifacts
    if not errors and actual:
        expected_order = [a for a in expected if a in actual_set]
        actual_order = [a for a in actual if a in expected_set]
        if expected_order != actual_order:
            errors.append(
                f"Artifact order mismatch: expected order {expected_order}, got {actual_order}"
            )

    passed = len(errors) == 0 and len(manifest_errors) == 0
    return HarnessResult(
        passed=passed,
        template_id=tid,
        expected_artifacts=expected,
        actual_artifacts=actual,
        errors=errors,
        manifest_errors=manifest_errors,
    )


def run_template_harness(
    template_id: str,
    workspace_path: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> HarnessResult:
    """
    Run harness for a template: if workspace_path given, validate it; else only load template
    and return expected artifact list (no workspace validation).
    """
    root = _root(repo_root)
    if workspace_path is not None:
        return validate_workspace_against_template(
            workspace_path, template_id, repo_root=root
        )
    # No workspace: just validate template loads and return expected list
    try:
        template = load_template(template_id.strip(), repo_root=root)
        expected = expected_artifact_list_for_template(template)
        return HarnessResult(
            passed=True,
            template_id=template.get("id", template_id),
            expected_artifacts=expected,
            actual_artifacts=[],
        )
    except FileNotFoundError:
        return HarnessResult(
            passed=False,
            template_id=template_id.strip(),
            errors=[f"Template not found: {template_id}"],
        )
    except Exception as e:
        return HarnessResult(
            passed=False,
            template_id=template_id.strip(),
            errors=[f"Template load failed: {e}"],
        )
