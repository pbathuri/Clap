import type { MissionSurfaceState } from '../../mocks/missionMock';
import { useDemoFlow } from '../../state/DemoFlowContext';
import { GlassSurface } from '../mission/GlassSurface';

export function RightMissionPanel({ m }: { m: MissionSurfaceState }) {
  const {
    desktopShell,
    toggleRightMissionPanel,
    surfaceClick,
    inboxPulse,
    clearInboxPulse,
  } = useDemoFlow();
  const inboxCount = m.inboxItems?.length ?? 0;
  if (!desktopShell.missionHome.rightPanelOpen) {
    return (
      <button
        type="button"
        className="shell-right-expand"
        onClick={() => {
          surfaceClick('Mission panel · Expand');
          toggleRightMissionPanel();
        }}
        aria-label="Show mission status"
      >
        ⟨
      </button>
    );
  }

  return (
    <aside className="shell-right" aria-label="Mission status">
      <div className="shell-right__header">
        <span className="label-caps">Mission</span>
        <button
          type="button"
          className="shell-right__collapse"
          onClick={() => {
            surfaceClick('Mission panel · Collapse');
            toggleRightMissionPanel();
          }}
          aria-label="Collapse panel"
        >
          ⟩
        </button>
      </div>
      <div className="shell-right__scroll">
        <GlassSurface label="Mission · Readiness" style={{ padding: 16 }}>
          <div className="label-caps" style={{ marginBottom: 6 }}>
            Readiness
          </div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{m.readinessLabel}</div>
          <div style={{ marginTop: 8, fontSize: 12, color: 'var(--accent)' }}>
            {m.assistState}
          </div>
        </GlassSurface>
        <GlassSurface label="Mission · Role" style={{ padding: 16 }}>
          <div className="label-caps" style={{ marginBottom: 6 }}>
            Role
          </div>
          <div className="display-title" style={{ fontSize: '1rem' }}>
            {m.roleLabel}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6 }}>
            {m.verticalPack}
          </div>
        </GlassSurface>
        <GlassSurface label="Mission · Memory" style={{ padding: 16 }}>
          <div className="label-caps" style={{ marginBottom: 6 }}>
            Memory
          </div>
          <div style={{ fontSize: 12, lineHeight: 1.45 }}>{m.memoryBootstrap}</div>
        </GlassSurface>
        <GlassSurface label="Mission · Trust" style={{ padding: 16 }}>
          <div className="label-caps" style={{ marginBottom: 6 }}>
            Trust
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--success)' }}>
            {m.trustPosture}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, lineHeight: 1.4 }}>
            {m.trustDetail.slice(0, 140)}
            {m.trustDetail.length > 140 ? '…' : ''}
          </div>
        </GlassSurface>
        <GlassSurface label="Mission · Timeline" style={{ padding: 16 }}>
          <div className="label-caps" style={{ marginBottom: 8 }}>
            Steps
          </div>
          <ul className="shell-right__timeline">
            {m.timeline.slice(0, 5).map((e) => (
              <li key={e.id}>{e.label}</li>
            ))}
          </ul>
        </GlassSurface>
        <GlassSurface
          label="Mission · Inbox"
          style={{ padding: 16 }}
          className={inboxPulse ? 'live-badge__glow' : undefined}
        >
          <div className="shell-right__inbox-header">
            <span className="label-caps">Inbox</span>
            {inboxPulse && (
              <span className="live-badge live-badge--on" aria-hidden />
            )}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            {inboxCount > 0
              ? `${inboxCount} item${inboxCount === 1 ? '' : 's'} pending review`
              : 'No pending review items in this slice.'}
          </div>
          {inboxPulse && (
            <button
              type="button"
              className="pill-btn pill-btn--ghost"
              style={{ marginTop: 10 }}
              onClick={() => {
                surfaceClick('Mission panel · Inbox badge cleared');
                clearInboxPulse();
              }}
            >
              Acknowledge
            </button>
          )}
        </GlassSurface>
      </div>
    </aside>
  );
}
