# M24G.1 — Capability Profiles + Domain/Pack Compatibility

Compatibility profiles between capabilities, domain packs, value packs, starter kits, and machine tiers. Worth-enabling vs not-worth-enabling logic and blocked/rejected reasoning for provisioning and activation.

## 1. Files modified

| File | Change |
|------|--------|
| `external_capability/compatibility.py` | VALUE_PACK_TO_CAPABILITY_CATEGORIES; BLOCKED_REASON_* constants; recommend_capabilities_for_pack(tier=); tier filtering and incompatible_tier blocked entries; pack_context.tier. |
| `external_capability/report.py` | format_capability_recommendation: include tier in pack context line. |
| `cli.py` | compatibility: optional --domain, --value-pack, --tier filters; recommend-pack: optional --pack, --domain, --field, --tier (no required --pack). |

## 2. Files created

| File | Purpose |
|------|--------|
| `tests/test_capability_compatibility_m24g1.py` | build_compatibility_matrix, recommend_capabilities_for_pack (value_pack, domain, tier), blocked reason codes, VALUE_PACK map, format_compatibility_report, format_capability_recommendation. |
| `docs/M24G1_CAPABILITY_COMPATIBILITY.md` | This doc. |

## 3. Sample compatibility report

```
=== Capability compatibility matrix ===

  openclaw  category=openclaw  status=optional  enabled=False
    domains: founder_ops, research_analyst
    value_packs: founder_ops_plus, analyst_research_plus
    starter_kits: founder_ops_starter, analyst_starter
    tiers: dev_full, local_standard

  coding_agent  category=coding_agent  status=optional  enabled=False
    domains: coding_development
    value_packs: developer_plus
    starter_kits: developer_starter
    tiers: dev_full, local_standard

  backend_ollama  category=ollama_model  status=missing  enabled=False
    domains: founder_ops, office_admin, logistics_ops, research_analyst, coding_development, document_knowledge_worker, multilingual, document_ocr_heavy
    value_packs: founder_ops_plus, analyst_research_plus, developer_plus, document_worker_plus, operations_logistics_plus
    starter_kits: founder_ops_starter, analyst_starter, developer_starter, document_worker_starter
    tiers: dev_full, local_standard, constrained_edge
```

## 4. Sample recommendation output

```
=== Capability recommendation ===

Pack context: value_pack=founder_ops_plus  domain_pack=founder_ops  task_class=desktop_copilot  tier=local_standard

[Worth enabling]
  backend_repo_local  reason=already_available  compatible=True  resource=low
  openclaw  reason=recommended_activation  compatible=True  resource=medium
  ollama_llama3.2  reason=recommended_activation  compatible=True  resource=high

[Not worth enabling for this pack]
  ide_editor  reason=low_value_for_this_pack  code=not_worth_for_pack

[Blocked / rejected]
  (none)
```

Blocked codes used: `rejected_by_policy`, `not_worth_for_pack`, `incompatible_tier`, `incompatible_domain`.

## 5. CLI usage

```bash
workflow-dataset capabilities external compatibility [--repo-root PATH] [--domain D] [--value-pack V] [--tier T]
workflow-dataset capabilities external recommend-pack [--pack P] [--domain D] [--field F] [--tier T] [--repo-root PATH]
```

Examples:
- `capabilities external compatibility --domain founder_ops`
- `capabilities external compatibility --value-pack developer_plus --tier local_standard`
- `capabilities external recommend-pack --pack founder_ops_plus`
- `capabilities external recommend-pack --domain coding_development --tier constrained_edge`
- `capabilities external recommend-pack --field research`

## 6. Tests run

```bash
pytest tests/test_capability_compatibility_m24g1.py -v
```

8 tests: build_compatibility_matrix, recommend_capabilities_for_pack (value_pack, domain, with_tier), blocked_reason_codes, value_pack_to_capability_categories, format_compatibility_report, format_capability_recommendation.

## 7. Next recommended step for the pane

- **Provisioning routing:** Use `recommend_capabilities_for_pack(value_pack_id=..., tier=...)` in provisioning or first-value flows to decide which capabilities to suggest for activation before running a value pack; surface “worth_enabling” and “blocked” with reason codes in UI or reports.
- **Mission control:** Optionally add a section that shows “recommended capabilities for current value pack” (from starter_kits / value_packs recommendation) using recommend_capabilities_for_pack with the recommended pack id and current tier.
- **Override file:** Persist per-source `supported_value_pack_ids` or `supported_domain_pack_ids` in external_capability_sources.json so operator customizations are reflected in the compatibility matrix.
