# Runtime and Models

## Runtime stance

Provider-agnostic from day 1.

## Base intelligence stance

Layered model stack:

1. tiny classifier / router
2. small reasoning model
3. optional specialist models

## Why this is the right architecture

- keeps idle cost lower
- supports routing by task type
- supports local intelligence on constrained hardware
- allows domain specialists later
- avoids lock-in to one model family

## Initial model responsibilities

### Tiny router / classifier

- route tasks
- identify domain
- select workflow subtree
- select tool policy path
- detect when escalation is needed

### Small reasoning model

- explain
- infer workflow structure
- summarize
- generate task decompositions
- prepare first-value outputs
- operate as the default interactive intelligence

### Optional specialist models

- coding
- spreadsheet / analytics
- design / media
- OCR / document extraction
- long-context synthesis where justified

## Web retrieval policy

User selected: always available.

Architecture interpretation:

- web retrieval is available as a first-class capability
- but still must be policy-aware, provenance-aware, and auditable
- retrieval results should be tagged by source and trust level
- retrieval should not silently overrule local truth

## Runtime boundaries

- simulation-first
- supervised live actions
- session-trusted execution within approved scope
- visible provenance
- explicit provider abstraction
