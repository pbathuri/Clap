/**
 * Pure transition helpers for tests and predictable presenter flow.
 */

import type { RoleId } from '../mocks/missionMock';
import type {
  AppShellPhase,
  BootReadinessTier,
  DesktopShellState,
  MissionHomeShellState,
  RailSectionId,
  WorkspaceLayoutMode,
} from './models';
import { DEFAULT_BOOT_CAPTIONS, createInitialDesktopShell } from './models';

export function shellAfterBootComplete(shell: DesktopShellState): DesktopShellState {
  return {
    ...shell,
    phase: 'role_select',
    boot: { ...shell.boot, progress: 1 },
  };
}

export function shellAfterRoleSelected(
  shell: DesktopShellState,
  _roleId: RoleId
): DesktopShellState {
  return {
    ...shell,
    phase: 'mission',
    missionHome: {
      ...shell.missionHome,
      layoutMode: shell.presenter.defaultLayoutOnMissionEnter,
      railActive: 'home',
    },
  };
}

export function shellToggleLayoutMode(shell: DesktopShellState): DesktopShellState {
  const next: WorkspaceLayoutMode =
    shell.missionHome.layoutMode === 'single_workspace'
      ? 'multi_window'
      : 'single_workspace';
  return {
    ...shell,
    missionHome: { ...shell.missionHome, layoutMode: next },
  };
}

export function shellSetRail(shell: DesktopShellState, rail: RailSectionId): DesktopShellState {
  return {
    ...shell,
    missionHome: { ...shell.missionHome, railActive: rail },
  };
}

export function shellSetRoleWhileInMission(
  shell: DesktopShellState,
  _roleId: RoleId
): DesktopShellState {
  if (shell.phase !== 'mission') return shell;
  return {
    ...shell,
    missionHome: { ...shell.missionHome, railActive: 'home' },
  };
}

export function shellGoToBoot(shell: DesktopShellState): DesktopShellState {
  return {
    ...createInitialDesktopShell(),
    presenter: shell.presenter,
  };
}

export function shellGoToRoleSelect(shell: DesktopShellState): DesktopShellState {
  return {
    ...shell,
    phase: 'role_select',
  };
}

export function shellSetBootReadinessTier(
  shell: DesktopShellState,
  tier: BootReadinessTier
): DesktopShellState {
  return {
    ...shell,
    boot: {
      ...shell.boot,
      readinessTier: tier,
      readinessCaption: DEFAULT_BOOT_CAPTIONS[tier],
    },
  };
}

export function shellToggleRightPanel(shell: DesktopShellState): DesktopShellState {
  const mh: MissionHomeShellState = {
    ...shell.missionHome,
    rightPanelOpen: !shell.missionHome.rightPanelOpen,
  };
  return { ...shell, missionHome: mh };
}

/** Ordered phases for presenter script */
export const PRESENTER_PHASE_ORDER: AppShellPhase[] = [
  'boot',
  'role_select',
  'mission',
];

export function shellPhaseIndex(phase: AppShellPhase): number {
  return PRESENTER_PHASE_ORDER.indexOf(phase);
}
