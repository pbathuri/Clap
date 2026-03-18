"""M23T: Runtime mesh — backend registry, model catalog, integration registry, policy, mission-control visibility."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.runtime_mesh.backend_registry import (
    load_backend_registry,
    list_backend_profiles,
    get_backend_profile,
    get_backend_status,
    BackendProfile,
)
from workflow_dataset.runtime_mesh.model_catalog import (
    load_model_catalog,
    list_models_by_capability,
    get_model_info,
    ModelEntry,
)
from workflow_dataset.runtime_mesh.integration_registry import (
    load_integration_registry,
    list_integrations,
    get_integration,
    set_integration_enabled,
)
from workflow_dataset.runtime_mesh.policy import (
    recommend_for_task_class,
    recommend_backend_for_task,
    compatibility_for_model,
    TASK_CLASSES,
)


def test_backend_registry_returns_profiles(tmp_path):
    """load_backend_registry returns list of BackendProfile with expected ids."""
    profiles = load_backend_registry(tmp_path)
    assert isinstance(profiles, list)
    ids = [p.backend_id for p in profiles]
    assert "repo_local" in ids
    assert "ollama" in ids
    assert "llama_cpp" in ids
    for p in profiles:
        assert isinstance(p, BackendProfile)
        assert p.backend_id
        assert p.status in ("available", "configured", "missing", "unsupported")


def test_get_backend_profile(tmp_path):
    """get_backend_profile returns profile for known id, None for unknown."""
    assert get_backend_profile("ollama", tmp_path) is not None
    assert get_backend_profile("repo_local", tmp_path).backend_id == "repo_local"
    assert get_backend_profile("nonexistent", tmp_path) is None


def test_get_backend_status(tmp_path):
    """get_backend_status returns a status string."""
    s = get_backend_status("ollama", tmp_path)
    assert s in ("available", "configured", "missing", "unsupported")
    assert get_backend_status("nonexistent", tmp_path) == "unsupported"


def test_catalog_load(tmp_path):
    """load_model_catalog returns list of ModelEntry with seed entries."""
    catalog = load_model_catalog(tmp_path)
    assert isinstance(catalog, list)
    assert len(catalog) >= 1
    for m in catalog:
        assert isinstance(m, ModelEntry)
        assert m.model_id
    ids = [m.model_id for m in catalog]
    assert "local/small" in ids or "llama3.2" in ids


def test_list_models_by_capability(tmp_path):
    """list_models_by_capability filters by capability class."""
    coding = list_models_by_capability("coding_agentic_coding", tmp_path)
    assert isinstance(coding, list)
    for m in coding:
        assert "coding_agentic_coding" in m.capability_classes


def test_get_model_info(tmp_path):
    """get_model_info returns entry for known model, None for unknown."""
    info = get_model_info("local/small", tmp_path)
    if info:
        assert info.model_id == "local/small"
    assert get_model_info("nonexistent_model_xyz", tmp_path) is None


def test_integration_registry_load(tmp_path):
    """load_integration_registry returns list of IntegrationManifest."""
    reg = load_integration_registry(tmp_path)
    assert isinstance(reg, list)
    assert any(i.integration_id == "openclaw" for i in reg)


def test_get_integration(tmp_path):
    """get_integration returns manifest for known id."""
    openclaw = get_integration("openclaw", tmp_path)
    assert openclaw is not None
    assert openclaw.integration_id == "openclaw"
    assert get_integration("nonexistent", tmp_path) is None


def test_set_integration_enabled(tmp_path):
    """M24D: set_integration_enabled toggles enabled and persists to file."""
    ok = set_integration_enabled("openclaw", True, tmp_path)
    assert ok is True
    m = get_integration("openclaw", tmp_path)
    assert m is not None
    assert m.enabled is True
    ok2 = set_integration_enabled("openclaw", False, tmp_path)
    assert ok2 is True
    m2 = get_integration("openclaw", tmp_path)
    assert m2 is not None
    assert m2.enabled is False
    assert set_integration_enabled("nonexistent", True, tmp_path) is False


def test_recommend_for_task_class(tmp_path):
    """recommend_for_task_class returns backend_id, model_class, missing, reason."""
    rec = recommend_for_task_class("desktop_copilot", tmp_path)
    assert "task_class" in rec
    assert rec["task_class"] == "desktop_copilot"
    assert "model_class" in rec
    assert "model_ids" in rec
    assert "missing" in rec
    assert "reason" in rec
    assert "backend_id" in rec
    assert "integrations_available" in rec


def test_recommend_unknown_task_class(tmp_path):
    """Unknown task_class returns missing and no backend."""
    rec = recommend_for_task_class("unknown_task_xyz", tmp_path)
    assert rec["task_class"] == "unknown_task_xyz"
    assert rec.get("backend_id") is None
    assert "Unknown" in str(rec.get("missing", []))


def test_recommend_backend_for_task(tmp_path):
    """recommend_backend_for_task returns backend_id or None."""
    bid = recommend_backend_for_task("codebase_task", tmp_path)
    assert bid is None or bid in ("ollama", "repo_local", "llama_cpp")


def test_compatibility_for_model_in_catalog(tmp_path):
    """compatibility_for_model returns in_catalog True and suitable_task_classes for known model."""
    report = compatibility_for_model("local/small", tmp_path)
    if report.get("in_catalog"):
        assert "suitable_task_classes" in report
        assert "backend_family" in report


def test_compatibility_for_model_not_in_catalog(tmp_path):
    """compatibility_for_model returns in_catalog False for unknown model."""
    report = compatibility_for_model("nonexistent_model_abc", tmp_path)
    assert report["in_catalog"] is False
    assert "model_id" in report
    assert report["model_id"] == "nonexistent_model_abc"


def test_mission_control_includes_runtime_mesh(tmp_path):
    """get_mission_control_state includes runtime_mesh section when runtime_mesh loads."""
    from workflow_dataset.mission_control.state import get_mission_control_state
    state = get_mission_control_state(tmp_path)
    assert "runtime_mesh" in state
    rm = state["runtime_mesh"]
    if "error" not in rm:
        assert "available_backends" in rm
        assert "missing_runtimes" in rm
        assert "integrations_count" in rm
        assert "runtime_validation_passed" in rm
        assert "llama_cpp_status" in rm


# ----- M23S Runtime manager: summary, validate, llama-cpp-check -----
def test_build_runtime_summary(tmp_path):
    """build_runtime_summary returns backends, task_class_dependencies, available/missing ids."""
    from workflow_dataset.runtime_mesh.summary import build_runtime_summary
    summary = build_runtime_summary(tmp_path)
    assert "backends" in summary
    assert "task_class_dependencies" in summary
    assert "available_backend_ids" in summary
    assert "missing_backend_ids" in summary
    assert "backend_count" in summary
    assert len(summary["backends"]) >= 2
    assert any(d["task_class"] == "desktop_copilot" for d in summary["task_class_dependencies"])


def test_format_runtime_summary(tmp_path):
    """format_runtime_summary produces string with Backends and Product surfaces."""
    from workflow_dataset.runtime_mesh.summary import format_runtime_summary
    report = format_runtime_summary(repo_root=tmp_path)
    assert "Runtime summary" in report
    assert "Backends" in report
    assert "Product surfaces" in report or "task classes" in report.lower()


def test_run_runtime_validate(tmp_path):
    """run_runtime_validate returns passed, task_class_results, model_results, summary."""
    from workflow_dataset.runtime_mesh.validate import run_runtime_validate
    result = run_runtime_validate(tmp_path, include_models=False)
    assert "passed" in result
    assert "task_class_results" in result
    assert "summary" in result
    assert isinstance(result["task_class_results"], list)
    assert any(r.get("task_class") == "desktop_copilot" for r in result["task_class_results"])


def test_format_validation_report(tmp_path):
    """format_validation_report produces Task class and optional Model sections."""
    from workflow_dataset.runtime_mesh.validate import run_runtime_validate, format_validation_report
    result = run_runtime_validate(tmp_path, include_models=True)
    report = format_validation_report(result)
    assert "Runtime compatibility" in report or "compatibility" in report.lower()
    assert "Task class" in report
    assert "Backend-agnostic" in report or "optional" in report.lower()


def test_llama_cpp_check(tmp_path):
    """llama_cpp_check returns available, status, message; no mandatory requirement."""
    from workflow_dataset.runtime_mesh.llama_cpp_check import llama_cpp_check
    result = llama_cpp_check(tmp_path)
    assert "available" in result
    assert result["status"] in ("available", "optional")
    assert "message" in result
    assert "optional" in result["message"].lower() or "llama" in result["message"].lower()


def test_format_llama_cpp_check_report(tmp_path):
    """format_llama_cpp_check_report produces optional/local runtime message."""
    from workflow_dataset.runtime_mesh.llama_cpp_check import llama_cpp_check, format_llama_cpp_check_report
    result = llama_cpp_check(tmp_path)
    report = format_llama_cpp_check_report(result)
    assert "llama" in report.lower()
    assert "Optional" in report or "optional" in report.lower()
