"""
M35D.1: Invalid/unsafe trust configuration reporting — clear validation and eligibility checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.trust.contracts import load_contracts, validate_contract, TrustedRoutineContract
from workflow_dataset.trust.tiers import get_tier
from workflow_dataset.trust.presets import get_preset, preset_allows_tier
from workflow_dataset.trust.eligibility import is_eligible, routine_type_for, max_tier_for_routine_under_preset


TRUST_DIR = "data/local/trust"
ACTIVE_PRESET_FILE = "active_preset.txt"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_active_preset_id(repo_root: Path | str | None = None) -> str | None:
    """Read active preset id from data/local/trust/active_preset.txt if present."""
    root = _repo_root(repo_root)
    path = root / TRUST_DIR / ACTIVE_PRESET_FILE
    if path.exists() and path.is_file():
        try:
            return path.read_text(encoding="utf-8").strip() or None
        except Exception:
            pass
    return None


@dataclass
class TrustConfigIssue:
    """Single issue: invalid, unsafe, or ineligible."""
    kind: str  # "invalid" | "unsafe" | "ineligible"
    contract_id: str = ""
    routine_id: str = ""
    message: str = ""
    details: list[str] = field(default_factory=list)


@dataclass
class TrustValidationReport:
    """Full report: valid flag, issues by kind, summary lines."""
    valid: bool = True
    invalid: list[TrustConfigIssue] = field(default_factory=list)
    unsafe: list[TrustConfigIssue] = field(default_factory=list)
    ineligible: list[TrustConfigIssue] = field(default_factory=list)
    active_preset_id: str | None = None
    summary_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "invalid": [
                {"contract_id": i.contract_id, "routine_id": i.routine_id, "message": i.message, "details": i.details}
                for i in self.invalid
            ],
            "unsafe": [
                {"contract_id": i.contract_id, "routine_id": i.routine_id, "message": i.message}
                for i in self.unsafe
            ],
            "ineligible": [
                {"contract_id": i.contract_id, "routine_id": i.routine_id, "message": i.message}
                for i in self.ineligible
            ],
            "active_preset_id": self.active_preset_id,
            "summary_lines": list(self.summary_lines),
        }


def _tier_order(tier_id: str) -> int:
    t = get_tier(tier_id)
    return t.order if t else -1


def validate_trust_config(
    contracts: list[TrustedRoutineContract] | None = None,
    active_preset_id: str | None = None,
    repo_root: Path | str | None = None,
) -> TrustValidationReport:
    """
    Validate trust configuration: contract schema, preset cap, and eligibility matrix.
    Returns report with invalid (schema/tier errors), unsafe (exceeds preset cap), ineligible (routine type not allowed at this tier).
    """
    root = _repo_root(repo_root)
    if contracts is None:
        contracts = load_contracts(root)
    preset_id = active_preset_id or get_active_preset_id(root)
    report = TrustValidationReport(active_preset_id=preset_id)
    preset = get_preset(preset_id) if preset_id else None

    for c in contracts:
        if not c.enabled:
            continue
        # 1. Invalid: contract validation errors
        valid_contract, errors = validate_contract(c)
        if not valid_contract:
            report.valid = False
            report.invalid.append(
                TrustConfigIssue(
                    kind="invalid",
                    contract_id=c.contract_id,
                    routine_id=c.routine_id,
                    message=f"Contract {c.contract_id} has validation errors.",
                    details=errors,
                )
            )
            continue
        # 2. Unsafe / ineligible: only when a preset is active
        if preset:
            max_tier = max_tier_for_routine_under_preset(preset_id, routine_type_for(c.routine_id))
            tier_ord = _tier_order(c.authority_tier_id)
            max_ord = _tier_order(max_tier) if max_tier else -1
            if max_tier and tier_ord >= 0 and max_ord >= 0 and tier_ord > max_ord:
                report.valid = False
                report.unsafe.append(
                    TrustConfigIssue(
                        kind="unsafe",
                        contract_id=c.contract_id,
                        routine_id=c.routine_id,
                        message=f"Contract {c.contract_id} tier {c.authority_tier_id} exceeds preset {preset_id} max for routine type {routine_type_for(c.routine_id)} ({max_tier}).",
                    )
                )
            else:
                eligible, reason = is_eligible(preset_id, c.routine_id, c.authority_tier_id)
                if not eligible:
                    report.valid = False
                    report.ineligible.append(
                        TrustConfigIssue(
                            kind="ineligible",
                            contract_id=c.contract_id,
                            routine_id=c.routine_id,
                            message=reason,
                        )
                    )

    # Summary lines for clear reporting
    if report.invalid:
        report.summary_lines.append(f"[INVALID] {len(report.invalid)} contract(s) with schema or tier errors.")
        for i in report.invalid[:5]:
            report.summary_lines.append(f"  - {i.contract_id}: {'; '.join(i.details[:2])}")
    if report.unsafe:
        report.summary_lines.append(f"[UNSAFE] {len(report.unsafe)} contract(s) exceed active preset cap.")
        for i in report.unsafe[:5]:
            report.summary_lines.append(f"  - {i.contract_id} ({i.routine_id}): {i.message[:80]}")
    if report.ineligible:
        report.summary_lines.append(f"[INELIGIBLE] {len(report.ineligible)} contract(s) not eligible under active preset.")
        for i in report.ineligible[:5]:
            report.summary_lines.append(f"  - {i.contract_id}: {i.message[:80]}")
    if report.valid and (report.invalid or report.unsafe or report.ineligible):
        report.valid = False
    if report.valid:
        report.summary_lines.append("Trust configuration is valid.")
        if preset_id:
            report.summary_lines.append(f"Active preset: {preset_id}.")

    return report


def format_validation_report(report: TrustValidationReport) -> str:
    """Human-readable validation report."""
    lines: list[str] = []
    lines.append("=== Trust configuration validation ===")
    if report.active_preset_id:
        lines.append(f"Active preset: {report.active_preset_id}")
    else:
        lines.append("Active preset: (none)")
    lines.append("")
    if report.valid:
        lines.append("Result: VALID")
    else:
        lines.append("Result: INVALID / UNSAFE / INELIGIBLE")
    lines.extend(report.summary_lines)
    return "\n".join(lines)
