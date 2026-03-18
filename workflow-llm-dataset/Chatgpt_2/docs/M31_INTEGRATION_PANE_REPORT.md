# M31 Integration Pane Report — Observation, Personal Graph, Personal Adaptation

## 1. Merge steps executed

The three panes are **already present in the same tree** (no git merge of separate branches was performed). Integration consisted of:

1. **Pane 1 (M31A–M31D + M31D.1) — Observation runtime**
   - **Verified present**: `observe/*` (runtime, boundaries, state, profiles, sources, file_activity, local_events); CLI `observe` group (sources, enable, disable, status, recent, boundaries, health, profiles, retention-policy, run).
   - **Data flow**: Observation writes to event log; no direct call to personal graph in `observe run` (downstream `suggest` or `personal graph ingest` consumes events).

2. **Pane 2 (M31E–M31H + M31H.1) — Personal work graph + routine mining**
   - **Verified present**: `personal/*` (work_graph, graph_builder, graph_store, routine_detector, pattern_mining, graph_reports, graph_review_inbox); CLI `personal` group (graph status/ingest/explain, routines, patterns).
   - **Data flow**: Top-level `suggest` loads events → `detect_routines` → `persist_routines(graph_path, routines)` and `persist_suggestions`; `personal graph ingest` uses `build_graph_from_recent_events` from event log.

3. **Pane 3 (M31I–M31L + M31L.1) — Personal adaptation**
   - **Verified present**: `personal_adaptation/*` (models, candidates, store, apply, explain, behavior_delta, presets); CLI under `personal`: preferences, style-candidates, apply-preference, behavior-delta, profile-presets, profile-preset, explain-preference.
   - **Data flow**: Adaptation uses corrections, routines (suggestions), style_profiles, imitation_candidates; does not mutate observation or graph; applies only accepted preferences.

4. **Mission control**
   - **State**: Already aggregates `observation_state`, `personal_graph_summary`, `personal_adaptation` (from prior work).
   - **Next action**: Recommender returns `observe_setup` when no observation sources enabled (Pane 1 integration).

5. **Test fix**
   - **mission_control**: Added `observe_setup` to `ACTIONS` in `next_action.py` so `recommend_next_action`’s new action is valid. Updated `test_recommend_replay_task_when_tasks_available` to pass `observation_state: {"enabled_sources": ["file"]}` so replay_task is recommended when tasks_count > 0 (observation block no longer takes precedence).

---

## 2. Files with conflicts

- **No merge conflicts** (no separate branches were merged).
- **Integration touchpoints**:
  - **cli.py**: Single `personal_group`; Pane 2 commands (graph, routines, patterns) and Pane 3 commands (preferences, style-candidates, apply-preference, behavior-delta, profile-presets, profile-preset, explain-preference) coexist under `personal`. No duplicate group names.
  - **mission_control/next_action.py**: Pane 1 added `observe_setup` recommendation; test expected a fixed `ACTIONS` tuple → resolved by extending `ACTIONS` and adjusting one test’s state.

---

## 3. How each conflict was resolved

| Location | Issue | Resolution |
|----------|--------|------------|
| `mission_control/next_action.py` | `ACTIONS` did not include `observe_setup` | Added `"observe_setup"` to `ACTIONS`. |
| `tests/test_mission_control.py` | `test_recommend_next_action_returns_valid_action` failed because recommender returned `observe_setup` for minimal state | Keeping minimal state; assertion now passes because `observe_setup` is in `ACTIONS`. |
| `tests/test_mission_control.py` | `test_recommend_replay_task_when_tasks_available` expected `replay_task` but got `observe_setup` | Added `observation_state: {"enabled_sources": ["file"]}` to test state so observation is “satisfied” and recommender proceeds to replay_task. |

---

## 4. Tests run after each merge

| Slice | Command | Result |
|-------|--------|--------|
| **Pane 1 (observation)** | `pytest tests/test_observe_m31.py tests/test_observe_profiles.py tests/test_observe_m1.py -v` | **Collection error**: `ModuleNotFoundError: No module named 'pydantic'` when loading `observe` (and thus `local_events`). **Not a code conflict**; requires `pydantic` in the test env. |
| **Pane 2 (personal graph)** | `pytest tests/test_personal_graph_builder.py -v` | **Collection error**: same `pydantic` import via `personal.work_graph`. **Not a code conflict**; env/setup. |
| **Pane 3 (personal adaptation)** | `pytest tests/test_personal_adaptation.py -v` | **17 passed.** |
| **Mission control** | `pytest tests/test_mission_control.py -v` | **9 passed** (after adding `observe_setup` to ACTIONS and fixing replay_task test state). |

**Conclusion**: Personal adaptation and mission control tests pass. Observation and personal graph tests require the project’s full dependency set (e.g. `pydantic`) in the test environment; once deps are installed, re-run to validate Pane 1 and Pane 2.

---

## 5. Final integrated command surface

- **observe** (Pane 1): `sources`, `enable`, `disable`, `status`, `recent`, `boundaries`, `health`, `profiles`, `retention-policy`, `run`.
- **personal** (Pane 2 + Pane 3):
  - **Graph / routines**: `graph` (status | ingest | explain), `routines`, `patterns`.
  - **Adaptation**: `preferences` (--refresh), `style-candidates` (--refresh), `apply-preference` (--id [--dry-run]), `behavior-delta` (--id or --preset), `profile-presets`, `profile-preset` (--id or --create --name --candidates), `explain-preference` (--id).
- **Top-level**: `suggest` (events → routines → persist to graph + suggestions).
- **Mission control**: State includes `observation_state`, `personal_graph_summary`, `personal_adaptation`; report includes [Observation], [Personal graph], [Personal adaptation]; next action can be `observe_setup`, `hold`, `replay_task`, etc.

---

## 6. Remaining risks

- **Env**: Observe and personal graph tests fail in a minimal env without `pydantic`; CI or local runs need full install (e.g. `pip install -e ".[dev]"` or equivalent).
- **Ordering**: Next-action priority is observation_setup before replay_task; if observation is disabled, replay_task is never recommended. Intentional; document for operators.
- **Data flow**: `observe run` does not auto-call `personal graph ingest`; operator must run `suggest` or `personal graph ingest` after observation. Document in operator docs.
- **Trust**: No change to trust/approval boundaries; adaptation applies only to accepted preferences and does not bypass review.

---

## 7. Exact recommendation for the next batch

1. **Run full test suite** with project deps installed (e.g. `uv run pytest tests/test_observe_m31.py tests/test_observe_profiles.py tests/test_personal_graph_builder.py tests/test_personal_adaptation.py tests/test_mission_control.py -v`) and fix any remaining failures.
2. **Docs**: Add a short “M31 operator flow” (observe → suggest or personal graph ingest → personal preferences/style-candidates and apply) to the operator runbook or README.
3. **Optional**: Add an integration test that (with tmp_path and mocked event log) runs: observe run (or append events) → personal graph ingest → personal preferences --refresh and asserts at least one of graph status or preference list is non-empty.
