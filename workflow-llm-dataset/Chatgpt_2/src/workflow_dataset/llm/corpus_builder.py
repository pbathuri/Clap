"""
Build domain-adaptation corpus from global work priors (processed parquet).

Converts industries, occupations, tasks, DWAs, workflow steps, tools, etc.
into structured natural-language documents. Deterministic formatting;
provenance preserved. No raw table dumps.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.llm.schemas import CorpusDocument
from workflow_dataset.utils.hashes import stable_id

PROCESSED_TABLES = [
    "industries",
    "occupations",
    "tasks",
    "detailed_work_activities",
    "workflow_steps",
    "tools_and_technology",
    "work_context",
    "skills_knowledge_abilities",
    "industry_occupation_map",
    "labor_market",
]

MAX_DOC_CHARS = 8000
CHUNK_OVERLAP = 200


def _read_table(processed: Path, stem: str) -> pd.DataFrame | None:
    p = processed / f"{stem}.parquet"
    if not p.exists():
        return None
    try:
        return pd.read_parquet(p)
    except Exception:
        return None


def _safe_str(v: Any, max_len: int = 500) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    return s[:max_len] if len(s) > max_len else s


def _occupation_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        oid = _safe_str(r.get("occupation_id", ""), 200)
        title = _safe_str(r.get("title", ""), 300)
        desc = _safe_str(r.get("description", ""), 2000)
        code = _safe_str(r.get("occupation_code", ""), 50)
        taxonomy = _safe_str(r.get("taxonomy_system", ""), 50)
        text_parts = [f"Occupation: {title}"]
        if code:
            text_parts.append(f"Code: {code} ({taxonomy})")
        if desc:
            text_parts.append(f"Description: {desc}")
        text = "\n".join(text_parts)
        doc_id = stable_id("corpus", "occupation", oid, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="occupation",
            title=title or oid,
            text=text,
            metadata={"occupation_id": oid, "occupation_code": code},
            provenance={"table": "occupations", "occupation_id": oid, "source_id": _safe_str(r.get("source_id", ""))},
        ))
    return docs


def _industry_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        iid = _safe_str(r.get("industry_id", ""), 200)
        title = _safe_str(r.get("title", ""), 300)
        desc = _safe_str(r.get("description", ""), 1500)
        taxonomy = _safe_str(r.get("taxonomy_system", ""), 50)
        text_parts = [f"Industry: {title} ({taxonomy})"]
        if desc:
            text_parts.append(desc)
        text = "\n".join(text_parts)
        doc_id = stable_id("corpus", "industry", iid, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="industry",
            title=title or iid,
            text=text,
            metadata={"industry_id": iid},
            provenance={"table": "industries", "industry_id": iid},
        ))
    return docs


def _task_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        tid = _safe_str(r.get("task_id", ""), 200)
        occ_id = _safe_str(r.get("occupation_id", ""), 200)
        task_text = _safe_str(r.get("task_text", ""), 1500)
        task_type = _safe_str(r.get("task_type", ""), 50)
        text = f"Task ({task_type}): {task_text}\nOccupation ID: {occ_id}"
        doc_id = stable_id("corpus", "task", tid, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="task",
            title=task_text[:80] + ("..." if len(task_text) > 80 else ""),
            text=text,
            metadata={"task_id": tid, "occupation_id": occ_id},
            provenance={"table": "tasks", "task_id": tid},
        ))
    return docs


def _dwa_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        dwa_id = _safe_str(r.get("dwa_id", ""), 200)
        title = _safe_str(r.get("dwa_title", ""), 500)
        occ_id = _safe_str(r.get("occupation_id", ""), 200)
        code = _safe_str(r.get("dwa_code", ""), 50)
        text = f"Detailed work activity: {title}\nCode: {code}\nOccupation ID: {occ_id}"
        doc_id = stable_id("corpus", "dwa", dwa_id, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="detailed_work_activity",
            title=title[:80] + ("..." if len(title) > 80 else ""),
            text=text,
            metadata={"dwa_id": dwa_id, "occupation_id": occ_id},
            provenance={"table": "detailed_work_activities", "dwa_id": dwa_id},
        ))
    return docs


def _workflow_step_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        wid = _safe_str(r.get("workflow_step_id", ""), 200)
        occ_id = _safe_str(r.get("occupation_id", ""), 200)
        name = _safe_str(r.get("step_name", ""), 200)
        desc = _safe_str(r.get("step_description", ""), 1000)
        order = r.get("step_order")
        text = f"Workflow step {order}: {name}\n{desc}\nOccupation ID: {occ_id}"
        doc_id = stable_id("corpus", "workflow_step", wid, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="workflow_step",
            title=name or wid,
            text=text,
            metadata={"workflow_step_id": wid, "occupation_id": occ_id, "step_order": order},
            provenance={"table": "workflow_steps", "workflow_step_id": wid},
        ))
    return docs


def _tools_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        tool_id = _safe_str(r.get("tool_id", ""), 200)
        name = _safe_str(r.get("tool_name", ""), 300)
        tool_type = _safe_str(r.get("tool_type", ""), 100)
        occ_id = _safe_str(r.get("occupation_id", ""), 200)
        text = f"Tool/technology: {name} ({tool_type})\nOccupation ID: {occ_id}"
        doc_id = stable_id("corpus", "tool", tool_id, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="tool",
            title=name or tool_id,
            text=text,
            metadata={"tool_id": tool_id, "occupation_id": occ_id},
            provenance={"table": "tools_and_technology", "tool_id": tool_id},
        ))
    return docs


def _work_context_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        cid = _safe_str(r.get("context_id", ""), 200)
        title = _safe_str(r.get("context_title", ""), 300)
        value = _safe_str(r.get("context_value", ""), 200)
        occ_id = _safe_str(r.get("occupation_id", ""), 200)
        text = f"Work context: {title}\nValue: {value}\nOccupation ID: {occ_id}"
        doc_id = stable_id("corpus", "work_context", cid, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="work_context",
            title=title or cid,
            text=text,
            metadata={"context_id": cid, "occupation_id": occ_id},
            provenance={"table": "work_context", "context_id": cid},
        ))
    return docs


def _ska_docs(df: pd.DataFrame) -> list[CorpusDocument]:
    docs: list[CorpusDocument] = []
    for _, r in df.iterrows():
        ska_id = _safe_str(r.get("ska_id", ""), 200)
        dim_type = _safe_str(r.get("dimension_type", ""), 50)
        name = _safe_str(r.get("dimension_name", ""), 300)
        occ_id = _safe_str(r.get("occupation_id", ""), 200)
        text = f"Skill/Knowledge/Ability ({dim_type}): {name}\nOccupation ID: {occ_id}"
        doc_id = stable_id("corpus", "ska", ska_id, prefix="doc")
        docs.append(CorpusDocument(
            doc_id=doc_id,
            source_type="skills_knowledge_abilities",
            title=name or ska_id,
            text=text,
            metadata={"ska_id": ska_id, "occupation_id": occ_id, "dimension_type": dim_type},
            provenance={"table": "skills_knowledge_abilities", "ska_id": ska_id},
        ))
    return docs


def build_corpus(
    processed_dir: Path | str,
    output_path: Path | str,
    max_doc_chars: int = MAX_DOC_CHARS,
) -> tuple[int, dict[str, int]]:
    """
    Load processed parquet tables, build CorpusDocuments, write corpus.jsonl.
    Returns (total_docs, counts_by_source_type).
    """
    processed = Path(processed_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_docs: list[CorpusDocument] = []
    counts: dict[str, int] = {}

    if (df := _read_table(processed, "occupations")) is not None and not df.empty:
        docs = _occupation_docs(df)
        all_docs.extend(docs)
        counts["occupation"] = len(docs)
    if (df := _read_table(processed, "industries")) is not None and not df.empty:
        docs = _industry_docs(df)
        all_docs.extend(docs)
        counts["industry"] = len(docs)
    if (df := _read_table(processed, "tasks")) is not None and not df.empty:
        docs = _task_docs(df)
        all_docs.extend(docs)
        counts["task"] = len(docs)
    if (df := _read_table(processed, "detailed_work_activities")) is not None and not df.empty:
        docs = _dwa_docs(df)
        all_docs.extend(docs)
        counts["detailed_work_activity"] = len(docs)
    if (df := _read_table(processed, "workflow_steps")) is not None and not df.empty:
        docs = _workflow_step_docs(df)
        all_docs.extend(docs)
        counts["workflow_step"] = len(docs)
    if (df := _read_table(processed, "tools_and_technology")) is not None and not df.empty:
        docs = _tools_docs(df)
        all_docs.extend(docs)
        counts["tool"] = len(docs)
    if (df := _read_table(processed, "work_context")) is not None and not df.empty:
        docs = _work_context_docs(df)
        all_docs.extend(docs)
        counts["work_context"] = len(docs)
    if (df := _read_table(processed, "skills_knowledge_abilities")) is not None and not df.empty:
        docs = _ska_docs(df)
        all_docs.extend(docs)
        counts["skills_knowledge_abilities"] = len(docs)

    with open(output_path, "w", encoding="utf-8") as f:
        for doc in all_docs:
            f.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")

    return len(all_docs), counts


def chunk_document(doc: CorpusDocument, max_chars: int = MAX_DOC_CHARS, overlap: int = CHUNK_OVERLAP) -> list[CorpusDocument]:
    """Split a long document into bounded chunks for training. Preserves doc_id with chunk index."""
    if len(doc.text) <= max_chars:
        return [doc]
    chunks: list[CorpusDocument] = []
    start = 0
    idx = 0
    while start < len(doc.text):
        end = min(start + max_chars, len(doc.text))
        chunk_text = doc.text[start:end]
        chunk_id = f"{doc.doc_id}_chunk{idx}"
        chunks.append(CorpusDocument(
            doc_id=chunk_id,
            source_type=doc.source_type,
            title=doc.title,
            text=chunk_text,
            metadata={**doc.metadata, "chunk_index": idx, "parent_doc_id": doc.doc_id},
            provenance=doc.provenance,
        ))
        idx += 1
        if end >= len(doc.text):
            break
        # Advance by at least 1 so we never loop (overlap may be >= max_chars)
        step = min(overlap, max_chars - 1) if max_chars > 1 else 1
        start = end - step
    return chunks


def build_personal_corpus_from_setup(
    parsed_artifacts_dir: Path | str,
    output_path: Path | str,
    allow_raw_text: bool = False,
    max_docs: int = 0,
) -> tuple[int, dict[str, int]]:
    """
    Build corpus from setup parsed artifacts. When allow_raw_text is True, include
    raw_text_snippet in document text; otherwise summaries and signals only.
    Returns (total_docs, counts_by_source_type).
    """
    from workflow_dataset.parse.document_models import ParsedDocument
    parsed_dir = Path(parsed_artifacts_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    docs: list[CorpusDocument] = []
    for path in sorted(parsed_dir.glob("*.json")):
        if max_docs and len(docs) >= max_docs:
            break
        try:
            with open(path, "r", encoding="utf-8") as f:
                parsed = ParsedDocument.model_validate_json(f.read())
        except Exception:
            continue
        if parsed.error:
            continue
        text_parts = [f"Title: {parsed.title}", f"Summary: {parsed.summary}"]
        if allow_raw_text and parsed.raw_text_snippet:
            text_parts.append(f"Content:\n{parsed.raw_text_snippet}")
        text = "\n\n".join(text_parts).strip()
        doc_id = stable_id("personal", parsed.source_path, prefix="doc")
        doc = CorpusDocument(
            doc_id=doc_id,
            source_type="personal_" + parsed.artifact_family,
            title=parsed.title or Path(parsed.source_path).name,
            text=text,
            metadata={"source_path": parsed.source_path, "artifact_family": parsed.artifact_family},
            provenance={"source": "setup_parsed", "path": parsed.source_path},
        )
        docs.append(doc)
        fam = "personal_" + parsed.artifact_family
        counts[fam] = counts.get(fam, 0) + 1
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")
    return len(docs), counts


def build_personal_corpus_from_setup_full(
    parsed_artifacts_dir: Path | str,
    style_signals_dir: Path | str,
    session_id: str,
    output_dir: Path | str,
    allow_raw_text: bool = False,
    max_docs: int = 0,
    include_style_signals: bool = True,
    include_session_summary: bool = True,
) -> tuple[int, dict[str, int]]:
    """
    Build personal corpus from setup: parsed artifacts, style signals, session summary.
    Writes to output_dir (e.g. data/local/llm/personal_corpus/). Returns (total_docs, counts).
    """
    from workflow_dataset.parse.document_models import ParsedDocument
    from workflow_dataset.setup.style_persistence import load_style_signals

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "personal_corpus.jsonl"
    counts: dict[str, int] = {}
    docs: list[CorpusDocument] = []
    parsed_dir = Path(parsed_artifacts_dir) / session_id
    if parsed_dir.exists():
        for path in sorted(parsed_dir.glob("*.json")):
            if max_docs and len(docs) >= max_docs:
                break
            try:
                with open(path, "r", encoding="utf-8") as f:
                    parsed = ParsedDocument.model_validate_json(f.read())
            except Exception:
                continue
            if parsed.error:
                continue
            text_parts = [f"Title: {parsed.title}", f"Summary: {parsed.summary}"]
            if allow_raw_text and parsed.raw_text_snippet:
                text_parts.append(f"Content:\n{parsed.raw_text_snippet}")
            text = "\n\n".join(text_parts).strip()
            doc_id = stable_id("personal", parsed.source_path, prefix="doc")
            doc = CorpusDocument(
                doc_id=doc_id,
                source_type="personal_" + parsed.artifact_family,
                title=parsed.title or Path(parsed.source_path).name,
                text=text,
                metadata={"source_path": parsed.source_path, "artifact_family": parsed.artifact_family},
                provenance={"source": "setup_parsed", "path": parsed.source_path, "session_id": session_id},
            )
            docs.append(doc)
            fam = "personal_" + parsed.artifact_family
            counts[fam] = counts.get(fam, 0) + 1
    if include_style_signals:
        style_records = load_style_signals(session_id, style_signals_dir)
        for i, rec in enumerate(style_records):
            if max_docs and len(docs) >= max_docs:
                break
            text = f"Style pattern: {rec.pattern_type}\nDescription: {rec.description}\nValue: {rec.value}"
            if rec.evidence_paths:
                text += "\nEvidence paths: " + ", ".join(rec.evidence_paths[:10])
            doc_id = stable_id("personal_style", session_id, rec.pattern_type, str(i), prefix="doc")
            doc = CorpusDocument(
                doc_id=doc_id,
                source_type="personal_style_signature",
                title=rec.pattern_type,
                text=text,
                metadata={"session_id": session_id, "confidence": rec.confidence},
                provenance={"source": "setup_style", "session_id": session_id},
            )
            docs.append(doc)
            counts["personal_style_signature"] = counts.get("personal_style_signature", 0) + 1
    if include_session_summary and session_id:
        doc_id = stable_id("personal_summary", session_id, prefix="doc")
        doc = CorpusDocument(
            doc_id=doc_id,
            source_type="personal_session_summary",
            title=f"Onboarding session {session_id}",
            text=f"Setup session {session_id}. Artifact families and style signals were extracted. Use for retrieval and local fine-tuning.",
            metadata={"session_id": session_id},
            provenance={"source": "setup_summary", "session_id": session_id},
        )
        docs.append(doc)
        counts["personal_session_summary"] = counts.get("personal_session_summary", 0) + 1
    with open(out_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")
    return len(docs), counts


def build_personal_corpus_from_assistive(
    suggestions_dir: Path | str,
    draft_structures_dir: Path | str,
    output_dir: Path | str,
    max_docs: int = 0,
) -> tuple[int, dict[str, int]]:
    """
    Build corpus docs from assistive outputs (style-aware suggestions, draft structures).
    Use for retrieval and fine-tuning on explainable assistive reasoning.
    """
    from workflow_dataset.personal.style_suggestion_engine import load_style_aware_suggestions
    from workflow_dataset.personal.draft_structure_engine import load_draft_structures

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    docs: list[CorpusDocument] = []
    suggestions = load_style_aware_suggestions(suggestions_dir)
    for i, s in enumerate(suggestions):
        if max_docs and len(docs) >= max_docs:
            break
        text = f"Suggestion: {s.title}\nType: {s.suggestion_type}\nDescription: {s.description}\nRationale: {s.rationale}\nConfidence: {s.confidence_score}"
        if s.supporting_signals:
            text += "\nSignals: " + ", ".join(str(x)[:100] for x in s.supporting_signals[:10])
        doc_id = stable_id("assistive_sug", s.suggestion_id, prefix="doc")
        doc = CorpusDocument(
            doc_id=doc_id,
            source_type="personal_style_aware_suggestion",
            title=s.title,
            text=text,
            metadata={"suggestion_type": s.suggestion_type, "domain": s.domain},
            provenance={"source": "assistive", "suggestion_id": s.suggestion_id},
        )
        docs.append(doc)
        counts["personal_style_aware_suggestion"] = counts.get("personal_style_aware_suggestion", 0) + 1
    drafts = load_draft_structures(draft_structures_dir)
    for i, d in enumerate(drafts):
        if max_docs and len(docs) >= max_docs:
            break
        text = f"Draft structure: {d.title}\nType: {d.draft_type}\nDomain: {d.domain}\nOutline:\n{d.structure_outline}"
        if d.recommended_sections:
            text += "\nSections: " + ", ".join(d.recommended_sections)
        doc_id = stable_id("assistive_draft", d.draft_id, prefix="doc")
        doc = CorpusDocument(
            doc_id=doc_id,
            source_type="personal_draft_structure",
            title=d.title,
            text=text,
            metadata={"draft_type": d.draft_type, "domain": d.domain},
            provenance={"source": "assistive", "draft_id": d.draft_id},
        )
        docs.append(doc)
        counts["personal_draft_structure"] = counts.get("personal_draft_structure", 0) + 1
    out_path = output_dir / "personal_corpus_assistive.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")
    return len(docs), counts


def load_corpus(path: Path | str, limit: int = 0) -> list[CorpusDocument]:
    """Load corpus from JSONL. limit=0 means all."""
    path = Path(path)
    if not path.exists():
        return []
    docs: list[CorpusDocument] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(CorpusDocument.model_validate(json.loads(line)))
            if limit and len(docs) >= limit:
                break
    return docs
