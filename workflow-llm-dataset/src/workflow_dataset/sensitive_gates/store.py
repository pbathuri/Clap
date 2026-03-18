"""
M35I–M35L: Persist sensitive action gates and append-only audit ledger.
Data: data/local/sensitive_gates/ — gates.json, ledger.jsonl.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.sensitive_gates.models import (
    SensitiveActionGate,
    AuditLedgerEntry,
)


SENSITIVE_GATES_DIR = "data/local/sensitive_gates"
GATES_FILE = "gates.json"
LEDGER_FILE = "ledger.jsonl"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_sensitive_gates_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / SENSITIVE_GATES_DIR


def _gates_path(repo_root: Path | str | None) -> Path:
    return get_sensitive_gates_dir(repo_root) / GATES_FILE


def _ledger_path(repo_root: Path | str | None) -> Path:
    return get_sensitive_gates_dir(repo_root) / LEDGER_FILE


def load_gates(repo_root: Path | str | None = None) -> list[SensitiveActionGate]:
    path = _gates_path(repo_root)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [SensitiveActionGate.from_dict(d) for d in raw.get("gates", [])]
    except Exception:
        return []


def save_gates(gates: list[SensitiveActionGate], repo_root: Path | str | None = None) -> Path:
    d = get_sensitive_gates_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = _gates_path(repo_root)
    path.write_text(
        json.dumps({"gates": [g.to_dict() for g in gates]}, indent=2),
        encoding="utf-8",
    )
    return path


def get_gate(gate_id: str, repo_root: Path | str | None = None) -> SensitiveActionGate | None:
    for g in load_gates(repo_root):
        if g.gate_id == gate_id:
            return g
    return None


def upsert_gate(gate: SensitiveActionGate, repo_root: Path | str | None = None) -> Path:
    gates = load_gates(repo_root)
    for i, g in enumerate(gates):
        if g.gate_id == gate.gate_id:
            gates[i] = gate
            return save_gates(gates, repo_root)
    gates.append(gate)
    return save_gates(gates, repo_root)


def append_ledger_entry(entry: AuditLedgerEntry, repo_root: Path | str | None = None) -> Path:
    d = get_sensitive_gates_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = _ledger_path(repo_root)
    line = json.dumps(entry.to_dict(), ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
    return path


def load_ledger_entries(
    repo_root: Path | str | None = None,
    limit: int = 500,
    reverse: bool = True,
) -> list[AuditLedgerEntry]:
    path = _ledger_path(repo_root)
    if not path.exists():
        return []
    entries: list[AuditLedgerEntry] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(AuditLedgerEntry.from_dict(json.loads(line)))
            except Exception:
                continue
    if reverse:
        entries = list(reversed(entries))
    return entries[:limit]


def ledger_by_project(
    project_id: str,
    repo_root: Path | str | None = None,
    limit: int = 100,
) -> list[AuditLedgerEntry]:
    all_entries = load_ledger_entries(repo_root=repo_root, limit=1000, reverse=True)
    out = [e for e in all_entries if e.linked and e.linked.project_id == project_id]
    return out[:limit]


def ledger_by_gate_id(
    gate_id: str,
    repo_root: Path | str | None = None,
) -> list[AuditLedgerEntry]:
    all_entries = load_ledger_entries(repo_root=repo_root, limit=1000, reverse=True)
    return [e for e in all_entries if e.gate_id == gate_id]
