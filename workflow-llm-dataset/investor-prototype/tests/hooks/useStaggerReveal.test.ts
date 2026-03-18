import { describe, expect, it } from 'vitest';
import { buildStaggerDelays } from '../../src/hooks/useStaggerReveal';

describe('buildStaggerDelays', () => {
  it('builds incremental delay values', () => {
    expect(buildStaggerDelays(3, 100, 50)).toEqual([100, 150, 200]);
  });

  it('returns empty array for zero count', () => {
    expect(buildStaggerDelays(0)).toEqual([]);
  });
});
