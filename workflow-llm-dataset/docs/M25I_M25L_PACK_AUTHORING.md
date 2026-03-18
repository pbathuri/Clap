# M25I–M25L — Pack Authoring SDK + Certification Harness

First-draft pack expansion factory: scaffold, validate, certify, scorecard. No marketplace or auto-publish; local and inspectable.

---

## 1. Files modified

- **packs/scaffold.py** — Prompt skeletons (prompts/system_guidance.md, prompts/task_prompt.md), tasks/workflow_defaults.json.skel, demos/README.md, tests/test_<pack_id>_smoke.py.skel.
- **packs/authoring_validation.py** — Trust/safety metadata checks; strict mode (missing docs/tests → errors); behavior.prompt_assets/task_defaults shape warnings.
- **packs/certification.py** — Checks: acceptance_scenario_compatibility, trust_readiness_signals; format_certification_report().
- **mission_control/state.py** — pack_authoring: added highest_value_certifiable (certifiable packs sorted by template count).
- **mission_control/report.py** — Pack authoring section prints highest_value_certifiable when present.
- **cli.py** — validate: --strict option; certify: uses format_certification_report for --output; validate passes full errors to exit.

## 2. Files created

- **docs/M25I_M25L_PRE_CODING_ANALYSIS.md** — Existing surfaces, gaps, file plan, safety, out-of-scope.
- **docs/M25I_M25L_PACK_AUTHORING.md** — This doc.

## 3. Exact CLI usage

```bash
# Scaffold new pack
workflow-dataset packs scaffold --id analyst_plus
workflow-dataset packs scaffold --id logistics_ops_plus --packs-dir data/local/packs

# Validate (optional --strict: missing docs/tests become errors)
workflow-dataset packs validate --id analyst_plus
workflow-dataset packs validate-manifest path/to/manifest.json
workflow-dataset packs validate --id analyst_plus --strict

# Run certification harness
workflow-dataset packs certify --id founder_ops_plus_v2
workflow-dataset packs certify --id founder_ops_plus_v2 --output cert_report.txt

# Pack scorecard
workflow-dataset packs scorecard --id founder_ops_plus_v2
workflow-dataset packs scorecard --id founder_ops_plus_v2 --output scorecard.txt
```

Mission control: `workflow-dataset mission-control` shows [Pack authoring] draft=, uncertified=, blocked=, certifiable=, and highest_value_certifiable: pack ids.

---

## 4. Sample scaffolded pack structure

After `workflow-dataset packs scaffold --id analyst_plus`:

```
data/local/packs/analyst_plus/
├── manifest.json          # pack_id, name, version, safety_policies, role_tags, prompts[], ...
├── prompts/
│   ├── system_guidance.md
│   └── task_prompt.md
├── tasks/
│   ├── README.md
│   └── workflow_defaults.json.skel
├── demos/
│   └── README.md
├── docs/
│   └── README.md
└── tests/
    └── test_analyst_plus_smoke.py.skel
```

---

## 5. Sample validation output

**Valid pack (after scaffold):**

```
Manifest valid.
```

**With warnings (no role_tags):**

```
[yellow]role_tags or workflow_tags recommended for resolution[/yellow]
[green]Manifest valid.[/green]
```

**Strict mode, missing docs:**

```
[red]docs/ directory missing (strict)[/red]
Exit 1
```

---

## 6. Sample certification report

Output of `workflow-dataset packs certify --id with_templates --output report.txt` (pack has templates + role_tags):

```
=== Pack certification: with_templates ===

Status: certifiable

[Checks]
  structural: pass
  installability: pass
  first_value_readiness: pass
    - Has templates
  acceptance_scenario_compatibility: pass
    - Has workflow/task templates for acceptance scenarios
  trust_readiness_signals: pass
    - safety_policies present and safe defaults
  conflict_simulation: pass
```

---

## 7. Sample scorecard

Output of `workflow-dataset packs scorecard --id with_templates`:

```
=== Pack scorecard: with_templates ===

[Roles supported] ops
[Tasks/workflows] weekly_status, ops_report
[Runtime requirements] 
[Conflict risk] none
[First-value strength] has_templates
[Acceptance readiness] ready
[Certification status] certifiable

[Recommended fixes]
  (none)
```

---

## 8. Exact tests run

```bash
python3 -m pytest tests/test_pack_authoring.py -v
```

Covers: manifest_skeleton, scaffold_pack (including prompt skeletons, demos/README, workflow_defaults.json.skel, test_*_smoke.py.skel), validate_pack_structure (and strict mode), validate_pack_full, conflict_risk_indicators, run_certification (and with_templates), acceptance_scenario_compatibility and trust_readiness_signals in checks, format_certification_report, build/format_pack_scorecard, blocked/invalid (missing manifest), gallery entry/build/format_showcase/format_gallery_report.

---

## 9. Remaining gaps for later refinement

- **Value-pack bridge** — No automatic mapping from capability pack to value_pack entry; operator creates value pack separately.
- **Behavior asset validation** — behavior.prompt_assets/task_defaults are checked for list shape only; no schema for each item.
- **Acceptance scenario list** — acceptance_scenario_compatibility is derived from templates only; no explicit acceptance scenario manifest yet.
- **Certification report machine-readable** — format_certification_report is human-readable; no JSON/structured export for CI.
- **Gallery from certifiable only** — gallery already has --certified-only; could be default in mission-control drill-down.
- **Scaffold from template** — No `--from-template` to clone an existing pack as starting point.
