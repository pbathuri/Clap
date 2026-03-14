"""Materialize processed tables to outputs/csv."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def export_csv(settings) -> None:
    processed = Path(settings.paths.processed)
    out = Path(settings.project.output_csv_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not processed.exists():
        return
    for f in sorted(processed.glob("*.parquet")):
        try:
            df = pd.read_parquet(f)
            df.to_csv(out / f"{f.stem}.csv", index=False, encoding="utf-8")
        except Exception as exc:
            print(f"CSV export failed for {f.name}: {exc}")
