"""
Persist apply requests, plans, results under data/local/applies.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.apply.apply_models import ApplyRequest, ApplyPlan, ApplyResult


def _ensure_applies_dir(store_path: Path | str) -> Path:
    store = Path(store_path)
    store.mkdir(parents=True, exist_ok=True)
    return store


def save_apply_request(request: ApplyRequest, store_path: Path | str) -> Path:
    path = _ensure_applies_dir(store_path) / "requests" / f"{request.apply_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(request.model_dump_json(indent=2))
    return path


def save_apply_plan(plan: ApplyPlan, store_path: Path | str) -> Path:
    path = _ensure_applies_dir(store_path) / "plans" / f"{plan.plan_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(plan.model_dump_json(indent=2))
    return path


def save_apply_result(result: ApplyResult, store_path: Path | str) -> Path:
    path = _ensure_applies_dir(store_path) / "results" / f"{result.result_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
    return path


def load_apply_result(result_id: str, store_path: Path | str) -> ApplyResult | None:
    path = Path(store_path) / "results" / f"{result_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return ApplyResult.model_validate_json(f.read())


def load_rollback_record(rollback_token: str, store_path: Path | str):
    from workflow_dataset.apply.apply_models import RollbackRecord
    path = Path(store_path) / "rollbacks" / f"{rollback_token}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return RollbackRecord.model_validate_json(f.read())
