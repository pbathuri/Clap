# M23Q — Trust / Evidence Cockpit + Operator Release Gates

## Objective

The trust/evidence cockpit gives the operator a single place to see:

1. **Benchmark trust** — latest run, outcome, coverage, regressions
2. **Approval readiness** — registry present, approved paths/scopes
3. **Job/macro trust state** — simulate-only vs trusted-for-real, approval-blocked
4. **Unresolved corrections** — proposed updates, review-recommended items
5. **Release gates** — unreviewed, package pending, staged, readiness report
6. **Safe to expand** — advisory: is the current system safe for broader use?

All outputs are **advisory only**. No automatic trust promotion or hidden state mutation.

---

## CLI

```bash
workflow-dataset trust cockpit [--repo-root PATH] [--output FILE]
workflow-dataset trust release-gates [--repo-root PATH]
workflow-dataset trust readiness-report [--repo-root PATH] [--output FILE]
```

- **trust cockpit** — Full trust/evidence report (benchmark, approval, job/macro, corrections, release gates).
- **trust release-gates** — Release gate status plus gate check results and safe-to-expand.
- **trust readiness-report** — Operator-facing “safe to expand?” summary and reasons.

---

## Data Model

- **trust/schema.py**: `BenchmarkTrust`, `ApprovalReadiness`, `JobMacroTrustState`, `UnresolvedCorrections`, `ReleaseGateStatus`, `GateCheck`, `TrustCockpit`. Built from `build_trust_cockpit()` output via `TrustCockpit.from_cockpit_dict()`.

---

## Release Gate Checks

- **no_regressions** — No benchmark regressions (critical for safe_to_expand).
- **approval_registry_ready** — Approval registry present (critical for real mode / safe_to_expand).
- **corrections_acceptable** — Proposed corrections and review-recommended within threshold (advisory).
- **benchmark_known** — Benchmark state known (advisory).
- **release_readiness_report** — Release readiness report exists (optional).

**Safe to expand** (advisory): `True` only when **no_regressions** and **approval_registry_ready** pass. Other gates do not block the flag but are reported.

---

## Mission Control

`get_mission_control_state()` includes **trust_cockpit**:

- `benchmark_trust_status`, `approval_registry_exists`, `release_gate_staged_count`
- **M23Q**: `safe_to_expand`, `failed_gates`, `release_gate_checks_summary`

---

## Sample Trust Cockpit Output

```
=== Trust / evidence cockpit ===

[Benchmark trust]
  latest_run: r123  outcome: pass  trust_status: ok
  simulate_only_coverage: 0.85  trusted_real_coverage: 0.0
  next: run desktop-bench run-suite --mode simulate

[Approval readiness]
  registry_exists: True  path: data/local/capability_discovery/approvals.yaml
  approved_paths: 0  approved_action_scopes: 2

[Job / macro trust state]
  total_jobs: 12  simulate_only: 8  trusted_for_real: 2  approval_blocked: 2
  recent_successful: 5  routines: 3

[Unresolved corrections]
  proposed_updates: 0
  review_recommended: 

[Release gate status]
  unreviewed: 0  package_pending: 0  staged: 0
  release_readiness_report_exists: False

(Operator-controlled. No automatic changes.)
```

---

## Sample Release Gate Report

```
=== Release gates ===

Unreviewed workspaces: 0
Package pending: 0
Staged items: 0
Release readiness report: missing

[Gate checks]
  PASS  No benchmark regressions — No regressions
  PASS  Approval registry present — Registry present
  PASS  Corrections acceptable — Proposed: 0, review recommended: 0 (within threshold)
  PASS  Benchmark state known — Latest: r123 outcome: pass
  FAIL  Release readiness report — Release readiness report missing (optional for expand).

Safe to expand (advisory): yes
```

---

## Sample Readiness Report

```
=== Trust / evidence readiness report ===

Advisory only. No automatic trust changes.

Safe to expand: YES

  • No critical gate failures (no regressions, approval registry ready).

[Release gate checks]
  PASS  No benchmark regressions — No regressions
  PASS  Approval registry present — Registry present
  ...

[Summary]
  Benchmark: r123  outcome: pass  regressions: 0
  Approval registry: present
  Proposed corrections: 0  review recommended: 0
```

---

## Tests

```bash
pytest tests/test_trust_cockpit.py -v
```

Covers: cockpit structure (including release_gate_checks, safe_to_expand), format_trust_cockpit, format_release_gates, evaluate_release_gates, safe_to_expand (critical fail / all pass), TrustCockpit.from_cockpit_dict, format_readiness_report.

---

## Files Modified / Created

| Action | Path |
|--------|------|
| Created | `src/workflow_dataset/trust/schema.py` — BenchmarkTrust, ApprovalReadiness, JobMacroTrustState, UnresolvedCorrections, ReleaseGateStatus, GateCheck, TrustCockpit |
| Created | `src/workflow_dataset/trust/release_gates.py` — evaluate_release_gates, safe_to_expand |
| Modified | `src/workflow_dataset/trust/cockpit.py` — run release gate checks, set safe_to_expand, safe_to_expand_reasons, failed_gates |
| Modified | `src/workflow_dataset/trust/report.py` — format_release_gates (gate checks + safe to expand), format_readiness_report |
| Modified | `src/workflow_dataset/cli.py` — trust readiness-report command |
| Modified | `src/workflow_dataset/trust/__init__.py` — export evaluate_release_gates, safe_to_expand |
| Modified | `src/workflow_dataset/mission_control/state.py` — trust_cockpit: safe_to_expand, failed_gates, release_gate_checks_summary |
| Modified | `tests/test_trust_cockpit.py` — M23Q tests for gates, safe_to_expand, schema, readiness report |
| Created | `docs/M23Q_TRUST_COCKPIT.md` — this doc |

---

## Next Phase

- **Dashboard UI**: Surface trust_cockpit.safe_to_expand and release_gate_checks_summary in the mission control / dashboard view.
- **Configurable gates**: Allow operator to enable/disable or weight specific gates (e.g. require release_readiness_report for “safe to expand” in some environments).
- **Regressions drill-down**: Link from cockpit regressions list to run compare or board view.
