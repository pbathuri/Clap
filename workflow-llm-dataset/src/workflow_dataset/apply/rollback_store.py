"""
Rollback support: backup overwritten files, record rollback token, restore on rollback.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from workflow_dataset.apply.apply_models import RollbackRecord
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def create_rollback_record(
    apply_id: str,
    backup_list: list[dict[str, str]],
    affected_paths: list[str],
    backup_root: Path | str,
) -> RollbackRecord:
    """Create a rollback record from backup list (original -> backup path)."""
    token = stable_id("rollback", apply_id, utc_now_iso(), prefix="rb")
    return RollbackRecord(
        rollback_token=token,
        apply_id=apply_id,
        backups=backup_list,
        affected_paths=affected_paths,
        created_utc=utc_now_iso(),
    )


def perform_rollback(
    rollback_token: str,
    rollback_store_path: Path | str,
) -> tuple[bool, str]:
    """
    Restore files from backup using rollback record. Returns (success, message).
    rollback_store_path: root for applies (e.g. data/local/applies) where rollbacks/ lives.
    """
    store = Path(rollback_store_path)
    record_path = store / "rollbacks" / f"{rollback_token}.json"
    if not record_path.exists():
        return False, f"Rollback record not found: {rollback_token}"
    import json
    with open(record_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    record = RollbackRecord.model_validate(data)
    restored = 0
    errors: list[str] = []
    for b in record.backups:
        original = b.get("original") or b.get("target")
        backup = b.get("backup")
        if not original or not backup:
            continue
        orig_p = Path(original)
        bak_p = Path(backup)
        if not bak_p.exists():
            errors.append(f"Backup missing: {backup}")
            continue
        try:
            if orig_p.exists():
                orig_p.unlink()
            shutil.copy2(bak_p, orig_p)
            restored += 1
        except Exception as e:
            errors.append(f"{original}: {e}")
    if errors:
        return False, "; ".join(errors)
    return True, f"Restored {restored} file(s)"


def save_rollback_record(record: RollbackRecord, store_path: Path | str) -> Path:
    """Persist rollback record to store_path/rollbacks/<token>.json."""
    store = Path(store_path)
    (store / "rollbacks").mkdir(parents=True, exist_ok=True)
    path = store / "rollbacks" / f"{record.rollback_token}.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(record.model_dump_json(indent=2))
    return path
