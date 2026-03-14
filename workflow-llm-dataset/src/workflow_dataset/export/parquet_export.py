"""Materialize processed tables to outputs/parquet."""

from __future__ import annotations

from pathlib import Path
import shutil


def export_parquet(settings) -> None:
    processed = Path(settings.paths.processed)
    out = Path(settings.project.output_parquet_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not processed.exists():
        return
    for f in sorted(processed.glob("*.parquet")):
        try:
            shutil.copy2(f, out / f.name)
        except Exception as exc:
            print(f"Parquet export failed for {f.name}: {exc}")
