"""
Strict JSON serialization for edge-desktop snapshots (json.tool / strict parsers).

Handles: NaN/Infinity floats, nested structures, strings with disallowed control chars.
Stdout emission must not go through Rich (markup can corrupt JSON containing `[...]`).
"""

from __future__ import annotations

import json
import math
from typing import Any


def sanitize_snapshot_for_json(obj: Any) -> Any:
    """Return a JSON-serializable tree safe for strict json.loads / python -m json.tool."""
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, int) and not isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, str):
        out: list[str] = []
        for ch in obj:
            o = ord(ch)
            if o == 0x7F or (o < 32 and ch not in "\n\r\t"):
                out.append(" ")
            else:
                out.append(ch)
        return "".join(out)
    if isinstance(obj, dict):
        return {str(k): sanitize_snapshot_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_snapshot_for_json(x) for x in obj]
    if isinstance(obj, set):
        return [sanitize_snapshot_for_json(x) for x in sorted(obj, key=str)]
    try:
        return str(obj)
    except Exception:
        return "<non-serializable>"


def dumps_snapshot_json(snap: dict[str, Any]) -> str:
    clean = sanitize_snapshot_for_json(snap)
    return json.dumps(clean, indent=2, ensure_ascii=True, allow_nan=False)
