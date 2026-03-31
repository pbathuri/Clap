# Control and Permission Model

## Host OS target

- First real target: macOS.
- Cross-platform later.

## Desktop control scope

- Session-trusted supervised.
- User grants trust for a session or workspace scope.
- Within that scope, the system may perform approved actions.
- Outside that scope, actions require explicit approval or are blocked.

## File access scope

- Approved folders first.
- Expandable to full-disk only after explicit setup and clear warning.
- Folder grants must be visible, revocable, and audit-logged.

## macOS permissions model

Architecture should account for:

- Files and Folders
- Full Disk Access
- Accessibility
- Automation
- Screen Recording if later needed
- App-specific access where applicable

## Execution tiers

1. Read-only inspection
2. Proposed actions only
3. Supervised execution
4. Session-trusted supervised execution within approved scope

## Approval classes

- Low-risk read operations
- Low-risk non-destructive actions
- Medium-risk tool interactions
- High-risk destructive or sensitive actions
- Restricted/blocked actions

## Non-negotiables

- No hidden autonomy
- No silent self-modification
- No irreversible action without explicit or pre-authorized policy
- No uncontrolled browsing or external execution without policy
