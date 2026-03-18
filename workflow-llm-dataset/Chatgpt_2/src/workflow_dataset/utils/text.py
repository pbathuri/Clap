from __future__ import annotations

import re


def normalize_whitespace(s: str | None) -> str:
    if s is None or not isinstance(s, str):
        return ""
    return " ".join(s.split())
