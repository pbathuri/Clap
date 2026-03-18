"""Stable hashes for IDs."""

from __future__ import annotations

import hashlib


def stable_id(*parts: str, prefix: str = "") -> str:
    """Stable short id from string parts. Optional prefix (e.g. 'q') prepended."""
    digest = hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()
    return (prefix + digest) if prefix else digest
