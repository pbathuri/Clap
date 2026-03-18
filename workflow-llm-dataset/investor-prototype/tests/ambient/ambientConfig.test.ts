import { describe, expect, it } from 'vitest';
import { AMBIENT_PHASE_CONFIG, getAmbientConfig } from '../../src/ambient/ambientConfig';

describe('ambientConfig', () => {
  it('maps known phases to configs', () => {
    expect(getAmbientConfig('boot')).toEqual(AMBIENT_PHASE_CONFIG.boot);
    expect(getAmbientConfig('role')).toEqual(AMBIENT_PHASE_CONFIG.role);
    expect(getAmbientConfig('mission')).toEqual(AMBIENT_PHASE_CONFIG.mission);
  });
});
