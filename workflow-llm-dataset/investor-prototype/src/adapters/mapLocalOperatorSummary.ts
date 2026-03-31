/**
 * Maps snapshot.local_operator_summary → investor-safe shell surface.
 * Live snapshot is source of truth; absent summary → not visible.
 */

import type { EdgeDesktopSnapshot } from './edgeDesktopTypes';

export interface LocalOperatorSurface {
  /** True when snapshot included local_operator_summary (live or cached) */
  visible: boolean;
  headline: string;
  subline: string;
  approvedFoldersCount: number;
  approvedFolderPaths: string[];
  workflowNodeCount: number;
  rootsPreview: string;
  toolsTotal: number;
  toolsInstalled: number;
  proposalsCount: number;
  proposalLabels: string[];
  lastExecutionLine: string | null;
  /** From snapshot.supervised_task_run (CLI supervised task runs) */
  taskRunsTotalStored: number;
  lastTaskRunSummaryLine: string | null;
  updatedAt: string;
}

function pathFromFolderEntry(item: unknown): string {
  if (item && typeof item === 'object' && 'path' in item) {
    return String((item as { path: string }).path || '').trim();
  }
  return '';
}

function labelFromProposal(item: unknown): string {
  if (!item || typeof item !== 'object') return '';
  const o = item as { label?: string; title?: string; action_id?: string };
  return (o.label || o.title || o.action_id || '').trim().slice(0, 72);
}

function taskRunSurfaceFromSnapshot(snap: {
  supervised_task_run?: EdgeDesktopSnapshot['supervised_task_run'];
}): { taskRunsTotalStored: number; lastTaskRunSummaryLine: string | null } {
  const str = snap.supervised_task_run;
  if (!str || typeof str !== 'object') {
    return { taskRunsTotalStored: 0, lastTaskRunSummaryLine: null };
  }
  const total =
    typeof str.total_stored === 'number' && Number.isFinite(str.total_stored)
      ? str.total_stored
      : 0;
  const ltr = str.last_task_run;
  if (!ltr || typeof ltr !== 'object') {
    return { taskRunsTotalStored: total, lastTaskRunSummaryLine: null };
  }
  const st = String(ltr.status || '').trim();
  const pat = String(ltr.workflow_pattern || '').trim();
  const rid = String(ltr.run_id || '').trim();
  const shortRid = rid.length > 18 ? `${rid.slice(0, 14)}…` : rid;
  const parts = [st, pat, shortRid].filter(Boolean);
  return {
    taskRunsTotalStored: total,
    lastTaskRunSummaryLine: parts.length ? parts.join(' · ') : null,
  };
}

export function mapLocalOperatorSummary(
  snap: Pick<
    EdgeDesktopSnapshot,
    'local_operator_summary' | 'sources_ok' | 'errors' | 'supervised_task_run'
  >
): LocalOperatorSurface | undefined {
  const lo = snap.local_operator_summary;
  const fromLive =
    snap.sources_ok?.includes('local_operator_summary') &&
    !snap.errors?.local_operator_summary;

  if (lo == null && !fromLive) {
    return undefined;
  }

  if (lo == null && fromLive) {
    const taskRunSurfEarly = taskRunSurfaceFromSnapshot(snap);
    return {
      visible: true,
      headline: 'Local operator',
      subline:
        'Connected to live snapshot — run ingest & propose-actions to populate scope.',
      approvedFoldersCount: 0,
      approvedFolderPaths: [],
      workflowNodeCount: 0,
      rootsPreview: '—',
      toolsTotal: 0,
      toolsInstalled: 0,
      proposalsCount: 0,
      proposalLabels: [],
      lastExecutionLine: null,
      taskRunsTotalStored: taskRunSurfEarly.taskRunsTotalStored,
      lastTaskRunSummaryLine: taskRunSurfEarly.lastTaskRunSummaryLine,
      updatedAt: '—',
    };
  }

  const mr = (lo?.machine_readiness || {}) as Record<string, unknown>;
  const or = (lo?.operator_readiness || {}) as Record<string, unknown>;
  const machineSummary = String(mr.summary || '').trim();
  const operatorSummary = String(or.summary || '').trim();
  const nextSteps = Array.isArray(or.next_steps)
    ? (or.next_steps as string[]).filter(Boolean).slice(0, 2)
    : [];

  const af = lo?.approved_folders;
  const items = Array.isArray(af?.items) ? af!.items! : [];
  const approvedPaths = items.map(pathFromFolderEntry).filter(Boolean);
  const approvedCount =
    typeof af?.count === 'number' ? af.count : approvedPaths.length;

  const wf = lo?.workflow_tree;
  const nodeCount =
    typeof wf?.node_count === 'number' ? wf.node_count : 0;
  const roots = Array.isArray(wf?.roots)
    ? (wf!.roots as string[]).filter(Boolean).slice(0, 3)
    : [];

  const toolReg = (lo?.tool_registry || {}) as Record<string, unknown>;
  const toolsTotal = typeof toolReg.total === 'number' ? toolReg.total : 0;
  const toolsInstalled =
    typeof toolReg.installed === 'number' ? toolReg.installed : 0;

  const ap = lo?.action_proposals;
  const propItems = Array.isArray(ap?.items) ? ap!.items! : [];
  const propCount =
    typeof ap?.count === 'number' ? ap.count : propItems.length;
  const proposalLabels = propItems
    .map(labelFromProposal)
    .filter(Boolean)
    .slice(0, 4);

  const le = lo?.last_execution;
  let lastExecutionLine: string | null = null;
  if (le && typeof le === 'object') {
    const ok = le.success === true ? 'OK' : le.success === false ? 'Failed' : '';
    const aid = String(le.action_id || '').slice(0, 24);
    if (aid || ok)
      lastExecutionLine = [ok, aid, le.at ? String(le.at).slice(11, 19) : '']
        .filter(Boolean)
        .join(' · ');
  }

  const headline =
    machineSummary || 'Local operator · laptop scope';
  const subline =
    operatorSummary ||
    (nextSteps.length
      ? nextSteps.join(' · ')
      : 'Add approved folders, then ingest and propose actions from the CLI.');

  const taskRunSurf = taskRunSurfaceFromSnapshot(snap);

  return {
    visible: true,
    headline,
    subline,
    approvedFoldersCount: approvedCount,
    approvedFolderPaths: approvedPaths.slice(0, 5),
    workflowNodeCount: nodeCount,
    rootsPreview: roots.length ? roots.join(' · ') : '—',
    toolsTotal,
    toolsInstalled,
    proposalsCount: propCount,
    proposalLabels,
    lastExecutionLine,
    taskRunsTotalStored: taskRunSurf.taskRunsTotalStored,
    lastTaskRunSummaryLine: taskRunSurf.lastTaskRunSummaryLine,
    updatedAt: String(lo?.updated_at || '').slice(0, 19) || '—',
  };
}
