import { DemoFlowProvider, useDemoFlow } from './state/DemoFlowContext';
import { BootScreen } from './components/BootScreen';
import { DemoToast } from './components/DemoToast';
import { MissionControlScreen } from './components/MissionControlScreen';
import { PresenterDemoOverlay } from './components/shell/PresenterDemoOverlay';
import { RoleScreen } from './components/RoleScreen';
import { AmbientCanvas } from './ambient/AmbientCanvas';

function DemoRouter() {
  const { phase } = useDemoFlow();

  return (
    <>
      {phase === 'boot' && <BootScreen />}
      {phase === 'role' && <RoleScreen />}
      {phase === 'mission' && <MissionControlScreen />}
      <DemoToast />
      <PresenterDemoOverlay />
    </>
  );
}

function AmbientLayer() {
  const { phase } = useDemoFlow();
  return <AmbientCanvas phase={phase} />;
}

export default function App() {
  return (
    <div className="app-shell">
      <DemoFlowProvider>
        <AmbientLayer />
        <div className="app-shell__content">
          <DemoRouter />
        </div>
      </DemoFlowProvider>
    </div>
  );
}
