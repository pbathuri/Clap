# Shot 2 — Implementation of the Chosen High-Leverage Step

You are working inside the `workflow-llm-dataset` project in the `Clap` repo.

This is Shot 2.
Use:

- the actual repo state after Shot 1
- all files in prompts/agent_os_pack/
- all docs created by Shot 1
- especially:
  - docs/REPO_REALITY.md
  - docs/ARCHITECTURE_RECONCILIATION.md
  - docs/NEXT_PHASE_EXECUTION_PLAN.md
  - docs/FILE_TREE_AGENT_MODEL.md
  - docs/SAFETY_AND_BOUNDARY_MODEL.md

Do not restart architecture planning.
Do not re-open broad design ideation.
Implement the exact highest-leverage step selected in Shot 1.

## Working mode

This is an integration-first implementation pass.

You must:

- preserve what already works
- avoid milestone sprawl
- avoid parallel architecture
- implement one coherent layer deeply
- validate with tests and exact outputs

## Hard rules

Do NOT:

- broaden scope beyond the chosen execution plan
- add speculative subsystems
- break stable state models casually
- copy external frameworks into the repo blindly
- introduce unsafe autonomy

Do:

- implement concretely
- keep the workflow-tree direction grounded
- improve real product coherence
- wire UI/backend/runtime meaningfully if in scope
- add tests/docs/runbooks as required by the chosen phase
- report remaining risks honestly

## Required implementation behavior

1. Re-read `docs/NEXT_PHASE_EXECUTION_PLAN.md`
2. Follow it as the controlling implementation plan
3. Update docs if implementation reality forces a necessary correction
4. Run the validation steps defined in the plan
5. Produce a final report in:
   - `docs/SHOT2_IMPLEMENTATION_REPORT.md`

That report must contain:

- files modified
- files created
- what was implemented
- what was deferred
- exact tests run
- failures fixed
- remaining risks
- exact recommended next step

## Final output required in chat

Your final response must include exactly:

1. Files Modified
2. Files Created
3. What Was Implemented
4. Tests Run
5. Remaining Risks
6. Recommended Next Step
