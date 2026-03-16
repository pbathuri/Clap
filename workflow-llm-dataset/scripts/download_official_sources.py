#!/usr/bin/env python3
"""
Download or unpack official sources for the workflow-llm-dataset pipeline.

O*NET: Download the "All Files" Text ZIP from
  https://www.onetcenter.org/database.html
  → O*NET 30.2 Database → Text (tab-delimited)
Save as data/raw/official/onet/db_30_2_text.zip (or place any O*NET text ZIP there),
then run this script with --onet-only to unpack.

Other sources (NAICS, ISIC, SOC, BLS, ESCO): See SOURCES.md in this repo for URLs.
Some require one-time manual download; this script can unpack ZIPs if placed in the
corresponding data/raw/official/<source>/ folder.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# Default: repo root is parent of scripts/
REPO_ROOT = Path(__file__).resolve().parent.parent
ONET_DIR = REPO_ROOT / "data" / "raw" / "official" / "onet"

# Known O*NET 30.2 ZIP URL (may redirect or require session)
ONET_TEXT_ZIP_URL = "https://www.onetcenter.org/dl_files/database/db_30_2_text.zip"


def ensure_dirs() -> None:
    ONET_DIR.mkdir(parents=True, exist_ok=True)


def unpack_zip(zip_path: Path, dest_dir: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.startswith("__MACOSX") or "/." in name:
                continue
            zf.extract(name, dest_dir)
    print(f"Unpacked {zip_path.name} -> {dest_dir}")


def try_download_onet() -> bool:
    if not requests:
        print("Install requests to enable download: pip install requests")
        return False
    ensure_dirs()
    dest = ONET_DIR / "db_30_2_text.zip"
    if dest.exists():
        print(f"O*NET ZIP already exists: {dest}")
        return True
    print(f"Downloading O*NET 30.2 Text ZIP from {ONET_TEXT_ZIP_URL} ...")
    try:
        r = requests.get(ONET_TEXT_ZIP_URL, timeout=120, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved to {dest}")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        print("Download manually from https://www.onetcenter.org/database.html (All Files → Text)")
        return False


def unpack_onet() -> bool:
    ensure_dirs()
    zips = list(ONET_DIR.glob("*.zip"))
    if not zips:
        print("No ZIP found in", ONET_DIR)
        print("Download from https://www.onetcenter.org/database.html → O*NET 30.2 Database → Text")
        return False
    for z in zips:
        unpack_zip(z, ONET_DIR)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Download or unpack official sources")
    ap.add_argument("--onet-only", action="store_true", help="Only handle O*NET (download if possible, then unpack)")
    ap.add_argument("--no-download", action="store_true", help="Only unpack existing ZIPs; do not download")
    args = ap.parse_args()

    if args.onet_only:
        if not args.no_download and not list(ONET_DIR.glob("*.zip")):
            try_download_onet()
        return 0 if unpack_onet() else 1

    # Default: ensure dirs and try O*NET
    ensure_dirs()
    if not args.no_download and not list(ONET_DIR.glob("*.zip")):
        try_download_onet()
    unpack_onet()
    return 0


if __name__ == "__main__":
    sys.exit(main())
