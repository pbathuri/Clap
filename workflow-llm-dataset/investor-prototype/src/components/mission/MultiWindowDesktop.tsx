import type { CSSProperties, ReactNode } from 'react';
import { useEffect, useRef } from 'react';
import { animate, stagger } from '@motionone/dom';
import type { MissionSurfaceState } from '../../mocks/missionMock';
import { useDemoFlow } from '../../state/DemoFlowContext';

type WinDef = {
  id: string;
  title: string;
  box: CSSProperties;
  render: (m: MissionSurfaceState) => ReactNode;
};

const WINDOWS: WinDef[] = [
  {
    id: 'status',
    title: 'Readiness',
    box: { top: '12%', left: '8%', width: 340 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Device
        </div>
        <div style={{ fontWeight: 600 }}>{m.readinessLabel}</div>
        <div style={{ marginTop: 8, color: 'var(--accent)' }}>{m.assistState}</div>
      </>
    ),
  },
  {
    id: 'role',
    title: 'Role & pack',
    box: { top: '14%', left: '52%', width: 360 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Role
        </div>
        <div className="display-title" style={{ fontSize: '1.1rem' }}>
          {m.roleLabel}
        </div>
        <div style={{ marginTop: 8, color: 'var(--text-secondary)', fontSize: 14 }}>
          {m.verticalPack}
        </div>
      </>
    ),
  },
  {
    id: 'memory',
    title: 'Memory',
    box: { top: '38%', left: '6%', width: 320 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Bootstrap
        </div>
        <div style={{ fontWeight: 600 }}>{m.memoryBootstrap}</div>
        <div style={{ marginTop: 10, fontSize: 13, color: 'var(--text-secondary)' }}>
          {m.memoryDetail}
        </div>
      </>
    ),
  },
  {
    id: 'context',
    title: 'Context',
    box: { top: '42%', left: '42%', width: 300 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Context
        </div>
        <div style={{ fontSize: 14, lineHeight: 1.5 }}>{m.currentContext}</div>
      </>
    ),
  },
  {
    id: 'action',
    title: 'Next action',
    box: { top: '36%', right: '6%', width: 300 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Next
        </div>
        <div style={{ fontWeight: 600, fontSize: 15 }}>{m.nextBestAction}</div>
      </>
    ),
  },
  {
    id: 'trust',
    title: 'Trust',
    box: { top: '62%', left: '18%', width: 280 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Posture
        </div>
        <div style={{ color: 'var(--success)', fontWeight: 600 }}>{m.trustPosture}</div>
        <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-secondary)' }}>
          {m.trustDetail}
        </div>
      </>
    ),
  },
  {
    id: 'artifact',
    title: 'First value',
    box: { top: '58%', left: '48%', width: 380 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Artifact
        </div>
        <div className="display-title" style={{ fontSize: '1rem' }}>
          {m.firstValueTitle}
        </div>
        <div
          style={{
            marginTop: 10,
            padding: 12,
            borderRadius: 10,
            background: 'rgba(126, 184, 218, 0.08)',
            fontSize: 13,
            color: 'var(--text-secondary)',
          }}
        >
          {m.firstValueBody}
        </div>
      </>
    ),
  },
  {
    id: 'timeline',
    title: 'Timeline',
    box: { top: '72%', right: '5%', width: 320 },
    render: (m) => (
      <>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          Steps
        </div>
        <ul style={{ margin: 0, padding: 0, listStyle: 'none', fontSize: 12 }}>
          {m.timeline.slice(0, 4).map((e) => (
            <li
              key={e.id}
              style={{
                padding: '6px 0',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                color: 'var(--text-secondary)',
              }}
            >
              {e.label}{' '}
              <span style={{ color: 'var(--text-muted)', float: 'right' }}>{e.time}</span>
            </li>
          ))}
        </ul>
      </>
    ),
  },
];

export function MultiWindowDesktop({ m }: { m: MissionSurfaceState }) {
  const {
    activeMultiWindowId,
    setActiveMultiWindowId,
    surfaceClick,
    setLayoutMode,
    demoViewModel,
  } = useDemoFlow();
  const topOffset = demoViewModel?.degradedSummary ? 88 : 48;
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const nodes = containerRef.current?.querySelectorAll('.multi-surface');
    if (!nodes?.length) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    animate(
      nodes,
      { opacity: [0, 1], transform: ['scale(0.96)', 'scale(1)'] },
      { delay: stagger(0.05), duration: 0.45, easing: [0.22, 1, 0.36, 1] }
    );
  }, []);

  return (
    <div
      ref={containerRef}
      className="phase-enter-delay"
      style={{
        position: 'fixed',
        top: topOffset,
        left: 0,
        right: 0,
        bottom: 0,
        overflow: 'hidden',
        paddingBottom: 100,
      }}
    >
      <p
        className="label-caps"
        style={{
          position: 'absolute',
          top: 16,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 5,
          pointerEvents: 'none',
        }}
      >
        Virtual desktop · tap a surface to focus
      </p>
      {WINDOWS.map((w, i) => {
        const focused = activeMultiWindowId === w.id;
        const baseZ = 20 + i;
        const zIndex = focused ? 55 : activeMultiWindowId ? 12 : baseZ;

        const dimmed = Boolean(activeMultiWindowId && !focused);
        return (
          <div
            key={w.id}
            className={`glass-panel glass-panel--interactive multi-surface ${
              focused ? 'multi-surface--front' : 'multi-surface--back'
            } ${dimmed ? 'multi-surface--dimmed' : ''}`}
            style={{
              position: 'absolute',
              ...w.box,
              maxWidth: '90vw',
              padding: 0,
              overflow: 'hidden',
              zIndex,
            }}
            role="button"
            tabIndex={0}
            onClick={() => {
              setActiveMultiWindowId(w.id);
              surfaceClick(`Multi-window · ${w.title}`);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                setActiveMultiWindowId(w.id);
                surfaceClick(`Multi-window · ${w.title}`);
              }
            }}
          >
            <div
              style={{
                padding: '10px 14px',
                borderBottom: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(0,0,0,0.15)',
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em' }}>
                {w.title}
              </span>
              <span style={{ opacity: 0.4 }} aria-hidden>
                ● ● ●
              </span>
            </div>
            <div style={{ padding: 16 }}>{w.render(m)}</div>
          </div>
        );
      })}
      <div
        style={{
          position: 'absolute',
          bottom: 88,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 70,
        }}
      >
        <button
          type="button"
          className="glass-panel glass-panel--interactive"
          style={{
            padding: '12px 22px',
            font: 'inherit',
            color: 'var(--text-secondary)',
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
          }}
          onClick={() => {
            surfaceClick('Layout · Return to single workspace');
            setLayoutMode('single');
            setActiveMultiWindowId(null);
          }}
        >
          ← Single AI workspace
        </button>
      </div>
    </div>
  );
}
