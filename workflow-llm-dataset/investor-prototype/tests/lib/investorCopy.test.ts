import { describe, expect, it } from 'vitest';
import { softenEngineeringCopy } from '../../src/lib/investorCopy';

describe('softenEngineeringCopy', () => {
  it('keeps normal product copy', () => {
    const s = 'Review the vendor exception queue before the board touchpoint.';
    expect(softenEngineeringCopy(s, 'fallback')).toBe(s);
  });

  it('strips benchmark-heavy sentences and falls back', () => {
    const s =
      'BLEU improved to 0.42 on the eval run. Draft the digest for operations.';
    const out = softenEngineeringCopy(s, 'Draft the digest for operations.');
    expect(out).not.toMatch(/bleu|eval run/i);
    expect(out).toContain('digest');
  });

  it('uses fallback when only toxic content remains', () => {
    expect(
      softenEngineeringCopy('F1 score 0.91 on benchmark suite.', 'Safe line.')
    ).toBe('Safe line.');
  });
});
