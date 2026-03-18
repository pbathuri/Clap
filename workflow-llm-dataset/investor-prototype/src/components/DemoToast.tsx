import { useEffect } from 'react';
import { useDemoFlow } from '../state/DemoFlowContext';

export function DemoToast() {
  const { lastInteraction, acknowledgeInteraction } = useDemoFlow();

  useEffect(() => {
    if (!lastInteraction) return;
    const t = window.setTimeout(acknowledgeInteraction, 2400);
    return () => window.clearTimeout(t);
  }, [lastInteraction, acknowledgeInteraction]);

  if (!lastInteraction) return null;

  return (
    <div className="demo-toast" role="status">
      <span style={{ color: 'var(--text-muted)', fontSize: 11, display: 'block' }}>
        Demo tap
      </span>
      {lastInteraction}
    </div>
  );
}
