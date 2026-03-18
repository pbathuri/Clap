# M49I–M49L Device-Aware Runtime Profiles + Continuity Confidence — Before Coding

## 1. What device/runtime readiness concepts already exist

- **continuity_confidence package (M49)**  
  - **Models**: TargetDeviceProfile, PostRestoreRuntimeProfile, ContinuityConfidenceScore, ContinuityConfidenceClass (high_confidence, usable_degraded, review_required, narrowed_production_cut, operator_mode_not_trusted, blocked, unknown), DowngradedCapabilityNote, PromotedCapabilityNote, ModelRouteAdjustment, OperatorModeSafetyAdjustment, RecommendedOperatingPosture, DeviceCapabilityClass (stronger, same, weaker, different, unknown).  
  - **device_profile.py**: build_target_device_profile (from edge tier, runtime, backends, version), compare_source_target (source vs target → capability_class).  
  - **confidence.py**: build_continuity_confidence (bundle_ref) → score, downgraded, promoted, recommended_posture; uses migration_restore.validation.validate_bundle_for_target.  
  - **adaptation.py**: build_post_restore_runtime_profile (routing policy, production_cut_narrowed, operator_mode_ready), get_downgraded_runtime_explanation.  
  - **report.py**: continuity_confidence_report (full report dict).  
  - **mission_control.py**: continuity_confidence_slice (current confidence, downgraded warnings, next review, operator_mode_readiness).  

- **migration_restore**  
  - ContinuityBundleManifest, TargetEnvironmentProfile, RestoreValidationReport, RestoreBlocker, RestoreConfidence; validate_bundle_for_target; get_bundle_manifest (latest or bundle_id).  

- **edge**  
  - build_edge_profile (tier: dev_full, local_standard, constrained_edge, minimal_eval), runtime_requirements, supported workflows.  

- **runtime_mesh**  
  - BackendProfile, load_backend_registry, get_backend_status (available/configured/missing).  

- **production_cut, deploy_bundle, long_run_health**  
  - Referenced in codebase; production_cut scope and deploy-bundle health exist.  

---

## 2. What is missing for device-aware post-restore operation

- **CLI**: No `workflow-dataset continuity-confidence` commands (status, report, device-profile, explain).  
- **Mission control**: continuity_confidence_slice exists but is **not** wired into mission_control/state.py or report.py; no dashboard visibility.  
- **Confidence logic**: capability_class from compare_source_target is not used in build_continuity_confidence (source profile not passed); NARROWED_PRODUCTION_CUT classification is defined but never assigned in the if/elif chain.  
- **Explain**: No dedicated “explain” output (downgraded-runtime explanation in report but no standalone explain command).  
- **Tests**: No tests/test_continuity_confidence.py.  
- **Samples**: No sample target-device profile, confidence report, or downgraded-explanation JSON.  
- **Documentation**: No “remaining gaps” or operator-facing “what this block will NOT do”.  

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| **Create** | `docs/M49I_M49L_BEFORE_CODING.md` — this document. |
| **Modify** | `src/workflow_dataset/continuity_confidence/confidence.py` — (optional) use capability_class when source profile available; add branch for NARROWED_PRODUCTION_CUT when restore ok but production cut should be narrowed. |
| **Modify** | `src/workflow_dataset/cli.py` — add `continuity-confidence` Typer and commands: status, report, device-profile, explain. |
| **Modify** | `src/workflow_dataset/mission_control/state.py` — add continuity_confidence_state from continuity_confidence_slice. |
| **Modify** | `src/workflow_dataset/mission_control/report.py` — add [Continuity confidence] section. |
| **Create** | `tests/test_continuity_confidence.py` — device profile, post-restore profile, confidence classification, downgraded explanation, operator-mode readiness, unknown/mismatch. |
| **Create** | `docs/samples/M49_target_device_profile.json`, `M49_continuity_confidence_report.json`, `M49_downgraded_runtime_explanation.json`. |
| **Create** | `docs/M49I_M49L_REMAINING_GAPS.md` — gaps for later refinement. |

---

## 4. Safety/risk note

- Device-aware continuity does **not** replace edge-readiness or runtime registry; it consumes them and adds post-restore confidence and recommendations.  
- Risk: if callers ignore the recommended posture (e.g. operator_mode_ready=False), they may run operator mode on a restored device that is not yet trusted; mitigation: mission control and CLI surface the recommendation; enforcement stays at operator_mode/governed_operator entry points.  
- “Weaker” or “different” device is heuristic (backends, tier, LLM); no hardware fingerprint or cloud attestation.  

---

## 5. Device-awareness principles

1. **Explicit target profile** — Current device is profiled (edge tier, runtime, backends, version); no silent assumption of “same as source”.  
2. **Compare when source exists** — If a source profile is available (e.g. from bundle manifest or stored snapshot), compare and set capability_class (stronger/same/weaker/different).  
3. **Do not over-claim** — Restored deployment must not advertise capabilities the target cannot support; downgraded notes and narrowed production cut reflect that.  
4. **Operator mode gated** — operator_mode_ready only true when confidence is high and posture allows; otherwise recommend allow_after_review or narrow.  
5. **Review before production** — When confidence is not high, require_review_before_production and next_review_action are set.  
6. **Explain downgrades** — Downgraded-runtime explanation is available so operators know what changed and what to do.  

---

## 6. What this block will NOT do

- **Not** cloud device fleet management or hardware-inventory SaaS.  
- **Not** replacing edge-readiness or runtime registry (only consuming them).  
- **Not** hidden auto-optimization (recommendations are explicit; operator chooses).  
- **Not** enforcing production cut or operator mode at runtime in this layer (enforcement remains in production_cut / governed_operator).  
- **Not** cryptographic or remote attestation of device identity.  
