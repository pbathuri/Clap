"""Load optional configs/demo_usb.yaml for thresholds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


def load_demo_usb_config(bundle_root: Path) -> dict[str, Any]:
    path = bundle_root / "configs" / "demo_usb.yaml"
    if not path.is_file() or yaml is None:
        return _defaults()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return _defaults()
    out = _defaults()
    if isinstance(raw, dict):
        out["min_disk_free_mb"] = int(raw.get("min_disk_free_mb", out["min_disk_free_mb"]))
        out["min_ram_mb_degraded_below"] = int(raw.get("min_ram_mb_degraded_below", out["min_ram_mb_degraded_below"]))
        out["python_min_major"] = int(raw.get("python_min_major", out["python_min_major"]))
        out["python_min_minor"] = int(raw.get("python_min_minor", out["python_min_minor"]))
    return out


def _defaults() -> dict[str, Any]:
    return {
        "min_disk_free_mb": 512,
        "min_ram_mb_degraded_below": 4096,
        "python_min_major": 3,
        "python_min_minor": 10,
    }
