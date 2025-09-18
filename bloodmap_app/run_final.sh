#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv || true
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install streamlit pandas
exec streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501
