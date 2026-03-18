# M33L.1 — Review Bundles + Common Handoff Kits

First-draft support for reusable review bundles, handoff kits for common workflow types, better linking from review output into approvals/planner/executor/workspace, and clearer readiness states (ready to send / approve / continue).

## Summary: files modified / created

| Type | Path |
|------|------|
| Modified | `src/workflow_dataset/in_flow/models.py` — HandoffPackage (readiness, nav_links), ReviewBundle, HandoffKit, READINESS_* |
| Modified | `src/workflow_dataset/in_flow/store.py` — bundle/kit save/load/list, get_in_flow_root |
| Modified | `src/workflow_dataset/in_flow/bundles.py` — config load, apply_review_bundle, create_handoff_from_kit, resolve_nav_links, set/get readiness |
| Modified | `src/workflow_dataset/in_flow/__init__.py` — exports for bundles, kits, readiness |
| Modified | `src/workflow_dataset/cli.py` — drafts_group, handoffs_group, in_flow_group + commands |
| Modified | `tests/test_in_flow.py` — M33L.1 tests |
| Created | `configs/in_flow/review_bundles.yaml` — sample review bundles |
| Created | `configs/in_flow/handoff_kits.yaml` — sample handoff kits |
| Created | `docs/M33L1_BUNDLES_AND_KITS.md` — this doc |

## 1. Review bundles

**Purpose:** Reusable checklist + summary template + decision questions applied at a workflow moment to create drafts (e.g. pre-approval, end-of-session, blocked escalation).

**Config:** `configs/in_flow/review_bundles.yaml` (optional). Store can also hold bundles in `data/local/in_flow/bundles.json`.

**Sample review bundle (from config):**

- **Path:** `configs/in_flow/review_bundles.yaml`
- **Example bundle id:** `pre_approval_review`
- **Fields:** `bundle_id`, `name`, `description`, `checklist_items`, `summary_template`, `decision_questions`, `draft_types`
- **Usage:** `workflow-dataset drafts apply-bundle --bundle-id pre_approval_review` (or via API: `apply_review_bundle("pre_approval_review", ...)`)

Other sample bundle ids in config: `end_of_session_handoff`, `blocked_escalation`.

## 2. Handoff kits

**Purpose:** Common workflow-type handoffs with title template, default target, default next steps, and nav links into approval_studio, planner, executor, workspace.

**Config:** `configs/in_flow/handoff_kits.yaml` (optional). Store: `data/local/in_flow/kits.json`.

**Sample handoff kit (from config):**

- **Path:** `configs/in_flow/handoff_kits.yaml`
- **Example kit id:** `approval_request`
- **Fields:** `kit_id`, `name`, `workflow_type`, `title_template`, `default_target`, `default_next_steps`, `nav_links` (list of `{label, view, command}`)
- **Usage:** `workflow-dataset handoffs create --kit approval_request` (or API: `create_handoff_from_kit("approval_request", ...)`)

Other sample kit ids: `end_of_session`, `blocked_escalation`, `next_phase_planner`.

## 3. Readiness states

- `ready_to_send` — handoff/draft ready to send (e.g. to artifact or queue)
- `ready_to_approve` — ready for human approval
- `ready_to_continue` — ready to continue in planner/executor/workspace

Set via `workflow-dataset handoffs set-readiness --id <handoff_id> --readiness ready_to_approve` or API `set_handoff_readiness(handoff_id, readiness)`.

## 4. Linking from review to approvals / planner / executor / workspace

- **HandoffPackage** has `nav_links` (list of `{label, view, command, ref}`).
- **resolve_nav_links(handoff_id)** returns the handoff’s nav_links and adds default links by `target` (approval_studio, planner, executor, workspace).
- CLI: `workflow-dataset handoffs show --id <id>` prints readiness and nav links; `workflow-dataset handoffs nav-links --id <id>` prints resolved links only.

## 5. CLI commands (M33L.1)

- **Drafts:** `drafts list`, `drafts apply-bundle --bundle-id <id>`
- **Handoffs:** `handoffs create` (optional `--kit <kit_id>`), `handoffs show --id <id>`, `handoffs set-readiness --id <id> --readiness <state>`, `handoffs nav-links --id <id>`
- **In-flow:** `in-flow bundles` (list bundles), `in-flow kits` (list kits)

## 6. Files touched

- **Models:** `src/workflow_dataset/in_flow/models.py` — `ReviewBundle`, `HandoffKit`, `HandoffPackage.readiness` / `nav_links`, `READINESS_*`
- **Store:** `src/workflow_dataset/in_flow/store.py` — bundle/kit save/load/list, `get_in_flow_root`
- **Bundles:** `src/workflow_dataset/in_flow/bundles.py` — config load, `apply_review_bundle`, `create_handoff_from_kit`, `resolve_nav_links`, `set_handoff_readiness`, `get_handoff_readiness`
- **Configs:** `configs/in_flow/review_bundles.yaml`, `configs/in_flow/handoff_kits.yaml`
- **CLI:** `src/workflow_dataset/cli.py` — `drafts_group`, `handoffs_group`, `in_flow_group`
- **Exports:** `src/workflow_dataset/in_flow/__init__.py`
- **Tests:** `tests/test_in_flow.py` — M33L.1 tests

## 7. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_in_flow.py -v
```

All 19 tests in `tests/test_in_flow.py` (including M33L.1: handoff readiness/nav_links roundtrip, list bundles/kits from store, apply_review_bundle, create_handoff_from_kit, resolve_nav_links, set/get_handoff_readiness).

## 8. Next recommended step for the pane

- **UI:** Surface readiness and nav links in the in-flow composer pane (e.g. badges for readiness, buttons/links for “Open approval”, “Open planner”, “Open executor”, “Open timeline”).
- **Flows:** When creating a handoff from a kit, pre-fill readiness from kit defaults (e.g. `approval_request` → `ready_to_approve`) and ensure `handoffs show` / `handoffs nav-links` are reachable from the same pane.
