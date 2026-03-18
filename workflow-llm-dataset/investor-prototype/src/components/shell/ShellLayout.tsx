import type { MissionSurfaceState } from '../../mocks/missionMock';
import { CentralWorkspace } from './CentralWorkspace';
import { LeftRail } from './LeftRail';
import { RightMissionPanel } from './RightMissionPanel';

export function ShellLayout({ mission }: { mission: MissionSurfaceState }) {
  return (
    <>
      <LeftRail />
      <CentralWorkspace m={mission} />
      <RightMissionPanel m={mission} />
    </>
  );
}
