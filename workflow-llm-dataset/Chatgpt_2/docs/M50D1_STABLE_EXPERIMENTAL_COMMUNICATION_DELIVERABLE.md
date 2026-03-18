# M50D.1 — Stable vs Experimental Communication Packs (Deliverable)

First-draft support for stable-v1 communication packs, experimental quarantine summaries, and clearer operator-facing explanation of what is safe to rely on vs what remains exploratory. Extends the M50A–M50D v1 freeze layer; the v1 freeze layer was **not** rebuilt.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/v1_contract/__init__.py` | Exported `StableV1CommunicationPack`, `SafeToRelyOnItem`, `DoNotRelyOnItem`, `ExperimentalQuarantineSummary`, `build_stable_v1_communication_pack`, `build_experimental_quarantine_summary`, `format_safe_vs_exploratory_text` |
| `src/workflow_dataset/v1_contract/mission_control.py` | Slice now includes `stable_pack_headline` and `experimental_summary_count`; builds pack and experimental summary when building slice |
| `src/workflow_dataset/cli.py` | Added `v1-contract stable-pack`, `v1-contract experimental-summary`, `v1-contract safe-vs-exploratory` commands |
| `tests/test_v1_contract.py` | Added tests for communication pack, experimental summary, format_safe_vs_exploratory_text; extended slice test for new keys |

---

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/v1_contract/communication_pack.py` | `build_stable_v1_communication_pack()`, `build_experimental_quarantine_summary()`, `format_safe_vs_exploratory_text()` |
| `docs/M50D1_STABLE_EXPERIMENTAL_COMMUNICATION_DELIVERABLE.md` | This deliverable |

Note: M50D.1 models (`SafeToRelyOnItem`, `DoNotRelyOnItem`, `StableV1CommunicationPack`, `ExperimentalQuarantineSummary`) were already added to `v1_contract/models.py` in a prior step; no new model file was created.

---

## 3. Sample stable-v1 communication pack

```json
{
  "pack_id": "stable_v1_communication_pack",
  "generated_at_utc": "2026-03-17T23:35:32.936855+00:00",
  "headline": "Stable v1: Founder / Operator. Safe to rely on core and advanced surfaces; quarantined is exploratory.",
  "safe_to_rely_on": [
    {
      "item_id": "support_commitment",
      "label": "Support commitment",
      "one_liner": "Stable v1: core and advanced surfaces supported; quarantined experimental; excluded out of scope.",
      "category": "support"
    },
    {
      "item_id": "migration",
      "label": "Migration continuity",
      "one_liner": "Continuity bundle and migration restore supported for v1.",
      "category": "migration"
    }
  ],
  "do_not_rely_on": [],
  "stable_surfaces_summary": "0 core and 0 advanced surfaces are supported for stable v1.",
  "stable_workflows_summary": "No workflow set locked.",
  "support_commitment_one_liner": "Stable v1: core and advanced surfaces supported; quarantined experimental; excluded out of scope.",
  "exploratory_summary_one_liner": "0 quarantined and 0 excluded; these are exploratory or out of scope."
}
```

With an active production cut and populated v1 core/advanced and quarantined/excluded surfaces, `safe_to_rely_on` and `do_not_rely_on` would list each surface/workflow/support item; categories are `surface`, `workflow`, `support`, `migration` for safe, and `quarantined`, `excluded` for do-not-rely-on.

---

## 4. Sample experimental quarantine summary

```json
{
  "summary_id": "experimental_quarantine_summary",
  "generated_at_utc": "2026-03-17T23:35:32.937600+00:00",
  "headline": "Experimental / out of scope: not safe to rely on for v1.",
  "one_liner": "0 quarantined and 0 excluded surfaces are not in stable v1; do not rely on them for supported use.",
  "items": [],
  "count": 0
}
```

With quarantined or excluded surfaces, each `items[]` entry includes `surface_id`, `label`, `why_exploratory`, and `reveal_rule` (for quarantined). `count` equals `len(quarantined_surfaces) + len(excluded_surfaces)`.

---

## 5. Exact tests run

```bash
python3 -m pytest tests/test_v1_contract.py -v --tb=short
```

**Result:** 12 passed.

- `test_build_stable_v1_contract_no_cut`
- `test_contract_to_dict`
- `test_get_v1_surfaces_classification`
- `test_explain_surface_core_or_unknown`
- `test_explain_surface_excluded`
- `test_build_freeze_report`
- `test_format_freeze_report_text`
- `test_v1_contract_slice` (includes `stable_pack_headline`, `experimental_summary_count`)
- `test_list_v1_core_advanced_quarantined_excluded`
- **`test_build_stable_v1_communication_pack`** (M50D.1)
- **`test_build_experimental_quarantine_summary`** (M50D.1)
- **`test_format_safe_vs_exploratory_text`** (M50D.1)

---

## 6. Next recommended step for the pane

- **Option A (product/ops):** Add a small “Safe vs exploratory” blurb to the mission-control report (or operator dashboard) that renders `stable_pack_headline` and `experimental_summary_count` (and optionally a link to `workflow-dataset v1-contract safe-vs-exploratory` or `stable-pack --json`).
- **Option B (automation):** Emit the stable-v1 communication pack (e.g. as JSON) on each freeze or release build so operators have a machine- and human-readable snapshot of what is safe to rely on.
- **Option C (content):** Refine one-liners and headlines in `communication_pack.py` (and/or add a content/config layer) so vertical-specific wording is consistent and on-message for operators.
