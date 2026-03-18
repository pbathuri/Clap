import { useEffect, useMemo, useRef } from 'react';
import { animate, stagger } from '@motionone/dom';

export function buildStaggerDelays(
  count: number,
  baseMs = 80,
  stepMs = 60
): number[] {
  return Array.from({ length: count }, (_, i) => baseMs + i * stepMs);
}

export function useStaggerReveal(
  count: number,
  enabled = true
): {
  register: (index: number) => (el: HTMLElement | null) => void;
} {
  const refs = useRef<Array<HTMLElement | null>>([]);

  const register = useMemo(
    () =>
      (index: number) =>
        (el: HTMLElement | null) => {
          refs.current[index] = el;
        },
    []
  );

  useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const targets = refs.current.filter(Boolean) as HTMLElement[];
    if (!targets.length) return;
    animate(
      targets,
      { opacity: [0, 1], transform: ['translateY(10px)', 'translateY(0)'] },
      { duration: 0.6, delay: stagger(0.08), easing: [0.22, 1, 0.36, 1] }
    );
  }, [count, enabled]);

  return { register };
}
