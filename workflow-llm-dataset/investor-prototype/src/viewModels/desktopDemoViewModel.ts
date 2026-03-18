/**
 * Single UI view model for Edge Operator Desktop demo.
 * Owns snapshot→mission mapping + data provenance + degraded signals.
 */

import type { RoleId } from '../mocks/missionMock';
import type { MissionSurfaceState, TimelineEntry } from '../mocks/missionMock';
import type { EdgeDataSource } from '../adapters/edgeDesktopTypes';
import type { EdgeDesktopSnapshot } from '../adapters/edgeDesktopTypes';
import { softenEngineeringCopy } from '../lib/investorCopy';

export type DesktopDemoViewModel = MissionSurfaceState & {
  dataProvenance: EdgeDataSource;
  /** One-line investor-safe degraded explanation */
  degradedSummary: string | null;
  staleFieldCount: number;
  timeoutOrPartial: boolean;
  adapterMeta?: EdgeDesktopSnapshot['adapter_meta'];
};

function cap(s: string, n: number): string {
  const t = (s || '').trim();
  if (t.length <= n) return t;
  return `${t.slice(0, n - 1)}…`;
}

function buildTimeline(
  snap: EdgeDesktopSnapshot,
  base: MissionSurfaceState
): TimelineEntry[] {
  const rows: TimelineEntry[] = [];
  const ok = snap.sources_ok || [];
  let i = 0;
  const push = (label: string, highlight = false) => {
    rows.push({
      id: `live-${i++}`,
      label,
      time: '',
      tone: highlight ? 'highlight' : 'neutral',
    });
  };
  if (ok.includes('readiness')) push('USB / demo readiness captured', true);
  if (snap.bootstrap_last) push('Host bootstrap manifest on disk', true);
  if (ok.includes('onboarding_ready')) push('Onboarding ready-state');
  if (ok.includes('workspace_home')) push('Workspace home snapshot');
  if (ok.includes('day_status')) push('Day status');
  if (ok.includes('guidance_next_action') && snap.guidance_next_action)
    push('Guidance · next action', true);
  if (ok.includes('operator_summary')) push('Operator summary');
  const inboxN = snap.inbox?.length ?? 0;
  push(`Inbox · ${inboxN} pending item(s)`, inboxN > 0);
  if (rows.length < 4) {
    return base.timeline.map((t, j) => ({ ...t, id: `mix-${j}` }));
  }
  rows.push({
    id: 'gen',
    label: `Snapshot ${snap.generated_at?.slice(11, 19) || ''} UTC`,
    time: snap.generated_at?.slice(0, 10) || '',
    tone: 'neutral',
  });
  return rows;
}

function countStale(meta: EdgeDesktopSnapshot['adapter_meta']): number {
  const fs = meta?.field_status || {};
  return Object.values(fs).filter((v) =>
    ['stale_cache', 'timeout', 'skipped_slow_path', 'error'].includes(v)
  ).length;
}

function buildDegradedSummary(
  snap: EdgeDesktopSnapshot | null,
  source: EdgeDataSource,
  staleN: number,
  timedOut: boolean
): string | null {
  if (timedOut && source === 'mock')
    return 'Workspace sync is taking a moment — showing a stable demo view. Refresh or use a prefetched snapshot for instant load.';
  if (staleN > 0 && snap?.adapter_meta)
    return 'Some details are from an earlier sync — the story still holds.';
  if (snap?.readiness?.degraded_explanation)
    return cap(String(snap.readiness.degraded_explanation), 160);
  const deg =
    snap?.readiness &&
    (typeof snap.readiness.degraded_mode === 'string'
      ? snap.readiness.degraded_mode
      : (snap.readiness.degraded_mode as { value?: string })?.value);
  if (deg && deg !== 'none' && deg !== 'false')
    return `Operating in ${deg} — local-first posture unchanged.`;
  return null;
}

/**
 * Build the canonical desktop demo view model from optional live snapshot + role mock.
 */
export function buildDesktopDemoViewModel(
  snap: EdgeDesktopSnapshot | null,
  _roleId: RoleId,
  mock: MissionSurfaceState,
  source: EdgeDataSource,
  opts?: { timedOut?: boolean }
): DesktopDemoViewModel {
  const timedOut = !!opts?.timedOut;
  if (!snap) {
    return {
      ...mock,
      dataProvenance: source,
      degradedSummary: buildDegradedSummary(null, source, 0, timedOut),
      staleFieldCount: 0,
      timeoutOrPartial: timedOut,
    };
  }

  const rt = snap.onboarding_ready?.ready_to_assist;
  const wh = snap.workspace_home;
  const day = snap.day_status;
  const g = snap.guidance_next_action;
  const op = snap.operator_summary;
  const rd = snap.readiness;

  let readinessLabel = mock.readinessLabel;
  const capLevel =
    rd &&
    (typeof rd.capability_level === 'string'
      ? rd.capability_level
      : (rd.capability_level as { value?: string } | undefined)?.value);
  const degMode =
    rd &&
    (typeof rd.degraded_mode === 'string'
      ? rd.degraded_mode
      : (rd.degraded_mode as { value?: string } | undefined)?.value);
  if (capLevel) {
    readinessLabel = degMode ? `${capLevel} · ${degMode}` : String(capLevel);
  } else if (snap.errors?.readiness) {
    readinessLabel = 'Workspace mode · USB bundle optional';
  }

  const assistState =
    rt?.ready === true
      ? 'Ready to assist'
      : rt?.ready === false
        ? 'Onboarding in progress'
        : mock.assistState;

  const roleLabel = rt?.chosen_role_label || mock.roleLabel;
  const verticalPack = rt?.vertical_pack_id || mock.verticalPack;
  const memoryBootstrap =
    cap(rt?.memory_bootstrap_summary || '', 120) || mock.memoryBootstrap;
  const themeList = (rt?.recurring_themes || []).filter(Boolean).slice(0, 6);
  const priorityList = (rt?.likely_priorities || []).filter(Boolean).slice(0, 5);
  const themes = themeList.length ? themeList.join(' · ') : '';
  const rawMemoryDetail =
    themes ||
    cap(wh?.trust_health_summary || '', 200) ||
    mock.memoryDetail;
  const memoryDetail = softenEngineeringCopy(rawMemoryDetail, mock.memoryDetail);

  const currentContext =
    cap(rt?.inferred_project_context || '', 200) ||
    cap(wh?.context?.active_goal_text || '', 200) ||
    mock.currentContext;

  const nextBestAction = softenEngineeringCopy(
    cap(g?.summary || '', 220) ||
      cap(wh?.context?.next_recommended_action || '', 220) ||
      mock.nextBestAction,
    mock.nextBestAction
  );

  const trustPosture =
    cap(day?.trust_posture || '', 100) || mock.trustPosture;
  const trustDetail = softenEngineeringCopy(
    cap(op?.what_it_needs_from_user || '', 280) ||
      cap(g?.rationale || '', 200) ||
      mock.trustDetail,
    mock.trustDetail
  );

  const firstValueTitle = mock.firstValueTitle;
  const firstValueBody = softenEngineeringCopy(
    cap(rt?.recommended_first_value_action || '', 320) ||
      cap(op?.what_it_recommends || '', 320) ||
      mock.firstValueBody,
    mock.firstValueBody
  );

  const staleN = countStale(snap.adapter_meta);
  const mission: MissionSurfaceState = {
    roleLabel,
    verticalPack,
    memoryBootstrap,
    memoryDetail,
    currentContext,
    nextBestAction,
    trustPosture,
    trustDetail,
    firstValueTitle,
    firstValueBody,
    readinessLabel,
    assistState,
    timeline: buildTimeline(snap, mock),
    inboxItems: snap.inbox?.length ? snap.inbox : undefined,
    workspaceHomePreview: snap.workspace_home_text
      ? cap(snap.workspace_home_text, 500)
      : undefined,
    dayStatusPreview: snap.day_status_text
      ? cap(snap.day_status_text, 400)
      : undefined,
    operatorSummaryPreview: op
      ? {
          knows: softenEngineeringCopy(
            cap(op.what_system_knows || '', 200),
            'Your workspace context is loaded locally.'
          ),
          recommends: softenEngineeringCopy(
            cap(op.what_it_recommends || '', 200),
            mock.firstValueBody
          ),
          needs: softenEngineeringCopy(
            cap(op.what_it_needs_from_user || '', 200),
            mock.trustDetail
          ),
        }
      : undefined,
    liveGeneratedAt: snap.generated_at,
    keyThemes: themeList.length ? themeList : mock.keyThemes,
    keyPriorities: priorityList.length ? priorityList : mock.keyPriorities,
  };

  return {
    ...mission,
    dataProvenance: source,
    degradedSummary: buildDegradedSummary(snap, source, staleN, timedOut),
    staleFieldCount: staleN,
    timeoutOrPartial: timedOut || staleN > 0,
    adapterMeta: snap.adapter_meta,
  };
}

export function missionSurfaceOnly(vm: DesktopDemoViewModel): MissionSurfaceState {
  const {
    dataProvenance: _p,
    degradedSummary: _d,
    staleFieldCount: _s,
    timeoutOrPartial: _t,
    adapterMeta: _a,
    ...m
  } = vm;
  return m;
}
