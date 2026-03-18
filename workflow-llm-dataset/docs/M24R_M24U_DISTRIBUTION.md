# M24R–M24U — Distribution / Installer / Update / Field Deployment

First-draft distribution layer: install bundle, pack-aware install profile, update planner, field deployment checklists, deploy readiness. Local-first; no cloud; no auto-update.

## CLI usage

```bash
# Define installable bundle from current profile (writes to data/local/distribution/bundles/)
workflow-dataset deploy bundle
workflow-dataset deploy bundle --output /path/to/bundle.json

# Pack-aware install profile (list packs or generate for one pack)
workflow-dataset deploy install-profile
workflow-dataset deploy install-profile --pack founder_ops_starter
workflow-dataset deploy install-profile --pack analyst_starter --output /tmp/profile.txt

# Update plan (current vs desired; no execution)
workflow-dataset deploy update-plan
workflow-dataset deploy update-plan --desired /path/to/desired_state.json --output /tmp/plan.txt

# Field deployment checklist per pack
workflow-dataset deploy checklist --pack founder_ops_starter
workflow-dataset deploy checklist --pack founder_ops_plus
workflow-dataset deploy checklist --pack analyst_starter --output /tmp/checklist.txt

# Deploy readiness summary
workflow-dataset deploy readiness
workflow-dataset deploy readiness --output /tmp/readiness.txt

# M24U.1 Handoff pack (install profile, readiness, support bundle pointers, runbooks, first-value instructions, known limitations)
workflow-dataset deploy handoff-pack --pack founder_ops_starter
workflow-dataset deploy handoff-pack --pack analyst_starter --output /tmp/handoff

# One-page release bundle summary
workflow-dataset deploy release-bundle-summary --pack founder_ops_starter
workflow-dataset deploy release-bundle-summary --pack analyst_starter --output /tmp/release_summary.txt
```

Valid `--pack` values for checklists: `founder_ops_starter`, `analyst_starter`, `developer_starter`, `document_worker_starter`, `founder_ops_plus` (alias for founder_ops_starter).

## Sample install profile

For `--pack founder_ops_starter`:

```
Pack: founder_ops_starter  Name: Founder / operator starter
Runtime prereqs: ['config_exists', 'edge_checks', 'job_packs_loaded', 'macros_available']
Pack provisioning: ['bootstrap_profile', 'onboarding_status']
Trust checks: ['trust_cockpit_available', 'simulate_first']
First-value run: workflow-dataset macro run --id morning_ops --mode simulate
```

## Sample update plan

```
=== Update plan (staged; no execution) ===

Plan id: update_plan  Generated: 2025-03-16T12:00:00

[Steps]
  - none: Current state matches or no desired state specified.  (reversible=True)

[Risks]
  (none)

Reversible overall: True
(Operator-controlled. Run deploy/install steps manually if desired.)
```

## Sample field deployment checklist

For `deploy checklist --pack founder_ops_starter`:

```
=== Field deployment checklist: Founder / operator starter ===

[Runtime prerequisites]
  - config_exists
  - edge_checks
  - job_packs_loaded
  - macros_available

[Pack provisioning prerequisites]
  - bootstrap_profile
  - onboarding_status

[Trust / readiness checks]
  - trust_cockpit_available
  - simulate_first

[First-value run after install]
  Command: workflow-dataset macro run --id morning_ops --mode simulate
  Next: Run 'workflow-dataset inbox' for daily digest; add approvals then try --mode real for trusted jobs.

[Suggested commands (in order)]
  workflow-dataset package install-check
  workflow-dataset package first-run
  workflow-dataset onboarding status
  workflow-dataset kits recommend
  workflow-dataset rollout launch --id founder_demo
  workflow-dataset trust cockpit
  workflow-dataset rollout readiness
```

## Sample readiness output

```
=== Deploy readiness ===

Install check passed: False
Package ready for first user install: False
Rollout demo-ready: False
Rollout first-user-ready: False

Summary: install_check=fail  first_user_install=not_ready  demo_ready=no

See: workflow-dataset package install-check | package readiness-report | rollout readiness
```

## Tests run

```bash
pytest tests/test_distribution.py -v
```

Covers: bundle build/write, pack-aware install profile, field deployment profile, update plan (default and with desired), field checklist build/format, list_checklist_packs, deploy readiness build/format, partial/blocked deployment behavior.

## M24U.1 Handoff pack and release bundle summary

- **handoff-pack** — Writes a directory with `HANDOFF_README.md` and `handoff_summary.json` containing: install profile (pack, runtime/prereqs, first-value run), readiness summary, support bundle pointers, runbooks (ids and paths), first-value launch instructions (ordered commands), known limitations (static + from package_readiness.experimental).
- **release-bundle-summary** — One-page text summary: pack, readiness, support bundle pointer, first-value command, runbooks, known limitations count. Use for quick handoff or release notes.

## Remaining gaps for later refinement

- **Bundle versioning and manifest**: Version bundle contents (e.g. checksums) for reproducible install; today bundle is a snapshot.
- **Desired state schema**: Formal schema for --desired state and diff logic in update planner.
- **Reversible steps execution**: Optional dry-run or step-by-step execution of update plan (with confirmation); today plan is display-only.
- **Pack alias founder_ops_plus**: Map to founder_ops_starter or add dedicated pack if product defines it.
- **Tarball / artifact export**: Export bundle or profile as a single file for handoff to another machine.
- **Multi-machine / fleet**: No support for multiple target machines; single-machine local deploy only.
