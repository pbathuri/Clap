import { describe, expect, it } from 'vitest';
import {
  EASING_DESKTOP,
  MOTION_MS,
  REDUCED_MOTION_QUERY,
} from '../../src/shell/motionTokens';

describe('M52D.1 motion tokens', () => {
  it('exposes presenter-stable durations', () => {
    expect(MOTION_MS.fast).toBe(180);
    expect(MOTION_MS.medium).toBe(340);
    expect(MOTION_MS.slow).toBe(520);
  });

  it('easing matches CSS contract', () => {
    expect(EASING_DESKTOP).toContain('cubic-bezier');
  });

  it('documents reduced-motion query', () => {
    expect(REDUCED_MOTION_QUERY).toBe('(prefers-reduced-motion: reduce)');
  });
});
