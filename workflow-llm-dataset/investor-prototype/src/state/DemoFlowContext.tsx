import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import {
  loadEdgeDesktopState,
  invalidateEdgeDesktopCache,
  peekEdgeDesktopCache,
  effectiveEdgeCacheTtlMs,
} from '../adapters/loadEdgeDesktopState';
import type { EdgeDataSource } from '../adapters/edgeDesktopTypes';
import type { EdgeDesktopSnapshot } from '../adapters/edgeDesktopTypes';
import {
  buildDesktopDemoViewModel,
  missionSurfaceOnly,
  type DesktopDemoViewModel,
} from '../viewModels/desktopDemoViewModel';
import {
  createInitialDesktopShell,
  type BootReadinessTier,
  type DesktopShellState,
  type RailSectionId,
} from '../shell/models';
import {
  shellAfterBootComplete,
  shellAfterRoleSelected,
  shellGoToBoot,
  shellGoToRoleSelect,
  shellSetBootReadinessTier,
  shellSetRail,
  shellToggleRightPanel,
} from '../shell/transitions';
import {
  advanceWalkthroughStep,
  parseInitialWalkthroughStep,
  walkthroughBack,
  type MissionWalkthroughStep,
} from '../demo/missionWalkthrough';
import {
  getMissionState,
  type RoleId,
  type MissionSurfaceState,
} from '../mocks/missionMock';

export type DemoPhase = 'boot' | 'role' | 'mission';
export type LayoutMode = 'single' | 'multi';

function edgeLiveEnabled(): boolean {
  if (typeof window === 'undefined') return false;
  if (new URLSearchParams(window.location.search).get('live') === '1')
    return true;
  return import.meta.env.VITE_EDGE_LIVE === '1';
}

function initialDesktopShell(
  initial: ReturnType<typeof parseInitialFromUrl>
): DesktopShellState {
  if (initial.resetDemo) return createInitialDesktopShell();
  const s = createInitialDesktopShell();
  if (initial.phase === 'mission') {
    s.phase = 'mission';
    s.boot.progress = 1;
  } else if (initial.phase === 'role') {
    s.phase = 'role_select';
    s.boot.progress = 1;
  }
  return s;
}

type DemoFlowContextValue = {
  phase: DemoPhase;
  roleId: RoleId | null;
  layoutMode: LayoutMode;
  desktopShell: DesktopShellState;
  activeMultiWindowId: string | null;
  setActiveMultiWindowId: (id: string | null) => void;
  goToPhase: (p: DemoPhase) => void;
  completeBoot: () => void;
  selectRole: (id: RoleId) => void;
  setLayoutMode: (m: LayoutMode) => void;
  setRailActive: (r: RailSectionId) => void;
  toggleRightMissionPanel: () => void;
  setBootReadinessTier: (t: BootReadinessTier) => void;
  /** Mission payload only (backward compatible) */
  mission: MissionSurfaceState | null;
  /** Full view model: provenance + degraded + adapter_meta */
  demoViewModel: DesktopDemoViewModel | null;
  missionWalkthroughStep: MissionWalkthroughStep;
  advanceMissionWalkthrough: () => void;
  backMissionWalkthrough: () => void;
  skipMissionWalkthrough: () => void;
  lastInteraction: string | null;
  acknowledgeInteraction: () => void;
  surfaceClick: (label: string) => void;
  edgeDataSource: EdgeDataSource | null;
  edgeLoading: boolean;
  /** True while refreshing live snapshot but UI already shows last-good data */
  edgeRevalidating: boolean;
  edgeLiveError?: string;
  refreshEdgeSnapshot: () => void;
  /** Cache clear + boot + walkthrough 0 — between rehearsals */
  resetDemoSession: () => void;
  inboxPulse: boolean;
  clearInboxPulse: () => void;
  edgeLiveActive: boolean;
};

const DemoFlowContext = createContext<DemoFlowContextValue | null>(null);

function parseInitialFromUrl(): {
  phase?: DemoPhase;
  role?: RoleId;
  skipBoot?: boolean;
  resetDemo?: boolean;
} {
  if (typeof window === 'undefined') return {};
  const q = new URLSearchParams(window.location.search);
  const phase = q.get('phase') as DemoPhase | null;
  const role = q.get('role') as RoleId | null;
  const skipBoot = q.get('skipBoot') === '1' || q.get('skipBoot') === 'true';
  const resetDemo = q.get('resetDemo') === '1';
  const validPhases: DemoPhase[] = ['boot', 'role', 'mission'];
  const validRoles: RoleId[] = [
    'founder_operator',
    'document_review',
    'analyst_followup',
  ];
  const envRole = (import.meta.env.VITE_DEMO_DEFAULT_ROLE as RoleId | undefined) ??
    undefined;
  return {
    phase: phase && validPhases.includes(phase) ? phase : undefined,
    role:
      (role && validRoles.includes(role) ? role : undefined) ||
      (envRole && validRoles.includes(envRole) ? envRole : undefined),
    skipBoot,
    resetDemo,
  };
}

export function DemoFlowProvider({ children }: { children: ReactNode }) {
  const initial = parseInitialFromUrl();
  const [phase, setPhase] = useState<DemoPhase>(() => {
    if (initial.resetDemo) return 'boot';
    if (initial.skipBoot && initial.phase === 'mission') return 'mission';
    if (initial.skipBoot && initial.phase === 'role') return 'role';
    if (initial.phase === 'mission') return 'mission';
    if (initial.phase === 'role') return 'role';
    return 'boot';
  });
  const [roleId, setRoleId] = useState<RoleId | null>(() => {
    if (initial.resetDemo) return null;
    if (initial.role) return initial.role;
    if (initial.phase === 'mission') return 'founder_operator';
    return null;
  });
  const [desktopShell, setDesktopShell] = useState<DesktopShellState>(() =>
    initialDesktopShell(initial)
  );
  const [activeMultiWindowId, setActiveMultiWindowId] = useState<string | null>(
    null
  );
  const [lastInteraction, setLastInteraction] = useState<string | null>(null);

  const [edgeSnapshot, setEdgeSnapshot] = useState<EdgeDesktopSnapshot | null>(
    null
  );
  const [edgeDataSource, setEdgeDataSource] = useState<EdgeDataSource | null>(
    null
  );
  const [edgeLoading, setEdgeLoading] = useState(false);
  const [edgeRevalidating, setEdgeRevalidating] = useState(false);
  const [edgeLiveError, setEdgeLiveError] = useState<string | undefined>();
  const [edgeTimedOut, setEdgeTimedOut] = useState(false);
  const [edgeRefreshToken, setEdgeRefreshToken] = useState(0);
  const edgeRefreshTokenRef = useRef(edgeRefreshToken);
  edgeRefreshTokenRef.current = edgeRefreshToken;
  const [inboxPulse, setInboxPulse] = useState(false);
  const inboxCountRef = useRef(0);

  const [missionWalkthroughStep, setMissionWalkthroughStep] =
    useState<MissionWalkthroughStep>(() => {
      if (typeof window === 'undefined') return 0;
      if (initial.resetDemo) return 0;
      return parseInitialWalkthroughStep(
        new URLSearchParams(window.location.search)
      );
    });

  const layoutMode: LayoutMode =
    desktopShell.missionHome.layoutMode === 'multi_window'
      ? 'multi'
      : 'single';

  const edgeLiveWarm =
    (phase === 'role' || phase === 'mission') && edgeLiveEnabled();
  const edgeLiveWarmRef = useRef(edgeLiveWarm);
  edgeLiveWarmRef.current = edgeLiveWarm;

  useEffect(() => {
    if (phase === 'boot') {
      setEdgeSnapshot(null);
      setEdgeDataSource(null);
      setEdgeLoading(false);
      setEdgeRevalidating(false);
      setEdgeTimedOut(false);
      setEdgeLiveError(undefined);
      setInboxPulse(false);
      return;
    }
    if (!edgeLiveEnabled()) {
      setEdgeSnapshot(null);
      setEdgeDataSource(null);
      setEdgeLoading(false);
      setEdgeRevalidating(false);
    }
  }, [phase]);

  useEffect(() => {
    if (!edgeLiveWarm) return;

    const ttl = effectiveEdgeCacheTtlMs();
    const peek = peekEdgeDesktopCache();
    const cacheFresh = peek && Date.now() - peek.at < ttl;

    if (peek) {
      setEdgeSnapshot(peek.data);
      setEdgeDataSource('cached');
      setEdgeLoading(false);
      setEdgeLiveError(undefined);
    } else {
      setEdgeLoading(true);
    }
    setEdgeRevalidating(!cacheFresh);

    const reqId = edgeRefreshToken;
    loadEdgeDesktopState({ cacheTtlMs: ttl }).then((r) => {
      if (!edgeLiveWarmRef.current) return;
      if (edgeRefreshTokenRef.current !== reqId) return;
      setEdgeRevalidating(false);
      setEdgeLoading(false);
      setEdgeDataSource(r.source);
      setEdgeLiveError(
        r.error && r.error !== 'aborted' ? r.error : undefined
      );
      setEdgeTimedOut(!!r.timedOut);
      if (r.snapshot) {
        setEdgeSnapshot(r.snapshot);
      } else if (!peek) {
        setEdgeSnapshot(null);
      }
    });
  }, [edgeLiveWarm, edgeRefreshToken]);

  const refreshEdgeSnapshot = useCallback(() => {
    invalidateEdgeDesktopCache();
    setEdgeRefreshToken((x) => x + 1);
  }, []);

  const clearInboxPulse = useCallback(() => {
    setInboxPulse(false);
  }, []);

  const resetDemoSession = useCallback(() => {
    invalidateEdgeDesktopCache();
    setEdgeRefreshToken((x) => x + 1);
    setDesktopShell((s) => shellGoToBoot(s));
    setPhase('boot');
    setRoleId(null);
    setMissionWalkthroughStep(0);
    setActiveMultiWindowId(null);
    setEdgeSnapshot(null);
    setEdgeDataSource(null);
    setEdgeLoading(false);
    setEdgeRevalidating(false);
    setEdgeLiveError(undefined);
    setEdgeTimedOut(false);
    setInboxPulse(false);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const q = new URLSearchParams(window.location.search);
    if (q.get('resetDemo') !== '1') return;
    invalidateEdgeDesktopCache();
    setEdgeRefreshToken((x) => x + 1);
    q.delete('resetDemo');
    const n = q.toString();
    const path = window.location.pathname;
    window.history.replaceState({}, '', n ? `${path}?${n}` : path);
  }, []);

  const completeBoot = useCallback(() => {
    setDesktopShell((s) => shellAfterBootComplete(s));
    setPhase('role');
  }, []);

  const selectRole = useCallback((id: RoleId) => {
    setRoleId(id);
    setDesktopShell((s) => shellAfterRoleSelected(s, id));
    setPhase('mission');
    setMissionWalkthroughStep(
      parseInitialWalkthroughStep(new URLSearchParams(window.location.search))
    );
  }, []);

  const goToPhase = useCallback((p: DemoPhase) => {
    if (p === 'boot') {
      setDesktopShell((s) => shellGoToBoot(s));
      setRoleId(null);
    } else if (p === 'role') {
      setDesktopShell((s) => shellGoToRoleSelect(s));
    }
    setPhase(p);
  }, []);

  const advanceMissionWalkthrough = useCallback(() => {
    setMissionWalkthroughStep((s) => advanceWalkthroughStep(s));
  }, []);

  const backMissionWalkthrough = useCallback(() => {
    setMissionWalkthroughStep((s) => walkthroughBack(s));
  }, []);

  const skipMissionWalkthrough = useCallback(() => {
    setMissionWalkthroughStep(4);
  }, []);

  const setLayoutMode = useCallback((m: LayoutMode) => {
    setDesktopShell((s) => ({
      ...s,
      missionHome: {
        ...s.missionHome,
        layoutMode: m === 'multi' ? 'multi_window' : 'single_workspace',
      },
    }));
  }, []);

  const setRailActive = useCallback((r: RailSectionId) => {
    setDesktopShell((s) => shellSetRail(s, r));
  }, []);

  const toggleRightMissionPanel = useCallback(() => {
    setDesktopShell((s) => shellToggleRightPanel(s));
  }, []);

  const setBootReadinessTier = useCallback((t: BootReadinessTier) => {
    setDesktopShell((s) => shellSetBootReadinessTier(s, t));
  }, []);

  const surfaceClick = useCallback((label: string) => {
    setLastInteraction(label);
  }, []);
  const acknowledgeInteraction = useCallback(() => {
    setLastInteraction(null);
  }, []);

  const demoViewModel = useMemo((): DesktopDemoViewModel | null => {
    if (!roleId || phase !== 'mission') return null;
    const mock = getMissionState(roleId);
    if (!edgeLiveEnabled()) {
      return buildDesktopDemoViewModel(null, roleId, mock, 'mock');
    }
    if (edgeLoading && !edgeSnapshot) {
      const base = buildDesktopDemoViewModel(null, roleId, mock, 'mock');
      return {
        ...base,
        degradedSummary: base.degradedSummary || 'Connecting to your workspace…',
      };
    }
    return buildDesktopDemoViewModel(
      edgeSnapshot,
      roleId,
      mock,
      edgeDataSource ?? 'mock',
      { timedOut: edgeTimedOut }
    );
  }, [
    roleId,
    phase,
    edgeSnapshot,
    edgeLoading,
    edgeDataSource,
    edgeTimedOut,
  ]);

  useEffect(() => {
    const count = demoViewModel?.inboxItems?.length ?? 0;
    if (count > inboxCountRef.current) {
      setInboxPulse(true);
    }
    inboxCountRef.current = count;
  }, [demoViewModel?.inboxItems?.length]);

  const mission = useMemo(() => {
    if (!demoViewModel) return null;
    return missionSurfaceOnly(demoViewModel);
  }, [demoViewModel]);

  const edgeLiveActive =
    phase === 'mission' && typeof window !== 'undefined' && edgeLiveEnabled();

  const value = useMemo(
    () => ({
      phase,
      roleId,
      layoutMode,
      desktopShell,
      activeMultiWindowId,
      setActiveMultiWindowId,
      goToPhase,
      completeBoot,
      selectRole,
      setLayoutMode,
      setRailActive,
      toggleRightMissionPanel,
      setBootReadinessTier,
      mission,
      demoViewModel,
      missionWalkthroughStep,
      advanceMissionWalkthrough,
      backMissionWalkthrough,
      skipMissionWalkthrough,
      lastInteraction,
      acknowledgeInteraction,
      surfaceClick,
      edgeDataSource,
      edgeLoading,
      edgeRevalidating,
      edgeLiveError,
      refreshEdgeSnapshot,
      resetDemoSession,
      inboxPulse,
      clearInboxPulse,
      edgeLiveActive,
    }),
    [
      phase,
      roleId,
      layoutMode,
      desktopShell,
      activeMultiWindowId,
      goToPhase,
      completeBoot,
      selectRole,
      setLayoutMode,
      setRailActive,
      toggleRightMissionPanel,
      setBootReadinessTier,
      mission,
      demoViewModel,
      missionWalkthroughStep,
      advanceMissionWalkthrough,
      backMissionWalkthrough,
      skipMissionWalkthrough,
      lastInteraction,
      acknowledgeInteraction,
      surfaceClick,
      edgeDataSource,
      edgeLoading,
      edgeRevalidating,
      edgeLiveError,
      refreshEdgeSnapshot,
      resetDemoSession,
      inboxPulse,
      clearInboxPulse,
      edgeLiveActive,
    ]
  );

  return (
    <DemoFlowContext.Provider value={value}>
      {children}
    </DemoFlowContext.Provider>
  );
}

export function useDemoFlow() {
  const ctx = useContext(DemoFlowContext);
  if (!ctx) throw new Error('useDemoFlow outside DemoFlowProvider');
  return ctx;
}
