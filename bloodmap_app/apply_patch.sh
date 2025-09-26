
#!/usr/bin/env bash
set -e
echo "[Bloodmap Patch] Applying files..."
HERE="$(cd "$(dirname "$0")" && pwd)"
cp -v "${HERE}/app.py" ./app.py
cp -v "${HERE}/style.css" ./style.css || true
cp -v "${HERE}/peds_profiles.py" ./peds_profiles.py || true
cp -v "${HERE}/peds_dose.py" ./peds_dose.py || true
cp -v "${HERE}/pdf_export.py" ./pdf_export.py || true
cp -v "${HERE}/core_utils.py" ./core_utils.py || true
echo "[Bloodmap Patch] Done. Restart Streamlit: streamlit run app.py"
