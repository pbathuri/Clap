/**
 * Shape of `workflow-dataset demo edge-desktop-snapshot` JSON.
 * Kept loose for forward compatibility.
 */

export interface EdgeDesktopSnapshot {
  generated_at: string;
  repo_root: string;
  sources_ok: string[];
  errors: Record<string, string>;
  readiness: {
    capability_level?: string | { value?: string };
    degraded_mode?: string | { value?: string };
    degraded_explanation?: string;
    summary_lines?: string[];
  } | null;
  bootstrap_last?: { path?: string; record?: Record<string, unknown> } | null;
  onboarding_ready?: {
    ready_to_assist?: {
      ready?: boolean;
      chosen_role_label?: string;
      vertical_pack_id?: string;
      memory_bootstrap_summary?: string;
      inferred_project_context?: string;
      recurring_themes?: string[];
      likely_priorities?: string[];
      recommended_first_value_action?: string;
      confirmation_message?: string;
    };
    completion?: Record<string, unknown>;
  } | null;
  workspace_home?: {
    context?: {
      active_project_id?: string;
      active_project_title?: string;
      active_goal_text?: string;
      next_recommended_action?: string;
      next_recommended_detail?: string;
    };
    trust_health_summary?: string;
  } | null;
  workspace_home_text?: string | null;
  day_status?: {
    current_workday_state?: string;
    trust_posture?: string;
    preset_id?: string;
    next_recommended_transition?: string;
    next_recommended_reason?: string;
    pending_approvals_count?: number;
  } | null;
  day_status_text?: string | null;
  guidance_next_action?: {
    summary?: string;
    rationale?: string;
    action_ref?: string;
  } | null;
  operator_summary?: {
    what_system_knows?: string;
    what_it_recommends?: string;
    what_it_needs_from_user?: string;
    preset_id?: string;
  } | null;
  local_operator_summary?: {
    machine_readiness?: Record<string, unknown>;
    operator_readiness?: Record<string, unknown>;
    approved_folders?: { count?: number; items?: unknown[] };
    workflow_tree?: { node_count?: number; roots?: string[] };
    tool_registry?: Record<string, unknown>;
    action_proposals?: { count?: number; items?: unknown[] };
    updated_at?: string;
    last_execution?: {
      action_id?: string;
      success?: boolean;
      message?: string;
      adapter_id?: string;
      action_type?: string;
      outcome?: string;
      at?: string;
    } | null;
    /** Optional; mirrors Python operator summary when present */
    task_runs?: { total_stored?: number; recent?: unknown[] };
    last_task_run?: Record<string, unknown> | null;
  } | null;
  /** Shallow supervised task-run surface from edge snapshot builder (Python) */
  supervised_task_run?: {
    last_task_run?: Record<string, unknown> | null;
    recent?: unknown[];
    total_stored?: number;
  } | null;
  inbox?: Array<{
    item_id: string;
    kind: string;
    priority: string;
    summary: string;
  }>;
  /** M52 live adapter: per-field provenance (live | stale_cache | timeout | …) */
  adapter_meta?: {
    adapter_version?: string;
    presenter_mode_active?: boolean;
    presenter_fast_path?: boolean;
    field_status?: Record<string, string>;
    sources_ok_live?: string[];
    degraded_notes?: string[];
    prefetch_written_at?: string;
    global_budget_seconds?: number;
  };
}

export type EdgeDataSource = 'live' | 'cached' | 'mock' | 'static_file';

export interface EdgeDesktopLoadResult {
  snapshot: EdgeDesktopSnapshot | null;
  source: EdgeDataSource;
  error?: string;
  timedOut?: boolean;
}
