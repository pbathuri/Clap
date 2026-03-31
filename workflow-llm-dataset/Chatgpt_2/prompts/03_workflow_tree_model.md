# Workflow Tree Model

## Core abstraction

The system is built around a recursive workflow tree.

## Canonical structure

- Workflow
  - Task
    - Prompt Set
    - Tool Set
    - Data Sources
    - Memory / Context
    - Policies / Constraints
    - Checks / Tests
    - Artifacts / Results
  - Subtask
    - Prompt Set
    - Tool Set
    - Data Sources
    - Memory / Context
    - Policies / Constraints
    - Checks / Tests
    - Artifacts / Results

## Required properties

- Recursive nesting
- Inheritance and defaults
- Dynamic subtask spawning
- Provenance at every node
- Simulation-first mode
- Live execution mode
- Approval state
- Result / artifact lineage
- Serialization and resume
- Role/domain reuse

## Node responsibilities

### Workflow

Owns objective, scope, policy envelope, and aggregate state.

### Task

Represents a coherent work unit with inputs, tools, and outputs.

### Subtask

Represents decomposed work that can be delegated or specialized.

### Prompt Set

Contains instructions, templates, role-specific prompting, and execution hints.

### Tool Set

Defines which tools are allowed, bounded, or blocked for this node.

### Data Sources

Defines approved folders, files, structured data, connectors, and external retrieval.

### Memory / Context

Defines short-term context, long-term user patterns, and reusable learned structure.

### Policies / Constraints

Defines what the node may or may not do.

### Checks / Tests

Defines validation, quality gates, safety gates, and acceptance criteria.

### Artifacts / Results

Defines deliverables, intermediate results, and final outputs.

## Execution modes

- Simulated
- Proposed
- Approved live
- Session-trusted live

## Why this matters

This model must become the substrate for dynamic local agents.
It allows the system to understand a user’s work as structured, composable, inspectable trees rather than as ad hoc commands.
