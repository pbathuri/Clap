"""
M25I: Pack scaffolder — generate manifest skeleton, prompt/task/demo placeholders, docs/tests placeholders.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _default_packs_dir(repo_root: Path | str | None) -> Path:
    root = _repo_root(repo_root)
    return root / "data/local/packs"


def manifest_skeleton(pack_id: str) -> dict[str, Any]:
    """Return minimal valid manifest skeleton for pack_id."""
    return {
        "pack_id": pack_id,
        "name": pack_id.replace("_", " ").title(),
        "version": "0.1.0",
        "description": "",
        "role_tags": [],
        "industry_tags": [],
        "workflow_tags": [],
        "task_tags": [],
        "supported_modes": ["baseline", "adapter"],
        "required_models": [],
        "recommended_models": [],
        "retrieval_profile": {},
        "prompts": [],
        "templates": [],
        "output_adapters": [],
        "recipe_steps": [],
        "safety_policies": {
            "sandbox_only": True,
            "require_apply_confirm": True,
            "no_network_default": True,
        },
        "safety_constraints": [],
        "workflow_templates": [],
        "evaluation_tasks": [],
        "release_modes": ["baseline", "adapter"],
        "license": "",
        "source_repo": "",
        "dependencies": [],
        "supported_os_hardware": [],
    }


def scaffold_pack(
    pack_id: str,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> Path:
    """
    Create pack directory with manifest skeleton, prompts/, tasks/, demos/, docs/, tests/ placeholders.
    Returns path to pack directory (packs_dir/pack_id).
    """
    root = _repo_root(repo_root)
    base = Path(packs_dir) if packs_dir else _default_packs_dir(root)
    pack_dir = base / pack_id
    pack_dir.mkdir(parents=True, exist_ok=True)

    # manifest.json
    manifest_path = pack_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_skeleton(pack_id), indent=2), encoding="utf-8")

    # prompts/ with asset skeletons
    (pack_dir / "prompts").mkdir(exist_ok=True)
    (pack_dir / "prompts" / "system_guidance.md").write_text(
        "# System guidance\nReplace with pack-specific system guidance for the assistant.\n",
        encoding="utf-8",
    )
    (pack_dir / "prompts" / "task_prompt.md").write_text(
        "# Task prompt\nReplace with default task prompt or reference from manifest behavior.prompt_assets.\n",
        encoding="utf-8",
    )

    # tasks/ or workflow defaults skeleton
    (pack_dir / "tasks").mkdir(exist_ok=True)
    (pack_dir / "tasks" / "README.md").write_text(
        "# Task / workflow defaults\nPlace workflow or task template ids here. Reference from manifest workflow_templates or templates.\n",
        encoding="utf-8",
    )
    task_defaults_skel = {
        "workflow_templates": [],
        "task_defaults": [],
        "comment": "Optional: add workflow template ids and task-level defaults; sync with manifest.",
    }
    (pack_dir / "tasks" / "workflow_defaults.json.skel").write_text(
        json.dumps(task_defaults_skel, indent=2),
        encoding="utf-8",
    )

    # demos/ with README placeholder
    (pack_dir / "demos").mkdir(exist_ok=True)
    (pack_dir / "demos" / "README.md").write_text(
        f"# Demos for {pack_id}\nAdd demo assets or task_demo ids used by this pack.\n",
        encoding="utf-8",
    )

    # docs/
    (pack_dir / "docs").mkdir(exist_ok=True)
    (pack_dir / "docs" / "README.md").write_text(
        f"# Pack: {pack_id}\nDescribe usage, first-value flow, and requirements.\n",
        encoding="utf-8",
    )

    # tests/ with smoke test placeholder
    (pack_dir / "tests").mkdir(exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in pack_id)
    (pack_dir / "tests" / f"test_{safe_id}_smoke.py.skel").write_text(
        f'"""Smoke test placeholder for pack {pack_id}. Rename to .py and run pytest."""\n'
        "def test_manifest_loads():\n"
        "    import json\n"
        "    from pathlib import Path\n"
        "    p = Path(__file__).resolve().parent.parent / \"manifest.json\"\n"
        "    assert p.exists()\n"
        "    data = json.loads(p.read_text())\n"
        "    assert data.get(\"pack_id\")\n"
        "    assert data.get(\"name\")\n",
        encoding="utf-8",
    )

    return pack_dir
