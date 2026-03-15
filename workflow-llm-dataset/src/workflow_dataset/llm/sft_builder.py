"""
Build supervised fine-tuning (SFT) dataset from corpus, local graph, routines, and suggestions.

Produces instruction examples with system/user/assistant messages. Deterministic and grounded.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.llm.corpus_builder import load_corpus
from workflow_dataset.llm.schemas import CorpusDocument, SFTExample
from workflow_dataset.llm.data_split import split_examples, write_split_jsonl
from workflow_dataset.utils.hashes import stable_id

SYSTEM_GENERIC = "You are a helpful assistant that explains work roles, workflows, and project patterns based on observed data. Answer only from the provided context or stated observations. Do not fabricate facts."


def _load_suggestions_and_routines(graph_path: Path | str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load suggestions and ROUTINE nodes from graph store."""
    path = Path(graph_path)
    if not path.exists():
        return [], []
    conn = sqlite3.connect(str(path))
    try:
        from workflow_dataset.personal.graph_store import list_suggestions, list_nodes
        suggestions = list_suggestions(conn, status_filter=None, limit=200)
        routine_nodes = list_nodes(conn, node_type="routine", limit=500)
        routines = []
        for n in routine_nodes:
            attrs = n.get("attributes", {})
            routines.append({
                "routine_id": n.get("node_id"),
                "routine_type": attrs.get("routine_type", ""),
                "label": n.get("label", ""),
                "touch_count": attrs.get("touch_count", 0),
                "project": attrs.get("project", ""),
                "path": attrs.get("path", ""),
                "extensions": attrs.get("extensions", []),
                "supporting_signals": attrs.get("supporting_signals", []),
            })
        return suggestions, routines
    finally:
        conn.close()


def _knowledge_qa_examples(docs: list[CorpusDocument], max_per_type: int = 50) -> list[dict[str, Any]]:
    """Occupation / workflow knowledge QA from corpus."""
    examples = []
    for doc in docs:
        if doc.source_type == "occupation" and "Occupation:" in doc.text:
            user = "Explain what this occupation typically does based on the available workflow priors."
            ctx = doc.text[:1500]
            assistant = f"Based on the priors:\n\n{ctx}\n\nThis occupation involves the tasks and context described above."
            ex_id = stable_id("sft", "knowledge_qa", doc.doc_id, prefix="ex")
            examples.append({
                "example_id": ex_id,
                "task_type": "knowledge_qa",
                "messages": [
                    {"role": "system", "content": SYSTEM_GENERIC},
                    {"role": "user", "content": user + "\n\nContext:\n" + ctx},
                    {"role": "assistant", "content": assistant},
                ],
                "metadata": {"source_type": doc.source_type, "doc_id": doc.doc_id},
                "provenance": doc.provenance,
            })
            if len(examples) >= max_per_type:
                break
    return examples


def _workflow_inference_examples(docs: list[CorpusDocument], max_ex: int = 30) -> list[dict[str, Any]]:
    """Workflow inference: map extensions/context to workflow type."""
    tool_docs = [d for d in docs if d.source_type == "tool"]
    if not tool_docs:
        return []
    examples = []
    for doc in tool_docs[:max_ex]:
        user = "A user repeatedly opens .csv and .xlsx files in a project. What kind of workflow might this be?"
        assistant = "This pattern often corresponds to an operations or data workflow: spreadsheet and CSV files are commonly used for inventory, dispatch, reporting, and reconciliation. Based on the tools and technologies associated with similar roles in the priors, such workflows typically involve data entry, analysis, and handoffs."
        ex_id = stable_id("sft", "workflow_inference", doc.doc_id, prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "workflow_inference",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"doc_id": doc.doc_id},
            "provenance": doc.provenance,
        })
    return examples


def _routine_interpretation_examples(routines: list[dict[str, Any]], max_ex: int = 40) -> list[dict[str, Any]]:
    """Routine interpretation: explain observed work pattern."""
    examples = []
    for r in routines[:max_ex]:
        label = r.get("label", "")
        project = r.get("project", "")
        path = r.get("path", "")
        signals = r.get("supporting_signals", [])
        user = "What does this observed work pattern indicate?"
        assistant = f"The pattern: {label}"
        if project:
            assistant += f" It relates to project or folder '{project}'."
        if signals:
            assistant += " Supporting signals: " + "; ".join(str(s) for s in signals[:5]) + "."
        assistant += " This was inferred from file and folder metadata only; no file content was read."
        ex_id = stable_id("sft", "routine_interpretation", r.get("routine_id", ""), prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "routine_interpretation",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user + "\n\nObserved pattern: " + label},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"routine_type": r.get("routine_type"), "project": project, "path": path},
            "provenance": {},
        })
    return examples


def _suggestion_explanation_examples(suggestions: list[dict[str, Any]], max_ex: int = 30) -> list[dict[str, Any]]:
    """Why did the agent suggest this? Explain from signals."""
    examples = []
    for s in suggestions[:max_ex]:
        title = s.get("title", "")
        desc = s.get("description", "")
        sigs = s.get("supporting_signals", [])
        user = f"Why did the agent suggest: {title}?"
        assistant = desc
        if sigs:
            assistant += " Evidence: " + "; ".join(str(x) for x in sigs[:5]) + "."
        ex_id = stable_id("sft", "suggestion_explanation", s.get("suggestion_id", ""), prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "suggestion_justification",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"suggestion_type": s.get("suggestion_type")},
            "provenance": {},
        })
    return examples


def _next_step_examples(routines: list[dict[str, Any]], max_ex: int = 20) -> list[dict[str, Any]]:
    """Next-step suggestion based on routine and context."""
    examples = []
    for r in routines[:max_ex]:
        label = r.get("label", "")
        project = r.get("project", "")
        user = "Based on the observed routine and current project context, what is a sensible next step?"
        assistant = f"Given the pattern '{label}'"
        if project:
            assistant += f" and project '{project}'"
        assistant += ", a sensible next step could be to continue work in this project or to review recent files. The agent does not execute any action without explicit user approval; it only suggests."
        ex_id = stable_id("sft", "next_step", r.get("routine_id", ""), prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "next_step_suggestion",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user + "\n\nRoutine: " + label},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {},
            "provenance": {},
        })
    return examples


def _safety_boundary_examples(max_ex: int = 15) -> list[dict[str, Any]]:
    """Safety: simulate-first and approval boundaries."""
    user = "Should the agent directly execute this action on the user's machine?"
    assistant = "No. The agent defaults to simulate mode: it may propose actions but must not change the user's real system unless the user has explicitly approved execution (assist or automate mode) and the action is within configured approval boundaries. When in doubt, the agent should only suggest and not execute."
    examples = []
    for i in range(max_ex):
        ex_id = stable_id("sft", "safety_boundary", str(i), prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "safety_boundary",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {},
            "provenance": {},
        })
    return examples


def build_sft(
    corpus_path: Path | str,
    graph_path: Path | str | None,
    output_dir: Path | str,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
    max_examples_per_type: int = 50,
) -> tuple[int, int, int, dict[str, int]]:
    """
    Build SFT train/val/test JSONL from corpus and local graph (suggestions, routines).
    Returns (n_train, n_val, n_test, counts_by_task_type).
    """
    corpus_path = Path(corpus_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    docs = load_corpus(corpus_path) if corpus_path.exists() else []
    suggestions: list[dict[str, Any]] = []
    routines: list[dict[str, Any]] = []
    if graph_path and Path(graph_path).exists():
        suggestions, routines = _load_suggestions_and_routines(graph_path)

    all_examples: list[dict[str, Any]] = []
    all_examples.extend(_knowledge_qa_examples(docs, max_per_type=max_examples_per_type))
    all_examples.extend(_workflow_inference_examples(docs, max_ex=max_examples_per_type))
    all_examples.extend(_routine_interpretation_examples(routines, max_ex=max_examples_per_type))
    all_examples.extend(_suggestion_explanation_examples(suggestions, max_ex=max_examples_per_type))
    all_examples.extend(_next_step_examples(routines, max_ex=20))
    all_examples.extend(_safety_boundary_examples(max_ex=15))

    counts: dict[str, int] = {}
    for ex in all_examples:
        t = ex.get("task_type", "unknown")
        counts[t] = counts.get(t, 0) + 1

    train, val, test = split_examples(
        all_examples,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
        stratify_by="task_type",
    )
    write_split_jsonl(train, val, test, output_dir)
    return len(train), len(val), len(test), counts


def _setup_explain_project_examples(
    parsed_docs: list[dict[str, Any]],
    allow_raw_text: bool,
    max_ex: int,
) -> list[dict[str, Any]]:
    """Explain this project from setup evidence."""
    examples = []
    seen_project: set[str] = set()
    for doc in parsed_docs:
        if len(examples) >= max_ex:
            break
        path = doc.get("source_path", "")
        if not path:
            continue
        parts = path.replace("\\", "/").strip("/").split("/")
        project = parts[0] if parts else "unknown"
        if project in seen_project:
            continue
        seen_project.add(project)
        summary = doc.get("summary", "")
        title = doc.get("title", "") or path.split("/")[-1]
        user = f"Explain what this project is about based on setup evidence: project folder '{project}', artifact: {title}."
        ctx = summary
        if allow_raw_text and doc.get("raw_text_snippet"):
            ctx += "\n\nSnippet: " + (doc["raw_text_snippet"][:500] or "")
        assistant = f"Based on setup analysis, project '{project}' contains artifacts such as '{title}'. Summary: {summary[:400]}."
        ex_id = stable_id("sft_setup", "explain_project", project, prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "explain_project",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"project": project},
            "provenance": {"source": "setup", "path": path},
        })
    return examples


def _setup_explain_artifact_domain_examples(
    parsed_docs: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Explain why this artifact belongs to this workflow/domain."""
    examples = []
    for doc in parsed_docs[:max_ex]:
        path = doc.get("source_path", "")
        family = doc.get("artifact_family", "document")
        title = doc.get("title", "") or path.split("/")[-1]
        summary = doc.get("summary", "")
        user = f"Why does artifact '{title}' (family: {family}) fit this workflow or domain?"
        assistant = f"The artifact '{title}' is classified as {family}. From setup: {summary[:350]}. It fits the workflow based on file type, location, and extracted signals."
        ex_id = stable_id("sft_setup", "explain_artifact_domain", path, prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "explain_artifact_domain",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"artifact_family": family},
            "provenance": {"source": "setup", "path": path},
        })
    return examples


def _setup_explain_style_pattern_examples(
    style_records: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Explain the user's likely style pattern."""
    examples = []
    for rec in style_records[:max_ex]:
        pattern_type = rec.get("pattern_type", "style")
        value = rec.get("value", "")
        desc = rec.get("description", "")
        user = f"What does this style pattern indicate about the user's work: {pattern_type}?"
        assistant = f"Style pattern '{pattern_type}': {desc}. Value/summary: {value}. This was inferred from file names, folder layout, or content structure during setup."
        ex_id = stable_id("sft_setup", "explain_style", pattern_type, str(value)[:50], prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "explain_style_pattern",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"pattern_type": pattern_type},
            "provenance": {"source": "setup_style"},
        })
    return examples


def _setup_justify_classification_examples(
    parsed_docs: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Justify project/domain classification."""
    examples = []
    for doc in parsed_docs[:max_ex]:
        family = doc.get("artifact_family", "document")
        path = doc.get("source_path", "")
        user = f"Justify why this artifact was classified as '{family}'."
        assistant = f"Classification as '{family}' is based on file extension, path, and optional content signals from setup. Path: {path}. No raw content is stored unless explicitly allowed by config."
        ex_id = stable_id("sft_setup", "justify", path, prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "justify_classification",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"artifact_family": family},
            "provenance": {"source": "setup", "path": path},
        })
    return examples


def _setup_next_step_examples(
    parsed_docs: list[dict[str, Any]],
    style_records: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Propose a likely next step from setup evidence."""
    examples = []
    for doc in parsed_docs[:max_ex]:
        path = doc.get("source_path", "")
        parts = path.replace("\\", "/").strip("/").split("/")
        project = parts[0] if parts else "unknown"
        user = "Based on setup evidence (project and artifacts), what is a sensible next step?"
        assistant = f"Given project '{project}' and the analyzed artifacts, a sensible next step could be to continue editing or reviewing files in this project, or to run the next phase of the workflow. The agent only suggests; it does not execute without approval."
        ex_id = stable_id("sft_setup", "next_step", path, prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "next_step_from_setup",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user + f"\n\nProject: {project}"},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"project": project},
            "provenance": {"source": "setup"},
        })
    return examples


def _setup_recurring_output_pattern_examples(
    style_records: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Explain a recurring output pattern."""
    examples = []
    for rec in style_records[:max_ex]:
        if rec.get("pattern_type") not in ("deliverable_bundle", "export_pattern", "revision_pattern"):
            continue
        pattern_type = rec.get("pattern_type", "")
        value = rec.get("value", "")
        user = "Explain this recurring output pattern from the user's setup."
        assistant = f"Pattern '{pattern_type}': {value}. This was detected from file names and folder structure during onboarding."
        ex_id = stable_id("sft_setup", "recurring", pattern_type, str(value)[:50], prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "recurring_output_pattern",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"pattern_type": pattern_type},
            "provenance": {"source": "setup_style"},
        })
    return examples


def _setup_creative_export_pattern_examples(
    style_records: list[dict[str, Any]],
    parsed_docs: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Interpret a creative/export pattern."""
    examples = []
    for rec in style_records[:max_ex]:
        pt = rec.get("pattern_type", "")
        if pt not in ("export_pattern", "revision_pattern", "naming_convention"):
            continue
        user = "How would you interpret this creative or export pattern for the user?"
        assistant = f"Pattern '{pt}': {rec.get('description', '')}. Value: {rec.get('value', '')}. Use this to tailor suggestions for exports and revisions."
        ex_id = stable_id("sft_setup", "creative", pt, str(rec.get("value", ""))[:40], prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "creative_export_pattern",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"pattern_type": pt},
            "provenance": {"source": "setup_style"},
        })
    return examples


def _setup_spreadsheet_pattern_examples(
    style_records: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Interpret a spreadsheet/reporting pattern."""
    examples = []
    for rec in style_records[:max_ex]:
        if rec.get("pattern_type") != "spreadsheet_schema":
            continue
        user = "Interpret this spreadsheet or reporting pattern from setup."
        assistant = f"Spreadsheet schema pattern: {rec.get('description', '')}. Summary: {rec.get('value', '')}. Use for reporting and table-aware suggestions."
        ex_id = stable_id("sft_setup", "spreadsheet", str(rec.get("value", ""))[:50], prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "spreadsheet_reporting_pattern",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"pattern_type": "spreadsheet_schema"},
            "provenance": {"source": "setup_style"},
        })
    return examples


def build_personal_sft_from_setup(
    parsed_artifacts_dir: Path | str,
    style_signals_dir: Path | str,
    session_id: str,
    output_dir: Path | str,
    allow_raw_text: bool = False,
    max_examples_per_type: int = 30,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[int, int, int, dict[str, int]]:
    """
    Build personal SFT examples from setup: parsed artifacts + style signals.
    Writes train/val/test JSONL to output_dir (e.g. data/local/llm/personal_sft/).
    Returns (n_train, n_val, n_test, counts_by_task_type).
    """
    from workflow_dataset.parse.document_models import ParsedDocument
    from workflow_dataset.setup.style_persistence import load_style_signals

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir = Path(parsed_artifacts_dir) / session_id
    parsed_docs: list[dict[str, Any]] = []
    if parsed_dir.exists():
        for path in sorted(parsed_dir.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    doc = ParsedDocument.model_validate_json(f.read())
                if doc.error:
                    continue
                parsed_docs.append(doc.model_dump())
            except Exception:
                continue
    style_records_raw: list[dict[str, Any]] = []
    try:
        records = load_style_signals(session_id, style_signals_dir)
        style_records_raw = [r.model_dump() for r in records]
    except Exception:
        pass
    all_examples: list[dict[str, Any]] = []
    all_examples.extend(_setup_explain_project_examples(parsed_docs, allow_raw_text, max_examples_per_type))
    all_examples.extend(_setup_explain_artifact_domain_examples(parsed_docs, max_examples_per_type))
    all_examples.extend(_setup_explain_style_pattern_examples(style_records_raw, max_examples_per_type))
    all_examples.extend(_setup_justify_classification_examples(parsed_docs, max_examples_per_type))
    all_examples.extend(_setup_next_step_examples(parsed_docs, style_records_raw, max_examples_per_type))
    all_examples.extend(_setup_recurring_output_pattern_examples(style_records_raw, max_examples_per_type))
    all_examples.extend(_setup_creative_export_pattern_examples(style_records_raw, parsed_docs, max_examples_per_type))
    all_examples.extend(_setup_spreadsheet_pattern_examples(style_records_raw, max_examples_per_type))
    counts: dict[str, int] = {}
    for ex in all_examples:
        t = ex.get("task_type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    train, val, test = split_examples(
        all_examples,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
        stratify_by="task_type",
    )
    write_split_jsonl(train, val, test, output_dir)
    return len(train), len(val), len(test), counts


def _assistive_why_suggestion_examples(
    suggestions: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Why-this-suggestion examples from style-aware suggestions."""
    examples = []
    for s in suggestions[:max_ex]:
        user = f"Why did the agent suggest: {s.get('title', '')}?"
        assistant = s.get("rationale", "") or s.get("description", "")
        if s.get("supporting_signals"):
            assistant += " Evidence: " + ", ".join(str(x)[:80] for x in s["supporting_signals"][:5])
        ex_id = stable_id("sft_assist", "why_suggestion", s.get("suggestion_id", ""), prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "why_this_suggestion",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"suggestion_type": s.get("suggestion_type")},
            "provenance": {"source": "assistive"},
        })
    return examples


def _assistive_why_structure_examples(
    drafts: list[dict[str, Any]],
    max_ex: int,
) -> list[dict[str, Any]]:
    """Why-this-structure / draft recommendation examples."""
    examples = []
    for d in drafts[:max_ex]:
        user = f"Why is this draft structure recommended: {d.get('title', '')}?"
        assistant = f"This structure ({d.get('draft_type', '')}) fits the domain '{d.get('domain', '')}' and observed patterns. Outline: {d.get('structure_outline', '')[:400]}."
        ex_id = stable_id("sft_assist", "why_structure", d.get("draft_id", ""), prefix="ex")
        examples.append({
            "example_id": ex_id,
            "task_type": "why_this_structure",
            "messages": [
                {"role": "system", "content": SYSTEM_GENERIC},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ],
            "metadata": {"draft_type": d.get("draft_type")},
            "provenance": {"source": "assistive"},
        })
    return examples


def build_personal_sft_from_assistive(
    suggestions_dir: Path | str,
    draft_structures_dir: Path | str,
    output_dir: Path | str,
    max_examples_per_type: int = 20,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[int, int, int, dict[str, int]]:
    """
    Build SFT examples from assistive outputs (suggestions, draft structures).
    Writes train/val/test to output_dir. Returns (n_train, n_val, n_test, counts).
    """
    from workflow_dataset.personal.style_suggestion_engine import load_style_aware_suggestions
    from workflow_dataset.personal.draft_structure_engine import load_draft_structures

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    suggestions_raw = [s.model_dump() for s in load_style_aware_suggestions(suggestions_dir)]
    drafts_raw = [d.model_dump() for d in load_draft_structures(draft_structures_dir)]
    all_examples: list[dict[str, Any]] = []
    all_examples.extend(_assistive_why_suggestion_examples(suggestions_raw, max_examples_per_type))
    all_examples.extend(_assistive_why_structure_examples(drafts_raw, max_examples_per_type))
    counts: dict[str, int] = {}
    for ex in all_examples:
        t = ex.get("task_type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    train, val, test = split_examples(
        all_examples,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
        stratify_by="task_type",
    )
    write_split_jsonl(train, val, test, output_dir)
    return len(train), len(val), len(test), counts
