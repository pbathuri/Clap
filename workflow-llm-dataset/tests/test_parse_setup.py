"""Tests for parse layer: artifact classification, domain detection, style extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.parse.artifact_classifier import classify_artifact, is_supported_for_parsing
from workflow_dataset.setup.setup_models import ArtifactFamily
from workflow_dataset.parse.domain_detector import detect_domains_from_path, merge_domains
from workflow_dataset.parse.document_router import route_and_parse_file
from workflow_dataset.parse.document_models import ExtractionPolicy
from workflow_dataset.parse.style_extractor import extract_naming_conventions, extract_folder_layout_style
from workflow_dataset.parse.adapters import get_adapters
from workflow_dataset.parse.document_models import ParsedDocument


def test_classify_artifact_families(tmp_path: Path) -> None:
    assert classify_artifact(Path("x.txt")) == ArtifactFamily.TEXT_DOCUMENT
    assert classify_artifact(Path("x.csv")) == ArtifactFamily.SPREADSHEET_TABLE
    assert classify_artifact(Path("x.png")) == ArtifactFamily.IMAGE_ASSET
    (tmp_path / "folder").mkdir()
    assert classify_artifact(tmp_path / "folder") == ArtifactFamily.PROJECT_DIRECTORY


def test_is_supported_for_parsing() -> None:
    assert is_supported_for_parsing(Path("a.txt")) is True
    assert is_supported_for_parsing(Path("a.md")) is True
    assert is_supported_for_parsing(Path("a.csv")) is True
    assert is_supported_for_parsing(Path("a.xlsx")) is True
    assert is_supported_for_parsing(Path("a.xyz")) is False


def test_domain_detection_from_path() -> None:
    domains = detect_domains_from_path(Path("/projects/invoice_2024.xlsx"))
    assert any(d.domain_id == "finance" for d in domains)
    domains2 = detect_domains_from_path(Path("/design/figma_export"))
    assert any(d.domain_id in ("creative", "design") for d in domains2)


def test_merge_domains() -> None:
    from workflow_dataset.setup.setup_models import DiscoveredDomain
    a = [DiscoveredDomain(domain_id="creative", label="Creative", confidence=0.6, evidence_count=1)]
    b = [DiscoveredDomain(domain_id="creative", label="Creative", confidence=0.5, evidence_count=2)]
    merged = merge_domains([a, b])
    assert len(merged) == 1
    assert merged[0].evidence_count == 3


def test_route_and_parse_txt(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("Hello world\nThis is a test.")
    doc = route_and_parse_file(f, policy=ExtractionPolicy.SIGNALS_AND_SUMMARIES)
    assert doc.source_path
    assert doc.artifact_family == "text_document"
    assert "Hello" in doc.summary or "Hello" in (doc.raw_text_snippet or "")


def test_adapters_emit_signals() -> None:
    adapters = get_adapters()
    assert len(adapters) >= 4
    doc = ParsedDocument(source_path="/x/invoice_q1.csv", artifact_family="spreadsheet_table", tables=[])
    tabular = next(a for a in adapters if a.name == "tabular")
    assert tabular.can_handle(doc)
    signals = tabular.process(doc)
    assert isinstance(signals, list)


def test_style_extract_naming(tmp_path: Path) -> None:
    (tmp_path / "file_v1.txt").write_text("")
    (tmp_path / "file_v2.txt").write_text("")
    paths = list(tmp_path.iterdir())
    patterns = extract_naming_conventions(paths)
    assert isinstance(patterns, list)


def test_media_metadata_extract(tmp_path: Path) -> None:
    from workflow_dataset.parse.media_metadata import extract_media_metadata
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    meta = extract_media_metadata(tmp_path / "image.png", include_pixel_metadata=False)
    assert meta.path
    assert meta.extension == "png"
    assert meta.size_bytes >= 0
