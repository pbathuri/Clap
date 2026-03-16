from __future__ import annotations

from workflow_dataset.utils.ids import stable_id


def test_stable_id() -> None:
    a = stable_id("onet", "15-1212.00", prefix="occ")
    b = stable_id("onet", "15-1212.00", prefix="occ")
    assert a == b
    assert a.startswith("occ_")
