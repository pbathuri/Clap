from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIRS = [
    "context",
    "data/raw/official/isic",
    "data/raw/official/naics",
    "data/raw/official/soc",
    "data/raw/official/onet",
    "data/raw/official/bls",
    "data/raw/official/esco",
    "data/raw/private_examples",
    "data/interim",
    "data/processed",
    "outputs/csv",
    "outputs/parquet",
    "outputs/excel",
    "outputs/qa",
    "prompts",
    "sql",
]

for d in DIRS:
    (REPO_ROOT / d).mkdir(parents=True, exist_ok=True)

print("Directory bootstrap complete")
