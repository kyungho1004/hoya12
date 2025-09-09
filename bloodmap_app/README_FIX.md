# BloodMap Clean Patch
## What this does
- Fixes `utils.py` vs `utils/` name conflict by renaming `utils.py` -> `app_utils.py`
- Rewrites only the specific imports for `user_key, init_state` to use `app_utils`
- Inserts a Universal Import Header at the top of `bloodmap_app/app.py`
- Normalizes fonts folder (renames `fonfs/` -> `fonts/` if needed) and adds font auto-detection to `config.py`
- Ensures `streamlit_app.py` properly launches the app

## How to use
1) Download this folder and place the two files in your repo root:
   - `fix_bloodmap_repo.py`
   - `UNIVERSAL_IMPORT_HEADER.py`
2) From repo root, run:
   ```bash
   python fix_bloodmap_repo.py
   ```
3) Commit and push:
   ```bash
   git add -A && git commit -m "fix: imports/fonts + universal header" && git push
   ```
4) On Streamlit Cloud, set **Main file** to `streamlit_app.py`.

