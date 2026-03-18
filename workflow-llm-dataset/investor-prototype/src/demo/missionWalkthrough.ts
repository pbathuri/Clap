/**
 * Deterministic investor click path inside mission phase (after role select).
 * Steps 0–3 = guided; 4 = free roam (full rail + dock).
 */

export const MISSION_WALKTHROUGH_LABELS = [
  'Ready to assist · what the desk learned (bounded)',
  'Mission overview · context & priorities',
  'First value · the next useful move',
  'Supervised posture · what needs you',
] as const;

export type MissionWalkthroughStep = 0 | 1 | 2 | 3 | 4;

export function parseInitialWalkthroughStep(params: URLSearchParams): MissionWalkthroughStep {
  if (params.get('freeMission') === '1') return 4;
  const n = params.get('walkthrough');
  if (n === '0' || n === '1' || n === '2' || n === '3') return Number(n) as MissionWalkthroughStep;
  return 0;
}

export function advanceWalkthroughStep(
  current: MissionWalkthroughStep
): MissionWalkthroughStep {
  if (current >= 4) return 4;
  return (current + 1) as MissionWalkthroughStep;
}

export function walkthroughBack(
  current: MissionWalkthroughStep
): MissionWalkthroughStep {
  if (current <= 0) return 0;
  if (current >= 4) return 4;
  return (current - 1) as MissionWalkthroughStep;
}
