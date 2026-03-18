import { useEffect, useRef } from 'react';
import { isPresenterDemoMode } from '../../demo/presenterMode';
import { triggerAmbientPulse } from '../../ambient/ambientEvents';
import { useDemoFlow } from '../../state/DemoFlowContext';

function sourceLabel(
  s: string | null,
  loading: boolean,
  revalidating: boolean,
  err?: string
): string {
  if (loading) return 'Connecting…';
  if (revalidating) return 'Refreshing…';
  if (err) return 'Demo story';
  if (s === 'live') return 'Connected';
  if (s === 'cached') return 'Last sync';
  if (s === 'static_file') return 'Snapshot file';
  return 'Demo story';
}

export function TopBar() {
  const {
    mission,
    demoViewModel,
    goToPhase,
    layoutMode,
    surfaceClick,
    edgeLiveActive,
    edgeDataSource,
    edgeLoading,
    edgeRevalidating,
    edgeLiveError,
    refreshEdgeSnapshot,
    resetDemoSession,
    desktopShell,
  } = useDemoFlow();

  const showPresenterTools =
    typeof window !== 'undefined' && isPresenterDemoMode();
  const prevProvenance = useRef<string | null>(null);

  useEffect(() => {
    const current = demoViewModel?.dataProvenance ?? null;
    if (prevProvenance.current && current && prevProvenance.current !== current) {
      triggerAmbientPulse(1);
    }
    prevProvenance.current = current;
  }, [demoViewModel?.dataProvenance]);

  return (
    <header
      className={`top-bar ${demoViewModel?.degradedSummary ? 'top-bar--degraded' : ''}`}
    >
      <div className="top-bar__row">
        <div className="top-bar__brand">
          <div className="top-bar__brand-mark" aria-hidden />
          <span>Workstation</span>
          {mission && (
            <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>
              · {mission.roleLabel}
            </span>
          )}
          <span
            style={{
              marginLeft: 8,
              fontSize: 11,
              color: 'var(--text-muted)',
              fontWeight: 500,
            }}
          >
            {desktopShell.topBar.contextHint}
          </span>
        </div>
        <div className="top-bar__actions">
          {edgeLiveActive && (
            <>
              <button
                type="button"
                className="pill-btn"
                style={{
                  borderColor: 'rgba(126, 184, 218, 0.35)',
                  color: 'var(--accent)',
                }}
                title={
                  edgeLiveError
                    ? 'Using demo-safe copy · tap to retry'
                    : 'Workspace snapshot · tap to refresh'
                }
                onClick={() => {
                  surfaceClick('Top bar → Refresh snapshot');
                  refreshEdgeSnapshot();
                }}
              >
                {sourceLabel(
                  edgeDataSource,
                  edgeLoading,
                  edgeRevalidating,
                  edgeLiveError
                )}
              </button>
            </>
          )}
          <span
            className="label-caps"
            style={{ marginRight: 8, alignSelf: 'center' }}
          >
            {layoutMode === 'single' ? 'Unified' : 'Multi-surface'}
          </span>
          <button
            type="button"
            className="pill-btn"
            onClick={() => {
              surfaceClick('Top bar → Switch role');
              goToPhase('role');
            }}
          >
            Switch role
          </button>
          <button
            type="button"
            className="pill-btn"
            onClick={() => {
              surfaceClick('Top bar → Reboot story');
              goToPhase('boot');
            }}
          >
            Reboot
          </button>
          {showPresenterTools && (
            <button
              type="button"
              className="pill-btn pill-btn--ghost"
              title="Clear session cache and return to boot — between rehearsals"
              onClick={() => {
                surfaceClick('Top bar → Reset demo session');
                resetDemoSession();
              }}
            >
              Reset demo
            </button>
          )}
        </div>
      </div>
      {demoViewModel?.degradedSummary && (
        <div className="top-bar__degraded" role="status" aria-live="polite">
          {demoViewModel.degradedSummary}
        </div>
      )}
    </header>
  );
}
