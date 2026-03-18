"""
Setup manager: runs the staged onboarding pipeline (stages 0-6).

Long-running, resumable, local-only. Uses job_store, progress_tracker, scan_scheduler,
parse layer, adapters, and graph_enrichment.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.setup.setup_models import (
    SetupSession,
    SetupStage,
    ScanJob,
    SetupProgress,
    ScanScope,
    DiscoveredDomain,
)
from workflow_dataset.setup.job_store import (
    load_session,
    save_session,
    save_progress,
    load_progress,
    list_jobs,
    create_session as _create_session,
)
from workflow_dataset.setup.progress_tracker import update_progress, get_progress
from workflow_dataset.setup.scan_scheduler import iter_scan_paths
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


# Default local paths (override via config)
DEFAULT_SETUP_DIR = Path("data/local/setup")
DEFAULT_PARSED_DIR = Path("data/local/parsed_artifacts")
DEFAULT_STYLE_DIR = Path("data/local/style_signals")
DEFAULT_REPORTS_DIR = Path("data/local/setup_reports")


class SetupManager:
    """Orchestrates setup stages 0-6 with resumable jobs and progress."""

    def __init__(
        self,
        setup_dir: Path | str = DEFAULT_SETUP_DIR,
        parsed_dir: Path | str = DEFAULT_PARSED_DIR,
        style_dir: Path | str = DEFAULT_STYLE_DIR,
        reports_dir: Path | str = DEFAULT_REPORTS_DIR,
        graph_path: Path | str | None = None,
    ):
        self.setup_dir = Path(setup_dir)
        self.parsed_dir = Path(parsed_dir)
        self.style_dir = Path(style_dir)
        self.reports_dir = Path(reports_dir)
        self.graph_path = Path(graph_path) if graph_path else None
        self.setup_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_dir.mkdir(parents=True, exist_ok=True)
        self.style_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        (self.setup_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (self.setup_dir / "jobs").mkdir(parents=True, exist_ok=True)
        (self.setup_dir / "progress").mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        scan_roots: list[str],
        exclude_dirs: list[str] | None = None,
        enabled_adapters: list[str] | None = None,
        max_runtime_hours: float = 36.0,
        onboarding_mode: str = "conservative",
        config_snapshot: dict | None = None,
    ) -> SetupSession:
        return _create_session(
            self.setup_dir,
            scan_roots=scan_roots,
            exclude_dirs=exclude_dirs,
            enabled_adapters=enabled_adapters,
            max_runtime_hours=max_runtime_hours,
            onboarding_mode=onboarding_mode,
            config_snapshot=config_snapshot,
        )

    def run_stage(self, session_id: str, from_stage: SetupStage | None = None) -> SetupProgress:
        """
        Run from current stage (or from_stage) through to SUMMARY. Resumable.
        """
        session = load_session(self.setup_dir, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        progress = load_progress(self.setup_dir, session_id) or SetupProgress(
            session_id=session_id,
            updated_utc=utc_now_iso(),
            current_stage=SetupStage.BOOTSTRAP,
        )
        start = from_stage or session.current_stage
        stage_order = [
            SetupStage.BOOTSTRAP,
            SetupStage.INVENTORY,
            SetupStage.PARSING,
            SetupStage.INTERPRETATION,
            SetupStage.GRAPH_ENRICHMENT,
            SetupStage.LLM_PREP,
            SetupStage.SUMMARY,
        ]
        idx = stage_order.index(start)
        for stage in stage_order[idx:]:
            if stage == SetupStage.BOOTSTRAP:
                progress = self._run_bootstrap(session, progress)
            elif stage == SetupStage.INVENTORY:
                progress = self._run_inventory(session, progress)
            elif stage == SetupStage.PARSING:
                progress = self._run_parsing(session, progress)
            elif stage == SetupStage.INTERPRETATION:
                progress = self._run_interpretation(session, progress)
            elif stage == SetupStage.GRAPH_ENRICHMENT:
                progress = self._run_graph_enrichment(session, progress)
            elif stage == SetupStage.LLM_PREP:
                progress = self._run_llm_prep(session, progress)
            elif stage == SetupStage.SUMMARY:
                progress = self._run_summary(session, progress)
            session.current_stage = stage
            session.updated_utc = utc_now_iso()
            save_session(self.setup_dir, session)
        return progress

    def _run_bootstrap(self, session: SetupSession, progress: SetupProgress) -> SetupProgress:
        """Stage 0: validate config, establish stores, record scan roots."""
        return update_progress(
            self.setup_dir,
            session.session_id,
            current_stage=SetupStage.BOOTSTRAP,
            details={"scan_roots": session.scan_scope.root_paths, "adapters": session.enabled_adapters},
        )

    def _run_inventory(self, session: SetupSession, progress: SetupProgress) -> SetupProgress:
        """Stage 1: scan files/folders, classify artifact families, detect domains."""
        from workflow_dataset.parse.artifact_classifier import classify_artifact
        from workflow_dataset.parse.domain_detector import detect_domains_from_path, merge_domains

        scope = session.scan_scope
        checkpoint_file = self.setup_dir / "jobs" / session.session_id / "inventory_checkpoint.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        files_scanned = 0
        artifacts_by_family: dict[str, int] = {}
        domain_lists: list[list[DiscoveredDomain]] = []
        for batch in iter_scan_paths(
            scope,
            checkpoint_path=checkpoint_file,
            batch_size=500,
            max_files=scope.max_files_per_scan,
        ):
            for p in batch:
                files_scanned += 1
                fam = classify_artifact(p)
                artifacts_by_family[fam.value] = artifacts_by_family.get(fam.value, 0) + 1
                domain_lists.append(detect_domains_from_path(p))
        domains = merge_domains(domain_lists)
        session.config_snapshot["discovered_domains"] = [d.model_dump() for d in domains]
        save_session(self.setup_dir, session)
        return update_progress(
            self.setup_dir,
            session.session_id,
            current_stage=SetupStage.INVENTORY,
            files_scanned=files_scanned,
            artifacts_classified=sum(artifacts_by_family.values()),
            details={"by_family": artifacts_by_family, "domains": [d.domain_id for d in domains]},
        )

    def _run_parsing(self, session: SetupSession, progress: SetupProgress) -> SetupProgress:
        """Stage 2: run low-level parsers on supported artifacts, extract signals."""
        from workflow_dataset.parse.document_router import route_and_parse_file
        from workflow_dataset.parse.artifact_classifier import is_supported_for_parsing
        from workflow_dataset.parse.document_models import ExtractionPolicy

        scope = session.scan_scope
        allow_raw = session.config_snapshot.get("allow_raw_text_parsing", False)
        policy = ExtractionPolicy.FULL_TEXT if (session.onboarding_mode == "full_onboarding" and allow_raw) else ExtractionPolicy.SIGNALS_AND_SUMMARIES
        checkpoint_file = self.setup_dir / "jobs" / session.session_id / "parse_checkpoint.json"
        parsed_count = 0
        errors = 0
        out_dir = self.parsed_dir / session.session_id
        out_dir.mkdir(parents=True, exist_ok=True)
        for batch in iter_scan_paths(scope, checkpoint_path=checkpoint_file, batch_size=100):
            for p in batch:
                if not is_supported_for_parsing(p):
                    continue
                try:
                    doc = route_and_parse_file(p, policy=policy, max_file_size=scope.max_file_size_bytes)
                    if doc.error:
                        errors += 1
                        continue
                    parsed_count += 1
                    manifest_path = out_dir / f"{stable_id('parsed', str(p), prefix='p')}.json"
                    with open(manifest_path, "w", encoding="utf-8") as f:
                        f.write(doc.model_dump_json())
                except Exception:
                    errors += 1
        return update_progress(
            self.setup_dir,
            session.session_id,
            current_stage=SetupStage.PARSING,
            docs_parsed=parsed_count,
            adapter_errors=errors,
            increment=True,
        )

    def _run_interpretation(self, session: SetupSession, progress: SetupProgress) -> SetupProgress:
        """Stage 3: run domain adapters, infer workflow/style signals; persist style signals."""
        from workflow_dataset.parse.adapters import get_adapters
        from workflow_dataset.parse.document_models import ParsedDocument
        from workflow_dataset.parse.style_extractor import (
            extract_naming_conventions,
            extract_folder_layout_style,
            extract_spreadsheet_schema_patterns,
        )
        from workflow_dataset.setup.style_persistence import persist_style_signals

        adapters = [a for a in get_adapters() if a.name in session.enabled_adapters]
        out_dir = self.parsed_dir / session.session_id
        if not out_dir.exists():
            return update_progress(self.setup_dir, session.session_id, current_stage=SetupStage.INTERPRETATION)
        signals_count = 0
        all_paths: list[Path] = []
        header_lists: list[list[str]] = []
        for path in out_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    doc = ParsedDocument.model_validate_json(f.read())
                all_paths.append(Path(doc.source_path))
                for t in doc.tables:
                    if t.headers:
                        header_lists.append(t.headers)
                for adapter in adapters:
                    if not adapter.can_handle(doc):
                        continue
                    for sig in adapter.process(doc):
                        signals_count += 1
            except Exception:
                continue
        style_signal_dicts: list[dict[str, Any]] = []
        if all_paths:
            for p in extract_naming_conventions(all_paths):
                style_signal_dicts.append({
                    "pattern_type": p.pattern_type,
                    "value": p.value,
                    "confidence": p.confidence,
                    "evidence_paths": p.evidence_paths[:20],
                    "description": p.description,
                })
            seen_dirs: set[Path] = set()
            for p in all_paths:
                parent = p.parent
                if parent and parent not in seen_dirs:
                    seen_dirs.add(parent)
                    for sp in extract_folder_layout_style(parent):
                        style_signal_dicts.append({
                            "pattern_type": sp.pattern_type,
                            "value": sp.value,
                            "confidence": sp.confidence,
                            "evidence_paths": sp.evidence_paths,
                            "project_path": str(parent),
                            "description": sp.description,
                        })
            for sp in extract_spreadsheet_schema_patterns([], header_lists):
                style_signal_dicts.append({
                    "pattern_type": sp.pattern_type,
                    "value": sp.value,
                    "confidence": sp.confidence,
                    "evidence_paths": sp.evidence_paths,
                    "description": sp.description,
                })
        if style_signal_dicts:
            persist_style_signals(session.session_id, style_signal_dicts, self.style_dir)
        return update_progress(
            self.setup_dir,
            session.session_id,
            current_stage=SetupStage.INTERPRETATION,
            details={"signals_emitted": signals_count, "style_signals_persisted": len(style_signal_dicts)},
            increment=True,
        )

    def _run_graph_enrichment(self, session: SetupSession, progress: SetupProgress) -> SetupProgress:
        """Stage 4: update personal graph with artifact, project, domain, style, workflow nodes and edges."""
        if not self.graph_path:
            return update_progress(self.setup_dir, session.session_id, current_stage=SetupStage.GRAPH_ENRICHMENT)
        from workflow_dataset.personal.graph_store import init_store
        from workflow_dataset.setup.graph_enrichment import (
            add_artifact_node,
            add_domain_node,
            add_style_pattern_node,
            add_workflow_hint_node,
            get_or_create_project,
            get_or_create_family_node,
            link_project_to_domain,
            link_style_pattern_to_project,
        )
        from workflow_dataset.setup.style_persistence import load_style_signals
        from workflow_dataset.parse.document_models import ParsedDocument

        init_store(self.graph_path)
        conn = sqlite3.connect(str(self.graph_path))
        nodes_created = 0
        scan_roots = [Path(r) for r in session.scan_scope.root_paths]
        try:
            domains_by_id: dict[str, str] = {}
            for d in session.config_snapshot.get("discovered_domains", []):
                domain_id = d.get("domain_id", "")
                if not domain_id:
                    continue
                nid = add_domain_node(conn, domain_id, d.get("label", ""))
                domains_by_id[domain_id] = nid
                nodes_created += 1
            style_records = load_style_signals(session.session_id, self.style_dir)
            style_pattern_ids: list[str] = []
            seen_style_key: set[tuple[str, str]] = set()
            for rec in style_records:
                key = (rec.pattern_type, str(rec.value)[:100])
                if key in seen_style_key:
                    continue
                seen_style_key.add(key)
                sid = add_style_pattern_node(
                    conn, rec.pattern_type, rec.value, description=rec.description,
                )
                style_pattern_ids.append(sid)
                nodes_created += 1
            parsed_dir = self.parsed_dir / session.session_id
            if not parsed_dir.exists():
                conn.commit()
                return update_progress(
                    self.setup_dir, session.session_id, current_stage=SetupStage.GRAPH_ENRICHMENT,
                    graph_nodes_created=nodes_created, increment=True,
                )
            project_ids_seen: set[str] = set()
            for path in sorted(parsed_dir.glob("*.json")):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        doc = ParsedDocument.model_validate_json(f.read())
                except Exception:
                    continue
                if doc.error:
                    continue
                src_path = Path(doc.source_path)
                project_label = ""
                for root in scan_roots:
                    try:
                        rel = src_path.relative_to(root)
                        if rel.parts:
                            project_label = rel.parts[0]
                        break
                    except ValueError:
                        continue
                if not project_label:
                    project_label = src_path.parent.name or "unknown"
                project_id = get_or_create_project(
                    conn, project_label, scan_root=scan_roots[0] if scan_roots else "",
                )
                if project_id not in project_ids_seen:
                    project_ids_seen.add(project_id)
                    for nid in domains_by_id.values():
                        link_project_to_domain(conn, project_id, nid)
                    add_workflow_hint_node(conn, "setup_analyzed", project_id)
                    nodes_created += 1
                    for sid in style_pattern_ids[:5]:
                        link_style_pattern_to_project(conn, sid, project_id)
                family_node_id = get_or_create_family_node(conn, doc.artifact_family)
                domain_ids = list(domains_by_id.values())
                art_id = add_artifact_node(
                    conn,
                    doc.source_path,
                    doc.artifact_family,
                    project_id=project_id,
                    family_node_id=family_node_id,
                    domain_ids=domain_ids,
                    style_pattern_ids=style_pattern_ids[:3],
                )
                nodes_created += 1
            conn.commit()
        finally:
            conn.close()
        return update_progress(
            self.setup_dir,
            session.session_id,
            current_stage=SetupStage.GRAPH_ENRICHMENT,
            graph_nodes_created=nodes_created,
            increment=True,
        )

    def _run_llm_prep(self, session: SetupSession, progress: SetupProgress) -> SetupProgress:
        """Stage 5: mark which artifacts/signals are suitable for corpus/SFT (no raw dump)."""
        manifest_path = self.setup_dir / "progress" / f"{session.session_id}_llm_prep.json"
        manifest = {
            "session_id": session.session_id,
            "suitable_for_corpus": True,
            "suitable_for_sft": True,
            "parsed_artifacts_dir": str(self.parsed_dir / session.session_id),
            "note": "Artifacts/signals may be consumed by llm corpus/SFT builders; no raw content dumped by default.",
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return update_progress(self.setup_dir, session.session_id, current_stage=SetupStage.LLM_PREP)

    def _run_summary(self, session: SetupSession, progress: SetupProgress) -> SetupProgress:
        """Stage 6: produce onboarding summary report."""
        from workflow_dataset.setup.setup_summary import build_summary_markdown
        report_path = self.reports_dir / f"{session.session_id}_summary.md"
        build_summary_markdown(session, progress, report_path=report_path)
        return update_progress(self.setup_dir, session.session_id, current_stage=SetupStage.SUMMARY, details={"report_path": str(report_path)})
