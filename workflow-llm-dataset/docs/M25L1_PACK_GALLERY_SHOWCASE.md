# M25L.1 — Pack Demo Gallery + Certified Pack Showcase

First-draft operator-facing gallery and showcase for certified (and all) packs: purpose, roles, first-value flow, readiness/certification status, demo assets/screenshots, recommended install path.

---

## 1. Files modified

- **packs/gallery.py** — Gallery entry: added `name`, `version`; `recommended_install_path` uses resolved manifest path. Showcase: added [Name] line (name + version); demo line labeled "[Demo assets / screenshots]" with hint when none. Gallery report: per-pack name+version in header; optional "Demo assets:" line when present.
- **tests/test_pack_authoring.py** — Gallery entry test asserts `name`, `version`; showcase test asserts `[Name]` and demo-related content.

## 2. Files created

- **docs/M25L1_PACK_GALLERY_SHOWCASE.md** — This doc (sample entry, sample output, tests, next step).

## 3. Sample gallery entry

Single entry from `build_gallery_entry("analyst_plus", packs_dir=...)` (dict):

```json
{
  "pack_id": "analyst_plus",
  "name": "Analyst Plus",
  "version": "0.1.0",
  "purpose": "Analyst reporting and research workflows.",
  "roles_supported": ["analyst", "reporting"],
  "first_value_flow": "weekly_status → ops_report → research_brief",
  "certification_status": "certifiable",
  "readiness": "ready",
  "demo_assets": ["demos/README.md", "docs/README.md"],
  "recommended_install_path": "workflow-dataset packs install /path/to/data/local/packs/analyst_plus/manifest.json"
}
```

## 4. Sample certified pack showcase output

Output of `workflow-dataset packs showcase --id analyst_plus`:

```
=== Certified pack showcase: analyst_plus ===

[Name] Analyst Plus 0.1.0
[Purpose] Analyst reporting and research workflows.
[Roles supported] analyst, reporting
[First-value flow] weekly_status → ops_report → research_brief
[Certification status] certifiable  [Readiness] ready

[Demo assets / screenshots] demos/README.md, docs/README.md

[Recommended install]
  workflow-dataset packs install /abs/path/to/data/local/packs/analyst_plus/manifest.json
```

(When no demo assets: `(none — add under demos/ or docs/)`.)

## 5. Exact tests run

```bash
python3 -m pytest tests/test_pack_authoring.py -v -k "gallery or showcase"
```

Or full pack authoring suite:

```bash
python3 -m pytest tests/test_pack_authoring.py -v
```

Relevant tests: `test_build_gallery_entry` (includes name, version), `test_build_gallery`, `test_format_showcase` ([Name], demo), `test_format_gallery_report`.

## 6. Next recommended step for the pane

- **Gallery in mission control** — Add a one-line gallery summary to mission control state/report (e.g. `gallery_pack_count`, `certified_gallery_count`) and/or a “view gallery” next action, so operators can jump to `packs gallery` or `packs gallery --certified-only` from the dashboard.
- **Screenshot convention** — Optionally document or detect a standard path (e.g. `demos/screenshots/`) and list only those in “Demo assets / screenshots” for clearer operator-facing screenshots.
- **Showcase from mission control** — From the pack_authoring “highest_value_certifiable” list, add a drill-down or link that runs `packs showcase --id <pack_id>` for the top certifiable pack.
