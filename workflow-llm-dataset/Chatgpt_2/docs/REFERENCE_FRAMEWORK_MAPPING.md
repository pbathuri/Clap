# Reference Framework Mapping (Adopt / Wrap / Reject)

These frameworks are reference patterns only. No framework should become the architecture owner.

## LangChain / LangGraph
- **Adopt:** durable execution and stateful orchestration patterns.
- **Wrap:** only at the pattern level (graph-style state, resumability), not as a dependency.
- **Reject:** chain sprawl or framework-owned runtime.

## Claude Agent SDK
- **Adopt:** local tool-loop discipline, command execution envelopes.
- **Wrap:** permissioned tool execution patterns; keep local-first.
- **Reject:** vendor runtime assumptions or implicit autonomy.

## Microsoft Semantic Kernel
- **Adopt:** orchestration abstraction and invocation boundaries.
- **Wrap:** interfaces for coordination styles, not a core dependency.
- **Reject:** complexity that does not map to current repo needs.

## AutoGen / Magentic‑One
- **Adopt:** orchestrator + specialist decomposition, replanning ledgers.
- **Wrap:** limited patterns when grounded in local safety boundaries.
- **Reject:** multi-agent theatrics or unsafe autonomy.

## CrewAI
- **Adopt:** guardrail concepts and flow framing.
- **Wrap:** only if it simplifies the workflow-tree model.
- **Reject:** replacing the repo’s existing workflow substrate with “crew” abstractions.

## OpenHands
- **Adopt:** local environment interaction patterns.
- **Wrap:** safe operator execution flows and guardrails.
- **Reject:** uncontrolled computer operation assumptions.

## Enforcement
- No vendoring of large external repos.
- Any dependency requires a concrete integration plan + tests.
- Patterns must preserve local-first + approval-gated semantics.
