import { describe, expect, it } from 'vitest';
import { createInitialDesktopShell } from '../../src/shell/models';
import {
  shellAfterBootComplete,
  shellAfterRoleSelected,
  shellGoToBoot,
  shellGoToRoleSelect,
  shellPhaseIndex,
  shellSetBootReadinessTier,
  shellSetRail,
  shellSetRoleWhileInMission,
  shellToggleLayoutMode,
  shellToggleRightPanel,
} from '../../src/shell/transitions';

describe('shell transitions', () => {
  it('boot complete → role_select', () => {
    const s0 = createInitialDesktopShell();
    expect(s0.phase).toBe('boot');
    const s1 = shellAfterBootComplete(s0);
    expect(s1.phase).toBe('role_select');
    expect(s1.boot.progress).toBe(1);
  });

  it('role selected → mission + rail home', () => {
    let s = createInitialDesktopShell();
    s = shellAfterBootComplete(s);
    s = shellAfterRoleSelected(s, 'founder_operator');
    expect(s.phase).toBe('mission');
    expect(s.missionHome.railActive).toBe('home');
    expect(s.missionHome.layoutMode).toBe('single_workspace');
  });

  it('toggle layout single ↔ multi', () => {
    let s = shellAfterRoleSelected(shellAfterBootComplete(createInitialDesktopShell()), 'founder_operator');
    s = shellToggleLayoutMode(s);
    expect(s.missionHome.layoutMode).toBe('multi_window');
    s = shellToggleLayoutMode(s);
    expect(s.missionHome.layoutMode).toBe('single_workspace');
  });

  it('rail sections', () => {
    let s = shellAfterRoleSelected(shellAfterBootComplete(createInitialDesktopShell()), 'analyst_followup');
    s = shellSetRail(s, 'inbox');
    expect(s.missionHome.railActive).toBe('inbox');
  });

  it('role switch in mission resets rail to home', () => {
    let s = shellAfterRoleSelected(shellAfterBootComplete(createInitialDesktopShell()), 'founder_operator');
    s = shellSetRail(s, 'guidance');
    s = shellSetRoleWhileInMission(s, 'document_review');
    expect(s.missionHome.railActive).toBe('home');
  });

  it('goToBoot resets shell, keeps presenter', () => {
    let s = shellAfterRoleSelected(shellAfterBootComplete(createInitialDesktopShell()), 'founder_operator');
    const pres = s.presenter;
    s = shellGoToBoot(s);
    expect(s.phase).toBe('boot');
    expect(s.presenter).toEqual(pres);
  });

  it('goToRoleSelect from mission', () => {
    let s = shellAfterRoleSelected(shellAfterBootComplete(createInitialDesktopShell()), 'founder_operator');
    s = shellGoToRoleSelect(s);
    expect(s.phase).toBe('role_select');
  });

  it('boot readiness tier', () => {
    let s = createInitialDesktopShell();
    s = shellSetBootReadinessTier(s, 'degraded');
    expect(s.boot.readinessTier).toBe('degraded');
    expect(s.boot.readinessCaption.length).toBeGreaterThan(0);
  });

  it('toggle right panel', () => {
    let s = shellAfterRoleSelected(shellAfterBootComplete(createInitialDesktopShell()), 'founder_operator');
    expect(s.missionHome.rightPanelOpen).toBe(true);
    s = shellToggleRightPanel(s);
    expect(s.missionHome.rightPanelOpen).toBe(false);
  });

  it('presenter phase order', () => {
    expect(shellPhaseIndex('boot')).toBe(0);
    expect(shellPhaseIndex('role_select')).toBe(1);
    expect(shellPhaseIndex('mission')).toBe(2);
  });
});
