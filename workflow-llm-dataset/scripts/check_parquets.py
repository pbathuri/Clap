#!/usr/bin/env python3
"""Quick check of interim/processed parquet files. Run from project root with: .venv/bin/python scripts/check_parquets.py"""

from pathlib import Path

import pandas as pd

def main():
    p = Path("data")
    for subdir, names in [
        ("interim", ["bls__occupation_xlsx_table_1_2.parquet"]),
        ("processed", ["labor_market.parquet", "industry_occupation_map.parquet", "bls_no_matrix_source.parquet", "labor_unmapped_occupation_codes.parquet"]),
    ]:
        base = p / subdir
        for name in names:
            fp = base / name
            if fp.exists():
                df = pd.read_parquet(fp)
                print(f"\n{subdir}/{name}: {len(df)} rows")
                if len(df):
                    print(df.head(10).to_string())
            else:
                print(f"\n{subdir}/{name}: MISSING")

if __name__ == "__main__":
    main()
