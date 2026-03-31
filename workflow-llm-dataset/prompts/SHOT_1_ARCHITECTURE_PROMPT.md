# Shot 1 — Architecture, Reconciliation, and Execution Plan

You are working inside the `workflow-llm-dataset` project in the `Clap` repo.

You are running in the same live workspace previously used by Cursor Auto Mode.
Do not ask for file uploads if the files already exist in the workspace.
Do not treat this as a cold start.

Use these files as grounding:

- prompts/agent_os_pack/00_repo_reality.md
- prompts/agent_os_pack/01_product_north_star.md
- prompts/agent_os_pack/02_control_and_permission_model.md
- prompts/agent_os_pack/03_workflow_tree_model.md
- prompts/agent_os_pack/04_reference_framework_mapping.md
- prompts/agent_os_pack/05_system_architecture.md
- prompts/agent_os_pack/06_runtime_and_models.md
- prompts/agent_os_pack/07_domain_and_tool_priority.md
- prompts/agent_os_pack/08_uiux_and_desktop_operator.md
- prompts/agent_os_pack/09_safety_compliance_enterprise.md
- prompts/agent_os_pack/10_phased_build_roadmap.md
- prompts/agent_os_pack/11_quality_gates_and_validation.md
- prompts/agent_os_pack/12_investor_and_product_paths.md
- prompts/agent_os_pack/13_execution_scope_now.md

Also inspect the actual repo deeply before coding.

## Your job in Shot 1

Do not start a giant implementation blindly.

Your job is to:

1. deeply inspect the current repo and workspace
2. reconcile current code reality against the architecture pack
3. determine what is already real, partial, stale, duplicated, or missing
4. define the exact highest-leverage implementation step
5. produce implementation-ready architecture outputs
6. avoid hallucinating systems that do not exist in the repo

## Hard rules

Do NOT:

- rewrite the whole repo in Shot 1
- add major dependencies yet unless absolutely required for the chosen next step
- produce vague strategy memos without file-level consequences
- ignore existing product surfaces
- trust historical reports without code verification

Do:

- inspect actual code
- verify UI/backend/demo state
- verify mock vs live vs cached vs fallback
- map existing systems to the workflow-tree model
- identify duplication and drift
- choose one high-leverage next implementation pass

## Required outputs of Shot 1

Create/update these repo files:

1. `docs/REPO_REALITY.md`
   - what is real now
   - what is partial
   - what is stale
   - what must not be rebuilt

2. `docs/REFERENCE_FRAMEWORK_MAPPING.md`
   - explicit adopt / wrap / reject mapping for each reference framework

3. `docs/FILE_TREE_AGENT_MODEL.md`
   - formal workflow-tree model grounded to this repo

4. `docs/SAFETY_AND_BOUNDARY_MODEL.md`
   - permission, approval, supervision, and enterprise control model

5. `docs/INVESTOR_PATH_AND_PRODUCT_PATH.md`
   - current investor path vs current product path vs convergence

6. `docs/OSS_EVALUATION_POLICY.md`
   - how external OSS will be evaluated and prevented from causing sprawl

7. `docs/ARCHITECTURE_RECONCILIATION.md`
   - code-grounded reconciliation summary
   - duplication/drift map
   - top risks
   - highest-leverage next build step

8. `docs/NEXT_PHASE_EXECUTION_PLAN.md`
   - exact next implementation step
   - target files
   - acceptance criteria
   - test plan

## Final output required in chat

Your final response must include exactly:

1. Files / Paths Actually Used
2. Reconciliation Summary
3. Mocked vs Live
4. Top Remaining Risks
5. Chosen Next Step
6. Exact Next Prompt
7. Execution Decision

## Execution decision rule

At the end of Shot 1:

- if the next step is obvious and implementation-ready, say “begin implementation now” and then stop
- do NOT actually start implementing until Shot 2 unless explicitly instructed otherwise
