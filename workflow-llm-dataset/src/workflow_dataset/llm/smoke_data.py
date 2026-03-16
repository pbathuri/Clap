"""
Minimal SFT data for smoke-training: proves the training path works end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path

SMOKE_TRAIN = [
    {
        "example_id": "smoke_1",
        "task_type": "knowledge_qa",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is workflow?"},
            {"role": "assistant",
                "content": "A workflow is a sequence of steps to accomplish a task."},
        ],
    },
    {
        "example_id": "smoke_2",
        "task_type": "workflow_inference",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "User opens CSV files often. What workflow?"},
            {"role": "assistant", "content": "Likely a data or operations workflow."},
        ],
    },
    {
        "example_id": "smoke_3",
        "task_type": "routine_interpretation",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain this pattern: daily edits to reports."},
            {"role": "assistant",
                "content": "This suggests a reporting or editorial routine."},
        ],
    },
    {
        "example_id": "smoke_4",
        "task_type": "knowledge_qa",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is an occupation?"},
            {"role": "assistant",
                "content": "An occupation is a role or job a person performs."},
        ],
    },
]

# At least 2 examples so mlx_lm validation (batch_size=2) does not fail
SMOKE_VALID = SMOKE_TRAIN[:2]


def write_smoke_sft(smoke_dir: Path) -> None:
    """Write minimal train.jsonl and valid.jsonl to smoke_dir for smoke-train."""
    smoke_dir.mkdir(parents=True, exist_ok=True)
    train_path = smoke_dir / "train.jsonl"
    valid_path = smoke_dir / "valid.jsonl"
    with open(train_path, "w", encoding="utf-8") as f:
        for ex in SMOKE_TRAIN:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    with open(valid_path, "w", encoding="utf-8") as f:
        for ex in SMOKE_VALID:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
