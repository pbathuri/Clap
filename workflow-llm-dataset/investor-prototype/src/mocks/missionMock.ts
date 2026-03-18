/**
 * Deterministic demo payloads per role. Replace with API/graph adapters later.
 */

export type RoleId = 'founder_operator' | 'document_review' | 'analyst_followup';

export interface TimelineEntry {
  id: string;
  label: string;
  time: string;
  tone: 'neutral' | 'highlight';
}

export interface InboxRow {
  item_id: string;
  kind: string;
  priority: string;
  summary: string;
}

export interface MissionSurfaceState {
  roleLabel: string;
  verticalPack: string;
  memoryBootstrap: string;
  memoryDetail: string;
  currentContext: string;
  nextBestAction: string;
  trustPosture: string;
  trustDetail: string;
  firstValueTitle: string;
  firstValueBody: string;
  readinessLabel: string;
  assistState: string;
  timeline: TimelineEntry[];
  /** Live adapter: intervention inbox */
  inboxItems?: InboxRow[];
  workspaceHomePreview?: string;
  dayStatusPreview?: string;
  operatorSummaryPreview?: {
    knows: string;
    recommends: string;
    needs: string;
  };
  liveGeneratedAt?: string;
  /** From onboarding ready-state recurring_themes */
  keyThemes?: string[];
  /** From onboarding ready-state likely_priorities */
  keyPriorities?: string[];
}

export const ROLE_OPTIONS: {
  id: RoleId;
  title: string;
  subtitle: string;
  icon: string;
  packId: string;
  trustLine: string;
  initLine: string;
}[] = [
  {
    id: 'founder_operator',
    title: 'Founder / Operator',
    subtitle: 'Dispatch, decisions, cross-workflow view',
    icon: '◆',
    packId: 'Operations · logistics prior',
    trustLine: 'Supervised · approvals on send & moves',
    initLine: 'Bounded org graph, workflows, exception patterns',
  },
  {
    id: 'document_review',
    title: 'Document Review',
    subtitle: 'Contracts, policies, redlines',
    icon: '◇',
    packId: 'Legal-ops · clause library',
    trustLine: 'No external send without approval',
    initLine: 'Session-scoped redlines & firm playbooks',
  },
  {
    id: 'analyst_followup',
    title: 'Analyst Follow-up',
    subtitle: 'Research threads, data pulls, briefs',
    icon: '○',
    packId: 'Research stack · prior briefs',
    trustLine: 'Pulls & exports gated until you confirm',
    initLine: 'Thread memory, citation style, open questions',
  },
];

const MISSION_BY_ROLE: Record<RoleId, MissionSurfaceState> = {
  founder_operator: {
    roleLabel: 'Founder / Operator',
    verticalPack: 'Operations prior · logistics graph',
    memoryBootstrap: 'Bounded personal graph — 12 active nodes',
    memoryDetail:
      'Org map, recurring workflows, approval boundaries loaded. No raw corpus on glass.',
    currentContext: 'Board prep week · three open operational exceptions',
    nextBestAction: 'Generate exception digest across dispatch, inventory, and vendor workflows',
    trustPosture: 'Supervised assistance',
    trustDetail:
      'Outbound messages and file moves require explicit approval. Simulated execution default.',
    firstValueTitle: 'First value · Exception digest',
    firstValueBody:
      'Three items surfaced with owner hints and suggested next touch — ready for your edit before any send.',
    readinessLabel: 'Device ready · full stack',
    assistState: 'Ready to assist',
    timeline: [
      { id: '1', label: 'USB secure boot verified', time: 'T−0:42', tone: 'neutral' },
      { id: '2', label: 'Role & vertical pack applied', time: 'T−0:38', tone: 'highlight' },
      { id: '3', label: 'Memory bootstrap (bounded)', time: 'T−0:35', tone: 'neutral' },
      { id: '4', label: 'Context window primed', time: 'T−0:31', tone: 'neutral' },
      { id: '5', label: 'Assist posture: supervised', time: 'T−0:28', tone: 'highlight' },
    ],
    keyThemes: ['Operational exceptions', 'Dispatch rhythm', 'Inventory signals'],
    keyPriorities: ['Board-ready digest', 'Owner clarity on three open items'],
  },
  document_review: {
    roleLabel: 'Document Review',
    verticalPack: 'Legal-ops pack · clause library',
    memoryBootstrap: 'Session-scoped memory · 8 clause patterns',
    memoryDetail:
      'Prior redlines and firm playbooks referenced locally. Full doc text stays in your vault.',
    currentContext: 'MSA renewal · liability & SLA sections in focus',
    nextBestAction: 'Propose aligned redlines against your standard positions',
    trustPosture: 'Supervised assistance',
    trustDetail: 'No external send without approval. Diff preview only until you confirm.',
    firstValueTitle: 'First value · Redline sketch',
    firstValueBody:
      'Two high-risk clauses flagged with suggested language and rationale — review before apply.',
    readinessLabel: 'Device ready · full stack',
    assistState: 'Ready to assist',
    timeline: [
      { id: '1', label: 'USB secure boot verified', time: 'T−0:40', tone: 'neutral' },
      { id: '2', label: 'Document review role loaded', time: 'T−0:36', tone: 'highlight' },
      { id: '3', label: 'Clause memory (bounded)', time: 'T−0:33', tone: 'neutral' },
      { id: '4', label: 'Active doc context bound', time: 'T−0:29', tone: 'neutral' },
      { id: '5', label: 'Supervised edit posture', time: 'T−0:26', tone: 'highlight' },
    ],
    keyThemes: ['Liability', 'SLA', 'Renewal cycle'],
    keyPriorities: ['Standard positions', 'Risk language alignment'],
  },
  analyst_followup: {
    roleLabel: 'Analyst Follow-up',
    verticalPack: 'Research stack · prior briefs',
    memoryBootstrap: 'Thread memory · 6 open questions tracked',
    memoryDetail:
      'Citation style and source tiers remembered. No auto-fetch without your scope.',
    currentContext: 'Competitor pricing move · follow-up from last brief',
    nextBestAction: 'Structure follow-up memo with gaps and source plan',
    trustPosture: 'Supervised assistance',
    trustDetail: 'Web pulls and exports gated. Draft stays local until approved.',
    firstValueTitle: 'First value · Memo outline',
    firstValueBody:
      'Section outline with three evidence gaps and proposed sources — expand or redirect in one tap.',
    readinessLabel: 'Device ready · full stack',
    assistState: 'Ready to assist',
    timeline: [
      { id: '1', label: 'USB secure boot verified', time: 'T−0:39', tone: 'neutral' },
      { id: '2', label: 'Analyst role & brief priors', time: 'T−0:35', tone: 'highlight' },
      { id: '3', label: 'Question graph (bounded)', time: 'T−0:32', tone: 'neutral' },
      { id: '4', label: 'Thread context resumed', time: 'T−0:28', tone: 'neutral' },
      { id: '5', label: 'Supervised research posture', time: 'T−0:25', tone: 'highlight' },
    ],
    keyThemes: ['Competitive intel', 'Source quality', 'Brief continuity'],
    keyPriorities: ['Evidence gaps', 'Credible source plan'],
  },
};

export function getMissionState(roleId: RoleId): MissionSurfaceState {
  return MISSION_BY_ROLE[roleId];
}
