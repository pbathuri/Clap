"""
M51D.1: Demo bundle profiles + USB launch playbooks. Extends demo_usb; no bootstrap rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from workflow_dataset.demo_usb.models import BootstrapReadinessReport, DemoCapabilityLevel


DEFAULT_PROFILES_PATH = "configs/demo_usb_profiles.yaml"


@dataclass
class DemoBundleProfile:
    profile_id: str = ""
    label: str = ""
    summary: str = ""
    when_to_use: str = ""
    capability_hint: str = ""
    skip_model_paths: bool = False
    command_hints: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "summary": self.summary,
            "when_to_use": self.when_to_use,
            "capability_hint": self.capability_hint,
            "skip_model_paths": self.skip_model_paths,
            "command_hints": list(self.command_hints),
            "avoid": list(self.avoid),
        }


@dataclass
class UsbLaunchPlaybook:
    playbook_id: str = ""
    title: str = ""
    audience: str = ""
    preamble: str = ""
    steps: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "title": self.title,
            "audience": self.audience,
            "preamble": self.preamble.strip(),
            "steps": list(self.steps),
        }


def _embedded_profiles_doc() -> dict[str, Any]:
    """Used when PyYAML is unavailable or file missing; keep in sync with configs/demo_usb_profiles.yaml."""
    return {
        "profiles": {
            "full_demo": {
                "label": "Full demo",
                "summary": "Writable bundle, Python 3.10+, optional LLM config.",
                "when_to_use": "Prepared laptop with venv tested.",
                "capability_hint": "full",
                "skip_model_paths": False,
                "command_hints": [
                    "demo bootstrap",
                    "demo onboarding start",
                    "demo onboarding role --id founder_operator_demo",
                ],
                "avoid": ["Read-only USB without copy to disk"],
            },
            "lightweight_demo": {
                "label": "Lightweight demo",
                "summary": "CLI-first; minimal model/memory.",
                "when_to_use": "No GPU or no llm_training_full.yaml.",
                "capability_hint": "degraded",
                "skip_model_paths": True,
                "command_hints": ["demo readiness", "demo playbook --id usb_lightweight"],
                "avoid": ["Promising full local LLM without config"],
            },
            "degraded_laptop_demo": {
                "label": "Degraded laptop demo",
                "summary": "Honest thin path: reports and walkthrough only.",
                "when_to_use": "Low RAM, blocked readiness.",
                "capability_hint": "degraded",
                "skip_model_paths": True,
                "command_hints": ["demo env-report", "demo degraded-report"],
                "avoid": ["Writes outside bundle or ~/.workflow-demo-host"],
            },
        },
        "playbooks": {
            "usb_fresh_laptop": {
                "title": "USB on an unfamiliar laptop (safe path)",
                "audience": "operator",
                "preamble": "Stay local and bounded. Do not enable cloud sync for demo data.",
                "steps": [
                    {"action": "Copy if read-only", "detail": "Copy product folder to Desktop if USB blocked."},
                    {"action": "Venv", "detail": "python3 -m venv .venv && source .venv/bin/activate"},
                    {"action": "Deps", "detail": "pip install -e . or pip install pyyaml typer rich; PYTHONPATH=src"},
                    {"action": "Verify", "detail": "workflow-dataset demo env-report"},
                    {"action": "Bootstrap", "detail": "demo bootstrap && demo readiness"},
                    {"action": "Playbook", "detail": "demo playbook --id auto"},
                ],
            },
            "usb_lightweight": {
                "title": "Lightweight USB demo (no local model)",
                "audience": "operator",
                "preamble": "Degraded: lead with workflows, not inference.",
                "steps": [
                    {"action": "degraded-report", "detail": "workflow-dataset demo degraded-report"},
                    {"action": "Onboarding", "detail": "demo onboarding start && demo onboarding role"},
                ],
            },
            "usb_degraded_honest": {
                "title": "Blocked laptop — honest narrative",
                "audience": "operator",
                "preamble": "Do not force full demo.",
                "steps": [
                    {"action": "readiness", "detail": "demo readiness"},
                    {"action": "Remediation", "detail": "Copy to disk / Python 3.10+ / free disk per report."},
                ],
            },
        },
    }


def _load_raw(bundle_root: Path) -> dict[str, Any]:
    path = bundle_root / DEFAULT_PROFILES_PATH
    if path.is_file() and yaml is not None:
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(raw, dict) and raw.get("profiles"):
                return raw
        except Exception:
            pass
    return _embedded_profiles_doc()


def _bundle_root(bundle_root: Path | None) -> Path:
    if bundle_root is not None:
        return Path(bundle_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def load_demo_bundle_profiles(bundle_root: Path | None = None) -> dict[str, DemoBundleProfile]:
    root = _bundle_root(bundle_root)
    raw = _load_raw(root)
    profiles: dict[str, DemoBundleProfile] = {}
    for pid, p in (raw.get("profiles") or {}).items():
        if not isinstance(p, dict):
            continue
        profiles[pid] = DemoBundleProfile(
            profile_id=str(pid),
            label=str(p.get("label", pid)),
            summary=str(p.get("summary", "")),
            when_to_use=str(p.get("when_to_use", "")),
            capability_hint=str(p.get("capability_hint", "")),
            skip_model_paths=bool(p.get("skip_model_paths", False)),
            command_hints=list(p.get("command_hints") or []),
            avoid=list(p.get("avoid") or []),
        )
    return profiles


def load_usb_playbooks(bundle_root: Path | None = None) -> dict[str, UsbLaunchPlaybook]:
    root = _bundle_root(bundle_root)
    raw = _load_raw(root)
    out: dict[str, UsbLaunchPlaybook] = {}
    for bid, b in (raw.get("playbooks") or {}).items():
        if not isinstance(b, dict):
            continue
        steps = b.get("steps") or []
        step_list = []
        if isinstance(steps, list):
            for s in steps:
                if isinstance(s, dict):
                    step_list.append({
                        "action": str(s.get("action", "")),
                        "detail": str(s.get("detail", "")),
                    })
        out[str(bid)] = UsbLaunchPlaybook(
            playbook_id=str(bid),
            title=str(b.get("title", bid)),
            audience=str(b.get("audience", "")),
            preamble=str(b.get("preamble", "")),
            steps=step_list,
        )
    return out


def suggest_profile_for_readiness(rep: BootstrapReadinessReport) -> str:
    """Map capability to recommended profile id."""
    if rep.capability_level == DemoCapabilityLevel.BLOCKED:
        return "degraded_laptop_demo"
    if rep.capability_level == DemoCapabilityLevel.DEGRADED:
        if "RAM" in (rep.degraded_explanation or "") or "LLM" in (rep.degraded_explanation or ""):
            return "lightweight_demo"
        return "lightweight_demo"
    return "full_demo"


def suggest_playbook_for_readiness(rep: BootstrapReadinessReport) -> str:
    if rep.capability_level == DemoCapabilityLevel.BLOCKED:
        return "usb_degraded_honest"
    if rep.capability_level == DemoCapabilityLevel.DEGRADED:
        return "usb_lightweight"
    return "usb_fresh_laptop"


def format_operator_safe_launch_guide() -> str:
    """Static operator-facing guidance for unfamiliar laptops."""
    return "\n".join([
        "=== Safe launch on an unfamiliar laptop ===",
        "",
        "Before you run anything:",
        "  • Ask the host whether copying the demo folder to Desktop is OK (often required if USB is read-only).",
        "  • Prefer a new Python venv in the copied folder — do not pip install --user on their global Python without consent.",
        "  • Everything stays local: no cloud account, no telemetry toggle required for this demo path.",
        "",
        "During demo:",
        "  • Use only: demo env-report | demo readiness | demo bootstrap | demo onboarding …",
        "  • Writable state lives under the product folder and ~/.workflow-demo-host — say that aloud if investors ask.",
        "",
        "After demo:",
        "  • Host can delete the copied folder and ~/.workflow-demo-host/<bundle-name> to remove traces.",
        "",
    ])


def format_playbook_text(pb: UsbLaunchPlaybook, profile: DemoBundleProfile | None = None) -> str:
    lines = [
        f"=== Playbook: {pb.title} ===",
        f"Audience: {pb.audience}",
        "",
        pb.preamble.strip(),
        "",
    ]
    if profile:
        lines.append(f"Suggested profile: {profile.label} ({profile.profile_id})")
        lines.append(f"  {profile.summary}")
        lines.append("")
    for i, st in enumerate(pb.steps, 1):
        lines.append(f"{i}. {st.get('action', '')}")
        lines.append(f"   {st.get('detail', '')}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def format_profile_list_text(profiles: dict[str, DemoBundleProfile]) -> str:
    lines = ["=== Demo bundle profiles ===", ""]
    for pid, p in sorted(profiles.items()):
        lines.append(f"• {pid} — {p.label}")
        lines.append(f"  {p.summary[:140]}{'…' if len(p.summary) > 140 else ''}")
        lines.append("")
    lines.append("Use: workflow-dataset demo playbook --profile <id>")
    lines.append("")
    return "\n".join(lines)


def format_profile_detail_text(p: DemoBundleProfile) -> str:
    lines = [
        f"=== Profile: {p.label} ({p.profile_id}) ===",
        "",
        p.summary,
        "",
        f"When to use: {p.when_to_use}",
        f"Capability hint: {p.capability_hint}",
        "",
        "Suggested commands:",
    ]
    for c in p.command_hints:
        lines.append(f"  workflow-dataset {c}")
    lines.append("")
    lines.append("Avoid:")
    for a in p.avoid:
        lines.append(f"  • {a}")
    lines.append("")
    return "\n".join(lines)
