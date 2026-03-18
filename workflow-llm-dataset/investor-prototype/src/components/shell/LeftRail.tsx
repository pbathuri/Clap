import type { RailSectionId } from '../../shell/models';
import { useEffect } from 'react';
import { useDemoFlow } from '../../state/DemoFlowContext';

const ITEMS: { id: RailSectionId; label: string; glyph: string }[] = [
  { id: 'home', label: 'Home', glyph: '⌂' },
  { id: 'work', label: 'Work', glyph: '◎' },
  { id: 'guidance', label: 'Guidance', glyph: '→' },
  { id: 'inbox', label: 'Inbox', glyph: '◫' },
];

export function LeftRail() {
  const {
    desktopShell,
    setRailActive,
    surfaceClick,
    inboxPulse,
    clearInboxPulse,
  } = useDemoFlow();
  const active = desktopShell.missionHome.railActive;

  useEffect(() => {
    if (active === 'inbox' && inboxPulse) clearInboxPulse();
  }, [active, inboxPulse, clearInboxPulse]);

  return (
    <nav
      className="shell-rail"
      aria-label="Workspace sections"
    >
      {ITEMS.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`shell-rail__btn ${active === item.id ? 'shell-rail__btn--active' : ''}`}
          title={item.label}
          aria-current={active === item.id ? 'page' : undefined}
          onClick={() => {
            surfaceClick(`Rail · ${item.label}`);
            setRailActive(item.id);
            if (item.id === 'inbox') clearInboxPulse();
          }}
        >
          <span className="shell-rail__glyph" aria-hidden>
            {item.glyph}
          </span>
          <span className="shell-rail__label">{item.label}</span>
          {item.id === 'inbox' && (
            <span
              className={`live-badge ${inboxPulse ? 'live-badge--on' : ''}`}
              aria-hidden
            />
          )}
        </button>
      ))}
    </nav>
  );
}
