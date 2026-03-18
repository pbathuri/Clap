#!/usr/bin/env bash
# User rehearsal — run from repo root: bash scripts/run_user_demo_rehearsal.sh
set +e
cd "$(dirname "$0")/.." || exit 1
source .venv/bin/activate

LOG="${TMPDIR:-/tmp}/demo_rehearsal_$$.log"
exec > >(tee "$LOG") 2>&1

echo "========== BLOCK 1 =========="
workflow-dataset demo onboarding start --reset
workflow-dataset demo onboarding user-preset --id investor_demo_primary
workflow-dataset demo onboarding bootstrap-memory
workflow-dataset demo onboarding ready-state
workflow-dataset workspace home --profile calm_default
workflow-dataset day preset set --id founder_operator
workflow-dataset day status
workflow-dataset guidance next-action
workflow-dataset guidance operator-summary
workflow-dataset inbox list

echo "========== BLOCK 2 (sequence + dirs + bootstrap) =========="
echo "=== 1. Startup framing ==="
workflow-dataset demo onboarding sequence
echo "=== 2. Reset clean demo state ==="
workflow-dataset demo onboarding start --reset
echo "=== 3. Apply primary investor preset ==="
workflow-dataset demo onboarding user-preset --id investor_demo_primary
echo "=== 4. Bootstrap bounded memory ==="
workflow-dataset demo onboarding bootstrap-memory
echo "=== 5. Show ready-to-assist summary ==="
workflow-dataset demo onboarding ready-state
echo "=== 6. Show actual workspace shell ==="
workflow-dataset workspace home --profile calm_default
echo "=== 7. Show workday status ==="
workflow-dataset day status
echo "=== 8. Show system recommendation ==="
workflow-dataset guidance next-action
echo "=== 9. Show operator summary ==="
workflow-dataset guidance operator-summary

mkdir -p configs data/local/{workspaces,packages,review,pilot,staging,eval,devlab,incubator,intake,chains}
find . -maxdepth 4 \( -name "settings.yaml" -o -name "settings.yml" \) 2>/dev/null | head -20

cat > configs/settings.yaml <<'EOF'
app:
  name: workflow-dataset-demo
  mode: demo
paths:
  data_root: data/local
demo:
  enabled: true
  profile: investor_demo_primary
EOF

workflow-dataset demo bootstrap
workflow-dataset demo readiness
workflow-dataset demo env-report

echo "========== BLOCK 3 (fix bundle retest) =========="
mkdir -p configs data/local/{workspaces,packages,review,pilot,staging,eval,devlab,incubator,intake,chains}
if [ ! -f configs/settings.yaml ]; then
  cat > configs/settings.yaml <<'EOF'
app:
  name: workflow-dataset-demo
  mode: demo
paths:
  data_root: data/local
demo:
  enabled: true
  profile: investor_demo_primary
EOF
fi
echo "=== RETEST BOOTSTRAP ==="
workflow-dataset demo bootstrap
workflow-dataset demo readiness
workflow-dataset demo env-report
echo "=== REHEARSE INVESTOR FLOW ==="
workflow-dataset demo onboarding start --reset
workflow-dataset demo onboarding user-preset --id investor_demo_primary
workflow-dataset demo onboarding bootstrap-memory
workflow-dataset demo onboarding ready-state
workflow-dataset workspace home --profile calm_default
workflow-dataset day status
workflow-dataset guidance next-action
workflow-dataset guidance operator-summary

echo "========== BLOCK 4 (timed + tails) =========="
time workflow-dataset workspace home --profile calm_default
time workflow-dataset day preset set --id founder_operator
time workflow-dataset day status
time workflow-dataset guidance next-action
time workflow-dataset guidance operator-summary
time workflow-dataset inbox list

time workflow-dataset workspace home --profile calm_default > /tmp/ws_home.txt 2>&1
time workflow-dataset day status > /tmp/day_status.txt 2>&1
time workflow-dataset guidance next-action > /tmp/guidance_next.txt 2>&1
time workflow-dataset guidance operator-summary > /tmp/guidance_summary.txt 2>&1
time workflow-dataset inbox list > /tmp/inbox_list.txt 2>&1

echo "--- tail /tmp/ws_home.txt ---"
tail -n 50 /tmp/ws_home.txt
echo "--- tail /tmp/day_status.txt ---"
tail -n 50 /tmp/day_status.txt
echo "--- tail /tmp/guidance_next.txt ---"
tail -n 50 /tmp/guidance_next.txt
echo "--- tail /tmp/guidance_summary.txt ---"
tail -n 50 /tmp/guidance_summary.txt
echo "--- tail /tmp/inbox_list.txt ---"
tail -n 50 /tmp/inbox_list.txt

workflow-dataset demo onboarding start --reset
workflow-dataset demo onboarding user-preset --id investor_demo_primary
workflow-dataset demo onboarding bootstrap-memory
workflow-dataset demo onboarding ready-state

echo "DONE. Full log: $LOG"
