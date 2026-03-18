import type { CSSProperties, ReactNode } from 'react';
import { useDemoFlow } from '../../state/DemoFlowContext';

export function GlassSurface({
  label,
  children,
  className = '',
  style,
}: {
  label: string;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}) {
  const { surfaceClick } = useDemoFlow();
  return (
    <div
      role="button"
      tabIndex={0}
      className={`glass-panel glass-panel--interactive ${className}`.trim()}
      style={{ padding: 20, ...style }}
      onClick={() => surfaceClick(label)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          surfaceClick(label);
        }
      }}
    >
      {children}
    </div>
  );
}
