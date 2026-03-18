/**
 * M52.5 — Canonical investor demo stages (documentation + tests).
 * Not a router; single source of truth for rehearsal checklists.
 */

export const INVESTOR_DEMO_STAGES = [
  'boot_readiness',
  'role_selection',
  'mission_overview',
  'memory_bootstrap',
  'ready_to_assist',
  'first_value',
  'supervised_posture',
] as const;

export type InvestorDemoStageId = (typeof INVESTOR_DEMO_STAGES)[number];

/** Primary ~5 min path: full walkthrough beats + boot + role */
export const CANONICAL_5MIN_STAGE_ORDER: InvestorDemoStageId[] = [
  'boot_readiness',
  'role_selection',
  'memory_bootstrap',
  'ready_to_assist',
  'mission_overview',
  'first_value',
  'supervised_posture',
];

/** ~2 min backup: skip boot animation rush, walkthrough optional */
export const BACKUP_2MIN_STAGE_ORDER: InvestorDemoStageId[] = [
  'role_selection',
  'ready_to_assist',
  'first_value',
  'supervised_posture',
];

/** Surfaces to hit in order (click path) — full path */
export const CANONICAL_CLICK_BEATS = [
  'Boot → Continue (or Skip)',
  'Role card → Load demo profile',
  'Mission walkthrough: Next ×4 (or Skip story)',
  'Optional: Home rail → first-value card already visible',
  'Optional: Switch role / Reboot for repeat',
] as const;

export const MUST_SHOW_MOMENTS = [
  'Local / laptop edge framing (boot)',
  'One desk at a time (role)',
  'Bounded memory / what was learned',
  'Ready to assist',
  'Concrete first-value recommendation',
  'Supervised / approval posture',
] as const;

/** Defer unless investor asks */
export const DEFER_UNLESS_ASKED = [
  'Multi-window desktop mode',
  'Raw workspace_home / day_status pre blocks',
  'Inbox deep-dive',
  'Boot tier toggles (Full / Degraded / Workspace)',
  'Refresh snapshot / engineering provenance',
] as const;

export function stageIndex(
  id: InvestorDemoStageId
): number {
  return INVESTOR_DEMO_STAGES.indexOf(id);
}
