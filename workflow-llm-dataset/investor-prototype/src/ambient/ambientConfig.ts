export type AmbientPhase = 'boot' | 'role' | 'mission';

export type AmbientConfig = {
  speed: number;
  scale: number;
  alpha: number;
  glow: number;
  baseColor: string;
  accentColor: string;
};

export const AMBIENT_PHASE_CONFIG: Record<AmbientPhase, AmbientConfig> = {
  boot: {
    speed: 0.0022,
    scale: 0.006,
    alpha: 0.5,
    glow: 0.65,
    baseColor: '#0b0f14',
    accentColor: '#7eb8da',
  },
  role: {
    speed: 0.0031,
    scale: 0.0072,
    alpha: 0.56,
    glow: 0.7,
    baseColor: '#0a0d13',
    accentColor: '#7eb8da',
  },
  mission: {
    speed: 0.0042,
    scale: 0.0082,
    alpha: 0.62,
    glow: 0.78,
    baseColor: '#090c12',
    accentColor: '#7eb8da',
  },
};

export function getAmbientConfig(phase: AmbientPhase): AmbientConfig {
  return AMBIENT_PHASE_CONFIG[phase] || AMBIENT_PHASE_CONFIG.mission;
}
