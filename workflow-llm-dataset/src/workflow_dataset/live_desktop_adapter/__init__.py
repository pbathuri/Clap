"""
M52: Live desktop adapter — timed fetch, cache merge, presenter-aware prefetch.
"""

from workflow_dataset.live_desktop_adapter.models import AdapterMeta, RefreshPolicy, FieldProvenance
from workflow_dataset.live_desktop_adapter.cache import load_last_good_snapshot, save_last_good_snapshot, cache_path
from workflow_dataset.live_desktop_adapter.pipeline import build_live_adapter_snapshot, prefetch_and_cache_snapshot

__all__ = [
    "AdapterMeta",
    "RefreshPolicy",
    "FieldProvenance",
    "load_last_good_snapshot",
    "save_last_good_snapshot",
    "cache_path",
    "build_live_adapter_snapshot",
    "prefetch_and_cache_snapshot",
]
