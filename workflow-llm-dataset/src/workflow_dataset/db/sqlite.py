from __future__ import annotations

from pathlib import Path
import sqlite3


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path))
