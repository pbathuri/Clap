# M47 Integration Pane — Three-Pane Merge Deliverable

## Merge order applied

1. **Pane 1 (M47A–M47D)** — Vertical UX Tightening + First-Value Compression  
2. **Pane 2 (M47E–M47H)** — High-Frequency Workflow Speed + Friction Reduction  
3. **Pane 3 (M47I–M47L)** — Quality Signals + Delightful Operator Guidance  

Rationale: Pane 1 tightens the top-level vertical path; Pane 2 speeds repeated workflows inside that path; Pane 3 adds quality and guidance on top of the tightened core.

---

## 1. Merge steps executed

| Step | Action | Location |
|------|--------|----------|
| 1 | Reordered mission_control **state** so Pane 1 is first: `vertical_excellence_state` (6j) then `vertical_speed_state` (6j2). Quality guidance remains in state as `quality_guidance` (later block). | `mission_control/state.py` |
| 2 | Reordered mission_control **report** to match: [Vertical excellence] (Pane 1) → [Vertical speed] (Pane 2) → [Quality guidance] (Pane 3) → [Review domains]… | `mission_control/report.py` |
| 3 | Added **[Quality guidance]** section to the report (was missing). It now prints `ready_to_act`, `most_ambiguous`, `next_recommended_guidance_improvement` from `state["quality_guidance"]`. | `mission_control/report.py` |

No file conflicts in the sense of git merge conflicts; the codebase already contained all three panes. Integration was **ordering + one additive report section**.

---

## 2. Files with conflicts

**None.** No git merge conflicts were present. All three panes were already in the same branch. Changes were:

- **state.py:** Comment and order swap (6j ↔ 6j2) so Pane 1 is 6j, Pane 2 is 6j2.
- **report.py:** (1) Order swap so Vertical excellence is reported before Vertical speed; (2) new [Quality guidance] block after Vertical speed.

---

## 3. How each “conflict” was resolved

- **Ordering:** Chosen order is Pane 1 → Pane 2 → Pane 3 everywhere (state build order and report section order). No functional conflict; vertical_excellence does not replace vertical_speed — it consumes friction from vertical_speed in `vertical_excellence.compression.list_friction_points()`.
- **Quality guidance in report:** Previously `quality_guidance` was in state but had no report section. Resolved by adding a dedicated **[Quality guidance]** block that reads `state.get("quality_guidance", {})` and prints the same keys the state slice provides.
- **Next-action overlap:** Both vertical_excellence (`recommend-next`) and quality_guidance (`guidance next-action`) suggest a “next” action. Left both additive: excellence = first-value path / blocked recovery; guidance = quality-signal / evidence-based next action. No scope broadening; no change to trust/review boundaries.

---

## 4. Tests run after each merge

Single integration pass was done (all three panes were already in repo; reorder + report addition is one logical merge).

**Recommended test slice:**

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_vertical_excellence.py tests/test_vertical_speed.py tests/test_quality_guidance.py tests/test_mission_control.py -v --tb=short
```

**Validation checklist:**

- **First-value path:** `test_vertical_excellence.py` (e.g. `test_assess_first_value_stage_not_started`, `test_recommend_next_for_vertical`, `test_get_role_tuned_entry_path_operator`).
- **High-frequency workflow speed:** `test_vertical_speed.py` (e.g. `test_list_frequent_workflows`, `test_build_friction_clusters`, `test_vertical_speed_slice`).
- **Quality / guidance:** `test_quality_guidance.py` (signals, guidance, presets, recovery packs).
- **Mission-control integration:** `test_mission_control.py` (state build and report format; ensure no KeyError on `vertical_excellence_state`, `vertical_speed_state`, `quality_guidance`).

*(Note: Full pytest can be slow due to heavy imports; run with a timeout or in CI.)*

---

## 5. Final integrated command surface

**Pane 1 — Vertical excellence** (`workflow-dataset vertical-excellence …`)

- `first-value` — current first-value stage and next step  
- `path-report` — first-value path report  
- `friction-points` — friction points and blocked cases  
- `recommend-next` [--new-user | --returning-user] [--role]  
- `entry-path` --role operator|reviewer|analyst  
- `on-ramp list` | `on-ramp show minimal|standard|full`  

**Pane 2 — Vertical speed** (`workflow-dataset vertical-speed …`)

- `top-workflows` — high-frequency workflows  
- `friction-report` — friction clusters  
- `action-route` — route queue item to action  
- `repeat-value` — repeat-value report  
- `fast-paths` — fast path list  
- `common-loop-bundles` — common loop bundles  
- `compression-report` — compression report  

**Pane 3 — Quality signals + guidance** (top-level + `workflow-dataset guidance …`)

- `quality-signals` — quality signals (next action, ambiguity, weak guidance)  
- `guidance next-action` — next best action with confidence  
- `guidance explain <id>` — explain guidance by id  
- `guidance ambiguity-report` — ambiguity report  
- `guidance preset show|set` — presets (concise, operator_first, review_heavy)  
- `guidance recovery-pack list|show` — recovery packs  
- `guidance operator-summary` — operator summary  

**Mission control**

- `workflow-dataset mission-control` — full state and report; report now includes [Vertical excellence], [Vertical speed], [Quality guidance] in that order.

---

## 6. Remaining risks

- **Two “next” surfaces:** `vertical-excellence recommend-next` and `guidance next-action` can both be shown. Risk: operator confusion. Mitigation: keep excellence for first-value/vertical path, guidance for quality/evidence; document in UI or help text.
- **quality_guidance state timing:** `quality_guidance` is built in a later block in `state.py`; if state is ever built in chunks, ensure this block runs so report does not see missing `quality_guidance`.
- **Test runtime:** Broad test slice can be slow; CI may need longer timeout or a smaller smoke set.
- **Scope creep:** All additions are additive and scoped to chosen vertical / operator guidance; no change to trust/review boundaries. Ongoing risk if new features broaden beyond the chosen vertical.

---

## 7. Exact recommendation for the next batch

1. **Unify “next” in one place (optional):** Add a single mission_control or dashboard “Next” line that prefers vertical_excellence when stage is not_started or blocked, and quality_guidance when first-value is reached.  
2. **Smoke test in CI:** Add a short smoke test that builds mission_control state and renders the report, asserting presence of `[Vertical excellence]`, `[Vertical speed]`, and `[Quality guidance]` in output.  
3. **Docs:** Add a short “M47 stack” section to the main docs: order (excellence → speed → quality), which CLI to use when, and that recommend-next is first-value and guidance next-action is quality-signal.  
4. **Leave as-is:** If no confusion in practice, keep both recommend-next and guidance next-action; no code change required.
