"""
M52: Live desktop adapter — timed pipeline, cache merge, presenter fast path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.live_desktop_adapter.models import RefreshPolicy
from workflow_dataset.live_desktop_adapter.cache import save_last_good_snapshot, load_last_good_snapshot
from workflow_dataset.live_desktop_adapter.pipeline import build_live_adapter_snapshot, prefetch_and_cache_snapshot


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_cache_roundtrip(tmp_path: Path):
    snap = {"generated_at": "t", "readiness": {"x": 1}, "sources_ok": ["readiness"], "errors": {}}
    save_last_good_snapshot(snap, tmp_path)
    loaded = load_last_good_snapshot(tmp_path)
    assert loaded is not None
    assert loaded["readiness"] == {"x": 1}


def test_adapter_meta_shape():
    pol = RefreshPolicy(
        timeout_seconds=8.0,
        merge_last_good_cache=False,
        max_parallel_wait_seconds=8.0,
    )
    snap = build_live_adapter_snapshot(_repo(), pol)
    assert "adapter_meta" in snap
    am = snap["adapter_meta"]
    assert am.get("adapter_version") == "m52_1"
    assert "field_status" in am
    assert isinstance(am["field_status"], dict)
    assert len(snap.get("sources_ok") or []) >= 1


def test_timeout_uses_stale_cache(tmp_path: Path):
    from unittest.mock import patch

    fake = {
        "generated_at": "cached",
        "repo_root": str(tmp_path),
        "sources_ok": ["readiness"],
        "errors": {},
        "readiness": {"capability_level": {"value": "from_cache"}},
        "bootstrap_last": None,
        "onboarding_ready": {"ready_to_assist": {"ready": True}},
        "workspace_home": None,
        "workspace_home_text": None,
        "day_status": None,
        "day_status_text": None,
        "guidance_next_action": None,
        "operator_summary": None,
        "inbox": [],
    }
    save_last_good_snapshot(fake, tmp_path)
    pol = RefreshPolicy(timeout_seconds=5.0, merge_last_good_cache=True)

    def force_all_pending(pending_set, **kwargs):
        return (set(), pending_set)

    with patch("workflow_dataset.live_desktop_adapter.pipeline.wait", side_effect=force_all_pending):
        snap = build_live_adapter_snapshot(tmp_path, pol)
    assert snap.get("readiness", {}).get("capability_level", {}).get("value") == "from_cache"
    st = snap["adapter_meta"]["field_status"]
    assert any(v == "stale_cache" for v in st.values())


def test_presenter_fast_skips_text_fetchers(tmp_path: Path):
    from unittest.mock import patch

    root = tmp_path
    (root / "data" / "local" / "investor_demo").mkdir(parents=True)
    (root / "data" / "local" / "investor_demo" / "presenter_mode.json").write_text(
        json.dumps({"enabled": True, "five_minute_script_active": True}), encoding="utf-8"
    )
    mini_fetchers = [
        ("readiness", lambda r: (["readiness"], {"readiness": {"ok": True}}), True),
        ("workspace_home_text", lambda r: (["workspace_home_text"], {"workspace_home_text": "FULL"}), False),
        ("day_status_text", lambda r: (["day_status_text"], {"day_status_text": "DAY"}), False),
    ]
    pol = RefreshPolicy(
        timeout_seconds=5.0,
        presenter_fast_path=True,
        merge_last_good_cache=False,
        skip_slow_text_fetchers=False,
    )
    with patch("workflow_dataset.edge_desktop.fetchers.FETCHERS", mini_fetchers):
        snap = build_live_adapter_snapshot(root, pol)
    assert snap["adapter_meta"].get("presenter_mode_active") is True
    assert snap["adapter_meta"].get("presenter_fast_path") is True
    assert snap.get("readiness") == {"ok": True}
    assert snap["adapter_meta"]["field_status"].get("workspace_home_text") == "skipped_slow_path"
    assert snap["adapter_meta"]["field_status"].get("day_status_text") == "skipped_slow_path"


@pytest.mark.integration
def test_prefetch_populates_cache():
    root = _repo()
    snap = prefetch_and_cache_snapshot(root, timeout_seconds=35.0)
    assert load_last_good_snapshot(root) is not None
    assert len(snap.get("sources_ok") or []) >= 3
