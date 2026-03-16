"""Load BLS O*NET-SOC to NEM crosswalk and build BLS occupation code -> O*NET-SOC (and occupation_id) mapping."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd


def _normalize_soc(code: str) -> str:
    if not code or not isinstance(code, str):
        return ""
    s = re.sub(r"\s+", "", str(code).strip())
    if not s:
        return ""
    if re.match(r"^\d{2}-\d{4}\.\d{2}$", s):
        return s
    if re.match(r"^\d{2}-\d{4}$", s):
        return s + ".00"
    if len(s) >= 6 and s.isdigit():
        return s[:2] + "-" + s[2:6] + ".00"
    return s


def _detect_crosswalk_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Return (bls_soc_col, onet_soc_col). BLS side might be SOC Code, NEM Code; O*NET side is O*NET-SOC Code."""
    cols_lower = {c.lower(): c for c in df.columns}
    onet_col = None
    for k in ("o*net-soc code", "onet-soc code", "onet_soc_code", "onet soc code"):
        if k in cols_lower:
            onet_col = cols_lower[k]
            break
    if not onet_col:
        for c in df.columns:
            if "onet" in c.lower() and "soc" in c.lower():
                onet_col = c
                break
    bls_col = None
    for k in ("soc code", "soc_code", "occupation code", "occupation_code", "nem code", "nem_code", "soc"):
        if k in cols_lower:
            bls_col = cols_lower[k]
            break
    if not bls_col:
        for c in df.columns:
            if c == onet_col:
                continue
            if "soc" in c.lower() or "occupation" in c.lower() or "nem" in c.lower():
                bls_col = c
                break
    return bls_col, onet_col


def load_crosswalk_to_onet_soc(interim: Path) -> dict[str, str]:
    """Return dict: normalized BLS/SOC code -> O*NET-SOC code (e.g. 11-1011.00)."""
    path = interim / "bls__onet_soc_to_nem_crosswalk.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    if df.empty or len(df.columns) < 2:
        return {}
    bls_col, onet_col = _detect_crosswalk_columns(df)
    if not bls_col or not onet_col:
        return {}
    out = {}
    for _, r in df.iterrows():
        bls_raw = str(r.get(bls_col, "")).strip() if pd.notna(r.get(bls_col)) else ""
        onet_raw = str(r.get(onet_col, "")).strip() if pd.notna(r.get(onet_col)) else ""
        if not bls_raw or not onet_raw:
            continue
        bls_norm = _normalize_soc(bls_raw)
        onet_norm = _normalize_soc(onet_raw)
        if bls_norm:
            out[bls_norm] = onet_norm
        # Also map raw forms
        if bls_raw and bls_raw not in out:
            out[bls_raw] = onet_norm
    return out


def bls_code_to_occupation_id(
    interim: Path,
    processed: Path,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns (bls_code_to_occ_id, bls_code_to_onet_soc).
    bls_code_to_occ_id: BLS/SOC code (normalized or raw) -> our occupation_id.
    bls_code_to_onet_soc: BLS code -> O*NET-SOC (for preserving original codes).
    """
    occ_path = processed / "occupations.parquet"
    if not occ_path.exists():
        return {}, {}
    occupations = pd.read_parquet(occ_path)
    occ_code_to_id = occupations.set_index(occupations["occupation_code"].astype(str).str.strip())["occupation_id"].to_dict()
    crosswalk = load_crosswalk_to_onet_soc(interim)
    bls_to_occ_id: dict[str, str] = {}
    bls_to_onet: dict[str, str] = {}
    for bls_code, onet_soc in crosswalk.items():
        bls_to_onet[bls_code] = onet_soc
        occ_id = occ_code_to_id.get(onet_soc)
        if occ_id:
            bls_to_occ_id[bls_code] = occ_id
    # Direct match: if BLS code equals O*NET-SOC in our occupations, use it
    for bls_code in set(bls_to_onet.values()) | set(crosswalk.values()):
        bls_norm = _normalize_soc(bls_code)
        if bls_norm and bls_norm not in bls_to_occ_id:
            occ_id = occ_code_to_id.get(bls_norm)
            if occ_id:
                bls_to_occ_id[bls_norm] = occ_id
                bls_to_onet[bls_norm] = bls_norm
    for code, occ_id in occ_code_to_id.items():
        if code not in bls_to_occ_id:
            bls_to_occ_id[code] = occ_id
            bls_to_onet[code] = code
    return bls_to_occ_id, bls_to_onet
