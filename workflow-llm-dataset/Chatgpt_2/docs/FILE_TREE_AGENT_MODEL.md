# File-Tree Agent Model (Repo-Grounded)

This document maps the **workflow-tree model** to current repo structures. It is intentionally grounded in existing code; gaps are explicitly noted.

## Canonical tree (target)
- **Workflow**
  - **Task**
    - Prompts
    - Tools
    - Data sources
    - Memory/context
    - Policies/constraints
    - Checks/tests
    - Artifacts/results
  - **Subtask**
    - Same structure as Task

## Current repo mapping (what exists)

### Workflow (root)
- **Workflow episodes**: `src/workflow_dataset/workflow_episodes/*`
- **Portfolio/projects**: `project_case`, `portfolio`
- **Sessions**: `session/models.py`, `session/store.py`

### Task / Subtask
- **Job packs & routines**: `job_packs`, `copilot`, `routines`
- **Executor / tasks**: `executor`, `agent_loop`, `workflow_episodes`
- **Workflow inference**: `infer/workflow.py` (inferred steps, not persisted as tree)

### Prompts
- **Prompt templates**: `templates/`, `prompts/`
- **Investor demo scripts**: `investor_demo/*`, `investor-prototype/src/components/shell/PresenterDemoOverlay.tsx`

### Tools
- **Desktop adapters**: `desktop_adapters`, `desktop_bench`
- **CLI and command surfaces**: `cli.py`
- **Tool policies**: `governance`, `review_domains`, `sensitive_gates`

### Data sources
- **Ingestion & observation**: `ingest`, `observe`, `live_context`
- **Approved folders / path utils**: `path_utils.py`, `settings.py`

### Memory / context
- **Memory substrate + OS**: `memory_substrate`, `memory_os`, `memory_intelligence`, `memory_curation`
- **Context snapshots**: `context/*`, `workspace/*`

### Policies / constraints
- **Trust tiers & presets**: `trust/*`
- **Governance**: `governance/*`, `review_domains/*`
- **Supervised execution**: `supervised_loop/*`, `supervisory_control/*`

### Checks / tests
- **Validation & acceptance**: `validate/*`, `validation/*`, `tests/*`
- **Quality gates**: `quality_guidance/*`, `signal_quality/*`

### Artifacts / results
- **Outcomes**: `outcomes/*`
- **Session artifacts**: `session/artifacts.py`
- **Export / output adapters**: `export/*`, `output_adapters/*`

## Gaps to close (explicit)
- **No first-class persisted workflow-tree object**: workflows are spread across sessions, packs, episodes, and inferred steps.
- **Inheritance/defaults across workflow nodes** are not modeled explicitly.
- **Dynamic subtask spawning** is partial (exists in runtime patterns but not a unified tree).
- **Unified provenance across nodes** is incomplete (live adapter and mission-control provide partial provenance).

## Implication
The workflow-tree model is a **directional substrate**; core pieces exist but are not yet unified into a single persisted tree with inheritance, defaults, and node-level provenance.
