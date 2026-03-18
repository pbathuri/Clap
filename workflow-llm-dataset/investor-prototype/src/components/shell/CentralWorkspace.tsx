import type { ReactNode } from 'react';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { MissionSurfaceState } from '../../mocks/missionMock';
import type { RailSectionId } from '../../shell/models';
import { useDemoFlow } from '../../state/DemoFlowContext';
import { GlassSurface } from '../mission/GlassSurface';
import { useStaggerReveal } from '../../hooks/useStaggerReveal';

const RAIL_ORDER: RailSectionId[] = ['home', 'work', 'guidance', 'inbox'];

function EmptyState({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="empty-state">
      <div className="label-caps">{title}</div>
      <p className="empty-state__body">{body}</p>
    </div>
  );
}

function HomeView({
  m,
}: {
  m: MissionSurfaceState;
  dataProvenance?: string | null;
}) {
  const { register } = useStaggerReveal(3);
  return (
    <>
      <div className="shell-center__hero">
        <p className="label-caps" style={{ marginBottom: 12 }}>
          AI workspace
        </p>
        <h2 className="display-title shell-center__headline">
          {m.nextBestAction}
        </h2>
        <p
          style={{
            marginTop: 16,
            color: 'var(--text-secondary)',
            fontSize: 15,
            maxWidth: 520,
            lineHeight: 1.5,
          }}
        >
          One calm surface for context, next move, and first value — you stay in control.
        </p>
      </div>
      <GlassSurface label="Center · First value" style={{ padding: 22 }}>
        <div className="label-caps" style={{ marginBottom: 8 }}>
          First value
        </div>
        <div
          ref={register(0)}
          className="display-title"
          style={{ fontSize: '1.05rem' }}
        >
          {m.firstValueTitle}
        </div>
        <div
          ref={register(1)}
          style={{
            marginTop: 14,
            padding: 16,
            borderRadius: 14,
            background: 'rgba(126, 184, 218, 0.08)',
            border: '1px solid rgba(126, 184, 218, 0.12)',
            fontSize: 14,
            color: 'var(--text-secondary)',
            lineHeight: 1.55,
          }}
        >
          {m.firstValueBody}
        </div>
        <div ref={register(2)} className="first-value__hint">
          Supervised delivery · one-click handoff once approved
        </div>
      </GlassSurface>
    </>
  );
}

function WorkView({
  m,
}: {
  m: MissionSurfaceState;
  dataProvenance?: string | null;
}) {
  return (
    <>
      <GlassSurface label="Work · Context" style={{ padding: 20 }}>
        <div className="label-caps" style={{ marginBottom: 10 }}>
          Current context
        </div>
        <div style={{ fontSize: 15, lineHeight: 1.55 }}>{m.currentContext}</div>
        {m.workspaceHomePreview && (
          <pre className="shell-center__pre">{m.workspaceHomePreview}</pre>
        )}
        {!m.workspaceHomePreview && (
          <EmptyState
            title="Workspace snapshot"
            body="Live workspace summary appears here after the first sync — the context above remains the source of truth."
          />
        )}
      </GlassSurface>
      <GlassSurface label="Work · Memory detail" style={{ padding: 20 }}>
        <div className="label-caps" style={{ marginBottom: 10 }}>
          Memory bootstrap
        </div>
        <div style={{ fontWeight: 600 }}>{m.memoryBootstrap}</div>
        <div
          style={{
            marginTop: 10,
            fontSize: 13,
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
          }}
        >
          {m.memoryDetail}
        </div>
      </GlassSurface>
    </>
  );
}

function GuidanceView({
  m,
  dataProvenance,
}: {
  m: MissionSurfaceState;
  dataProvenance?: string | null;
}) {
  const [pulse, setPulse] = useState(false);
  const prev = useRef<string | null>(null);
  useEffect(() => {
    if (prev.current === 'mock' && dataProvenance && dataProvenance !== 'mock') {
      setPulse(true);
      const t = window.setTimeout(() => setPulse(false), 2200);
      return () => window.clearTimeout(t);
    }
    prev.current = dataProvenance ?? null;
    return undefined;
  }, [dataProvenance]);

  return (
    <>
      <GlassSurface label="Guidance · Next action" style={{ padding: 20 }}>
        <div className="label-caps" style={{ marginBottom: 10 }}>
          Next best action
        </div>
        <div style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.45 }}>
          {m.nextBestAction}
        </div>
      </GlassSurface>
      {m.operatorSummaryPreview &&
        (m.operatorSummaryPreview.knows ||
          m.operatorSummaryPreview.recommends) && (
          <GlassSurface
            label="Guidance · Desk readout"
            style={{ padding: 20 }}
            className={pulse ? 'operator-summary--pulse' : undefined}
          >
            <div className="label-caps" style={{ marginBottom: 12 }}>
              What the desk sees
            </div>
            {m.operatorSummaryPreview.knows && (
              <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                <strong style={{ color: 'var(--text-muted)' }}>Context · </strong>
                {m.operatorSummaryPreview.knows}
              </p>
            )}
            {m.operatorSummaryPreview.recommends && (
              <p
                style={{
                  fontSize: 13,
                  color: 'var(--text-secondary)',
                  marginTop: 10,
                }}
              >
                <strong style={{ color: 'var(--text-muted)' }}>Suggests · </strong>
                {m.operatorSummaryPreview.recommends}
              </p>
            )}
            {m.operatorSummaryPreview.needs && (
              <p
                style={{
                  fontSize: 13,
                  color: 'var(--text-secondary)',
                  marginTop: 10,
                }}
              >
                <strong style={{ color: 'var(--text-muted)' }}>From you · </strong>
                {m.operatorSummaryPreview.needs}
              </p>
            )}
          </GlassSurface>
        )}
      {!m.operatorSummaryPreview && (
        <GlassSurface label="Guidance · Desk readout" style={{ padding: 20 }}>
          <EmptyState
            title="Operator summary"
            body="This panel lights up after the live snapshot arrives — until then, stay on the next action above."
          />
        </GlassSurface>
      )}
    </>
  );
}

function InboxView({
  m,
}: {
  m: MissionSurfaceState;
  dataProvenance?: string | null;
}) {
  const items = m.inboxItems;
  return (
    <GlassSurface label="Inbox · Pending" style={{ padding: 20 }}>
      <div className="label-caps" style={{ marginBottom: 14 }}>
        Inbox
      </div>
      {!items?.length ? (
        <EmptyState
          title="No pending interventions"
          body="Everything is supervised and clear — new review items will surface here."
        />
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
          {items.slice(0, 12).map((row) => (
            <li
              key={row.item_id}
              style={{
                padding: '12px 0',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                fontSize: 13,
              }}
            >
              <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                {row.kind}
              </span>
              <div style={{ marginTop: 4 }}>{row.summary}</div>
            </li>
          ))}
        </ul>
      )}
    </GlassSurface>
  );
}

const VIEWS: Record<
  RailSectionId,
  (props: { m: MissionSurfaceState; dataProvenance?: string | null }) => ReactNode
> =
  {
    home: HomeView,
    work: WorkView,
    guidance: GuidanceView,
    inbox: InboxView,
  };

export function CentralWorkspace({ m }: { m: MissionSurfaceState }) {
  const { desktopShell, demoViewModel } = useDemoFlow();
  const rail = desktopShell.missionHome.railActive;
  const View = VIEWS[rail];
  const prevRailRef = useRef<RailSectionId>(rail);
  const prevRail = prevRailRef.current;
  const direction = useMemo(() => {
    if (prevRail === rail) return 'right';
    const nextIdx = RAIL_ORDER.indexOf(rail);
    const prevIdx = RAIL_ORDER.indexOf(prevRail);
    return nextIdx >= prevIdx ? 'right' : 'left';
  }, [prevRail, rail]);

  useEffect(() => {
    prevRailRef.current = rail;
  }, [rail]);

  return (
    <main className="shell-center" aria-label="AI workspace">
      <div
        key={rail}
        className={`shell-center-view shell-center--enter-${direction}`}
      >
        <View
          m={m}
          dataProvenance={demoViewModel?.dataProvenance ?? null}
        />
      </div>
    </main>
  );
}
