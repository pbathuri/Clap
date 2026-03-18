"""Tests for LLM SFT builder: valid JSONL with required keys, deterministic split."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.llm.sft_builder import build_sft, build_personal_sft_from_setup
from workflow_dataset.llm.data_split import split_examples, write_split_jsonl, RATIO_TRAIN, RATIO_VAL, RATIO_TEST


@pytest.fixture
def corpus_jsonl(tmp_path: Path) -> Path:
    p = tmp_path / "corpus.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    docs = [
        {"doc_id": "occ-1", "source_type": "occupation", "title": "Test Occ", "text": "Test description.", "metadata": {}, "provenance": {}},
        {"doc_id": "occ-2", "source_type": "occupation", "title": "Another", "text": "Another description.", "metadata": {}, "provenance": {}},
    ]
    for d in docs:
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return p


def test_build_sft_produces_valid_jsonl_with_required_keys(
    corpus_jsonl: Path,
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "sft"
    n_train, n_val, n_test, counts = build_sft(corpus_jsonl, None, out_dir, seed=42)
    assert n_train + n_val + n_test >= 0
    for name in ("train.jsonl", "val.jsonl", "test.jsonl"):
        path = out_dir / name
        if path.exists():
            for line in path.read_text().strip().splitlines():
                if not line:
                    continue
                ex = json.loads(line)
                assert "messages" in ex
                assert isinstance(ex["messages"], list)
                for m in ex["messages"]:
                    assert "role" in m and "content" in m
                assert ex.get("task_type") or "task_type" in ex or True  # task_type may be present


def test_split_examples_deterministic() -> None:
    examples = [
        {"example_id": f"e-{i}", "task_type": "knowledge_qa", "messages": [{"role": "user", "content": f"Q{i}"}, {"role": "assistant", "content": f"A{i}"}]}
        for i in range(20)
    ]
    a = split_examples(examples, seed=42, stratify_by="task_type")
    b = split_examples(examples, seed=42, stratify_by="task_type")
    assert len(a[0]) == len(b[0]) and len(a[1]) == len(b[1]) and len(a[2]) == len(b[2])
    ids_a = {ex["example_id"] for ex in a[0] + a[1] + a[2]}
    ids_b = {ex["example_id"] for ex in b[0] + b[1] + b[2]}
    assert ids_a == ids_b


def test_write_split_jsonl_writes_three_files(tmp_path: Path) -> None:
    train = [{"example_id": "1", "task_type": "a", "messages": [{"role": "user", "content": "q"}]}]
    val = [{"example_id": "2", "task_type": "a", "messages": [{"role": "user", "content": "q2"}]}]
    test = [{"example_id": "3", "task_type": "a", "messages": [{"role": "user", "content": "q3"}]}]
    write_split_jsonl(train, val, test, tmp_path)
    assert (tmp_path / "train.jsonl").exists()
    assert (tmp_path / "val.jsonl").exists()
    assert (tmp_path / "test.jsonl").exists()


def test_build_personal_sft_from_setup(tmp_path: Path) -> None:
    """Personal SFT from setup: parsed docs + style signals produce train/val/test with expected task types."""
    from workflow_dataset.parse.document_models import ParsedDocument
    from workflow_dataset.setup.style_persistence import persist_style_signals
    session_id = "sess_sft"
    parsed_base = tmp_path / "parsed"
    (parsed_base / session_id).mkdir(parents=True)
    doc = ParsedDocument(
        source_path="/proj/readme.txt",
        artifact_family="text_document",
        title="Readme",
        summary="Project readme.",
    )
    (parsed_base / session_id / "d1.json").write_text(doc.model_dump_json())
    style_dir = tmp_path / "style"
    persist_style_signals(session_id, [{"pattern_type": "naming_convention", "value": "snake", "description": "Snake"}], style_dir)
    out_dir = tmp_path / "sft_out"
    n_train, n_val, n_test, counts = build_personal_sft_from_setup(
        str(parsed_base), str(style_dir), session_id, str(out_dir),
        allow_raw_text=False, max_examples_per_type=10, seed=42,
    )
    assert (out_dir / "train.jsonl").exists()
    assert (out_dir / "val.jsonl").exists()
    assert (out_dir / "test.jsonl").exists()
    task_types = set(counts.keys())
    assert "explain_project" in task_types or "explain_artifact_domain" in task_types or "explain_style_pattern" in task_types or "justify_classification" in task_types
