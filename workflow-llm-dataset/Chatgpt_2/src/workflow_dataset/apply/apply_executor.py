"""
Execute apply: copy from sandbox to target only after explicit confirmation.
Create backups when overwriting; record apply result and rollback.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from workflow_dataset.apply.apply_models import ApplyRequest, ApplyPlan, ApplyResult, RollbackRecord
from workflow_dataset.apply.rollback_store import create_rollback_record, save_rollback_record
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def execute_apply(
    plan: ApplyPlan,
    workspace_path: Path | str,
    target_root: Path | str,
    user_confirmed: bool,
    create_backups: bool = True,
    backup_root: Path | str | None = None,
) -> tuple[ApplyResult | None, str]:
    """
    Execute the apply plan. Returns (result, error_message).
    If user_confirmed is False, returns (None, "Confirmation required").
    """
    if not user_confirmed:
        return None, "Confirmation required (pass --confirm)"
    ws = Path(workspace_path).resolve()
    target = Path(target_root).resolve()
    if not ws.exists() or not target.parent.exists():
        return None, "Workspace or target parent does not exist"
    applied: list[str] = []
    overwritten: list[str] = []
    backup_paths: list[str] = []
    backup_list: list[dict[str, str]] = []
    errors: list[str] = []
    for op in plan.operations:
        src = ws / op["source"]
        tgt = Path(op["target"])
        if not src.exists():
            continue
        try:
            if tgt.exists():
                if tgt.is_file() and src.is_file():
                    if create_backups and backup_root is not None:
                        backup_dir = Path(backup_root) / "backups"
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        backup_name = f"{stable_id('bak', op['source'], utc_now_iso(), prefix='bak')}_{tgt.name}"
                        backup_file = backup_dir / backup_name
                        shutil.copy2(tgt, backup_file)
                        backup_paths.append(str(backup_file))
                        backup_list.append({"original": str(tgt), "backup": str(backup_file), "target": str(tgt)})
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, tgt)
                    overwritten.append(str(tgt))
                    applied.append(str(tgt))
                elif tgt.is_dir() and src.is_dir():
                    for f in src.rglob("*"):
                        if f.is_file():
                            rel = f.relative_to(src)
                            dst = tgt / rel
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(f, dst)
                            applied.append(str(dst))
                else:
                    pass
            else:
                tgt.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    tgt.mkdir(parents=True, exist_ok=True)
                    for f in src.rglob("*"):
                        if f.is_file():
                            rel = f.relative_to(src)
                            dst = tgt / rel
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(f, dst)
                            applied.append(str(dst))
                else:
                    shutil.copy2(src, tgt)
                    applied.append(str(tgt))
        except Exception as e:
            errors.append(f"{op['source']}: {e}")
    result_id = stable_id("result", plan.plan_id, utc_now_iso(), prefix="result")
    result = ApplyResult(
        result_id=result_id,
        apply_id=plan.apply_id,
        applied_paths=applied,
        skipped_paths=plan.skipped_paths,
        overwritten_paths=overwritten,
        backup_paths=backup_paths,
        errors=errors,
        created_utc=utc_now_iso(),
    )
    if backup_list and backup_root is not None:
        rollback_record = create_rollback_record(
            plan.apply_id or result_id,
            backup_list,
            overwritten,
            backup_root,
        )
        result.rollback_token = rollback_record.rollback_token
        save_rollback_record(rollback_record, backup_root)
    return result, "" if not errors else "; ".join(errors)
