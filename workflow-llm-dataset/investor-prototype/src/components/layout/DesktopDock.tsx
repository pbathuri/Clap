import { useEffect, useState } from 'react';
import { useDemoFlow } from '../../state/DemoFlowContext';

const DOCK_ITEMS = [
  { id: 'home', emoji: '⌂', label: 'Mission home' },
  { id: 'context', emoji: '◎', label: 'Context' },
  { id: 'next', emoji: '→', label: 'Next action' },
  { id: 'inbox', emoji: '◫', label: 'Inbox' },
  { id: 'trust', emoji: '✓', label: 'Trust' },
  { id: 'artifact', emoji: '◧', label: 'Artifact' },
] as const;

export function DesktopDock() {
  const {
    surfaceClick,
    layoutMode,
    setLayoutMode,
    setRailActive,
    inboxPulse,
    clearInboxPulse,
  } = useDemoFlow();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <nav
      className={`dock ${ready ? 'dock--ready' : ''}`}
      aria-label="Quick surfaces"
    >
      {DOCK_ITEMS.map((item) => (
        <button
          key={item.id}
          type="button"
          className="dock__item"
          title={item.label}
          aria-label={item.label}
          onClick={() => {
            surfaceClick(`Dock · ${item.label}`);
            if (item.id === 'home') setRailActive('home');
            if (item.id === 'context') setRailActive('work');
            if (item.id === 'next') setRailActive('guidance');
            if (item.id === 'inbox') {
              setRailActive('inbox');
              clearInboxPulse();
            }
            if (item.id === 'trust' || item.id === 'artifact')
              setRailActive('home');
          }}
        >
          {item.emoji}
          {item.id === 'inbox' && (
            <span
              className={`live-badge ${inboxPulse ? 'live-badge--on' : ''}`}
              aria-hidden
            />
          )}
        </button>
      ))}
      <button
        type="button"
        className={`dock__item dock__item--layout ${
          layoutMode === 'multi' ? 'dock__item--layout-multi' : ''
        }`}
        title={
          layoutMode === 'single'
            ? 'Switch to multi-window'
            : 'Single workspace'
        }
        aria-pressed={layoutMode === 'multi'}
        onClick={() => {
          const next = layoutMode === 'single' ? 'multi' : 'single';
          surfaceClick(
            next === 'multi'
              ? 'Dock · Multi-window mode'
              : 'Dock · Single workspace'
          );
          setLayoutMode(next);
        }}
      >
        {layoutMode === 'single' ? '▢' : '▣'}
      </button>
    </nav>
  );
}
