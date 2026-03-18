/**
 * M52D.1 — Presenter-safe motion constants (mirror CSS where possible).
 */

export const MOTION_MS = {
  /** Rail, small UI */
  fast: 180,
  /** Panel cross-fade, dock lift */
  medium: 340,
  /** Phase-level */
  slow: 520,
} as const;

/** Primary desktop easing — matches CSS --ease-desktop */
export const EASING_DESKTOP = 'cubic-bezier(0.22, 1, 0.36, 1)';

export const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)';
