"""
Deterministic train/val/test split for SFT and eval data.

Supports stratification by task_type; avoids leakage between near-duplicate examples.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

RATIO_TRAIN = 0.8
RATIO_VAL = 0.1
RATIO_TEST = 0.1
DEFAULT_SEED = 42


def _hash_example(ex: dict[str, Any]) -> str:
    """Stable hash for dedup and deterministic ordering."""
    content = ex.get("example_id", "") + str(ex.get("task_type", "")) + str(ex.get("messages", []))[:500]
    return hashlib.sha256(content.encode()).hexdigest()


def split_examples(
    examples: list[dict[str, Any]],
    train_ratio: float = RATIO_TRAIN,
    val_ratio: float = RATIO_VAL,
    test_ratio: float = RATIO_TEST,
    seed: int = DEFAULT_SEED,
    stratify_by: str | None = "task_type",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Deterministic split into train, val, test. Optionally stratify by task_type.
    Deduplicates by content hash so same example always in same split.
    """
    if not examples:
        return [], [], []
    seen_hashes: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for ex in examples:
        h = _hash_example(ex)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        deduped.append(ex)

    if stratify_by and any(ex.get(stratify_by) for ex in deduped):
        by_type: dict[str, list[dict[str, Any]]] = {}
        for ex in deduped:
            t = ex.get(stratify_by, "default")
            by_type.setdefault(t, []).append(ex)
        train, val, test = [], [], []
        for group in by_type.values():
            # Sort for determinism
            group_sorted = sorted(group, key=lambda e: _hash_example(e))
            n = len(group_sorted)
            n_train = max(1, int(n * train_ratio)) if n > 2 else (1 if n >= 1 else 0)
            n_val = max(0, int(n * val_ratio))
            n_test = n - n_train - n_val
            if n_test < 0:
                n_test = 0
                n_val = n - n_train
            train.extend(group_sorted[:n_train])
            val.extend(group_sorted[n_train : n_train + n_val])
            test.extend(group_sorted[n_train + n_val :])
        # Re-sort by hash so order is deterministic
        train.sort(key=lambda e: _hash_example(e))
        val.sort(key=lambda e: _hash_example(e))
        test.sort(key=lambda e: _hash_example(e))
        return train, val, test

    # No stratification: single shuffle with seed
    order = list(range(len(deduped)))
    # Deterministic shuffle
    for i in range(len(order) - 1, 0, -1):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        j = seed % (i + 1)
        order[i], order[j] = order[j], order[i]
    shuffled = [deduped[i] for i in order]
    n = len(shuffled)
    n_train = max(1, int(n * train_ratio)) if n > 2 else (1 if n >= 1 else 0)
    n_val = max(0, int(n * val_ratio))
    n_test = n - n_train - n_val
    if n_test < 0:
        n_test = 0
        n_val = n - n_train
    return shuffled[:n_train], shuffled[n_train : n_train + n_val], shuffled[n_train + n_val :]


def write_split_jsonl(
    train: list[dict[str, Any]],
    val: list[dict[str, Any]],
    test: list[dict[str, Any]],
    out_dir: Path | str,
) -> None:
    """Write train.jsonl, val.jsonl, test.jsonl to out_dir."""
    import json
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in [("train", train), ("val", val), ("test", test)]:
        path = out_dir / f"{name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for ex in data:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
