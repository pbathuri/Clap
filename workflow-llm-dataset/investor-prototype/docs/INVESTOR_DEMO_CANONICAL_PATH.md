# Canonical investor demo path (M52.5)

## Launch (meeting)

Use **`npm run demo:launch`** from `investor-prototype/` (after **`npm run demo:preflight`**). See **[demo/OPERATOR_MEETING_PLAYBOOK.md](../demo/OPERATOR_MEETING_PLAYBOOK.md)**.

**URLs**

- First run / clean: `http://localhost:5173/?live=1&presenter=1&resetDemo=1`
- Normal: `http://localhost:5173/?live=1&presenter=1`

**Before the room:** preflight writes `public/edge-desktop-snapshot.json`; role screen warms live payload while you speak.

---

## Primary path (~5 minutes)

| # | Stage | Presenter says (gist) | Click / UI |
|---|--------|------------------------|------------|
| 1 | **Boot / readiness** | “This runs on the laptop as a local-first edge operator — USB bundle optional, same trust story.” | Wait ~2s → **Continue** (tiers optional) |
| 2 | **Role** | “One desk at a time — pack, posture, bounded learning for that role.” | **Load demo profile** on one card |
| 3 | **Memory / ready** | “Bounded onboarding — what we learned, without dumping the corpus on screen.” | Walkthrough beat 1 → **Next** |
| 4 | **Mission overview** | “Context, themes, priorities — tuned to this desk.” | Beat 2 → **Next** |
| 5 | **First value** | “Here’s the useful next move — not a black box.” | Beat 3 → **Next** |
| 6 | **Supervised posture** | “Nothing sensitive leaves without you — supervised by default.” | Beat 4 → optional **Explore** |
| 7 | **Future** | “Same stack on dedicated edge hardware when you’re ready.” | One sentence close |

**Must-show moments:** local edge framing · one desk · bounded memory · ready-to-assist · first value · supervised posture.

**Do not show unless asked:** multi-window mode · raw JSON/pre blocks · inbox rabbit holes · boot tier demo · top-bar refresh story.

---

## Backup path (~2 minutes)

Use when time is short or live snapshot is slow.

| Step | Action |
|------|--------|
| 1 | Open `?phase=role&live=1&presenter=1` (or Skip boot from full path) |
| 2 | Pick **one role** → mission |
| 3 | **Skip story** (walkthrough) or hit **Next** twice to land on first-value + posture panels |
| 4 | Narrate: ready-to-assist + first value + supervised — **Demo story** top bar is OK: “stable narrative, live path optional.” |

**If live is slow:** do not wait in silence — narrate bounded learning while **Connecting…** / **Last sync** shows; or use static snapshot file (`VITE_EDGE_STATIC_SNAPSHOT`).

---

## Presenter stage order (script overlay)

1. Boot  
2. Role  
3. Mission beat 1–4 (memory → overview → first value → supervised)  
4. Explore (optional)

---

## Between rehearsals

- **Reset demo** (presenter mode): top bar **Reset demo** clears session snapshot cache and returns to boot with a fresh walkthrough.  
- Or open once with **`?resetDemo=1`** (cache cleared, boot reset).

---

## Honesty rule

Never claim “live” when the pill reads **Demo story** — say “demo-safe copy” or “rehearsal mode.”
