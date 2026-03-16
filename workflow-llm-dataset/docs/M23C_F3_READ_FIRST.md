# M23C-F3 — Browser/URL + App-Launch Simulation Adapter — Read First

## 1. Current adapter layer (post F1/F2)

- **file_ops:** Contract + execute. Actions: read_file, list_dir, write_file (simulate only), inspect_path, list_directory, snapshot_to_sandbox (real read/sandbox copy). Registry, run_simulate, run_execute.
- **notes_document:** Contract + execute. Actions: create_note, append_to_note (simulate only), read_text, summarize_text_for_workflow, propose_status_from_notes (real read). run_execute for notes.
- **browser_open:** Contract only. Action open_url; simulate prints "Would open URL: {url}" and "Real execution not implemented in F1." No URL validation; no real execution.
- **app_launch:** Contract only. Action launch_app; simulate prints "Would launch: {app}." No approved-app list; no resolve; no real execution.
- **Registry:** list_adapters, get_adapter, check_availability (returns supports_simulate, supports_real_execution).
- **CLI:** adapters list, show, simulate, run (run only for file_ops and notes_document).

## 2. Exact next addition (F3)

- **browser_open adapter:**  
  - open_url remains **simulate only** (no real browser open unless a safe runtime helper exists; F3 does not add one).  
  - **Validate** URL format: allow http/https, file://, and localhost; reject malformed or disallowed schemes.  
  - **Preview** what would be opened: include validation result (valid / invalid + reason) and the normalized or displayed URL in the simulate preview.
- **app_launch adapter:**  
  - launch_app remains **simulate only** (no real launcher unless safe helper exists; F3 does not add one).  
  - **Resolve** against an approved-app list (e.g. display names or allowed identifiers).  
  - **Preview** what would be launched: resolved app name and "simulate only" in the simulate preview.
- **Availability:** check_availability already exists; document that browser_open and app_launch are simulate-only (supports_real_execution=False). Optionally add a small helper or extend result to indicate "simulate_only" for clarity.
- **CLI:** No new commands; existing `adapters simulate --id browser_open --action open_url --param url=...` and `adapters simulate --id app_launch --action launch_app --param app_name_or_path=...` show the enhanced previews. Document in F3 delivery.
- **Tests and docs:** Tests for URL validation, app resolve, simulate open_url (valid/invalid), simulate launch_app; M23C_F3_DELIVERY.md.

## 3. File plan

| Item | Path | Content |
|------|------|--------|
| Pre-coding doc | docs/M23C_F3_READ_FIRST.md | This file. |
| URL validation | desktop_adapters/url_validation.py | validate_local_or_allowed_url(url) → valid: bool, reason: str, category: str (http|https|file|localhost). Reject invalid scheme/malformed. |
| App allowlist | desktop_adapters/app_allowlist.py | APPROVED_APP_NAMES (e.g. Notes, Safari, Terminal, TextEdit), resolve_app_display_name(name) → display name or None. |
| Contracts | desktop_adapters/contracts.py | Update browser_open and app_launch capability_description for F3 (simulate-only, URL validated, approved apps). |
| Simulate | desktop_adapters/simulate.py | open_url: call validator; append validation result to preview. launch_app: call resolve; append resolved name and "Simulate only (F3)." |
| Package init | desktop_adapters/__init__.py | Export validate_local_or_allowed_url, resolve_app_display_name, APPROVED_APP_NAMES (if desired). |
| Tests | tests/test_desktop_adapters.py | URL validation (valid http/https/file/localhost, invalid scheme); app resolve; simulate open_url valid/invalid; simulate launch_app. |
| Delivery doc | docs/M23C_F3_DELIVERY.md | Modified/created files, CLI usage, sample simulate previews, tests. |

## 4. Safety note

- **No uncontrolled browser automation:** F3 does not open a browser, drive a browser, or perform remote browsing. Only validation and preview text.
- **No remote browsing logic:** Validation is format/scheme only; no fetch, no headless browser, no cloud.
- **No hidden execution:** All behavior is in run_simulate (preview); no subprocess, no webbrowser.open.
- **Explicit simulate only:** browser_open and app_launch remain supports_real_execution=False; preview clearly states "Simulate only" or "Real execution not implemented."
- **URL allowlist:** Only http, https, file, and localhost-style URLs accepted; other schemes (javascript:, data:, etc.) rejected.
- **App allowlist:** Only approved display names/identifiers are "resolved"; others can still be shown in preview as "unapproved" or as-is per product choice (we show preview with resolved or raw name and note simulate only).
