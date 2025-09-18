#!/usr/bin/env bash
# prod_one_shot_apply.sh — One-click deploy to production (with app.py)
set -euo pipefail

APP_DIR="/mount/src/hoya12/bloodmap_app"
echo "==> Deploying to $APP_DIR"

cd "$APP_DIR"

# Backup current app.py
if [[ -f app.py ]]; then
  BAK="app.py.bak.20250918_033100"
  cp -a app.py "$BAK"
  echo "   - Backed up app.py -> $BAK"
fi

# Copy files from /mnt/data (this chat bundle)
cp -a /mnt/data/app_prod_ready.py ./app.py
cp -a /mnt/data/onco_antipyretic_log.py ./onco_antipyretic_log.py
cp -a /mnt/data/cancer_support_panel.py ./cancer_support_panel.py
echo "   - Placed app.py + panels"

# Quick syntax check
python - <<'PY'
import py_compile, sys
for t in ["app.py","onco_antipyretic_log.py","cancer_support_panel.py"]:
    try:
        py_compile.compile(t, doraise=True)
        print("OK", t)
    except Exception as e:
        print("ERR", t, e); sys.exit(2)
print("ALL OK")
PY

# Restart (systemd if available; else nohup)
if systemctl list-units --type=service | grep -q bloodmap; then
  echo "==> Restarting systemd service: bloodmap"
  sudo systemctl restart bloodmap
  sudo systemctl status --no-pager bloodmap || true
else
  echo "==> Launching via nohup"
  pkill -f "streamlit run" || true
  nohup streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501 >/tmp/bloodmap.out 2>&1 &
  sleep 2
  tail -n 50 /tmp/bloodmap.out || true
fi

echo "✅ Deploy done. Open: http://<서버주소>:8501"
