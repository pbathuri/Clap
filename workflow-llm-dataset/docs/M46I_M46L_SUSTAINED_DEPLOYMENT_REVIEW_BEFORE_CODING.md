# M46I–M46L — Sustained Deployment Reviews + Stability Decision Packs: Before Coding

## 1. What deployment review structures already exist

| Area | What exists | Limitation for sustained deployment decision support |
|------|-------------|------------------------------------------------------|
| **production_launch/decision_pack** | build_launch_decision_pack: vertical, gates, blockers, warnings, recovery/trust/support posture; recommended_decision (launch \| launch_narrowly \| pause \| repair_and_review). | Point-in-time launch decision; no daily/weekly/rolling window; no explicit rollback; no assembled “stability” pack over long-run evidence. |
| **production_launch/review_cycles** | ProductionReviewCycle (at_iso, summary, findings, guidance_snapshot, recommended_actions, next_due_iso); build_production_review_cycle, record_review_cycle, list_review_cycles. | Snapshot + record; no first-class “stability window” or “evidence bundle” for a decision. |
| **production_launch/sustained_use** | SustainedUseCheckpoint (kind: session_5/session_10/day_7/auto); build_sustained_use_checkpoint, list_sustained_use_checkpoints. | Milestone checkpoints; not aggregated into a stability decision with continue/narrow/repair/pause/rollback. |
| **production_launch/post_deployment_guidance** | build_post_deployment_guidance: continue \| narrow \| rollback \| repair from release readiness, triage, reliability. | Single guidance output; no decision “pack” with rationale + evidence links; no explicit “continue with watch” or “pause deployment.” |
| **production_launch/ongoing_summary** | build_ongoing_production_summary: current review, latest cycle, checkpoint, post_deployment_guidance, launch decision summary, key_metrics. | Aggregates for display; no stability decision pack model or historical review tracking for “next scheduled deployment review.” |
| **reliability/** | Golden paths, harness, recovery playbooks, degraded profiles. | Health signal source; not a “stability decision” output. |
| **production_cut, release_readiness, triage, ops_jobs** | Scope, gates, cohort health, jobs. | Evidence sources; no unified “sustained deployment review” layer. |
| **mission_control** | production_launch slice: recommended_decision, post_deployment_guidance, latest_review_cycle_at, ongoing_summary_one_liner. | Read-only summary; no “current sustained-use recommendation,” “top stability risk,” “next scheduled deployment review,” or “strongest reason to continue or pause.” |

So: **Launch decision, review cycles, sustained-use checkpoints, and post-deployment guidance exist; missing a sustained deployment review layer that assembles long-run evidence into stability decision packs over daily/weekly/rolling windows with explicit continue/narrow/repair/pause/rollback and evidence bundles.**

---

## 2. What is missing for sustained deployment decision support

- **Sustained deployment review** — First-class review record over a stability window (daily/weekly/rolling) that references an evidence bundle and a stability decision pack.
- **Stability window** — Explicit time window (e.g. last 7 days, last 30 days) for which evidence is assembled.
- **Stability decision pack** — Single artifact: recommended decision (continue \| continue_with_watch \| narrow \| repair \| pause \| rollback), rationale, evidence_refs, and optional link to prior stable state for rollback.
- **Recommendation types** — Explicit models for continue, narrow, repair, pause, rollback (each with rationale and evidence links).
- **Evidence bundle** — Assembled snapshot: health summary, drift signals (if any), repair history, support/triage burden, operator burden, vertical-value retention, trust/review posture, production-cut scope compliance — without rebuilding those systems.
- **Decision outputs** — First-draft outputs: continue as-is, continue with watch, narrow scope, run repair bundle, pause deployment, rollback to prior stable; each with rationale and evidence links.
- **Historical review tracking** — Persisted sustained deployment reviews so we can report “next scheduled deployment review” and “last N reviews.”
- **Mission control slice** — current sustained-use recommendation, top stability risk, next scheduled review, watch/degraded/repair-needed state, strongest reason to continue or pause.

---

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M46I_M46L_SUSTAINED_DEPLOYMENT_REVIEW_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/stability_reviews/models.py` | SustainedDeploymentReview, StabilityWindow, StabilityDecisionPack, ContinueRecommendation, NarrowRecommendation, RepairRecommendation, PauseRecommendation, RollbackRecommendation, EvidenceBundle. |
| Store | `src/workflow_dataset/stability_reviews/store.py` | Persist reviews and decision packs under data/local/stability_reviews/. |
| Pack builder | `src/workflow_dataset/stability_reviews/pack_builder.py` | Generate decision pack from launch pack, ongoing summary, review cycles, sustained use, triage, reliability (read-only). |
| Outputs | `src/workflow_dataset/stability_reviews/decisions.py` | Map pack to continue/narrow/repair/pause/rollback output with rationale and evidence links. |
| CLI | `src/workflow_dataset/cli.py` | stability-reviews latest \| generate \| history; stability-decision-pack; stability-decision explain. |
| Mission control | `src/workflow_dataset/mission_control/state.py` | stability_reviews_state: current recommendation, top stability risk, next scheduled review, watch/degraded/repair state, strongest continue/pause reason. |
| Tests | `tests/test_stability_reviews.py` | Pack generation, evidence bundle, decision outcomes, contradictory evidence, no-review/weak-evidence, history. |
| Deliverable | `docs/M46I_M46L_SUSTAINED_DEPLOYMENT_REVIEW_DELIVERABLE.md` | Files, CLI, samples, tests, gaps. |

---

## 4. Safety/risk note

- **Do not hide instability** — If evidence points to repair/pause/rollback, the pack must surface it; no soft suppression of failure trends.
- **Do not overstate confidence** — When evidence is weak or missing, recommend “continue with watch” or “gather more evidence” rather than “continue as-is” with high confidence.
- **Do not blur repair with promotion** — Repair recommendations are for fixing issues before expanding; they are not production promotion gates.
- **Explicit pause/rollback** — Pause and rollback recommendations are first-class; rationale and evidence links must be present so the operator can act or override with full context.

---

## 5. Stability-decision principles

- **Evidence-based** — Every recommendation ties to an evidence bundle (health, gates, triage, reliability, sustained-use, etc.); no opaque “green/red.”
- **Inspectable** — Packs and evidence are stored and retrievable; CLI and mission control expose “why” and “what evidence.”
- **Windowed** — Reviews can be generated for a stability window (e.g. last 7 days) so long-run trends are visible.
- **Disciplined long-run** — The layer supports “should we continue, narrow, repair, pause, or roll back?” over longer time windows so the product can be operated safely over sustained use.

---

## 6. What this block will NOT do

- Rebuild release gates, reliability, production_launch, production_cut, triage, ops_jobs, or mission_control from scratch.
- Implement actual rollback execution (only recommend “rollback to prior stable state” with a reference; execution is out of scope).
- Replace launch-decision-pack or post-deployment guidance; we consume them and add a sustained-review layer on top.
- Add cloud deployment governance or generic analytics dashboards; local-first only.
- Automatically apply pause/rollback; recommendations are operator-facing and require explicit action.
