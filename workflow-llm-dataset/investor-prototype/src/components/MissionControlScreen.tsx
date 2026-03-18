import { useDemoFlow } from '../state/DemoFlowContext';
import { DesktopDock } from './layout/DesktopDock';
import { TopBar } from './layout/TopBar';
import { MultiWindowDesktop } from './mission/MultiWindowDesktop';
import { InvestorWalkthrough } from './shell/InvestorWalkthrough';
import { ShellLayout } from './shell/ShellLayout';

export function MissionControlScreen() {
  const { mission, layoutMode, desktopShell, demoViewModel } = useDemoFlow();
  const shellTop = demoViewModel?.degradedSummary ? '88px' : '48px';

  if (!mission) {
    return (
      <div style={{ padding: 80, textAlign: 'center', color: 'var(--text-muted)' }}>
        No role selected
      </div>
    );
  }

  return (
    <>
      <TopBar />
      <div
        key={layoutMode}
        className="mission-layout-root"
        style={{ ['--shell-top' as string]: shellTop }}
      >
        {layoutMode === 'single' ? (
          <div
            className={
              desktopShell.missionHome.rightPanelOpen
                ? 'shell-body'
                : 'shell-body shell-body--right-collapsed'
            }
          >
            <ShellLayout mission={mission} />
          </div>
        ) : (
          <MultiWindowDesktop m={mission} />
        )}
      </div>
      <InvestorWalkthrough />
      <DesktopDock />
    </>
  );
}
