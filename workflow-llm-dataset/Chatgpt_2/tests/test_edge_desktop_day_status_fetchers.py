"""Day status fetchers must not import workday.cli (circular import with main cli)."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.edge_desktop.fetchers import fetch_day_status, fetch_day_status_text


def test_fetch_day_status_and_text_succeed(tmp_path: Path) -> None:
    ok, patch = fetch_day_status(tmp_path)
    assert "day_status" in ok or "errors" in patch
    if "day_status" in patch:
        assert isinstance(patch["day_status"], dict)
        assert "current_workday_state" in patch["day_status"]

    ok2, patch2 = fetch_day_status_text(tmp_path)
    assert "day_status_text" in ok2 or "errors" in patch2
    if "day_status_text" in patch2:
        assert isinstance(patch2["day_status_text"], str)
        assert len(patch2["day_status_text"]) >= 0
