import { useMemo } from 'react';
import type { AmbientConfig, AmbientPhase } from './ambientConfig';
import { getAmbientConfig } from './ambientConfig';

export function useAmbientPhase(phase: AmbientPhase): AmbientConfig {
  return useMemo(() => getAmbientConfig(phase), [phase]);
}
