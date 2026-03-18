"""M25I–M25L: Tests for pack authoring — scaffold, validation, certification, scorecard."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.packs.scaffold import scaffold_pack, manifest_skeleton
from workflow_dataset.packs.authoring_validation import (
    validate_pack_structure,
    validate_pack_full,
    conflict_risk_indicators,
)
from workflow_dataset.packs.certification import (
    run_certification,
    format_certification_report,
    CERT_STATUS_DRAFT,
    CERT_STATUS_VALID,
    CERT_STATUS_CERTIFIABLE,
    CERT_STATUS_NEEDS_REVISION,
)
from workflow_dataset.packs.scorecard import build_pack_scorecard, format_pack_scorecard
from workflow_dataset.packs.gallery import (
    build_gallery_entry,
    build_gallery,
    format_showcase,
    format_gallery_report,
)


def test_manifest_skeleton() -> None:
    s = manifest_skeleton("analyst_plus")
    assert s["pack_id"] == "analyst_plus"
    assert s["name"] == "Analyst Plus"
    assert s["version"] == "0.1.0"
    assert s["safety_policies"]["sandbox_only"] is True


def test_scaffold_pack(tmp_path: Path) -> None:
    out = scaffold_pack("logistics_ops_plus", packs_dir=tmp_path)
    assert out == tmp_path / "logistics_ops_plus"
    assert (out / "manifest.json").exists()
    assert (out / "prompts").is_dir()
    assert (out / "tasks").is_dir()
    assert (out / "demos").is_dir()
    assert (out / "docs").is_dir()
    assert (out / "tests").is_dir()
    assert (out / "docs" / "README.md").exists()
    data = __import__("json").loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert data["pack_id"] == "logistics_ops_plus"
    # M25I extended scaffold: prompt skeletons, demos README, task defaults skel, test placeholder
    assert (out / "prompts" / "system_guidance.md").exists()
    assert (out / "prompts" / "task_prompt.md").exists()
    assert (out / "demos" / "README.md").exists()
    assert (out / "tasks" / "workflow_defaults.json.skel").exists()
    smoke = list((out / "tests").glob("test_*_smoke.py.skel"))
    assert len(smoke) == 1
    assert "logistics_ops_plus" in smoke[0].name or "logistics_ops_plus" in smoke[0].read_text()


def test_validate_pack_structure_scaffolded(tmp_path: Path) -> None:
    scaffold_pack("analyst_plus", packs_dir=tmp_path)
    valid, errors, warnings = validate_pack_structure(pack_id="analyst_plus", packs_dir=tmp_path)
    assert valid is True
    assert len(errors) == 0
    # May have warnings for role_tags/workflow_tags
    assert isinstance(warnings, list)


def test_validate_pack_structure_strict(tmp_path: Path) -> None:
    pack_dir = tmp_path / "no_docs_pack"
    pack_dir.mkdir()
    (pack_dir / "manifest.json").write_text(
        __import__("json").dumps({
            "pack_id": "no_docs_pack",
            "name": "No Docs",
            "version": "0.1.0",
            "safety_policies": {"sandbox_only": True, "require_apply_confirm": True, "no_network_default": True},
        }),
        encoding="utf-8",
    )
    (pack_dir / "prompts").mkdir()
    valid, errors, warnings = validate_pack_structure(pack_id="no_docs_pack", packs_dir=tmp_path, strict=True)
    assert valid is False
    assert any("docs" in e.lower() for e in errors)


def test_validate_pack_full(tmp_path: Path) -> None:
    scaffold_pack("founder_ops_plus_v2", packs_dir=tmp_path)
    full = validate_pack_full(pack_id="founder_ops_plus_v2", packs_dir=tmp_path)
    assert full["valid"] is True
    assert "pack_id" in full
    assert "warnings" in full or "errors" in full


def test_conflict_risk_indicators(tmp_path: Path) -> None:
    scaffold_pack("x", packs_dir=tmp_path)
    risks = conflict_risk_indicators("x", packs_dir=tmp_path)
    assert isinstance(risks, list)


def test_run_certification_scaffolded(tmp_path: Path) -> None:
    scaffold_pack("cert_test", packs_dir=tmp_path)
    cert = run_certification("cert_test", packs_dir=tmp_path)
    assert cert["pack_id"] == "cert_test"
    assert cert["status"] in (
        CERT_STATUS_DRAFT,
        CERT_STATUS_VALID,
        CERT_STATUS_NEEDS_REVISION,
        CERT_STATUS_CERTIFIABLE,
    )
    assert "checks" in cert
    assert any(c["name"] == "structural" for c in cert["checks"])


def test_run_certification_with_templates(tmp_path: Path) -> None:
    scaffold_pack("with_templates", packs_dir=tmp_path)
    manifest_path = tmp_path / "with_templates" / "manifest.json"
    data = __import__("json").loads(manifest_path.read_text(encoding="utf-8"))
    data["templates"] = ["weekly_status", "ops_report"]
    data["role_tags"] = ["ops"]
    manifest_path.write_text(__import__("json").dumps(data, indent=2), encoding="utf-8")
    cert = run_certification("with_templates", packs_dir=tmp_path)
    assert cert["status"] in (CERT_STATUS_VALID, CERT_STATUS_CERTIFIABLE)
    assert any(c["name"] == "acceptance_scenario_compatibility" for c in cert["checks"])
    assert any(c["name"] == "trust_readiness_signals" for c in cert["checks"])


def test_format_certification_report(tmp_path: Path) -> None:
    scaffold_pack("report_pack", packs_dir=tmp_path)
    cert = run_certification("report_pack", packs_dir=tmp_path)
    text = format_certification_report(cert)
    assert "Pack certification" in text
    assert "report_pack" in text
    assert "Status:" in text
    assert "Checks" in text or "checks" in text.lower()


def test_build_pack_scorecard(tmp_path: Path) -> None:
    scaffold_pack("scorecard_test", packs_dir=tmp_path)
    sc = build_pack_scorecard("scorecard_test", packs_dir=tmp_path)
    assert sc["pack_id"] == "scorecard_test"
    assert "roles_supported" in sc
    assert "certification_status" in sc
    assert "recommended_fixes" in sc


def test_format_pack_scorecard(tmp_path: Path) -> None:
    scaffold_pack("fmt_test", packs_dir=tmp_path)
    text = format_pack_scorecard("fmt_test", packs_dir=tmp_path)
    assert "Pack scorecard" in text
    assert "Certification status" in text
    assert "Recommended fixes" in text


def test_blocked_invalid_pack_missing_manifest(tmp_path: Path) -> None:
    full = validate_pack_full(pack_id="nonexistent_pack_xyz", packs_dir=tmp_path)
    assert full["valid"] is False
    assert len(full["errors"]) >= 1


def test_build_gallery_entry(tmp_path: Path) -> None:
    scaffold_pack("gallery_test", packs_dir=tmp_path)
    entry = build_gallery_entry("gallery_test", packs_dir=tmp_path)
    assert entry["pack_id"] == "gallery_test"
    assert "name" in entry
    assert "version" in entry
    assert entry.get("name") == "Gallery Test"
    assert entry.get("version") == "0.1.0"
    assert "purpose" in entry
    assert "roles_supported" in entry
    assert "first_value_flow" in entry
    assert "certification_status" in entry
    assert "readiness" in entry
    assert "demo_assets" in entry
    assert "recommended_install_path" in entry
    assert "workflow-dataset packs install" in entry["recommended_install_path"]


def test_build_gallery(tmp_path: Path) -> None:
    scaffold_pack("ga1", packs_dir=tmp_path)
    scaffold_pack("ga2", packs_dir=tmp_path)
    entries = build_gallery(packs_dir=tmp_path)
    assert len(entries) >= 2
    ids = [e["pack_id"] for e in entries]
    assert "ga1" in ids
    assert "ga2" in ids


def test_format_showcase(tmp_path: Path) -> None:
    scaffold_pack("showcase_pack", packs_dir=tmp_path)
    text = format_showcase("showcase_pack", packs_dir=tmp_path)
    assert "Certified pack showcase" in text
    assert "[Name]" in text
    assert "Purpose" in text or "[Purpose]" in text
    assert "Roles supported" in text
    assert "First-value flow" in text
    assert "Certification status" in text
    assert "Recommended install" in text
    assert "Demo assets" in text or "demo" in text.lower()


def test_format_gallery_report(tmp_path: Path) -> None:
    scaffold_pack("gr1", packs_dir=tmp_path)
    report = format_gallery_report(packs_dir=tmp_path)
    assert "Pack demo gallery" in report
    assert "gr1" in report
