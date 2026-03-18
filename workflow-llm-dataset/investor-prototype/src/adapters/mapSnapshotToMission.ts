import type { RoleId } from '../mocks/missionMock';
import type { MissionSurfaceState } from '../mocks/missionMock';
import type { EdgeDesktopSnapshot } from './edgeDesktopTypes';
import {
  buildDesktopDemoViewModel,
  missionSurfaceOnly,
} from '../viewModels/desktopDemoViewModel';

/**
 * @deprecated Prefer buildDesktopDemoViewModel + missionSurfaceOnly for full provenance.
 * Kept for CLI/tests that expect mission-only merge.
 */
export function mapSnapshotToMission(
  snap: EdgeDesktopSnapshot | null,
  roleId: RoleId,
  mock: MissionSurfaceState
): MissionSurfaceState {
  if (!snap) return { ...mock };
  const vm = buildDesktopDemoViewModel(snap, roleId, mock, 'live');
  return missionSurfaceOnly(vm);
}

export { buildDesktopDemoViewModel, missionSurfaceOnly } from '../viewModels/desktopDemoViewModel';
