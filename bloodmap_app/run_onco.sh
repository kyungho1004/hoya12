#!/usr/bin/env bash
set -euo pipefail
echo "👉 Setting up venv (.venv) and running app_onco_with_log.py ..."
python3 -m venv .venv || true
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade streamlit pandas
echo "✅ Ready. Launching on http://localhost:8501"
exec streamlit run app_onco_with_log.py --server.headless true --server.address 0.0.0.0 --server.port 8501
