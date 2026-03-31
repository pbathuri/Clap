"""
Tool/app discovery based on approved folder evidence and adapter availability.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.capability_discovery.approval_registry import load_approval_registry, normalize_approved_paths
from workflow_dataset.capability_discovery.discovery import run_scan
from workflow_dataset.desktop_adapters import list_adapters
from workflow_dataset.local_operator.state_store import load_operator_state, save_operator_state
from workflow_dataset.utils.dates import utc_now_iso


TOOL_CATALOG: list[dict[str, Any]] = [
    {
        "tool_id": "finder",
        "label": "Finder",
        "extensions": [],
        "app_bundle": "/System/Library/CoreServices/Finder.app",
        "adapter_id": "finder_open",
    },
    {
        "tool_id": "terminal",
        "label": "Terminal",
        "extensions": [],
        "app_bundle": "/Applications/Utilities/Terminal.app",
        "adapter_id": "app_launch",
    },
    {
        "tool_id": "browser",
        "label": "Browser",
        "extensions": [],
        "app_bundle": "Safari.app",
        "adapter_id": "browser_open",
    },
    {
        "tool_id": "vscode",
        "label": "VS Code / Cursor",
        "extensions": [".code-workspace"],
        "app_bundle": "Visual Studio Code.app",
        "adapter_id": "file_ops",
    },
    {
        "tool_id": "figma",
        "label": "Figma",
        "extensions": [".fig"],
        "app_bundle": "Figma.app",
        "adapter_id": "",
    },
    {
        "tool_id": "notebooks",
        "label": "Jupyter Notebooks",
        "extensions": [".ipynb"],
        "app_bundle": "",
        "adapter_id": "file_ops",
    },
    {
        "tool_id": "spreadsheets",
        "label": "Spreadsheets",
        "extensions": [".csv", ".xlsx"],
        "app_bundle": "Microsoft Excel.app",
        "adapter_id": "file_ops",
    },
]


def _scan_extensions(paths: list[Path], exts: list[str], limit: int = 500) -> list[str]:
    hits: list[str] = []
    wanted = {e.lower() for e in exts}
    for root in paths:
        if not root.exists() or not root.is_dir():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in wanted:
                hits.append(str(p))
                if len(hits) >= limit:
                    return hits
    return hits


def discover_tools(
    repo_root: Path | str | None = None,
    apps_dir: Path | str | None = None,
) -> list[dict[str, Any]]:
    root = Path(repo_root).resolve() if repo_root else None
    apps_root = Path(apps_dir).resolve() if apps_dir else Path("/Applications")
    registry = load_approval_registry(root)
    approved_paths = normalize_approved_paths(
        registry.approved_paths, exclude_template_paths=True
    )
    active_paths = [
        Path(p.get("path")).expanduser().resolve()
        for p in approved_paths
        if p.get("revocation_state") == "active" and p.get("path")
    ]

    profile = run_scan(repo_root=root, approval_registry=registry)
    adapter_caps = {a.adapter_id: a for a in profile.adapters_available}
    approved_apps = set(registry.approved_apps or [])

    tools: list[dict[str, Any]] = []
    for tool in TOOL_CATALOG:
        evidence = _scan_extensions(active_paths, tool.get("extensions") or [])
        inferred = len(evidence) > 0
        bundle = tool.get("app_bundle") or ""
        if bundle and Path(bundle).is_absolute():
            installed = Path(bundle).exists()
        else:
            installed = bool(bundle and (apps_root / bundle).exists())
        actively_relevant = inferred

        adapter_id = tool.get("adapter_id") or ""
        adapter_cap = adapter_caps.get(adapter_id)
        adapter_supported = bool(adapter_cap and adapter_cap.available)
        permission_ready = False
        if adapter_id == "file_ops":
            permission_ready = len(active_paths) > 0
        elif bundle:
            permission_ready = not approved_apps or tool.get("label") in approved_apps

        if not adapter_supported:
            adapter_mode = "none"
        elif adapter_cap and adapter_cap.supports_real_execution and permission_ready:
            adapter_mode = "supervised_live"
        elif adapter_cap and adapter_cap.supports_simulate:
            adapter_mode = "simulated"
        else:
            adapter_mode = "propose_only"

        tools.append({
            "tool_id": tool.get("tool_id"),
            "label": tool.get("label"),
            "installed": installed,
            "inferred": inferred,
            "actively_relevant": actively_relevant,
            "adapter_supported": adapter_supported,
            "permission_ready": permission_ready,
            "adapter_mode": adapter_mode,
            "evidence_refs": evidence[:25],
        })

    state = load_operator_state(root)
    state["tool_registry"] = tools
    state["updated_at"] = utc_now_iso()
    save_operator_state(state, root)
    return tools
