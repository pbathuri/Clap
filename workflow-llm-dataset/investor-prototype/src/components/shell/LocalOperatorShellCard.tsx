import type { LocalOperatorSurface } from '../../adapters/mapLocalOperatorSummary';
import { GlassSurface } from '../mission/GlassSurface';

export function LocalOperatorShellCard({
  lo,
  compact,
}: {
  lo: LocalOperatorSurface;
  compact?: boolean;
}) {
  if (!lo.visible) return null;

  return (
    <GlassSurface
      label={compact ? 'Local operator' : 'Work · Local operator'}
      style={{ padding: compact ? 14 : 20 }}
    >
      <div className="label-caps" style={{ marginBottom: 8 }}>
        Laptop scope
      </div>
      <div style={{ fontWeight: 600, fontSize: compact ? 12 : 14, lineHeight: 1.4 }}>
        {lo.headline}
      </div>
      <div
        style={{
          marginTop: 8,
          fontSize: compact ? 11 : 12,
          color: 'var(--text-secondary)',
          lineHeight: 1.45,
        }}
      >
        {lo.subline}
      </div>
      {!compact && (
        <div
          style={{
            marginTop: 14,
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 10,
            fontSize: 12,
          }}
        >
          <div>
            <div className="label-caps" style={{ marginBottom: 4 }}>
              Approved folders
            </div>
            <div style={{ fontWeight: 600 }}>{lo.approvedFoldersCount}</div>
            {lo.approvedFolderPaths.length > 0 && (
              <ul
                style={{
                  margin: '6px 0 0',
                  paddingLeft: 16,
                  color: 'var(--text-muted)',
                  fontSize: 11,
                }}
              >
                {lo.approvedFolderPaths.map((p) => (
                  <li key={p} style={{ wordBreak: 'break-all' }}>
                    {p}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <div className="label-caps" style={{ marginBottom: 4 }}>
              Workflow
            </div>
            <div style={{ fontWeight: 600 }}>{lo.workflowNodeCount} nodes</div>
            <div
              style={{
                marginTop: 6,
                fontSize: 11,
                color: 'var(--text-muted)',
                wordBreak: 'break-all',
              }}
            >
              {lo.rootsPreview}
            </div>
          </div>
          <div>
            <div className="label-caps" style={{ marginBottom: 4 }}>
              Tools
            </div>
            <div style={{ fontWeight: 600 }}>
              {lo.toolsTotal} total · {lo.toolsInstalled} installed
            </div>
          </div>
          <div>
            <div className="label-caps" style={{ marginBottom: 4 }}>
              Proposals
            </div>
            <div style={{ fontWeight: 600 }}>{lo.proposalsCount}</div>
            {lo.proposalLabels.length > 0 && (
              <ul
                style={{
                  margin: '6px 0 0',
                  paddingLeft: 16,
                  color: 'var(--text-muted)',
                  fontSize: 11,
                }}
              >
                {lo.proposalLabels.map((t, i) => (
                  <li key={`${i}-${t.slice(0, 20)}`}>{t}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
      {compact && (
        <div
          style={{
            marginTop: 10,
            fontSize: 11,
            color: 'var(--text-muted)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px 12px',
          }}
        >
          <span>Folders {lo.approvedFoldersCount}</span>
          <span>Nodes {lo.workflowNodeCount}</span>
          <span>Tools {lo.toolsTotal}</span>
          <span>Actions {lo.proposalsCount}</span>
          {lo.taskRunsTotalStored > 0 ? (
            <span>Task runs {lo.taskRunsTotalStored}</span>
          ) : null}
        </div>
      )}
      <div
        style={{
          marginTop: compact ? 8 : 12,
          paddingTop: compact ? 8 : 10,
          borderTop: '1px solid rgba(126, 184, 218, 0.12)',
          fontSize: 11,
          color: 'var(--text-muted)',
        }}
      >
        {lo.taskRunsTotalStored > 0 || lo.lastTaskRunSummaryLine ? (
          <div style={{ marginBottom: 6 }}>
            Task runs · {lo.taskRunsTotalStored} stored
            {lo.lastTaskRunSummaryLine ? ` · ${lo.lastTaskRunSummaryLine}` : ''}
          </div>
        ) : null}
        {lo.lastExecutionLine ? (
          <span>Last action · {lo.lastExecutionLine}</span>
        ) : (
          <span>No supervised action execution recorded yet</span>
        )}
        <span style={{ marginLeft: 10 }}>Updated {lo.updatedAt}</span>
      </div>
    </GlassSurface>
  );
}
