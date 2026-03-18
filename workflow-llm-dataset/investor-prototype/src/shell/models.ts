/**
 * M52 — Explicit UI/state models for Edge Operator Desktop shell.
 * Presentation layer only; mission payload stays MissionSurfaceState.
 */

import type { RoleId } from '../mocks/missionMock';

/** App-level flow (presenter narrative) */
export type AppShellPhase = 'boot' | 'role_select' | 'mission';

/** USB / device readiness presentation (mock; wire to demo readiness later) */
export type BootReadinessTier = 'full' | 'degraded' | 'workspace_session';

export type BootShellState = {
  /** Progress 0–1 during boot animation */
  progress: number;
  /** Shown after progress; presenter can imply USB vs repo-only */
  readinessTier: BootReadinessTier;
  /** Copy line under tier */
  readinessCaption: string;
};

export type RoleSelectionShellState = {
  /** Highlighted card id for keyboard-style demo; null = none */
  focusedPresetId: RoleId | null;
};

/** Left rail: switches central workspace view without leaving mission */
export type RailSectionId = 'home' | 'work' | 'guidance' | 'inbox';

/** Single vs multi-window desktop */
export type WorkspaceLayoutMode = 'single_workspace' | 'multi_window';

export type DockShellState = {
  /** Last tapped dock item (demo feedback) */
  lastTappedId: string | null;
};

export type TopBarShellState = {
  /** Subtitle next to brand */
  contextHint: string;
};

export type PresenterNavState = {
  /** URL-driven skip boot */
  skipBootAllowed: boolean;
  /** Deterministic: prefer single workspace on mission entry */
  defaultLayoutOnMissionEnter: WorkspaceLayoutMode;
};

export type MissionHomeShellState = {
  layoutMode: WorkspaceLayoutMode;
  railActive: RailSectionId;
  rightPanelOpen: boolean;
  rightPanelWidthPx: number;
};

/** Aggregate desktop shell (persisted in React context) */
export type DesktopShellState = {
  phase: AppShellPhase;
  boot: BootShellState;
  roleSelection: RoleSelectionShellState;
  missionHome: MissionHomeShellState;
  dock: DockShellState;
  topBar: TopBarShellState;
  presenter: PresenterNavState;
};

export const DEFAULT_BOOT_CAPTIONS: Record<BootReadinessTier, string> = {
  full: 'Trust chain verified · Ready for operator work',
  degraded: 'Reduced path — still local, still supervised',
  workspace_session: 'Session mode — USB bundle optional on dedicated hardware',
};

export function createInitialDesktopShell(): DesktopShellState {
  return {
    phase: 'boot',
    boot: {
      progress: 0,
      readinessTier: 'full',
      readinessCaption: DEFAULT_BOOT_CAPTIONS.full,
    },
    roleSelection: { focusedPresetId: null },
    missionHome: {
      layoutMode: 'single_workspace',
      railActive: 'home',
      rightPanelOpen: true,
      rightPanelWidthPx: 300,
    },
    dock: { lastTappedId: null },
    topBar: { contextHint: 'Local-first' },
    presenter: {
      skipBootAllowed: true,
      defaultLayoutOnMissionEnter: 'single_workspace',
    },
  };
}
