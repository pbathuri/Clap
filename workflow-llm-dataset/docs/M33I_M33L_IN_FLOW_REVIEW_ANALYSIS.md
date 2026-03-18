# M33I–M33L In-Flow Review Studio + Draft / Handoff Composer — Pre-Coding Analysis

## 1. What review/composition/artifact surfaces already exist

- **review_studio**: TimelineEvent, InterventionItem; inbox built from approval queue, blocked runs, replan, skills, policy, stalled, graph routine/pattern. Store: inbox snapshot, operator_notes. No draft creation at workflow moments; no handoff package composer.
- **workspace**: WorkspaceArea, ActiveWorkContext; views include timeline, inbox. No in-flow draft or handoff creation.
- **action_cards**: ActionCard, HandoffTarget (CREATE_DRAFT, COMPILE_PLAN, QUEUE_SIMULATED, etc.). execute_handoff() routes to planner/executor/supervised_loop; CREATE_DRAFT uses handoff_params suggestion_id and materialize. Cards are “do this next” rather than “compose a draft here.”
- **planner**: Plan, PlanStep, Checkpoint, ExpectedArtifact. No model for “review checkpoint” or “staged summary” tied to a step.
- **session/artifacts**: add_artifact, list_artifacts, add_note, get_handoff(session_id), set_handoff(session_id, summary, next_steps). Session handoff is a single summary + next_steps JSON; no workflow-episode or step linkage.
- **release_readiness/handoff_pack**: build_handoff_pack (readiness + user pack + supportability), handoff_summary.md, load_latest_handoff_pack. Release/operator handoff only; not in-flow.
- **personal/draft_structure_engine**: DraftStructure (outline, sections, naming), persist to draft_structures dir; generate_draft_structures from context. No link to workflow episode, step, or review checkpoint; no “promote to artifact” or “hand off to approval/executor.”
- **executor**: list_runs, load_run (executor.hub). Runs have status (e.g. blocked); no composed draft/handoff attached to a run.
- **outcomes**: outcome history, patterns; no draft/handoff model.

## 2. What is missing for an in-flow review/composer layer

- **Explicit models**: workflow-scoped draft artifact (with episode/step/session/project refs); handoff package (from-workflow, contents, target); review checkpoint (linked to step or episode); staged summary / checklist / decision request; affected_workflow_step; review_status; revision_history.
- **Creation at key moments**: Create draft/handoff at “after step,” “at checkpoint,” “on block,” “end of episode” using active workflow/plan/session/outcomes.
- **Staging**: Stage summaries, checklists, decision requests and link to episode/step/project/artifacts.
- **Contextual review**: Inspect draft in context (with step/episode/artifact refs); revise or regenerate; attach notes; promote draft into artifact or review flow; hand off to approval, planner, executor, or workspace.
- **CLI**: drafts list/create/review; handoffs create/show (e.g. --from-workflow latest).
- **Mission control**: Latest draft waiting review, active review checkpoint, latest handoff package, workflow step awaiting composed output, recent promoted drafts.

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/in_flow/models.py` — DraftArtifact, HandoffPackage, ReviewCheckpoint, StagedSummary, StagedChecklist, StagedDecisionRequest, AffectedWorkflowStep, ReviewStatus, RevisionEntry |
| Store | Create | `src/workflow_dataset/in_flow/store.py` — save/load/list drafts, handoffs, checkpoints; revision history append |
| Composition | Create | `src/workflow_dataset/in_flow/composition.py` — create_draft(type, project_id, session_id, step_ref, episode_ref), create_handoff(from_workflow), stage_summary/checklist/decision |
| Review | Create | `src/workflow_dataset/in_flow/review.py` — get_draft_in_context, revise_draft, attach_note, promote_to_artifact, handoff_to_target (approval/planner/executor/workspace) |
| Init | Create | `src/workflow_dataset/in_flow/__init__.py` |
| CLI | Create | `src/workflow_dataset/in_flow/cli.py` — drafts list/create/review, handoffs create/show; register in main cli |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — in_flow block (latest_draft_waiting_review, active_review_checkpoint, latest_handoff, step_awaiting_output, recent_promoted) |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — [In-flow] section |
| Tests | Create | `tests/test_in_flow.py` |
| Docs | Create | `docs/M33I_M33L_IN_FLOW_REVIEW.md` |

## 4. Safety/risk note

- **No hidden generation**: Draft creation is explicit (CLI or API); content is staged/template-driven or from existing context (plan, session, outcomes), not autonomous LLM output without operator trigger.
- **Trust/approval**: Promote and handoff do not bypass approval; handoff to approval_studio queues for review; handoff to executor still gated by existing executor/approval semantics.
- **Local-only**: All state under data/local/in_flow/; no telemetry.

## 5. What this block will NOT do

- **Not a full document editor**: No rich WYSIWYG; drafts are structured content (markdown/outline) with revise/attach notes.
- **Not hidden autonomous content generation**: Creation is operator- or workflow-triggered (e.g. “drafts create --type status_summary”).
- **Not replacing review/approval**: Promoted drafts feed into existing review/artifact flows; handoffs point at existing surfaces (approval, planner, executor, workspace).
- **Not rebuilding** review_studio, workspace, planner, executor, session artifacts, or draft_structure_engine; we add an in-flow layer that uses them.
