import { describe, expect, it } from 'vitest';
import {
  buildDesktopDemoViewModel,
  missionSurfaceOnly,
} from '../../src/viewModels/desktopDemoViewModel';
import { getMissionState } from '../../src/mocks/missionMock';
import type { EdgeDesktopSnapshot } from '../../src/adapters/edgeDesktopTypes';

describe('buildDesktopDemoViewModel', () => {
  it('mock-only path has dataProvenance mock', () => {
    const mock = getMissionState('founder_operator');
    const vm = buildDesktopDemoViewModel(null, 'founder_operator', mock, 'mock');
    expect(vm.dataProvenance).toBe('mock');
    expect(vm.roleLabel).toBe(mock.roleLabel);
    expect(missionSurfaceOnly(vm).roleLabel).toBe(mock.roleLabel);
  });

  it('reports degraded when adapter fields are stale', () => {
    const mock = getMissionState('founder_operator');
    const snap = {
      generated_at: '2025-01-01T12:00:00',
      repo_root: '/x',
      sources_ok: ['readiness'],
      errors: {},
      readiness: { capability_level: { value: 'L2' } },
      adapter_meta: {
        field_status: { workspace_home: 'stale_cache', day_status: 'timeout' },
      },
    } as unknown as EdgeDesktopSnapshot;
    const vm = buildDesktopDemoViewModel(
      snap,
      'founder_operator',
      mock,
      'live'
    );
    expect(vm.staleFieldCount).toBeGreaterThanOrEqual(1);
    expect(vm.degradedSummary).toMatch(/earlier sync|story/i);
  });

  it('timeout path surfaces investor-safe copy', () => {
    const mock = getMissionState('document_review');
    const vm = buildDesktopDemoViewModel(null, 'document_review', mock, 'mock', {
      timedOut: true,
    });
    expect(vm.degradedSummary).toMatch(/moment|stable|prefetch|demo/i);
  });

  it('maps themes and priorities from onboarding ready-state', () => {
    const mock = getMissionState('founder_operator');
    const snap = {
      generated_at: '2025-01-01T12:00:00',
      repo_root: '/x',
      sources_ok: ['onboarding_ready'],
      errors: {},
      onboarding_ready: {
        ready_to_assist: {
          recurring_themes: ['A', 'B'],
          likely_priorities: ['P1', 'P2'],
          memory_bootstrap_summary: 'm',
        },
      },
    } as unknown as EdgeDesktopSnapshot;
    const vm = buildDesktopDemoViewModel(snap, 'founder_operator', mock, 'live');
    expect(vm.keyThemes).toEqual(['A', 'B']);
    expect(vm.keyPriorities).toEqual(['P1', 'P2']);
  });
});
