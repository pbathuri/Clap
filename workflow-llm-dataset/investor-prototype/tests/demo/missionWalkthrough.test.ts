import { describe, expect, it } from 'vitest';
import {
  advanceWalkthroughStep,
  parseInitialWalkthroughStep,
  walkthroughBack,
} from '../../src/demo/missionWalkthrough';

describe('missionWalkthrough', () => {
  it('freeMission skips to free roam', () => {
    expect(parseInitialWalkthroughStep(new URLSearchParams('freeMission=1'))).toBe(
      4
    );
  });

  it('defaults to step 0', () => {
    expect(parseInitialWalkthroughStep(new URLSearchParams())).toBe(0);
  });

  it('advances through story then stays at 4', () => {
    let s = 0 as 0 | 1 | 2 | 3 | 4;
    s = advanceWalkthroughStep(s);
    expect(s).toBe(1);
    s = advanceWalkthroughStep(s);
    s = advanceWalkthroughStep(s);
    s = advanceWalkthroughStep(s);
    expect(s).toBe(4);
    expect(advanceWalkthroughStep(s)).toBe(4);
  });

  it('back from step 2', () => {
    expect(walkthroughBack(2)).toBe(1);
    expect(walkthroughBack(0)).toBe(0);
    expect(walkthroughBack(4)).toBe(4);
  });
});
