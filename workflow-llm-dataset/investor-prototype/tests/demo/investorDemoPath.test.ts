import { describe, expect, it } from 'vitest';
import {
  BACKUP_2MIN_STAGE_ORDER,
  CANONICAL_5MIN_STAGE_ORDER,
  DEFER_UNLESS_ASKED,
  INVESTOR_DEMO_STAGES,
  MUST_SHOW_MOMENTS,
  stageIndex,
} from '../../src/demo/investorDemoPath';

describe('investorDemoPath', () => {
  it('defines ordered canonical 5-min stages', () => {
    expect(CANONICAL_5MIN_STAGE_ORDER.length).toBeGreaterThanOrEqual(5);
    for (const id of CANONICAL_5MIN_STAGE_ORDER) {
      expect(INVESTOR_DEMO_STAGES).toContain(id);
    }
  });

  it('backup path is a short subset', () => {
    expect(BACKUP_2MIN_STAGE_ORDER.length).toBeLessThan(
      CANONICAL_5MIN_STAGE_ORDER.length
    );
    expect(BACKUP_2MIN_STAGE_ORDER).toContain('first_value');
    expect(BACKUP_2MIN_STAGE_ORDER).toContain('supervised_posture');
  });

  it('must-show and defer lists are non-empty', () => {
    expect(MUST_SHOW_MOMENTS.length).toBeGreaterThanOrEqual(5);
    expect(DEFER_UNLESS_ASKED.length).toBeGreaterThanOrEqual(3);
  });

  it('stageIndex is stable', () => {
    expect(stageIndex('boot_readiness')).toBe(0);
    expect(stageIndex('supervised_posture')).toBe(
      INVESTOR_DEMO_STAGES.length - 1
    );
  });
});
