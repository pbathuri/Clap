# Privacy and Local-First Model

## Principles

1. **Data residency**  
   Raw observation data and the personal work graph are stored only on the user’s device (or dedicated edge device) unless the user explicitly enables sync.

2. **No silent sync**  
   Sync (if any) is opt-in, scoped (e.g. graph only, not raw events), and documented. No telemetry or training on user data without consent.

3. **Observation is configurable**  
   The user can disable observation entirely or enable only specific sources (e.g. files + calendar, no browser). Default is tier 1, off until the user turns it on in config.

4. **Execution is gated**  
   The agent does not modify the user’s real system unless the user has chosen a mode that allows it (assist/automate) and has approved the boundaries (e.g. which apps, which paths).

5. **Updates and downloads**  
   Software updates and model/workflow-pack downloads must not contain or request user data. Integrity of downloads is verified.

## Config implications

- `sync_enabled`: default `false`.
- `observation_enabled`: default `false` (or tier 0 = no observation until user opts in).
- `execution_mode`: default `simulate`.
- `privacy_mode`: default to most restrictive (local-only, no sync, no external calls with user content).

These defaults are reflected in `configs/settings.yaml` and `src/workflow_dataset/settings.py`.
