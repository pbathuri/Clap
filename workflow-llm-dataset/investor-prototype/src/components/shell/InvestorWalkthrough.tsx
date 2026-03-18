import { useDemoFlow } from '../../state/DemoFlowContext';
import { isPresenterDemoMode } from '../../demo/presenterMode';
import {
  MISSION_WALKTHROUGH_LABELS,
  type MissionWalkthroughStep,
} from '../../demo/missionWalkthrough';

function StepContent({
  step,
}: {
  step: Exclude<MissionWalkthroughStep, 4>;
}) {
  const { demoViewModel: vm } = useDemoFlow();
  if (!vm) return null;

  if (step === 0) {
    return (
      <>
        <p className="walkthrough__lede">
          Local readiness and bounded memory — no cloud required for this story.
        </p>
        <div className="walkthrough__grid">
          <div>
            <span className="label-caps">Readiness</span>
            <p className="walkthrough__strong">{vm.readinessLabel}</p>
            <p className="walkthrough__muted">{vm.assistState}</p>
          </div>
          <div>
            <span className="label-caps">Memory bootstrap</span>
            <p className="walkthrough__strong">{vm.memoryBootstrap}</p>
            <p className="walkthrough__muted">{vm.memoryDetail}</p>
          </div>
        </div>
      </>
    );
  }
  if (step === 1) {
    return (
      <>
        <p className="walkthrough__lede">
          Mission overview — role, pack, context, themes, and priorities (shaped from
          ready-state, not raw CLI).
        </p>
        <div className="walkthrough__grid">
          <div>
            <span className="label-caps">Role & pack</span>
            <p className="walkthrough__strong">{vm.roleLabel}</p>
            <p className="walkthrough__muted">{vm.verticalPack}</p>
          </div>
          <div>
            <span className="label-caps">Inferred context</span>
            <p className="walkthrough__muted">{vm.currentContext}</p>
          </div>
        </div>
        {(vm.keyThemes?.length || vm.keyPriorities?.length) ? (
          <div className="walkthrough__grid walkthrough__grid--chips">
            {vm.keyThemes && vm.keyThemes.length > 0 && (
              <div>
                <span className="label-caps">Key themes</span>
                <ul className="walkthrough__chips">
                  {vm.keyThemes.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </div>
            )}
            {vm.keyPriorities && vm.keyPriorities.length > 0 && (
              <div>
                <span className="label-caps">Priorities</span>
                <ul className="walkthrough__chips">
                  {vm.keyPriorities.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : null}
      </>
    );
  }
  if (step === 2) {
    return (
      <>
        <p className="walkthrough__lede">
          First value is grounded in state — supervised, not autonomous send.
        </p>
        <div className="walkthrough__artifact">
          <span className="label-caps">First value</span>
          <p className="walkthrough__strong">{vm.firstValueTitle}</p>
          <p className="walkthrough__muted">{vm.firstValueBody}</p>
        </div>
      </>
    );
  }
  return (
    <>
      <p className="walkthrough__lede">
        Outbound and file moves stay approval-gated. Default is simulate.
      </p>
      <div className="walkthrough__grid">
        <div>
          <span className="label-caps">Trust posture</span>
          <p className="walkthrough__strong">{vm.trustPosture}</p>
          <p className="walkthrough__muted">{vm.trustDetail}</p>
        </div>
        <div>
          <span className="label-caps">Next action</span>
          <p className="walkthrough__muted">{vm.nextBestAction}</p>
          {vm.inboxItems && vm.inboxItems.length > 0 && (
            <p className="walkthrough__inbox">
              Inbox · {vm.inboxItems.length} pending (review, don&apos;t auto-act)
            </p>
          )}
        </div>
      </div>
    </>
  );
}

export function InvestorWalkthrough() {
  const {
    missionWalkthroughStep,
    advanceMissionWalkthrough,
    backMissionWalkthrough,
    skipMissionWalkthrough,
    surfaceClick,
  } = useDemoFlow();
  const presenterMode =
    typeof window !== 'undefined' && isPresenterDemoMode();

  if (missionWalkthroughStep >= 4) return null;

  const step = missionWalkthroughStep as 0 | 1 | 2 | 3;
  const label = MISSION_WALKTHROUGH_LABELS[step];

  return (
    <div
      className={`investor-walkthrough ${presenterMode ? 'investor-walkthrough--presenter' : ''}`}
      role="region"
      aria-label="Investor demo story"
    >
      <div className="glass-panel investor-walkthrough__surface">
        <div className="investor-walkthrough__header">
          <div className="investor-walkthrough__dots" aria-hidden>
            {MISSION_WALKTHROUGH_LABELS.map((_, i) => (
              <span
                key={i}
                className={`investor-walkthrough__dot ${i === step ? 'investor-walkthrough__dot--on' : ''} ${i < step ? 'investor-walkthrough__dot--done' : ''}`}
              />
            ))}
          </div>
          <span className="label-caps">{label}</span>
          <button
            type="button"
            className="investor-walkthrough__skip"
            onClick={() => {
              surfaceClick('Walkthrough → Enter workspace');
              skipMissionWalkthrough();
            }}
          >
            Enter workspace
          </button>
        </div>
        <div className="investor-walkthrough__body">
          <StepContent step={step} />
        </div>
        <div className="investor-walkthrough__footer">
          <button
            type="button"
            className="pill-btn pill-btn--ghost"
            disabled={step === 0}
            onClick={() => {
              surfaceClick('Walkthrough → Back');
              backMissionWalkthrough();
            }}
          >
            Back
          </button>
          <button
            type="button"
            className="pill-btn"
            onClick={() => {
              surfaceClick(
                step === 3
                  ? 'Walkthrough → Complete'
                  : `Walkthrough → Next (${MISSION_WALKTHROUGH_LABELS[step + 1]})`
              );
              advanceMissionWalkthrough();
            }}
          >
            {step === 3 ? 'Finish · explore rails' : 'Continue'}
          </button>
        </div>
      </div>
    </div>
  );
}
