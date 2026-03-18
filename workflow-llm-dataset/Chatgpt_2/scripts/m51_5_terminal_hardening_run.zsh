#!/usr/bin/env zsh
# M51.5 terminal hardening run — run with: zsh scripts/m51_5_terminal_hardening_run.zsh
# (Do not paste line-by-line into zsh; history expansion can break on some lines.)
setopt NO_HIST_EXPAND 2>/dev/null || true
set +e

# =========================
# M51.5 terminal hardening run
# =========================

# ---- editable defaults ----
export USB_ROOT="/Volumes/OPSPILOT_USB"
export REPO_DIR="$USB_ROOT/workflow-llm-dataset"
export DEMO_ROLE="founder_operator_demo"
export SAMPLE_WORKSPACE="$REPO_DIR/demo_assets/sample_workspace"

# ---- derived paths ----
export OPSPILOT_DEMO_HOST="$HOME/opspilot_demo_host"
export OPSPILOT_DEMO_MODE=1
export OPSPILOT_LOG_DIR="$OPSPILOT_DEMO_HOST/logs"
export OPSPILOT_ARTIFACT_DIR="$OPSPILOT_DEMO_HOST/artifacts"
export OPSPILOT_REPORT_DIR="$OPSPILOT_DEMO_HOST/reports"
export DEMO_RUN_ID="$(date +%Y%m%d_%H%M%S)"
export DEMO_LOG="$OPSPILOT_LOG_DIR/demo_run_${DEMO_RUN_ID}.log"
export FAIL_LOG="$OPSPILOT_LOG_DIR/demo_failures_${DEMO_RUN_ID}.md"
export HANDOFF_LOG="$OPSPILOT_REPORT_DIR/m51_5_hardening_handoff_${DEMO_RUN_ID}.md"

# Narrative / investor walkthrough (USB demo group does not define these)
INV() { workflow-dataset investor-demo "$@"; }

# ---- create host dirs ----
mkdir -p "$OPSPILOT_DEMO_HOST" "$OPSPILOT_LOG_DIR" "$OPSPILOT_ARTIFACT_DIR" "$OPSPILOT_REPORT_DIR"

# ---- start log files ----
touch "$DEMO_LOG" "$FAIL_LOG"
echo "# Demo Failure Log" > "$FAIL_LOG"
echo "" >> "$FAIL_LOG"

# ---- go to repo ----
cd "$REPO_DIR" || { echo "Repo not found at $REPO_DIR"; exit 1; }

echo "=== M51.5 HARDENING RUN $DEMO_RUN_ID ===" | tee -a "$DEMO_LOG"

# =========================
# 1. machine + environment inspection
# =========================
{
  echo "=== MACHINE INFO ==="
  date
  uname -a
  sw_vers 2>/dev/null || true
  python3 --version || python --version
  which python3 || which python
  which pip3 || which pip || true
  df -h .
  sysctl -n hw.memsize 2>/dev/null || true
  sysctl -n machdep.cpu.brand_string 2>/dev/null || true
  echo "PWD=$(pwd)"
  echo "USB_ROOT=$USB_ROOT"
  echo "REPO_DIR=$REPO_DIR"
  echo "DEMO_ROLE=$DEMO_ROLE"
  echo "SAMPLE_WORKSPACE=$SAMPLE_WORKSPACE"
  echo "OPSPILOT_DEMO_HOST=$OPSPILOT_DEMO_HOST"
} | tee -a "$DEMO_LOG"

# =========================
# 2. fresh venv + install
# =========================
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel 2>&1 | tee -a "$DEMO_LOG"
pip install -e . 2>&1 | tee -a "$DEMO_LOG"

# =========================
# 3. static sanity
# =========================
python -m compileall src tests 2>&1 | tee -a "$DEMO_LOG"

python - <<'PY' 2>&1 | tee -a "$DEMO_LOG"
import importlib
mods = ["workflow_dataset"]
for m in mods:
    importlib.import_module(m)
    print("OK import:", m)
PY

workflow-dataset --help 2>&1 | tee -a "$DEMO_LOG"
workflow-dataset --help > "$OPSPILOT_REPORT_DIR/cli_help_${DEMO_RUN_ID}.txt" 2>&1 || true

# =========================
# 4. demo-critical tests
# =========================
pytest -q tests -k "demo or bootstrap or onboarding or readiness or mission_control or continuity or memory or operator or assist" \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/pytest_demo_subset_${DEMO_RUN_ID}.txt"

pytest -q tests -k "not slow" \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/pytest_broad_${DEMO_RUN_ID}.txt"

grep -n "FAILED\|ERROR" "$OPSPILOT_REPORT_DIR/pytest_demo_subset_${DEMO_RUN_ID}.txt" | tee -a "$DEMO_LOG" || true
grep -n "FAILED\|ERROR" "$OPSPILOT_REPORT_DIR/pytest_broad_${DEMO_RUN_ID}.txt" | tee -a "$DEMO_LOG" || true

# =========================
# 5. bootstrap rehearsal
# =========================
date | tee -a "$DEMO_LOG"
time workflow-dataset demo bootstrap \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_bootstrap_${DEMO_RUN_ID}.txt"
date | tee -a "$DEMO_LOG"

time workflow-dataset demo readiness \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_readiness_${DEMO_RUN_ID}.txt"

time workflow-dataset demo env-report \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_env_report_${DEMO_RUN_ID}.txt"

grep -i "degraded\|blocked\|fallback\|warning" "$OPSPILOT_REPORT_DIR"/demo_*_"${DEMO_RUN_ID}".txt | tee -a "$DEMO_LOG" || true

# =========================
# 6. onboarding rehearsal
# =========================
time workflow-dataset demo onboarding start \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/onboarding_start_${DEMO_RUN_ID}.txt"

time workflow-dataset demo onboarding role --id "$DEMO_ROLE" \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/onboarding_role_${DEMO_RUN_ID}.txt"

time workflow-dataset demo onboarding bootstrap-memory \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/onboarding_memory_${DEMO_RUN_ID}.txt"

time workflow-dataset demo onboarding ready-state \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/onboarding_ready_${DEMO_RUN_ID}.txt"

# =========================
# 7. mission-control rehearsal (investor-demo narrative)
# =========================
time INV session start \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_session_start_${DEMO_RUN_ID}.txt"

time INV session stage \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_session_stage_${DEMO_RUN_ID}.txt"

time INV mission-control \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_mission_control_${DEMO_RUN_ID}.txt"

# =========================
# 8. first-value artifact generation
# =========================
date | tee -a "$DEMO_LOG"
time INV first-value \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_first_value_${DEMO_RUN_ID}.txt"
date | tee -a "$DEMO_LOG"

grep -i "artifact\|summary\|draft\|next action\|recommend" "$OPSPILOT_REPORT_DIR/demo_first_value_${DEMO_RUN_ID}.txt" | tee -a "$DEMO_LOG" || true

# =========================
# 9. supervised-action demo
# =========================
date | tee -a "$DEMO_LOG"
time INV supervised-action \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/demo_supervised_action_${DEMO_RUN_ID}.txt"
date | tee -a "$DEMO_LOG"

grep -i "approve\|review\|safe\|supervised\|blocked\|requires" "$OPSPILOT_REPORT_DIR/demo_supervised_action_${DEMO_RUN_ID}.txt" | tee -a "$DEMO_LOG" || true

# =========================
# 10. timed investor run-through
# =========================
echo "=== TIMED INVESTOR RUN-THROUGH START ===" | tee -a "$DEMO_LOG"
date | tee -a "$DEMO_LOG"

time workflow-dataset demo bootstrap \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/timed_bootstrap_${DEMO_RUN_ID}.txt"

time workflow-dataset demo onboarding start \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/timed_onboarding_start_${DEMO_RUN_ID}.txt"

time workflow-dataset demo onboarding role --id "$DEMO_ROLE" \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/timed_onboarding_role_${DEMO_RUN_ID}.txt"

time workflow-dataset demo onboarding bootstrap-memory \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/timed_onboarding_memory_${DEMO_RUN_ID}.txt"

time INV mission-control \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/timed_mission_control_${DEMO_RUN_ID}.txt"

time INV first-value \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/timed_first_value_${DEMO_RUN_ID}.txt"

time INV supervised-action \
  2>&1 | tee "$OPSPILOT_REPORT_DIR/timed_supervised_action_${DEMO_RUN_ID}.txt"

date | tee -a "$DEMO_LOG"
echo "=== TIMED INVESTOR RUN-THROUGH END ===" | tee -a "$DEMO_LOG"

# =========================
# 11. ordering validation
# =========================
echo "=== ORDERING CHECKS ===" | tee -a "$DEMO_LOG"

workflow-dataset demo bootstrap > /tmp/m51_bootstrap.txt 2>&1
workflow-dataset demo readiness > /tmp/m51_readiness.txt 2>&1
workflow-dataset demo onboarding start > /tmp/m51_onboarding_start.txt 2>&1
workflow-dataset demo onboarding role --id "$DEMO_ROLE" > /tmp/m51_onboarding_role.txt 2>&1
workflow-dataset demo onboarding bootstrap-memory > /tmp/m51_onboarding_memory.txt 2>&1
workflow-dataset demo onboarding ready-state > /tmp/m51_ready_state.txt 2>&1
INV mission-control > /tmp/m51_mission.txt 2>&1
INV first-value > /tmp/m51_firstvalue.txt 2>&1
INV supervised-action > /tmp/m51_supervised.txt 2>&1

for f in /tmp/m51_*.txt; do
  echo "===== $f ====="
  tail -n 40 "$f"
done | tee "$OPSPILOT_REPORT_DIR/ordering_validation_${DEMO_RUN_ID}.txt"

# =========================
# 12. aggregate fail signals
# =========================
grep -i "error\|failed\|traceback\|blocked\|warning" "$OPSPILOT_REPORT_DIR"/*_"${DEMO_RUN_ID}".txt \
  | tee "$OPSPILOT_REPORT_DIR/aggregated_fail_signals_${DEMO_RUN_ID}.txt" || true

# =========================
# 13. latency summary template
# =========================
cat > "$OPSPILOT_REPORT_DIR/latency_summary_${DEMO_RUN_ID}.md" <<'EOF'
# Latency Summary
- Bootstrap:
- Readiness:
- Onboarding start:
- Role select:
- Memory bootstrap:
- Ready-state:
- Mission-control:
- First-value:
- Supervised action:

## Assessment
- acceptable for live demo:
- risky but manageable:
- too slow:
- should be preloaded:
EOF

# =========================
# 14. hardening handoff bundle
# =========================
cat > "$HANDOFF_LOG" <<EOF
# M51.5 Hardening Handoff

## Run ID
$DEMO_RUN_ID

## Main logs
- Demo log: $DEMO_LOG
- Failure log: $FAIL_LOG

## Core reports
- CLI help: $OPSPILOT_REPORT_DIR/cli_help_${DEMO_RUN_ID}.txt
- Demo subset tests: $OPSPILOT_REPORT_DIR/pytest_demo_subset_${DEMO_RUN_ID}.txt
- Broad tests: $OPSPILOT_REPORT_DIR/pytest_broad_${DEMO_RUN_ID}.txt
- Ordering validation: $OPSPILOT_REPORT_DIR/ordering_validation_${DEMO_RUN_ID}.txt
- Aggregated fail signals: $OPSPILOT_REPORT_DIR/aggregated_fail_signals_${DEMO_RUN_ID}.txt
- Latency summary: $OPSPILOT_REPORT_DIR/latency_summary_${DEMO_RUN_ID}.md

## Demo flow reports
- Bootstrap: $OPSPILOT_REPORT_DIR/demo_bootstrap_${DEMO_RUN_ID}.txt
- Readiness: $OPSPILOT_REPORT_DIR/demo_readiness_${DEMO_RUN_ID}.txt
- Env report: $OPSPILOT_REPORT_DIR/demo_env_report_${DEMO_RUN_ID}.txt
- Onboarding start: $OPSPILOT_REPORT_DIR/onboarding_start_${DEMO_RUN_ID}.txt
- Onboarding role: $OPSPILOT_REPORT_DIR/onboarding_role_${DEMO_RUN_ID}.txt
- Onboarding memory: $OPSPILOT_REPORT_DIR/onboarding_memory_${DEMO_RUN_ID}.txt
- Ready-state: $OPSPILOT_REPORT_DIR/onboarding_ready_${DEMO_RUN_ID}.txt
- Mission-control: $OPSPILOT_REPORT_DIR/demo_mission_control_${DEMO_RUN_ID}.txt
- First value: $OPSPILOT_REPORT_DIR/demo_first_value_${DEMO_RUN_ID}.txt
- Supervised action: $OPSPILOT_REPORT_DIR/demo_supervised_action_${DEMO_RUN_ID}.txt

## Timed run-through
- Timed bootstrap: $OPSPILOT_REPORT_DIR/timed_bootstrap_${DEMO_RUN_ID}.txt
- Timed onboarding start: $OPSPILOT_REPORT_DIR/timed_onboarding_start_${DEMO_RUN_ID}.txt
- Timed onboarding role: $OPSPILOT_REPORT_DIR/timed_onboarding_role_${DEMO_RUN_ID}.txt
- Timed onboarding memory: $OPSPILOT_REPORT_DIR/timed_onboarding_memory_${DEMO_RUN_ID}.txt
- Timed mission-control: $OPSPILOT_REPORT_DIR/timed_mission_control_${DEMO_RUN_ID}.txt
- Timed first value: $OPSPILOT_REPORT_DIR/timed_first_value_${DEMO_RUN_ID}.txt
- Timed supervised action: $OPSPILOT_REPORT_DIR/timed_supervised_action_${DEMO_RUN_ID}.txt

## Next task
Use these logs to run the M51.5 hardening prompt.
EOF

echo "=== HARDENING HANDOFF READY ===" | tee -a "$DEMO_LOG"
echo "$HANDOFF_LOG"
echo "$FAIL_LOG"
echo "$DEMO_LOG"
echo "$OPSPILOT_REPORT_DIR"
