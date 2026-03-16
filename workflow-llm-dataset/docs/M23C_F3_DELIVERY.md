# M23C-F3 — Browser/URL + App-Launch Simulation Adapter — Delivery

## 1. Files modified

| File | Change |
|------|--------|
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/contracts.py` | browser_open: capability updated for F3 (simulate only; validate local/allowed URL); failure_modes include scheme_not_allowed. app_launch: capability updated (simulate only; resolve approved app names); failure_modes include app_not_approved. |
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/simulate.py` | open_url: call validate_local_or_allowed_url; preview includes Validation: ok (category=…) or invalid reason; "Would open URL in browser (simulate only; F3)". launch_app: call resolve_app_display_name; preview includes Resolved (approved) or "not in approved list"; "Would launch app (simulate only; F3)." |
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/__init__.py` | Exported validate_local_or_allowed_url, UrlValidationResult, resolve_app_display_name, APPROVED_APP_NAMES. |
| `workflow-llm-dataset/tests/test_desktop_adapters.py` | F3 tests: URL validation (http, file, localhost, invalid scheme, empty); app resolve (approved, unapproved); simulate open_url valid/invalid; simulate launch_app approved/unapproved; check_availability browser_open and app_launch. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M23C_F3_READ_FIRST.md` | Pre-coding: current adapter layer, exact F3 addition, file plan, safety note. |
| `docs/M23C_F3_DELIVERY.md` | This file. |
| `src/workflow_dataset/desktop_adapters/url_validation.py` | validate_local_or_allowed_url(url) → UrlValidationResult (valid, reason, category). Allows http, https, file, localhost; rejects javascript:, data:, vbscript:, etc. |
| `src/workflow_dataset/desktop_adapters/app_allowlist.py` | APPROVED_APP_NAMES (Notes, Safari, Terminal, TextEdit, Finder, Mail, Calendar, Reminders, System Preferences, System Settings); resolve_app_display_name(name) → display name or None. |

## 3. CLI usage

No new CLI commands. Use existing `adapters simulate` for browser and app:

```bash
# Browser/open URL (simulate; URL validated)
workflow-dataset adapters simulate --id browser_open --action open_url --param url=https://example.com
workflow-dataset adapters simulate --id browser_open --action open_url --param url=file:///tmp/doc.html
workflow-dataset adapters simulate --id browser_open --action open_url --param url=http://localhost:8080
workflow-dataset adapters simulate --id browser_open --action open_url --param url=javascript:alert(1)

# App launch (simulate; resolve approved names)
workflow-dataset adapters simulate --id app_launch --action launch_app --param app_name_or_path=Safari
workflow-dataset adapters simulate --id app_launch --action launch_app --param app_name_or_path=Notes
workflow-dataset adapters simulate --id app_launch --action launch_app --param app_name_or_path=SomeApp

# Availability (existing command)
workflow-dataset adapters show --id browser_open
workflow-dataset adapters show --id app_launch
```

## 4. Sample simulate previews

### Valid URL — `adapters simulate --id browser_open --action open_url --param url=https://example.com`

```
Simulate OK
[Simulate] adapter=browser_open action=open_url
  url=https://example.com
  Validation: ok (category=https)
  Would open URL in browser (simulate only; F3).
Real execution not implemented for this adapter/action.
```

### Invalid URL — `adapters simulate --id browser_open --action open_url --param url=javascript:void(0)`

```
Simulate OK
[Simulate] adapter=browser_open action=open_url
  url=javascript:void(0)
  Validation: invalid — scheme_not_allowed
  Would not open; fix URL and retry.
```

### Approved app — `adapters simulate --id app_launch --action launch_app --param app_name_or_path=Safari`

```
Simulate OK
[Simulate] adapter=app_launch action=launch_app
  App: Safari
  Resolved (approved): Safari
  Would launch app (simulate only; F3).
Real execution not implemented for this adapter/action.
```

### Unapproved app — `adapters simulate --id app_launch --action launch_app --param app_name_or_path=MyApp`

```
Simulate OK
[Simulate] adapter=app_launch action=launch_app
  App: MyApp
  Resolved: not in approved list (preview only).
  Would launch app (simulate only; F3).
```

## 5. Tests run

```bash
cd workflow-llm-dataset
pytest tests/test_desktop_adapters.py -v
```

**36 tests total** (25 existing + 11 F3). F3-specific:

- **URL validation:** test_validate_url_http, test_validate_url_file, test_validate_url_localhost, test_validate_url_invalid_scheme, test_validate_url_empty.
- **App allowlist:** test_resolve_app_approved, test_resolve_app_unapproved.
- **Simulate:** test_simulate_open_url_valid, test_simulate_open_url_invalid, test_simulate_launch_app_approved, test_simulate_launch_app_unapproved.
- **Availability:** test_check_availability_browser_open, test_check_availability_app_launch (available=True, supports_simulate=True, supports_real_execution=False).

All 36 passed.

## 6. Remaining weaknesses (F3 only)

- **Simulate only:** browser_open and app_launch have no real execution; no webbrowser.open or subprocess.
- **URL validation is format-only:** No fetch or DNS; no check that host exists or is reachable.
- **App list is fixed:** APPROVED_APP_NAMES is a constant tuple; not loaded from config.
- **Case-insensitive match only:** App resolve matches by lowercased name; no path or bundle-id resolution.
