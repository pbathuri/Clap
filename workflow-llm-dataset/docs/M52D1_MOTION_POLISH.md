# M52D.1 — Motion polish + desktop interaction refinement

## Summary

- **CSS:** `--ease-desktop`, `--motion-*`, dock rise-in, glass/dock/rail/pill focus-visible rings, multi-window dim/focus transitions, rail slide hover, boot tier + caption pulse, layout cross-fade on single↔multi.
- **`prefers-reduced-motion: reduce`:** collapses motion variables; disables dock pulse and layout-multi animation; dock visible without slide-in delay.
- **Dock:** `dock--ready` after first frame; layout toggle shows `dock__item--layout-multi` pulse in multi mode; dock icons map to left rail (home/work/guidance).
- **Components:** `CentralWorkspace` keys rail for enter animation; `MissionControlScreen` keys layout mode; `MultiWindowDesktop` uses `multi-surface--dimmed` class instead of inline opacity.

## Files

- Created: `src/shell/motionTokens.ts`, `tests/motion/motionTokens.test.ts`, this doc.
- Modified: `src/styles/global.css`, `DesktopDock.tsx`, `MultiWindowDesktop.tsx`, `CentralWorkspace.tsx`, `MissionControlScreen.tsx`, `BootScreen.tsx`.

## Next pane step

Wire **dock/rail sync** to real `workspace open` / deep links when live API returns suggested commands.
