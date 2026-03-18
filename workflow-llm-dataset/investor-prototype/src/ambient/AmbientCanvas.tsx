import { useEffect, useRef, useState } from 'react';
import { createNoise3D } from 'simplex-noise';
import type { AmbientPhase } from './ambientConfig';
import { useAmbientPhase } from './useAmbientPhase';
import { subscribeAmbientPulse } from './ambientEvents';

type Props = {
  phase: AmbientPhase;
};

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return true;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const clean = hex.replace('#', '');
  if (clean.length !== 6) return null;
  const num = Number.parseInt(clean, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255,
  };
}

export function AmbientCanvas({ phase }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const config = useAmbientPhase(phase);
  const [reducedMotion, setReducedMotion] = useState(prefersReducedMotion());

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const noise3d = createNoise3D();
    let frame = 0;
    let pulse = 0;
    let raf = 0;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(window.innerWidth * dpr));
      canvas.height = Math.max(1, Math.floor(window.innerHeight * dpr));
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener('resize', resize);

    const unsub = subscribeAmbientPulse(({ intensity }) => {
      pulse = Math.min(1.6, pulse + intensity * 0.6);
    });

    const draw = (animateLoop: boolean) => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      const gradient = ctx.createRadialGradient(
        w * 0.5,
        h * 0.35,
        40,
        w * 0.5,
        h * 0.5,
        Math.max(w, h)
      );
      gradient.addColorStop(0, `${config.baseColor}`);
      gradient.addColorStop(1, '#05070b');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, w, h);

      const step = Math.max(24, Math.min(64, Math.floor(Math.min(w, h) / 10)));
      const time = frame * config.speed;
      const accent = hexToRgb(config.accentColor) || { r: 126, g: 184, b: 218 };
      for (let y = 0; y <= h + step; y += step) {
        for (let x = 0; x <= w + step; x += step) {
          const n = noise3d(x * config.scale, y * config.scale, time);
          const lum = (n + 1) * 0.5;
          const alpha = (0.08 + lum * 0.12) * config.alpha;
          ctx.fillStyle = `rgba(${accent.r}, ${accent.g}, ${accent.b}, ${alpha})`;
          ctx.fillRect(x, y, step, step);
        }
      }

      if (pulse > 0.02) {
        const pulseRadius = (Math.min(w, h) * 0.15) * (1 + pulse);
        ctx.beginPath();
        ctx.arc(w * 0.5, h * 0.45, pulseRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${accent.r}, ${accent.g}, ${accent.b}, ${0.2 * pulse})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
        pulse *= 0.92;
      }

      frame += 1;
      if (animateLoop) {
        raf = requestAnimationFrame(() => draw(true));
      }
    };

    if (!reducedMotion) {
      raf = requestAnimationFrame(() => draw(true));
    } else {
      draw(false);
    }

    return () => {
      window.removeEventListener('resize', resize);
      unsub();
      cancelAnimationFrame(raf);
    };
  }, [config, reducedMotion]);

  return (
    <canvas
      ref={canvasRef}
      className="ambient-canvas"
      aria-hidden
    />
  );
}
