"""
M23J: Save job pack to disk.
"""

from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from workflow_dataset.job_packs.schema import JobPack, job_pack_to_dict
from workflow_dataset.job_packs.config import get_job_pack_path

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def save_job_pack(job: JobPack, repo_root: Path | str | None = None) -> Path:
    """Write job pack to data/local/job_packs/<job_pack_id>.yaml."""
    path = get_job_pack_path(job.job_pack_id, repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not job.updated_at:
        job.updated_at = utc_now_iso()
    data = job_pack_to_dict(job)
    if yaml:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path
