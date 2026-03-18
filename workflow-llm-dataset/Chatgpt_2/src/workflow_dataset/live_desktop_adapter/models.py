"""
M52: Live desktop adapter models — refresh policy, per-field status, shaped envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FieldProvenance(str, Enum):
    LIVE = "live"
    TIMEOUT = "timeout"
    ERROR = "error"
    STALE_CACHE = "stale_cache"
    SKIPPED_SLOW_PATH = "skipped_slow_path"  # presenter fast: text formatters not run live
    MISSING = "missing"


@dataclass
class RefreshPolicy:
    """Per-source timeout and presenter behavior."""
    timeout_seconds: float = 5.0
    presenter_fast_path: bool = False
    merge_last_good_cache: bool = True
    skip_slow_text_fetchers: bool = False  # workspace_home_text, day_status_text
    max_parallel_wait_seconds: float | None = None  # cap concurrent.futures.wait (default derived)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "presenter_fast_path": self.presenter_fast_path,
            "merge_last_good_cache": self.merge_last_good_cache,
            "skip_slow_text_fetchers": self.skip_slow_text_fetchers,
            "max_parallel_wait_seconds": self.max_parallel_wait_seconds,
        }


@dataclass
class AdapterMeta:
    """Honest wiring metadata for investor desktop UI."""
    adapter_version: str = "m52_1"
    presenter_mode_active: bool = False
    field_status: dict[str, str] = field(default_factory=dict)
    sources_ok_live: list[str] = field(default_factory=list)
    degraded_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_version": self.adapter_version,
            "presenter_mode_active": self.presenter_mode_active,
            "field_status": dict(self.field_status),
            "sources_ok_live": list(self.sources_ok_live),
            "degraded_notes": list(self.degraded_notes),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AdapterMeta":
        return cls(
            adapter_version=d.get("adapter_version", "m52_1"),
            presenter_mode_active=bool(d.get("presenter_mode_active", False)),
            field_status=dict(d.get("field_status") or {}),
            sources_ok_live=list(d.get("sources_ok_live") or []),
            degraded_notes=list(d.get("degraded_notes") or []),
        )
