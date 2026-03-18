import { ROLE_OPTIONS, type RoleId } from '../mocks/missionMock';
import { useDemoFlow } from '../state/DemoFlowContext';

export function RoleScreen() {
  const { selectRole, surfaceClick, goToPhase } = useDemoFlow();

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
        padding: '48px 24px 120px',
        overflow: 'auto',
      }}
    >
      <p className="label-caps" style={{ marginBottom: 12 }}>
        Edge Operator Desktop
      </p>
      <h1
        className="display-title"
        style={{
          fontSize: 'clamp(1.35rem, 3.5vw, 1.85rem)',
          margin: 0,
          textAlign: 'center',
        }}
      >
        Choose your desk
      </h1>
      <p
        style={{
          margin: '10px 0 36px',
          color: 'var(--text-secondary)',
          fontSize: 14,
          textAlign: 'center',
          maxWidth: 440,
          lineHeight: 1.5,
        }}
      >
        Each desk loads a pack, supervised posture, and bounded onboarding — nothing
        leaves your machine without you.
      </p>
      <div
        className="stagger"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 18,
          width: '100%',
          maxWidth: 980,
        }}
      >
        {ROLE_OPTIONS.map((r) => (
          <button
            key={r.id}
            type="button"
            className="glass-panel glass-panel--interactive role-card"
            style={{
              padding: 26,
              textAlign: 'left',
              font: 'inherit',
              color: 'inherit',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
            onClick={() => {
              surfaceClick(`Role → ${r.title}`);
              selectRole(r.id as RoleId);
            }}
          >
            <div className="role-card__header">
              <span className="role-card__icon" aria-hidden>
                {r.icon}
              </span>
              <span className="display-title role-card__title">{r.title}</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, margin: 0 }}>
              {r.subtitle}
            </p>
            <div
              style={{
                paddingTop: 8,
                borderTop: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                fontSize: 12,
              }}
            >
              <div>
                <span className="label-caps">Pack / workspace</span>
                <p style={{ margin: '6px 0 0', color: 'var(--text-secondary)' }}>
                  {r.packId}
                </p>
              </div>
              <div>
                <span className="label-caps">Trust</span>
                <p style={{ margin: '6px 0 0', color: 'var(--success)' }}>{r.trustLine}</p>
              </div>
              <div>
                <span className="label-caps">Initializes</span>
                <p style={{ margin: '6px 0 0', color: 'var(--text-muted)' }}>{r.initLine}</p>
              </div>
            </div>
            <div className="role-card__cta">
              Load demo profile
              <span aria-hidden>→</span>
            </div>
            <span className="role-card__hint">
              Hover for trust + pack details · Click to load
            </span>
          </button>
        ))}
      </div>
      <button
        type="button"
        className="pill-btn"
        style={{ marginTop: 28 }}
        onClick={() => {
          surfaceClick('Role → Back to boot');
          goToPhase('boot');
        }}
      >
        Back
      </button>
    </div>
  );
}
