#!/usr/bin/env bash
set -euo pipefail
echo "🔎 Checking required files ..."
for f in app_onco_with_log.py onco_antipyretic_log.py cancer_support_panel.py requirements.txt; do
  if [[ ! -f "$f" ]]; then echo "❌ missing: $f"; exit 1; else echo "✅ $f"; fi
done
echo "🔎 Verifying panel is called under schedule_block() ..."
if grep -n "render_onco_antipyretic_log" app_onco_with_log.py >/dev/null; then
  echo "✅ panel call found"
else
  echo "❌ panel call missing in app_onco_with_log.py"; exit 1
fi
echo "All checks passed."
