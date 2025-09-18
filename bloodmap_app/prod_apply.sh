#!/usr/bin/env bash
# prod_apply.sh — Apply antipyretic panel to prod safely
set -euo pipefail

APP_DIR="/mount/src/hoya12/bloodmap_app"
echo "==> Applying patch in $APP_DIR"

cd "$APP_DIR"

# 0) Backup
BACKUP_DIR="backup20250918_032400"
mkdir -p "$BACKUP_DIR"
cp -a app.py "$BACKUP_DIR/app.py.bak" 2>/dev/null || true

# 1) Drop in latest modules (from /mnt/data)
for f in onco_antipyretic_log.py cancer_support_panel.py; do
  if [[ -f "/mnt/data/$f" ]]; then
    cp -a "/mnt/data/$f" "./$f"
    echo "   - updated: $f"
  elif [[ -f "./$f" ]]; then
    echo "   - keep existing: $f"
  else
    echo "   - ERROR: missing $f"; exit 1
  fi
done

# 2) Prefer integrated app if present; otherwise leave app.py and just import+call lines required
if [[ -f "/mnt/data/app_onco_with_log.py" ]]; then
  cp -a "/mnt/data/app_onco_with_log.py" "./app_onco_with_log.py"
  echo "   - placed app_onco_with_log.py"
  # If prod strictly requires app.py, swap (idempotent)
  if [[ -n "${FORCE_APP_PY:-}" ]]; then
    cp -a app_onco_with_log.py app.py
    echo "   - FORCE_APP_PY active → replaced app.py"
  fi
fi

# 3) Quick syntax check
python - <<'PY'
import py_compile, sys
targets = ["app_onco_with_log.py","app.py","onco_antipyretic_log.py","cancer_support_panel.py"]
ok = True
for t in targets:
    try:
        with open(t): pass
    except: 
        continue
    try:
        py_compile.compile(t, doraise=True)
        print("OK", t)
    except Exception as e:
        print("ERR", t, e); ok=False
if not ok:
    sys.exit(2)
PY

# 4) Restart service if systemd unit exists; else nohup fallback
if systemctl list-units --type=service | grep -q bloodmap; then
  echo "==> Restarting systemd service: bloodmap"
  sudo systemctl restart bloodmap
  sudo systemctl status --no-pager bloodmap || true
else
  echo "==> Launching Streamlit manually (nohup)"
  pkill -f "streamlit run" || true
  nohup streamlit run app_onco_with_log.py --server.headless true --server.address 0.0.0.0 --server.port 8501 >/tmp/bloodmap.out 2>&1 &
  sleep 2
  tail -n +1 /tmp/bloodmap.out | tail -n 50 || true
fi

echo "✅ Done. Check http://<서버주소>:8501"
