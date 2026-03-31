# Quality Gates and Validation

## Non-negotiable gates

- tests must pass
- build must pass
- no stable export should be silently broken
- no existing state model should be changed casually
- no destructive action should bypass safety boundaries

## Validation categories

1. workflow-tree model tests
2. runtime tests
3. adapter tests
4. UI state tests
5. live/cached/fallback tests
6. investor path tests
7. supervised execution tests
8. degradation and timeout tests

## Performance expectations

- bounded waits on expensive aggregation
- explicit stale/live behavior
- presenter-safe caching
- no frozen-feeling primary path

## Product truth tests

The system must clearly distinguish:

- mock
- cached
- live
- degraded

## Release gates

- architecture coherent
- UI reflects real substrate
- permissions and control model explicit
- demo path deterministic
- product path not dependent on investor-only hacks
