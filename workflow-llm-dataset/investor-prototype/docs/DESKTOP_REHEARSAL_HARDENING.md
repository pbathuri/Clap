# Edge Operator Desktop — rehearsal hardening (M52X+)

## What changed

| Area | Behavior |
|------|----------|
| **Prefetch window** | Live snapshot load starts on **role** screen (with `?live=1`), not only after mission. Role → mission reuses the same in-flight or completed fetch — **no duplicate fetch on phase change**. |
| **Stale-while-revalidate** | Any **sessionStorage** snapshot paints immediately; background refresh updates when ready. |
| **Presenter cache** | `?presenter=1` or `VITE_PRESENTER_LONG_CACHE=1` → session cache TTL **45 min** (default 2 min). |
| **Top bar** | Labels: Connected · Last sync · Demo story · Connecting… · Refreshing… (honest, less engineering noise). |
| **Copy** | `softenEngineeringCopy` removes benchmark/eval-flavored sentences from live strings; degraded banners are investor-softer. |
| **Guidance rail** | "Operator summary" → **What the desk sees** (Context · Suggests · From you). |
| **Presenter overlay** | **Active beat** highlighted; prefetch + cache hint in footer (no raw CLI-only tone). |

## Rehearsal path (canonical)

See **`INVESTOR_DEMO_CANONICAL_PATH.md`** (5-min + 2-min backup) and **`REHEARSAL_SCORECARD.md`**.

- **`?resetDemo=1`** — boot reset + cache clear (URL param stripped after load).  
- **Reset demo** — same, from top bar when `?presenter=1`.

**Before the room:** snapshot export to `public/edge-desktop-snapshot.json` and/or warm with `?live=1` on role screen.

## Live vs cached vs demo story

- **Connected** — Fresh API snapshot.  
- **Last sync** — Session cache (within TTL).  
- **Refreshing…** — Showing last-good data while a new snapshot loads.  
- **Demo story** — Mock / timeout / API down; narrative still coherent.  

**Adapter provenance (dev only):** set `EDGE_DESKTOP_USE_ADAPTER=1` (or `VITE_EDGE_USE_ADAPTER=1`) before `npm run dev` to include `adapter_meta.field_status` in `/api/edge-desktop-snapshot`.

## Remaining risks

- First cold load with no cache still waits on Python snapshot (bounded timeout).  
- Very stale session cache can show old themes until refresh completes.  
- Multi-tab sessionStorage is not shared.

## Recommended next step

**Meeting packaging:** [demo/OPERATOR_MEETING_PLAYBOOK.md](../demo/OPERATOR_MEETING_PLAYBOOK.md) · `npm run demo:preflight` · `npm run demo:launch`.
