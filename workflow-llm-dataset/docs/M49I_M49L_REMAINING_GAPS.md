# M49I–M49L Device-Aware Continuity — Remaining Gaps for Later Refinement

## Implemented in this block

- **BEFORE CODING**: docs/M49I_M49L_BEFORE_CODING.md (what exists, what’s missing, file plan, safety, principles, what we won’t do).
- **Confidence**: NARROWED_PRODUCTION_CUT branch when restore_score >= 0.7 and report.warnings.
- **CLI**: continuity-confidence status, report, device-profile, explain.
- **Mission control**: continuity_confidence_state in state.py; [Continuity confidence] section in report.py.
- **Tests**: test_continuity_confidence.py (profile, compare, confidence, post-restore profile, downgraded explanation, slice, operator-mode readiness).
- **Samples**: M49_target_device_profile.json, M49_continuity_confidence_report.json, M49_downgraded_runtime_explanation.json.

---

## Exact remaining gaps (for later)

1. **Source device profile**  
   compare_source_target exists but build_continuity_confidence never receives a source profile (no stored “source device” in bundle or elsewhere). Capability_class stays unknown unless a future bundle manifest or snapshot carries source device info.

2. **Storing target device profile**  
   build_target_device_profile builds from current environment but does not persist; no history of device profiles for “last restore target” vs “current”.

3. **Memory/retrieval expectations**  
   Phase B mentioned “adjust memory/retrieval expectations where needed”; no explicit model or API for that in this layer (could be a note on PostRestoreRuntimeProfile or a separate adjustment type).

4. **Automation/adaptive-execution posture**  
   “Adjust automation or adaptive-execution posture” is not yet modeled (e.g. recommend “reduce adaptive steps” on weaker device); could be an extension of ModelRouteAdjustment or a new adjustment kind.

5. **Mismatched or unknown device**  
   When capability_class is different/unknown, confidence could explicitly add a reason (“Target device capability unknown or different from source”) and recommendation; currently we only add promoted note when stronger.

6. **Enforcement at entry points**  
   production_cut and operator_mode do not yet read continuity_confidence_state to block or narrow; recommendations are advisory. Enforcement would require those layers to call continuity_confidence_slice and respect operator_mode_readiness_after_restore / production_cut_narrowed.

7. **Bundle ref in mission control slice**  
   continuity_confidence_slice uses bundle_ref="latest" only; mission control does not expose which bundle ref was used. If multiple bundles exist, “current” confidence could be ambiguous.

8. **Edge tier from bundle**  
   Restore validation does not currently pass a “source edge tier” from the bundle into device_profile comparison; capability_class remains heuristic (backends, LLM, tier) without bundle-authored source profile.
