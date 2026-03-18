"""
M43B: Memory storage backends — in-memory and SQLite. Local-only, inspectable.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.memory_substrate.models import (
    CompressedMemoryUnit,
    MemorySessionLink,
    MemoryStorageBackend,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


MEMORY_SUBSTRATE_DIR = "data/local/memory_substrate"
DB_FILENAME = "memory.db"


def _db_path(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / MEMORY_SUBSTRATE_DIR / DB_FILENAME


class InMemoryBackend:
    """In-memory backend for tests and ephemeral use."""

    def __init__(self) -> None:
        self._units: dict[str, CompressedMemoryUnit] = {}
        self._links: list[MemorySessionLink] = []
        self._sessions: set[str] = set()

    def store(self, unit: CompressedMemoryUnit, link: MemorySessionLink | None) -> None:
        self._units[unit.unit_id] = unit
        if link:
            self._links.append(link)
            self._sessions.add(link.session_id)
        if unit.session_id:
            self._sessions.add(unit.session_id)

    def get(self, unit_id: str) -> CompressedMemoryUnit | None:
        return self._units.get(unit_id)

    def list_units(self, session_id: str | None, limit: int) -> list[CompressedMemoryUnit]:
        out = [u for u in self._units.values() if session_id is None or u.session_id == session_id]
        out.sort(key=lambda u: u.created_at_utc or u.timestamp, reverse=True)
        return out[:limit]

    def search_keyword(self, query: str, top_k: int, session_id: str | None) -> list[CompressedMemoryUnit]:
        q = query.lower()
        out: list[tuple[CompressedMemoryUnit, int]] = []
        for u in self._units.values():
            if session_id and u.session_id != session_id:
                continue
            score = 0
            if q in (u.lossless_restatement or "").lower():
                score += 2
            for kw in u.keywords:
                if q in kw.lower():
                    score += 1
            if score > 0:
                out.append((u, score))
        out.sort(key=lambda x: -x[1])
        return [u for u, _ in out[:top_k]]

    def search_structured(self, session_id: str | None, source: str | None, limit: int) -> list[CompressedMemoryUnit]:
        out = [
            u for u in self._units.values()
            if (session_id is None or u.session_id == session_id)
            and (source is None or u.source == source)
        ]
        out.sort(key=lambda u: u.created_at_utc or u.timestamp, reverse=True)
        return out[:limit]

    def list_sessions(self, limit: int) -> list[str]:
        return sorted(self._sessions, reverse=True)[:limit]

    def get_stats(self) -> dict[str, Any]:
        return {
            "backend_id": "in_memory",
            "units_count": len(self._units),
            "links_count": len(self._links),
            "sessions_count": len(self._sessions),
        }

    def backend_id(self) -> str:
        return "in_memory"


class SQLiteBackend:
    """SQLite-backed storage for durable local memory."""

    def __init__(self, repo_root: Path | str | None = None) -> None:
        self._path = _db_path(repo_root)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._path))

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS units (
                    unit_id TEXT PRIMARY KEY,
                    lossless_restatement TEXT NOT NULL,
                    keywords_json TEXT NOT NULL DEFAULT '[]',
                    timestamp TEXT,
                    location TEXT,
                    persons_json TEXT NOT NULL DEFAULT '[]',
                    entities_json TEXT NOT NULL DEFAULT '[]',
                    topic TEXT,
                    session_id TEXT,
                    source TEXT,
                    source_ref TEXT,
                    created_at_utc TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS session_links (
                    link_id TEXT PRIMARY KEY,
                    unit_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at_utc TEXT,
                    FOREIGN KEY (unit_id) REFERENCES units(unit_id)
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_units_session ON units(session_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_units_source ON units(source)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_links_session ON session_links(session_id)")
            c.commit()

    def store(self, unit: CompressedMemoryUnit, link: MemorySessionLink | None) -> None:
        kw = json.dumps(unit.keywords)
        persons = json.dumps(unit.persons)
        entities = json.dumps(unit.entities)
        with self._conn() as c:
            c.execute(
                """INSERT OR REPLACE INTO units
                   (unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    unit.unit_id,
                    unit.lossless_restatement,
                    kw,
                    unit.timestamp,
                    unit.location,
                    persons,
                    entities,
                    unit.topic,
                    unit.session_id,
                    unit.source,
                    unit.source_ref,
                    unit.created_at_utc,
                ),
            )
            if link:
                c.execute(
                    "INSERT OR REPLACE INTO session_links (link_id, unit_id, session_id, created_at_utc) VALUES (?, ?, ?, ?)",
                    (link.link_id, link.unit_id, link.session_id, link.created_at_utc),
                )
            c.commit()

    def get(self, unit_id: str) -> CompressedMemoryUnit | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc FROM units WHERE unit_id = ?",
                (unit_id,),
            ).fetchone()
        if not row:
            return None
        return CompressedMemoryUnit(
            unit_id=row[0],
            lossless_restatement=row[1],
            keywords=json.loads(row[2]) if row[2] else [],
            timestamp=row[3] or "",
            location=row[4],
            persons=json.loads(row[5]) if row[5] else [],
            entities=json.loads(row[6]) if row[6] else [],
            topic=row[7],
            session_id=row[8] or "",
            source=row[9] or "",
            source_ref=row[10] or "",
            created_at_utc=row[11] or "",
        )

    def list_units(self, session_id: str | None, limit: int) -> list[CompressedMemoryUnit]:
        with self._conn() as c:
            if session_id:
                cur = c.execute(
                    "SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc FROM units WHERE session_id = ? ORDER BY created_at_utc DESC, timestamp DESC LIMIT ?",
                    (session_id, limit),
                )
            else:
                cur = c.execute(
                    "SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc FROM units ORDER BY created_at_utc DESC, timestamp DESC LIMIT ?",
                    (limit,),
                )
            rows = cur.fetchall()
        return [
            CompressedMemoryUnit(
                unit_id=r[0],
                lossless_restatement=r[1],
                keywords=json.loads(r[2]) if r[2] else [],
                timestamp=r[3] or "",
                location=r[4],
                persons=json.loads(r[5]) if r[5] else [],
                entities=json.loads(r[6]) if r[6] else [],
                topic=r[7],
                session_id=r[8] or "",
                source=r[9] or "",
                source_ref=r[10] or "",
                created_at_utc=r[11] or "",
            )
            for r in rows
        ]

    def search_keyword(self, query: str, top_k: int, session_id: str | None) -> list[CompressedMemoryUnit]:
        q = f"%{query.lower()}%"
        with self._conn() as c:
            if session_id:
                cur = c.execute(
                    """SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc
                       FROM units WHERE session_id = ? AND (lower(lossless_restatement) LIKE ? OR unit_id IN (
                         SELECT unit_id FROM units WHERE session_id = ? AND keywords_json LIKE ?
                       )) ORDER BY created_at_utc DESC LIMIT ?""",
                    (session_id, q, session_id, q, top_k),
                )
            else:
                cur = c.execute(
                    """SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc
                       FROM units WHERE lower(lossless_restatement) LIKE ? OR keywords_json LIKE ? ORDER BY created_at_utc DESC LIMIT ?""",
                    (q, q, top_k),
                )
            rows = cur.fetchall()
        return [
            CompressedMemoryUnit(
                unit_id=r[0],
                lossless_restatement=r[1],
                keywords=json.loads(r[2]) if r[2] else [],
                timestamp=r[3] or "",
                location=r[4],
                persons=json.loads(r[5]) if r[5] else [],
                entities=json.loads(r[6]) if r[6] else [],
                topic=r[7],
                session_id=r[8] or "",
                source=r[9] or "",
                source_ref=r[10] or "",
                created_at_utc=r[11] or "",
            )
            for r in rows
        ]

    def search_structured(self, session_id: str | None, source: str | None, limit: int) -> list[CompressedMemoryUnit]:
        with self._conn() as c:
            if session_id and source:
                cur = c.execute(
                    "SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc FROM units WHERE session_id = ? AND source = ? ORDER BY created_at_utc DESC LIMIT ?",
                    (session_id, source, limit),
                )
            elif session_id:
                cur = c.execute(
                    "SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc FROM units WHERE session_id = ? ORDER BY created_at_utc DESC LIMIT ?",
                    (session_id, limit),
                )
            elif source:
                cur = c.execute(
                    "SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc FROM units WHERE source = ? ORDER BY created_at_utc DESC LIMIT ?",
                    (source, limit),
                )
            else:
                cur = c.execute(
                    "SELECT unit_id, lossless_restatement, keywords_json, timestamp, location, persons_json, entities_json, topic, session_id, source, source_ref, created_at_utc FROM units ORDER BY created_at_utc DESC LIMIT ?",
                    (limit,),
                )
            rows = cur.fetchall()
        return [
            CompressedMemoryUnit(
                unit_id=r[0],
                lossless_restatement=r[1],
                keywords=json.loads(r[2]) if r[2] else [],
                timestamp=r[3] or "",
                location=r[4],
                persons=json.loads(r[5]) if r[5] else [],
                entities=json.loads(r[6]) if r[6] else [],
                topic=r[7],
                session_id=r[8] or "",
                source=r[9] or "",
                source_ref=r[10] or "",
                created_at_utc=r[11] or "",
            )
            for r in rows
        ]

    def list_sessions(self, limit: int) -> list[str]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT session_id FROM (
                   SELECT session_id, MAX(created_at_utc) AS m FROM units WHERE session_id != '' GROUP BY session_id
                   ORDER BY m DESC LIMIT ?
                   )""",
                (limit,),
            ).fetchall()
            if not rows:
                rows = c.execute(
                    "SELECT DISTINCT session_id FROM session_links WHERE session_id != '' ORDER BY created_at_utc DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [r[0] for r in rows if r[0]]

    def get_stats(self) -> dict[str, Any]:
        with self._conn() as c:
            n_units = c.execute("SELECT COUNT(*) FROM units").fetchone()[0]
            n_links = c.execute("SELECT COUNT(*) FROM session_links").fetchone()[0]
            n_sessions = c.execute("SELECT COUNT(DISTINCT session_id) FROM units WHERE session_id != ''").fetchone()[0]
        return {
            "backend_id": "sqlite",
            "path": str(self._path),
            "units_count": n_units,
            "links_count": n_links,
            "sessions_count": n_sessions,
        }

    def backend_id(self) -> str:
        return "sqlite"
