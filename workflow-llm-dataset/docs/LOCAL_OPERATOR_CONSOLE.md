# Local Operator Console (M9)

The **Local Operator Console** is the first guided product shell around the workflow-llm-dataset system. It lets you use the system end-to-end without memorizing many CLI commands.

## What it is

- **TUI-first**: Rich-based guided menus and prompts in the terminal.
- **Local-only**: No web/cloud; all data stays on your machine.
- **Privacy-first**: No telemetry; config and state are under your control.
- **Safe and explicit**: Apply and rollback require typing `yes` to confirm.
- **Inspectable**: Evidence, rationale, and diff previews are shown before any write.

## How it fits

The console sits **on top of** the existing CLI. It does not replace it:

- Headless and scripted flows still use `workflow-dataset setup ...`, `workflow-dataset assist ...`, etc.
- The console **orchestrates** the same backend modules (setup, project interpreter, suggestions, drafts, materialize, apply, rollback, agent loop).

## How to launch

From the project root (with the same venv you use for the CLI):

```bash
workflow-dataset console
```

Optional config path:

```bash
workflow-dataset console --config path/to/settings.yaml
```

If the config file is missing or invalid, the console exits with an error and does not start.

## What it can do today

| Flow | Description |
|------|-------------|
| **Home** | High-level summary: session count, projects, domains, style profiles, suggestions, drafts, workspaces, rollback records. |
| **Setup summary** | List setup sessions, show progress (files scanned, artifacts, docs parsed, projects, style patterns, graph nodes), and summary report markdown. |
| **Project explorer** | List projects from the graph; show domains, style signals, parsed artifact count. Select a project for context. |
| **Suggestions** | List style-aware suggestions with type, title, confidence; show rationale and supporting signals (evidence-aware). |
| **Drafts** | List draft structures with type, title, sections; show outline and style signals. |
| **Materialize** | Choose a draft or suggestion, materialize to sandbox workspace, show preview. **Sandbox only** — no real project writes. |
| **Apply** | Choose a workspace and target path, build apply plan, view diff preview, then **confirm with `yes`** to execute. Shows rollback token and backup/rollback availability. |
| **Rollback** | List rollback records, show affected paths, **confirm with `yes`** to restore from backup. |
| **Chat / explain** | Ask questions about projects, style, suggestions, drafts. Answers are grounded in graph and optional retrieval/LLM. |

## Safety and confirmation

- **Inspect only**: Setup, projects, suggestions, drafts — no writes.
- **Sandbox**: Materialize writes only under `data/local/workspaces`.
- **Apply plan**: Diff preview is shown **before** any copy; nothing is written until you confirm.
- **Apply**: Requires typing `yes`; backups are created when enabled; rollback token is shown after apply.
- **Rollback**: Requires typing `yes`; restores files from the backup recorded at apply time.

The UI labels these clearly (e.g. “Action: SANDBOX”, “Action: APPLY — requires explicit confirmation”) so you always know the impact of the next step.

## What it does not do (yet)

- No full-screen TUI (e.g. Textual/curses); it is menu- and prompt-driven.
- No multimodal generation; no image/audio.
- No cloud or web frontend.
- No execution without explicit confirmation for apply/rollback.

## Known limitations

- Single-user, single-session flow; no multi-window or concurrent sessions.
- Console state (selected project, workspace, etc.) is in-memory and resets when you exit.
- Apply is only available when `apply.apply_enabled` is `true` in config; rollback when `apply_rollback_enabled` is `true`.

## Next milestone

After M9, the next step is to harden and extend the console (e.g. more evidence drill-down, session persistence, or a full TUI framework) and/or move toward multimodal generation when the rest of the stack is ready.
