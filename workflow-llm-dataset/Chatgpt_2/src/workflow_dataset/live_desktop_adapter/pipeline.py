"""
M52: Timed parallel fetch, cache merge, presenter-aware live adapter pipeline.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.edge_desktop.fetchers import merge_patches
from workflow_dataset.live_desktop_adapter.models import AdapterMeta, RefreshPolicy
from workflow_dataset.live_desktop_adapter.cache import load_last_good_snapshot, save_last_good_snapshot


def _empty_snapshot(root: Path) -> dict[str, Any]:
    return {
        "generated_at": utc_now_iso(),
        "repo_root": str(root),
        "sources_ok": [],
        "errors": {},
        "readiness": None,
        "bootstrap_last": None,
        "onboarding_ready": None,
        "workspace_home": None,
        "workspace_home_text": None,
        "day_status": None,
        "day_status_text": None,
        "guidance_next_action": None,
        "operator_summary": None,
        "inbox": [],
        "adapter_meta": {},
    }


def _apply_cache_for(out: dict[str, Any], cache_snap: dict[str, Any] | None, fid: str) -> None:
    if cache_snap and cache_snap.get(fid) is not None:
        out[fid] = cache_snap[fid]


def _safe_run(fid: str, fn, root: Path):
    try:
        return (fid, fn(root), None)
    except BaseException as e:
        return (fid, None, e)


def build_live_adapter_snapshot(
    repo_root: Path | str | None = None,
    policy: RefreshPolicy | None = None,
) -> dict[str, Any]:
    """
    Parallel fetch with global wall-clock budget; merge last-good cache for failures/timeouts.
    """
    if repo_root is not None:
        root = Path(repo_root).resolve()
    else:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    pol = policy or RefreshPolicy()
    cache_snap = load_last_good_snapshot(root) if pol.merge_last_good_cache else None

    try:
        from workflow_dataset.investor_demo.presenter_mode import load_presenter_config

        presenter_on = load_presenter_config(root).enabled
    except Exception:
        presenter_on = False

    skip_text = pol.skip_slow_text_fetchers or (presenter_on and pol.presenter_fast_path)

    from workflow_dataset.edge_desktop.fetchers import FETCHERS

    meta = AdapterMeta(presenter_mode_active=presenter_on, field_status={})
    out = _empty_snapshot(root)
    live_sources: list[str] = []
    notes: list[str] = []

    to_run: list[tuple[str, Any]] = []
    for fid, fn, presenter_ok in FETCHERS:
        if skip_text and not presenter_ok:
            meta.field_status[fid] = "skipped_slow_path"
            if cache_snap and cache_snap.get(fid) is not None:
                out[fid] = cache_snap[fid]
                meta.field_status[fid] = "stale_cache"
            notes.append(f"{fid}: skipped_slow_path")
            continue
        to_run.append((fid, fn))

    n = len(to_run)
    per = max(1.5, pol.timeout_seconds)
    derived = min(50.0, per * max(4.0, n * 0.5 + 3))
    global_budget = pol.max_parallel_wait_seconds if pol.max_parallel_wait_seconds is not None else derived
    global_budget = max(0.5, min(60.0, global_budget))

    if to_run:
        ex = ThreadPoolExecutor(max_workers=min(10, n))
        try:
            futs = {ex.submit(_safe_run, fid, fn, root): fid for fid, fn in to_run}
            done_set, pending = wait(futs.keys(), timeout=global_budget)
            for fut in done_set:
                fid = futs[fut]
                try:
                    _fid, res, err = fut.result(timeout=0)
                    if err is not None:
                        meta.field_status[fid] = "error"
                        out.setdefault("errors", {})[fid] = str(err)[:500]
                        _apply_cache_for(out, cache_snap, fid)
                        if cache_snap and cache_snap.get(fid) is not None:
                            meta.field_status[fid] = "stale_cache"
                        else:
                            notes.append(f"{fid}: error_no_cache")
                    elif res is not None:
                        ok_src, patch = res
                        merge_patches(out, patch)
                        if ok_src:
                            live_sources.extend(ok_src)
                            meta.field_status[fid] = "live"
                        elif patch.get("errors"):
                            meta.field_status[fid] = "error"
                            _apply_cache_for(out, cache_snap, fid)
                            if cache_snap and cache_snap.get(fid) is not None:
                                meta.field_status[fid] = "stale_cache"
                        else:
                            meta.field_status[fid] = "live"
                except Exception as e:
                    meta.field_status[fid] = "error"
                    out.setdefault("errors", {})[fid] = str(e)[:500]
                    _apply_cache_for(out, cache_snap, fid)
                    if cache_snap and cache_snap.get(fid) is not None:
                        meta.field_status[fid] = "stale_cache"

            for fut in pending:
                fid = futs[fut]
                try:
                    fut.cancel()
                except Exception:
                    pass
                meta.field_status[fid] = "timeout"
                _apply_cache_for(out, cache_snap, fid)
                if cache_snap and cache_snap.get(fid) is not None:
                    meta.field_status[fid] = "stale_cache"
                    notes.append(f"{fid}: timeout→cache")
                else:
                    notes.append(f"{fid}: timeout_empty")
        finally:
            ex.shutdown(wait=False, cancel_futures=True)

    out["sources_ok"] = sorted(set(live_sources))
    meta.sources_ok_live = list(out["sources_ok"])
    meta.degraded_notes = notes[:25]
    out["adapter_meta"] = {
        **meta.to_dict(),
        "presenter_fast_path": skip_text,
        "global_budget_seconds": global_budget if to_run else 0,
    }
    return out


def prefetch_and_cache_snapshot(
    repo_root: Path | str | None = None,
    timeout_seconds: float = 25.0,
) -> dict[str, Any]:
    pol = RefreshPolicy(
        timeout_seconds=timeout_seconds,
        presenter_fast_path=False,
        merge_last_good_cache=True,
        skip_slow_text_fetchers=False,
    )
    snap = build_live_adapter_snapshot(repo_root, pol)
    snap["adapter_meta"] = dict(snap.get("adapter_meta") or {})
    snap["adapter_meta"]["prefetch_written_at"] = utc_now_iso()
    save_last_good_snapshot(snap, repo_root)
    return snap
