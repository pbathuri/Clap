# Operator playbook · Investor meeting (Edge Operator Desktop)

**Single launch command (after preflight):** from `investor-prototype/`, run `npm run demo:launch`, then open the URL printed in the terminal.

---

## Before the meeting (30–60 min)

| Step | Action |
|------|--------|
| 1 | `cd workflow-llm-dataset` — activate venv, `workflow-dataset` on PATH |
| 2 | `cd investor-prototype && npm install` (if fresh machine) |
| 3 | **`npm run demo:preflight`** — writes `public/edge-desktop-snapshot.json` (fallback + faster paint) |
| 4 | Optional: copy `.env.meeting.example` → `.env.meeting` if paths are non-default |
| 5 | **`npm run demo:validate`** — green tests + build |
| 6 | Rehearse once: launch → full 5-min path (see canonical path doc) |

---

## At demo start (in the room)

1. **`npm run demo:launch`** (keep terminal visible for errors).
2. Open **first URL** (clean slate):  
   **`http://localhost:5173/?live=1&presenter=1&resetDemo=1`**
3. Confirm top bar eventually shows **Connected**, **Last sync**, or **Demo story** (all three are honest states).
4. Follow presenter overlay (right) — **Guide** panel.

**Do not improvise another URL** unless using the **2-minute backup** below.

---

## What to preload

- **Preflight snapshot** (`demo:preflight`) — strongly recommended.
- **Python env + `EDGE_DESKTOP_REPO_ROOT`** — required for live API path.

---

## Reset between runs (same meeting, second demo)

| Method | When |
|--------|------|
| **Reset demo** button | Top bar (visible with `?presenter=1`) |
| **`?resetDemo=1`** | Full reload; clears session cache + boot |

Avoid **Refresh snapshot** unless you intend a slow re-fetch.

---

## What not to click (unless asked)

- Multi-window toggle (investor asks for “more surfaces” only).
- **Work** rail first — raw workspace text can distract.
- Boot tier buttons (Full / Degraded / Workspace) during tight time.
- **Reboot** unless you mean to restart the story from boot.

---

## If the browser reloads

1. Re-open **`?live=1&presenter=1`** (session cache may still help).
2. If story is wrong: add **`&resetDemo=1`** once.

---

## If a panel is slow

- **Connecting…** — keep narrating boot / bounded learning; ≤ ~15s typical.
- **Refreshing…** — you already have **Last sync** data; keep going.
- **Demo story** — say *“rehearsal-safe copy — same supervised story.”* **Never say “live”** when pill says Demo story.

---

## 2-minute backup (time cut)

1. Open **`http://localhost:5173/?phase=role&live=1&presenter=1`** (skip boot).
2. One role → mission → **Skip story** in walkthrough.
3. Hit **Next** until first-value + supervised beats, or narrate from **Home** rail.

---

## Canonical paths (summary)

| Flow | Command / URL |
|------|----------------|
| **Prefetch** | `npm run demo:preflight` |
| **Launch** | `npm run demo:launch` |
| **Entry (clean)** | `?live=1&presenter=1&resetDemo=1` |
| **Entry (repeat)** | `?live=1&presenter=1` |

---

## Remaining room risks

| Risk | Mitigation |
|------|------------|
| No network / wrong repo root | Preflight JSON + `EDGE_DESKTOP_REPO_ROOT` |
| Laptop sleep mid-demo | Wake → reload same URL |
| Wrong browser tab | Bookmark canonical URL |

---

## Final check before investors enter

- [ ] `demo:preflight` run today  
- [ ] `demo:launch` running, page loaded  
- [ ] Presenter overlay visible  
- [ ] You know which role card you will pick  

**Recommendation:** If preflight + one rehearsal pass are green → **ready for the room**. If not → **one micro-rehearsal** then go.
