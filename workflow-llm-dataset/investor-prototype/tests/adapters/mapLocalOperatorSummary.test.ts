import { describe, expect, it } from 'vitest';
import { mapLocalOperatorSummary } from '../../src/adapters/mapLocalOperatorSummary';

describe('mapLocalOperatorSummary', () => {
  it('returns undefined when snapshot has no local operator signal', () => {
    expect(
      mapLocalOperatorSummary({
        sources_ok: ['readiness'],
        errors: {},
      })
    ).toBeUndefined();
  });

  it('maps full local_operator_summary', () => {
    const lo = mapLocalOperatorSummary({
      sources_ok: ['local_operator_summary'],
      errors: {},
      local_operator_summary: {
        machine_readiness: { summary: 'platform=Darwin; active_approved_folders=1' },
        operator_readiness: {
          summary: 'nodes=3 tools=2 proposals=4',
          next_steps: ['run propose-actions'],
        },
        approved_folders: {
          count: 1,
          items: [{ path: '/tmp/ws', revocation_state: 'active' }],
        },
        workflow_tree: { node_count: 3, roots: ['wf_root1'] },
        tool_registry: { total: 5, installed: 2 },
        action_proposals: {
          count: 2,
          items: [{ label: 'Open in Finder' }, { label: 'Inspect path' }],
        },
        last_execution: {
          success: true,
          action_id: 'act_finder',
          at: '2025-01-01T12:00:00+00:00',
        },
        updated_at: '2025-01-01T11:00:00',
      },
    });
    expect(lo).toBeDefined();
    expect(lo!.visible).toBe(true);
    expect(lo!.headline).toContain('Darwin');
    expect(lo!.approvedFoldersCount).toBe(1);
    expect(lo!.approvedFolderPaths).toContain('/tmp/ws');
    expect(lo!.workflowNodeCount).toBe(3);
    expect(lo!.toolsTotal).toBe(5);
    expect(lo!.proposalsCount).toBe(2);
    expect(lo!.proposalLabels).toContain('Open in Finder');
    expect(lo!.lastExecutionLine).toMatch(/OK/);
    expect(lo!.taskRunsTotalStored).toBe(0);
    expect(lo!.lastTaskRunSummaryLine).toBeNull();
  });

  it('maps supervised_task_run into task run surface fields', () => {
    const lo = mapLocalOperatorSummary({
      sources_ok: ['local_operator_summary'],
      errors: {},
      local_operator_summary: {
        machine_readiness: { summary: 'ok' },
        operator_readiness: { summary: 'ok' },
        approved_folders: { count: 0, items: [] },
        workflow_tree: { node_count: 0, roots: [] },
        tool_registry: { total: 0, installed: 0 },
        action_proposals: { count: 0, items: [] },
      },
      supervised_task_run: {
        total_stored: 3,
        recent: [],
        last_task_run: {
          run_id: 'run_abcdefghijklmnop',
          status: 'completed',
          workflow_pattern: 'inspect_status_report',
        },
      },
    });
    expect(lo!.taskRunsTotalStored).toBe(3);
    expect(lo!.lastTaskRunSummaryLine).toMatch(/completed/);
    expect(lo!.lastTaskRunSummaryLine).toMatch(/inspect_status_report/);
  });

  it('graceful fallback when live source but payload empty', () => {
    const lo = mapLocalOperatorSummary({
      sources_ok: ['local_operator_summary'],
      errors: {},
      local_operator_summary: null,
    });
    expect(lo?.visible).toBe(true);
    expect(lo?.approvedFoldersCount).toBe(0);
    expect(lo?.taskRunsTotalStored).toBe(0);
  });

  it('returns undefined on fetcher error', () => {
    expect(
      mapLocalOperatorSummary({
        sources_ok: [],
        errors: { local_operator_summary: 'timeout' },
        local_operator_summary: null,
      })
    ).toBeUndefined();
  });
});
