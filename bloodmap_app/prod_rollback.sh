#!/usr/bin/env bash
# prod_rollback.sh — Roll back to previous app.py
set -euo pipefail

APP_DIR="/mount/src/hoya12/bloodmap_app"
cd "$APP_DIR"

# find the latest backup and restore
last_backup=$(ls -d backup_* 2>/dev/null | sort | tail -n 1 || true)
if [[ -z "$last_backup" ]]; then
  echo "No backup_* folder found."
  exit 1
fi

cp -a "$last_backup/app.py.bak" app.py
echo "Restored app.py from $last_backup"

# restart
if systemctl list-units --type=service | grep -q bloodmap; then
  sudo systemctl restart bloodmap
else
  pkill -f "streamlit run" || true
  nohup streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501 >/tmp/bloodmap.out 2>&1 &
  sleep 2
  tail -n 50 /tmp/bloodmap.out || true
fi
echo "✅ Rolled back."
