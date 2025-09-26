
# Bloodmap Patch Bundle (Hotfix)
Date: 2025-09-26 05:50:28 KST

## What this patch includes
- Fix: `wkey` NameError by adding a safe shim at top of app.py (before any usage).
- Fix: `st.set_page_config` corruption (duplicated call) → normalized to a single valid call.
- Labs: WBC-first order, 0.00 formatting, graph view.
- Care Log: detailed GI entries, KST temp logs, ORS guidance, next-3 doses .ics export.
- Safety Flow: automatic emergency/warning banners + ER one-page PDF button.
- Dev Utils: duplicate key scanner, save/restore session state, Undo (labs/care).

## How to apply (safe/quick)
1) Backup your current files.
2) Unzip this bundle into your project root (same folder containing `app.py`). Overwrite when asked.
3) Restart Streamlit:
   ```bash
   streamlit run app.py
   ```
4) Hard refresh your browser.

## Files included
- app.py
- style.css
- peds_profiles.py
- peds_dose.py
- pdf_export.py
- core_utils.py
