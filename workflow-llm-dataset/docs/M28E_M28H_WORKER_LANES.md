# M28E–M28H — Bounded Worker Lanes + Delegated Subplans

## Purpose

Bounded, supervised delegation: split a project goal into delegated subplans, assign them to worker lanes, keep each lane narrow and inspectable, and return artifacts/results to the main supervised loop. No open-ended multi-agent autonomy; operator visibility over active/blocked lanes and results awaiting review.

## Concepts

- **Worker lane** — Bounded execution lane tied to a project and goal, with scope, permissions, status, optional subplan, artifacts, and handoff.
- **Delegated subplan** — Explicit subplan with scope, expected outputs, trust/approval mode, and stop conditions; derived from planner output or goal text.
- **Lane scope** — Narrow scope (e.g. `extract_only`, `summarize_only`) and optional allowed step classes.
- **Lane permissions** — `simulate_only` or `trusted_real_if_approved`; approval can be required before real execution.
- **Lane status** — `open` | `running` | `blocked` | `completed` | `closed`.
- **Lane artifact/result** — Label, path_or_type, step_index; collected and returned to parent.
- **Lane handoff** — Record of delivering lane results to the parent project/loop (delivered / acknowledged).
- **Lane failure/blocked** — Reason, step_index, approval_scope; stored on the lane when blocked.

## CLI

- `workflow-dataset lanes list` — List lanes (optional `--project`, `--status`, `--limit`).
- `workflow-dataset lanes create --project <id> --goal <goal_id>` — Create a lane with a delegated subplan for that project/goal.
- `workflow-dataset lanes status --id <lane_id>` — Show lane status and summary.
- `workflow-dataset lanes simulate --id <lane_id>` — Simulate the lane’s subplan (no executor run).
- `workflow-dataset lanes results --id <lane_id>` — Show artifacts/results for the lane.
- `workflow-dataset lanes handoff --id <lane_id>` — Deliver lane results as handoff to parent.
- `workflow-dataset lanes close --id <lane_id>` — Close the lane.

## Mission control

The mission control report includes a **[Worker lanes]** section: active count, blocked count, results awaiting review, total lanes, and `next_handoff_needed` with a suggested `lanes results --id` command.

State keys under `worker_lanes`: `active_lanes`, `blocked_lanes`, `results_awaiting_review`, `parent_project_to_lanes`, `next_handoff_needed`, `total_lanes`.

## Storage

Lanes are stored under `data/local/lanes/lanes/<lane_id>/lane.json`.

## Safety

- Lanes do not bypass policy/trust/approval; permissions and approval_mode are explicit.
- No hidden background swarms; all lanes are listable and closable.
- Results and handoffs are inspectable; no uncontrolled autonomy.

## Remaining gaps (for later refinement)

- Wiring lane execution to the real executor (optional handoff of bounded steps to executor when allowed).
- Acknowledging handoffs from the supervised loop (acknowledged_at).
- Scope enforcement (allowed_step_classes) during execution.
- Pack defaults and accepted skills feeding subplan generation (stubs in gather_subplan_context).
