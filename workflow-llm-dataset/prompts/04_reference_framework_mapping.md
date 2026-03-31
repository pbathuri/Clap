# Reference Framework Mapping

These frameworks are references, not architecture owners.

## LangChain / LangGraph

Use for:

- durable execution
- graph-oriented orchestration
- long-running stateful flows
- memory and resumability patterns
Reject:
- unnecessary framework ownership over the repo
- generic chain sprawl without product grounding

## Claude Agent SDK

Use for:

- file / command / local coding loop patterns
- structured tool execution envelopes
- strong local operator patterns
Reject:
- coupling architecture to one vendor’s runtime assumptions

## Semantic Kernel

Use for:

- orchestration abstraction
- interchangeable coordination styles
- explicit invocation boundaries
- agent coordination interfaces
Reject:
- complexity that does not map to current repo needs

## AutoGen / Magentic-One

Use for:

- orchestrator + specialist decomposition
- replanning and progress ledgers
- specialist team interaction patterns
Reject:
- unsafe autonomy
- over-complex multi-agent theatrics without clear value

## CrewAI

Use for:

- crews
- flows
- guardrails
- memory and observability concepts
Reject:
- using crew abstractions where a simpler workflow-tree model is better

## OpenHands

Use for:

- software-agent interaction patterns
- local environment and file interaction patterns
- coding and operator execution concepts
Reject:
- any architecture that assumes uncontrolled computer operation

## Evaluation policy

Adopt only:

- abstractions that materially strengthen the current repo
- patterns that preserve local-first and approval-gated operation
- components whose value clearly outweighs complexity

Reject:

- dependency sprawl
- giant vendored frameworks
- architecture drift caused by copying popular repos blindly
