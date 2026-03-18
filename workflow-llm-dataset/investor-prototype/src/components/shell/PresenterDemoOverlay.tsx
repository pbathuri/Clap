import { useMemo, useState } from 'react';
import { useDemoFlow } from '../../state/DemoFlowContext';
import { MISSION_WALKTHROUGH_LABELS } from '../../demo/missionWalkthrough';
import { isPresenterDemoMode } from '../../demo/presenterMode';

const SCRIPT_LINES = [
  {
    phase: 'Boot',
    key: 'boot',
    cue: 'Laptop-local edge operator · USB bundle optional · privacy-first boot',
  },
  {
    phase: 'Role',
    key: 'role',
    cue: 'One desk · vertical pack + bounded learning for that role',
  },
  ...MISSION_WALKTHROUGH_LABELS.map((l, i) => ({
    phase: 'Mission',
    key: `m${i}`,
    cue: l,
  })),
  {
    phase: 'Explore',
    key: 'free',
    cue: 'Rails: Home · Work · Guidance · Inbox — optional multi-window',
  },
] as const;

function activeScriptIndex(
  phase: string,
  walkStep: number
): number {
  if (phase === 'boot') return 0;
  if (phase === 'role') return 1;
  if (phase === 'mission') {
    if (walkStep >= 4) return SCRIPT_LINES.length - 1;
    return 2 + walkStep;
  }
  return 0;
}

export function PresenterDemoOverlay() {
  const [open, setOpen] = useState(true);
  const {
    phase,
    missionWalkthroughStep,
    demoViewModel,
    edgeRevalidating,
    edgeLiveActive,
  } = useDemoFlow();

  const isDemoStory =
    edgeLiveActive && demoViewModel?.dataProvenance === 'mock';

  const activeIdx = useMemo(
    () => activeScriptIndex(phase, missionWalkthroughStep),
    [phase, missionWalkthroughStep]
  );

  if (!isPresenterDemoMode()) return null;

  return (
    <div
      className={`presenter-overlay ${open ? 'presenter-overlay--open' : ''}`}
    >
      <button
        type="button"
        className="presenter-overlay__toggle"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        {open ? '▼ Guide' : '▲ Guide'}
      </button>
      {open && (
        <div className="presenter-overlay__panel">
          <div className="label-caps presenter-overlay__title">
            Presenter guide
          </div>
          <p className="presenter-overlay__meta">
            Now: <strong>{SCRIPT_LINES[activeIdx]?.phase}</strong>
            {phase === 'mission' && missionWalkthroughStep < 4 && (
              <>
                {' · '}
                Beat {missionWalkthroughStep + 1}/4
              </>
            )}
            {demoViewModel?.dataProvenance === 'live' && (
              <span className="presenter-overlay__live"> · Live</span>
            )}
            {demoViewModel?.dataProvenance === 'cached' && (
              <span className="presenter-overlay__cached"> · Last sync</span>
            )}
            {edgeRevalidating && (
              <span className="presenter-overlay__sync"> · Refreshing…</span>
            )}
          </p>
          <ol className="presenter-overlay__list presenter-overlay__list--script">
            {SCRIPT_LINES.map((row, i) => (
              <li
                key={row.key}
                className={
                  i === activeIdx ? 'presenter-overlay__li--active' : undefined
                }
              >
                <span className="presenter-overlay__phase">{row.phase}</span>
                {row.cue}
              </li>
            ))}
          </ol>
          <div className="presenter-overlay__failure" role="region" aria-label="If something goes wrong">
            <div className="label-caps presenter-overlay__failure-title">
              If live is slow or shows Demo story
            </div>
            <p className="presenter-overlay__failure-body">
              Keep talking: bounded learning + first value still land on mock. Say
              &quot;rehearsal-safe copy&quot; — never imply live when the top bar says{' '}
              <strong>Demo story</strong>. Prefetch JSON before the room; or tap{' '}
              <strong>Reset demo</strong> (top bar) between runs.
            </p>
            {isDemoStory && (
              <p className="presenter-overlay__failure-warn">
                Now: narrative is coherent — emphasize supervised posture + roadmap to
                dedicated hardware.
              </p>
            )}
          </div>
          <p className="presenter-overlay__foot">
            Prefetch:{' '}
            <code className="presenter-overlay__code">
              workflow-dataset demo edge-desktop-snapshot -o
              investor-prototype/public/edge-desktop-snapshot.json
            </code>
            · <code>?presenter=1</code> · <code>?resetDemo=1</code> cold reset
          </p>
        </div>
      )}
    </div>
  );
}
