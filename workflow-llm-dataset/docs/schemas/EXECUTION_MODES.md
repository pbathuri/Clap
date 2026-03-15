# Execution Modes

## Purpose

Execution modes define what the agent is allowed to do with respect to the user’s real system. The default is **simulate**: the agent proposes and demonstrates in a safe environment and makes **no** changes to the user’s actual machine unless the user explicitly approves.

## Modes

| Mode | Description | Local system changes |
|------|-------------|----------------------|
| **observe** | Agent only learns from observation and teaching; no actions, no suggestions. | None. |
| **simulate** | Agent proposes actions and runs them inside a sandbox/virtual environment; user sees planned outputs and dry-runs. | None to real system. |
| **assist** | Agent can prepare actions (e.g. drafts, scripts); user explicitly approves each execution before it runs on the real system. | Only after explicit per-action approval. |
| **automate** | Agent can act on the real system within user-approved boundaries (e.g. specific paths, apps, or time windows). | Yes, within boundaries. |
| **delegate** | Future: agent delegates to another service or human; not in v1. | N/A for v1. |

## Default

- **Default mode is `simulate`.** No writes to the user’s real filesystem, apps, or network unless the user switches to `assist` or `automate` and has configured approval boundaries.

## Configuration

- `execution_mode`: one of `observe` \| `simulate` \| `assist` \| `automate`.
- For `assist` and `automate`: optional `approval_boundaries` (paths, apps, time windows) and/or require-explicit-approval flag.

## v1 scope

- Implement mode selection and policy checks in scaffolding.
- Real sandbox runner and approval flow are later milestones.
