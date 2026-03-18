# M49A–M49D Before-Coding Analysis — Portable State Model + Continuity Bundle

## 1. What stateful subsystems already exist

- **state_durability/boundaries.py:** SUBSYSTEM_BOUNDARIES lists workday, continuity_shutdown, continuity_carry_forward, continuity_next_session, project_current, background_queue, workday_preset with paths under data/local. collect_all_boundaries(), collect_stale_markers(), collect_corrupt_notes().
- **migration_restore/bundle.py:** ContinuityBundleManifest (bundle_id, created_at_utc, product_version, subsystem_ids, paths_in_bundle, source_repo_root, local_only_excluded). get_bundle_manifest("latest" | bundle_id), _build_latest_manifest() from SUBSYSTEM_BOUNDARIES, list_bundle_refs(). LOCAL_ONLY_SUBSYSTEMS = ["background_queue"]. Bundles dir: data/local/migration_restore/bundles.
- **migration_restore:** validate_bundle_for_target, dry_run_restore, restore_with_review, conflict_aware_reconcile, post_restore_verify, reconcile policies, restore playbooks, operator guidance.
- **continuity_engine/store.py:** data/local/continuity_engine (last_session, last_shutdown, carry_forward, next_session, rhythm templates).
- **mission_control/state.py:** local_sources keys for many subsystems (eval, devlab, incubator, approval_registry, event_log, live_context, memory_curation, memory_intelligence, memory_os, repair_loops, job_packs, copilot, context, action_cards, automations, background_run, automation_inbox, sensitive_gates, workflow_episodes, personal_graph, workday, trust_contracts, operator_mode, governed_operator, continuity_engine, state_durability, governance, vertical_packs, production_cut, etc.).
- **Persistence:** Each subsystem typically writes under data/local/<subsystem>/ (e.g. trust, governance, vertical_packs, production_cut, operator_mode, workday, project_case, session, queue, outcomes, progress). No single “portable state” registry beyond migration_restore manifest and state_durability boundaries.

## 2. What is portable vs non-portable today

- **Portable (in manifest today):** workday, continuity_* (shutdown, carry_forward, next_session), project_current, workday_preset. Paths are listed in manifest; restore flows copy/reconcile.
- **Non-portable / local-only (excluded today):** background_queue (LOCAL_ONLY_SUBSYSTEMS). Machine-specific queue not transferred.
- **Not yet classified:** Many subsystems in mission_control local_sources are not in SUBSYSTEM_BOUNDARIES (e.g. memory_curation, memory_intelligence, operator_mode, governance, vertical_packs, production_cut, trust, approvals, automations, session, outcomes). So “portable vs non-portable” is only partially defined; no explicit “transfer with review”, “sensitive”, “rebuild on restore”, or “experimental” yet.

## 3. What is missing for a real continuity-bundle layer

- **Explicit portable state model:** PortableStateClass, NonPortableStateClass, BundleComponent with transfer_class (safe_to_transfer | transfer_with_review | local_only | rebuild_on_restore | experimental), sensitive/review_required/optional flags, provenance/version metadata.
- **Broader component set:** Register components for personal memory index, project/session continuity, queue/day shell, operator_mode config, trust contracts, production_cut defaults, governance preset, vertical_packs progress, and optionally benchmarks/learning-lab refs where safe; each with a transfer class.
- **Bundle creation with selective include/exclude:** Create bundle from current state with explicit include/exclude by component or transfer class; persist to a continuity-bundle directory with manifest and optional payload copy.
- **Bundle inspection and validation:** Human-readable inspect (manifest + component list + transfer classes); validate (version, runtime, and optional conflict check).
- **Portability boundaries document:** Operator-facing report of which components are safe to transfer, which require review, which are local-only, which are rebuild-on-restore, which are experimental.
- **Explain component:** explain(component_id) → transfer class, why, sensitive/review/optional, and what happens on restore.
- **Mission control slice:** Latest continuity bundle ref, transfer-sensitive components count, excluded local-only list, next recommended portability review.
- **CLI group:** continuity-bundle create, inspect, validate, components, explain (without replacing existing migration_restore CLI).

## 4. Exact file plan

- **New package:** src/workflow_dataset/continuity_bundle/ (extends use of migration_restore and state_durability; does not replace them).
- **continuity_bundle/models.py:** PortableStateClass, NonPortableStateClass, BundleComponent (component_id, path, transfer_class, sensitive, review_required, optional, provenance), ContinuityBundle (manifest + components list), BundleProvenance.
- **continuity_bundle/components.py:** Component registry: list of components with id, path_pattern, transfer_class, sensitive, review_required, optional; include personal memory, continuity_engine, project/session, workday, queue/day, operator_mode, trust, governance, production_cut defaults, vertical_packs, etc. get_component(component_id), list_components(include_local_only=False), classify_component(component_id).
- **continuity_bundle/build.py:** create_bundle(repo_root, include_components=None, exclude_components=None, include_transfer_classes=None) → ContinuityBundle; write to data/local/continuity_bundle/bundles/<bundle_id>/ (manifest.json + optional payload dir). inspect_bundle(bundle_ref, repo_root). validate_bundle(bundle_ref, repo_root, target_profile=None).
- **continuity_bundle/portability.py:** get_portability_boundaries(repo_root) → report dict (safe_to_transfer, transfer_with_review, local_only, rebuild_on_restore, experimental). explain_component(component_id, repo_root) → human-readable explanation.
- **continuity_bundle/mission_control.py:** continuity_bundle_slice(repo_root) → latest_bundle_ref, transfer_sensitive_components, excluded_local_only, next_portability_review.
- **continuity_bundle/__init__.py:** Exports.
- **cli.py:** New group continuity-bundle with commands: create, inspect, validate, components, explain.
- **mission_control/state.py:** Add continuity_bundle_state from slice (additive).
- **mission_control/report.py:** Add "[Continuity bundle]" section (additive).
- **tests/test_continuity_bundle.py:** Tests for bundle creation, component classification, include/exclude, sensitive handling, invalid/version mismatch, no portable state.
- **docs/M49A_M49D_CONTINUITY_BUNDLE_DELIVERABLE.md:** File list, CLI, sample bundle, sample classification report, sample explain, tests, gaps.

## 5. Safety/risk note

- **Local-first, no cloud:** All bundle data stays under data/local; no automatic upload or sync. Export is explicit (create); import is explicit (existing migration_restore restore flows).
- **Sensitive and review-required explicit:** Components marked sensitive or review_required are listed in manifest and in components report so operator can review before transfer. No silent inclusion of local-only or machine-specific state in “portable” bundle by default.
- **No replacement of persistence:** We do not change how workday, continuity_engine, trust, etc. persist; we only add a classification and bundle-build layer on top. Restore still uses migration_restore flows where applicable.
- **Version and conflict:** Validate step can flag version mismatch or target conflict; restore remains human-approved.

## 6. Portability principles

- **Explicit over implicit:** Every component has a declared transfer_class and visibility (sensitive, review_required, optional).
- **Inspectable:** Manifest and component list are human-readable; explain gives rationale.
- **Safe defaults:** Local-only and machine-specific are excluded unless explicitly opted in; sensitive and review-required are clearly marked.
- **Migration-safe:** Bundle format and provenance support migration-safe continuity (same product version or compatible); no opaque binary blobs.

## 7. What this block will NOT do

- **No cloud sync or background replication:** No automatic sync to cloud or other machines.
- **No account-based SaaS identity:** No login or tenant id in the bundle.
- **No replacing current persistence:** state_durability, continuity_engine, migration_restore, and subsystem stores remain as-is.
- **No hiding transfer boundaries:** Local-only and non-portable are explicitly listed and excluded by default.
- **No unsafe copying:** Sensitive or review-required components are marked and included only with clear semantics (e.g. include in bundle but require review on restore).
