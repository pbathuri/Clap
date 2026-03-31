"""
Task run execution and artifact generation for local operator workflows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.desktop_adapters.execute import run_execute
from workflow_dataset.local_operator.state_store import load_operator_state, save_operator_state
from workflow_dataset.local_operator.task_store import (
    compact_steps_preview,
    load_task_plan,
    save_task_plan,
    save_task_run,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def approve_task_plan(plan_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    plan = load_task_plan(plan_id, repo_root)
    if not plan:
        return {"error": "plan_not_found"}
    if plan.get("status") != "planned":
        return {"error": "plan_not_executable"}
    plan["approved"] = True
    plan["approved_at"] = utc_now_iso()
    save_task_plan(plan, repo_root)
    return plan


def _resolve_scope_path(plan: dict[str, Any]) -> str:
    scope = plan.get("approved_scope") or {}
    path = str(scope.get("path") or "").strip()
    if path:
        return path
    for step in plan.get("steps") or []:
        if step.get("step_id") == "list_directory":
            params = step.get("params") or {}
            path = str(params.get("path") or "").strip()
            if path:
                return path
    return ""


def _pick_notes_path(scope_path: str, entries: list[dict[str, Any]]) -> str | None:
    if not scope_path:
        return None
    preferred = {
        "readme.md",
        "readme.txt",
        "notes.md",
        "notes.txt",
    }
    for entry in entries or []:
        name = str(entry.get("name") or "")
        if not name or not entry.get("is_file"):
            continue
        if name.lower() in preferred:
            return str(Path(scope_path) / name)
    return None


def _identify_relevant_files(entries: list[dict[str, Any]], limit: int = 6) -> list[str]:
    """Pick key files deterministically using simple filename heuristics."""
    preferred = [
        "readme.md",
        "readme.txt",
        "notes.md",
        "notes.txt",
        "pyproject.toml",
        "package.json",
        "requirements.txt",
        "setup.py",
    ]
    files = sorted(
        [str(e.get("name") or "") for e in entries if e.get("is_file") and str(e.get("name") or "")],
        key=lambda x: x.lower(),
    )
    picked: list[str] = []
    lower_to_name = {f.lower(): f for f in files}
    for p in preferred:
        if p in lower_to_name and lower_to_name[p] not in picked:
            picked.append(lower_to_name[p])
    for f in files:
        if f not in picked and (f.lower().endswith(".md") or f.lower().endswith(".txt")):
            picked.append(f)
        if len(picked) >= limit:
            break
    for f in files:
        if len(picked) >= limit:
            break
        if f not in picked:
            picked.append(f)
    return picked[:limit]


def _infer_project_context(entries: list[dict[str, Any]]) -> dict[str, Any]:
    names = [str(e.get("name") or "") for e in entries]
    lowers = {n.lower() for n in names}
    signals: list[str] = []
    if "pyproject.toml" in lowers or any(n.endswith(".py") for n in lowers):
        signals.append("python_project_signals")
    if "package.json" in lowers or any(n.endswith(".ts") or n.endswith(".tsx") or n.endswith(".js") for n in lowers):
        signals.append("javascript_project_signals")
    if "readme.md" in lowers:
        signals.append("readme_present")
    if any("task-runs" == n.lower() for n in lowers):
        signals.append("prior_task_runs_present")
    if not signals:
        signals.append("minimal_or_unknown_project_structure")
    brief = "Detected project context: " + ", ".join(signals) + "."
    return {"signals": signals, "brief": brief}


def _suggested_next_steps_for_pattern(workflow_pattern: str) -> list[str]:
    """Deterministic, pattern-specific guidance for artifact consumers."""
    tail = "Open the markdown artifact under the approved folder's task-runs/ directory and verify scope."
    if workflow_pattern == "inspect_status_report":
        return [
            "Validate the listed files and key-file heuristics match what you consider relevant.",
            "Add README.md or notes.md if you want a richer auto-summary on the next run.",
            tail,
        ]
    if workflow_pattern == "inspect_project_brief":
        return [
            "If context inference missed stack signals, add markers such as pyproject.toml or package.json.",
            "Expand README with goals, constraints, and stakeholders for the next brief.",
            tail,
        ]
    if workflow_pattern == "inspect_finder_report":
        return [
            "Confirm Finder opened the intended approved folder only.",
            "Omit Finder-related wording in the prompt if you want a report without a UI step.",
            tail,
        ]
    return [
        "Review the generated summary for accuracy.",
        "Collect any additional notes that should be captured.",
        tail,
    ]


def _pattern_extra_open_questions(workflow_pattern: str) -> list[str]:
    if workflow_pattern == "inspect_status_report":
        return ["Should future runs filter to specific file extensions or subfolders?"]
    if workflow_pattern == "inspect_project_brief":
        return ["Should the brief always align with a folder name explicitly named in the prompt?"]
    if workflow_pattern == "inspect_finder_report":
        return ["Should Finder execution stay optional when the workflow pattern implies Finder?"]
    return []


def _step_summary_line(step: dict[str, Any], index: int) -> str:
    """One-line summary for a run step, e.g. '1. list_directory: 5 entries'."""
    step_id = step.get("step_id") or "step"
    msg = step.get("message") or ""
    out = step.get("output") or {}
    if step_id == "list_directory" and isinstance(out.get("entries"), list):
        n = len(out["entries"])
        return f"{index}. list_directory: {n} entries"
    if step_id == "summarize_notes":
        if msg == "no_notes_file":
            return f"{index}. summarize_notes: no notes file"
        return f"{index}. summarize_notes: {msg or 'ok'}"
    if step_id == "open_finder":
        return f"{index}. open_finder: {msg or 'ok'}"
    if step_id == "identify_relevant_files":
        key_files = out.get("key_files") or []
        return f"{index}. identify_relevant_files: {len(key_files)} key files"
    if step_id == "infer_project_context":
        signals = out.get("signals") or []
        return f"{index}. infer_project_context: {len(signals)} signals"
    if step_id == "write_artifact":
        return f"{index}. write_artifact: {msg or 'ok'}"
    return f"{index}. {step_id}: {msg or 'ok'}"


def _artifact_markdown(
    *,
    prompt: str,
    scope_path: str,
    summary: str,
    next_steps: list[str],
    provenance_lines: list[str],
    generated_at: str,
    workflow_pattern: str = "",
    step_summaries: list[str] | None = None,
    structured_entries: list[dict[str, Any]] | None = None,
    key_files: list[str] | None = None,
    structured_result: list[str] | None = None,
    open_questions: list[str] | None = None,
) -> str:
    summary_block = summary.strip() or "No notes summary was generated."
    steps_block = "\n".join(f"- {step}" for step in next_steps if step.strip())
    provenance_block = "\n".join(f"- {line}" for line in provenance_lines if line.strip())
    sections = [
        "# Task Run Artifact",
        "",
        "## Prompt",
        prompt.strip() or "(empty)",
        "",
        "## Workflow Pattern",
        workflow_pattern or "inspect_summarize_brief",
        "",
        "## Source Scope",
        scope_path or "(unspecified)",
        "",
        "## Key Files Considered",
        "\n".join(f"- `{name}`" for name in (key_files or [])) or "- (none)",
        "",
        "## Summary / Result",
        summary_block,
        "",
    ]
    if step_summaries:
        sections.extend(
            [
                "## Per-Step Summary",
                "",
                "\n".join(step_summaries),
                "",
            ]
        )
    if structured_entries is not None and len(structured_entries) > 0:
        lines = ["### File list"]
        for e in structured_entries:
            name = e.get("name") or "(unknown)"
            kind = "dir" if e.get("is_dir") else "file"
            lines.append(f"- {name} ({kind})")
        sections.extend(lines)
        sections.append("")
    if structured_result:
        sections.extend(
            [
                "## Structured Result Sections",
                "",
                "\n".join(f"- {line}" for line in structured_result),
                "",
            ]
        )
    sections.extend(
        [
            "## Suggested Next Steps",
            steps_block or "- Review the artifact and confirm next actions.",
            "",
            "## Open Questions",
            "\n".join(f"- {q}" for q in (open_questions or []))
            or "- Should additional files be included in this run?",
            "",
            "## Provenance / Evidence",
            provenance_block or "- No provenance captured.",
            "",
            "## Generated At",
            generated_at,
            "",
        ]
    )
    return "\n".join(sections)


def _record_state(
    run: dict[str, Any],
    repo_root: Path | str | None,
) -> None:
    try:
        state = load_operator_state(repo_root)
        state["last_task_plan_id"] = run.get("plan_id")
        state["last_task_run_id"] = run.get("run_id")
        run_steps = run.get("steps") or []
        steps_preview = compact_steps_preview(run_steps, max_steps=12)
        state["last_task_run"] = {
            "run_id": run.get("run_id"),
            "plan_id": run.get("plan_id"),
            "prompt": run.get("prompt"),
            "status": run.get("status"),
            "reason": run.get("reason"),
            "artifact_path": run.get("artifact_path"),
            "workflow_pattern": run.get("workflow_pattern") or "",
            "step_count": len(run_steps),
            "steps_preview": steps_preview,
            "created_at": run.get("created_at"),
            "completed_at": run.get("completed_at"),
        }
        state["updated_at"] = utc_now_iso()
        save_operator_state(state, repo_root)
    except Exception:
        return


def run_task_plan(
    plan_id: str,
    approved: bool,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    created_at = utc_now_iso()
    run_id = stable_id("run", plan_id, created_at, prefix="run")
    plan = load_task_plan(plan_id, repo_root)
    if not plan:
        run = {
            "run_id": run_id,
            "plan_id": plan_id,
            "prompt": "",
            "status": "failed",
            "reason": "plan_not_found",
            "created_at": created_at,
            "completed_at": utc_now_iso(),
            "artifact_path": "",
            "workflow_pattern": "",
            "steps": [],
        }
        save_task_run(run, repo_root)
        _record_state(run, repo_root)
        return run

    if plan.get("status") != "planned":
        run = {
            "run_id": run_id,
            "plan_id": plan_id,
            "prompt": plan.get("prompt", ""),
            "status": "failed",
            "reason": "plan_not_executable",
            "created_at": created_at,
            "completed_at": utc_now_iso(),
            "artifact_path": "",
            "workflow_pattern": plan.get("workflow_pattern") or "",
            "steps": [],
        }
        save_task_run(run, repo_root)
        _record_state(run, repo_root)
        return run

    scope_path = _resolve_scope_path(plan)
    if not scope_path:
        run = {
            "run_id": run_id,
            "plan_id": plan_id,
            "prompt": plan.get("prompt", ""),
            "status": "failed",
            "reason": "scope_missing",
            "created_at": created_at,
            "completed_at": utc_now_iso(),
            "artifact_path": "",
            "workflow_pattern": plan.get("workflow_pattern") or "",
            "steps": [],
        }
        save_task_run(run, repo_root)
        _record_state(run, repo_root)
        return run

    if not approved or not plan.get("approved"):
        run = {
            "run_id": run_id,
            "plan_id": plan_id,
            "prompt": plan.get("prompt", ""),
            "status": "blocked",
            "reason": "approval_required",
            "created_at": created_at,
            "completed_at": utc_now_iso(),
            "artifact_path": "",
            "workflow_pattern": plan.get("workflow_pattern") or "",
            "steps": [],
        }
        save_task_run(run, repo_root)
        _record_state(run, repo_root)
        return run

    steps: list[dict[str, Any]] = []
    provenance: list[str] = []
    workflow_pattern = plan.get("workflow_pattern") or "inspect_summarize_brief"

    def _append_step(step_id: str, success: bool, message: str, output: dict[str, Any], path: str | None = None) -> None:
        step: dict[str, Any] = {
            "step_index": len(steps) + 1,
            "step_id": step_id,
            "step_status": "completed" if success else "failed",
            "success": success,
            "message": message,
            "output": output,
            "completed_at": utc_now_iso(),
        }
        if path is not None:
            step["path"] = path
        steps.append(step)

    list_result = run_execute(
        "file_ops",
        "list_directory",
        {"path": scope_path},
        repo_root=repo_root,
    )
    _append_step("list_directory", list_result.success, list_result.message, list_result.output)
    provenance.extend(
        f"{entry.adapter_id}/{entry.action_id}: {entry.path_or_param} ({entry.outcome})"
        for entry in list_result.provenance
    )
    if not list_result.success:
        run = {
            "run_id": run_id,
            "plan_id": plan_id,
            "prompt": plan.get("prompt", ""),
            "status": "failed",
            "reason": "list_directory_failed",
            "created_at": created_at,
            "completed_at": utc_now_iso(),
            "artifact_path": "",
            "workflow_pattern": workflow_pattern,
            "steps": steps,
        }
        save_task_run(run, repo_root)
        _record_state(run, repo_root)
        return run

    entries = list_result.output.get("entries") or []
    key_files = _identify_relevant_files(entries)
    structured_result: list[str] = []
    open_questions: list[str] = []

    if workflow_pattern == "inspect_status_report":
        _append_step(
            "identify_relevant_files",
            True,
            "ok",
            {"key_files": key_files},
        )
        structured_result.append(f"relevant_files_identified={len(key_files)}")
        if not key_files:
            open_questions.append("No clear key files were detected; should file heuristics be expanded?")

    if workflow_pattern == "inspect_project_brief":
        context = _infer_project_context(entries)
        _append_step(
            "infer_project_context",
            True,
            "ok",
            context,
        )
        structured_result.append(context.get("brief", "project_context_inferred"))

    if workflow_pattern == "inspect_finder_report":
        finder_result = run_execute(
            "finder_open",
            "open_folder",
            {"path": scope_path},
            repo_root=repo_root,
        )
        _append_step("open_finder", finder_result.success, finder_result.message, finder_result.output)
        provenance.extend(
            f"{entry.adapter_id}/{entry.action_id}: {entry.path_or_param} ({entry.outcome})"
            for entry in finder_result.provenance
        )
        if not finder_result.success:
            open_questions.append("Finder step failed or was unavailable; should capability readiness be rechecked?")

    notes_path = _pick_notes_path(scope_path, entries)
    summary_text = ""
    summary_failed = False
    if notes_path:
        summary_result = run_execute(
            "notes_document",
            "summarize_text_for_workflow",
            {"path": notes_path},
            repo_root=repo_root,
        )
        _append_step(
            "summarize_notes",
            summary_result.success,
            summary_result.message,
            summary_result.output,
            path=notes_path,
        )
        provenance.extend(
            f"{entry.adapter_id}/{entry.action_id}: {entry.path_or_param} ({entry.outcome})"
            for entry in summary_result.provenance
        )
        if summary_result.success:
            summary_text = summary_result.output.get("summary", "")
        else:
            summary_failed = True
    else:
        _append_step("summarize_notes", True, "no_notes_file", {})
        open_questions.append("No README/notes file was found; should one be added for better summaries?")

    summary_fallback = "No README/notes file found to summarize."
    if summary_failed:
        summary_fallback = "Notes summary failed; see provenance."

    step_summaries = [_step_summary_line(s, s.get("step_index", i)) for i, s in enumerate(steps, 1)]
    step_summaries.append(f"{len(steps) + 1}. write_artifact: ok")
    structured_entries: list[dict[str, Any]] | None = None
    if workflow_pattern in {"inspect_status_report", "inspect_project_brief"}:
        structured_entries = entries
    if workflow_pattern == "inspect_finder_report":
        structured_result.append("finder_open_attempted=true")
    if workflow_pattern == "inspect_status_report":
        structured_result.append("artifact_type=structured_status_report")
    if workflow_pattern == "inspect_project_brief":
        structured_result.append("artifact_type=project_brief")

    open_questions.extend(_pattern_extra_open_questions(workflow_pattern))
    artifact_path = str(Path(scope_path) / "task-runs" / f"{run_id}.md")
    content = _artifact_markdown(
        prompt=plan.get("prompt", ""),
        scope_path=scope_path,
        summary=summary_text or summary_fallback,
        next_steps=_suggested_next_steps_for_pattern(workflow_pattern),
        provenance_lines=provenance,
        generated_at=utc_now_iso(),
        workflow_pattern=workflow_pattern,
        step_summaries=step_summaries,
        structured_entries=structured_entries,
        key_files=key_files,
        structured_result=structured_result,
        open_questions=open_questions,
    )
    write_result = run_execute(
        "file_ops",
        "write_file",
        {"path": artifact_path, "content": content},
        repo_root=repo_root,
    )
    _append_step(
        "write_artifact",
        write_result.success,
        write_result.message,
        write_result.output,
        path=artifact_path,
    )
    provenance.extend(
        f"{entry.adapter_id}/{entry.action_id}: {entry.path_or_param} ({entry.outcome})"
        for entry in write_result.provenance
    )
    if not write_result.success:
        run = {
            "run_id": run_id,
            "plan_id": plan_id,
            "prompt": plan.get("prompt", ""),
            "status": "failed",
            "reason": "artifact_write_failed",
            "created_at": created_at,
            "completed_at": utc_now_iso(),
            "artifact_path": artifact_path,
            "workflow_pattern": workflow_pattern,
            "steps": steps,
        }
        save_task_run(run, repo_root)
        _record_state(run, repo_root)
        return run

    run = {
        "run_id": run_id,
        "plan_id": plan_id,
        "prompt": plan.get("prompt", ""),
        "status": "completed",
        "reason": "",
        "created_at": created_at,
        "completed_at": utc_now_iso(),
        "artifact_path": artifact_path,
        "workflow_pattern": workflow_pattern,
        "steps": steps,
    }
    save_task_run(run, repo_root)
    _record_state(run, repo_root)
    return run
