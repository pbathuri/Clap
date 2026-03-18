import { useEffect, useState } from 'react';
import type { BootReadinessTier } from '../shell/models';
import { useDemoFlow } from '../state/DemoFlowContext';

const TIERS: { id: BootReadinessTier; label: string }[] = [
  { id: 'full', label: 'Full' },
  { id: 'degraded', label: 'Degraded' },
  { id: 'workspace_session', label: 'Workspace' },
];

export function BootScreen() {
  const { completeBoot, surfaceClick, desktopShell, setBootReadinessTier } =
    useDemoFlow();
  const [showEnter, setShowEnter] = useState(false);
  const tier = desktopShell.boot.readinessTier;
  const caption = desktopShell.boot.readinessCaption;

  useEffect(() => {
    const t = window.setTimeout(() => setShowEnter(true), 2200);
    return () => window.clearTimeout(t);
  }, []);

  return (
    <div
      className="phase-enter"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 32,
      }}
    >
      <div className="boot-orbit" aria-hidden>
        <div className="boot-rings">
          <span />
          <span />
          <span />
        </div>
        <div
          className="boot-phase"
          style={{
            width: 88,
            height: 88,
            borderRadius: 22,
            background:
              tier === 'full'
                ? 'linear-gradient(145deg, rgba(126,184,218,0.35), rgba(60,100,80,0.35))'
                : tier === 'degraded'
                  ? 'linear-gradient(145deg, rgba(200,180,100,0.25), rgba(80,80,70,0.35))'
                  : 'linear-gradient(145deg, rgba(126,184,218,0.25), rgba(60,80,100,0.35))',
            border: '1px solid rgba(255,255,255,0.18)',
            marginBottom: 28,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 36,
          }}
        >
          ◈
        </div>
      </div>
      <h1
        className="display-title"
        style={{
          fontSize: 'clamp(1.5rem, 4vw, 2rem)',
          margin: 0,
          textAlign: 'center',
        }}
      >
        Edge operator desk
      </h1>
      <p
        style={{
          margin: '12px 0 0',
          color: 'var(--text-secondary)',
          fontSize: 14,
          textAlign: 'center',
          maxWidth: 360,
        }}
      >
        Runs on your laptop today · Local-first · Same stack on dedicated edge later
      </p>
      <div className="boot-progress" style={{ width: 'min(320px, 85vw)' }}>
        <div className="boot-progress__fill" />
      </div>
      <p
        key={tier}
        className="boot-caption boot-caption--tick"
        style={{
          marginTop: 16,
          fontSize: 13,
          color: 'var(--accent)',
          textAlign: 'center',
          maxWidth: 380,
          lineHeight: 1.45,
        }}
      >
        {caption}
      </p>
      <div className="boot-readiness-tiers" role="group" aria-label="Readiness story">
        {TIERS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`boot-tier boot-tier--${t.id} ${tier === t.id ? 'boot-tier--active' : ''}`}
            onClick={() => {
              surfaceClick(`Boot · Readiness tier ${t.label}`);
              setBootReadinessTier(t.id);
            }}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div
        style={{
          marginTop: 28,
          minHeight: 48,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {showEnter && (
          <button
            type="button"
            className="glass-panel glass-panel--interactive"
            style={{
              padding: '14px 32px',
              fontFamily: 'var(--font-sans)',
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--text-primary)',
              cursor: 'pointer',
            }}
            onClick={() => {
              surfaceClick('Boot → Continue to role selection');
              completeBoot();
            }}
          >
            Continue
          </button>
        )}
      </div>
      <button
        type="button"
        className="pill-btn"
        style={{ marginTop: 24, opacity: 0.7 }}
        onClick={() => {
          surfaceClick('Boot → Skip (presenter)');
          completeBoot();
        }}
      >
        Skip
      </button>
    </div>
  );
}
