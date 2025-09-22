Hotfix P3 — Writable-path fallback for profile/carelog without any hardcoded /mnt/data

Drop-in usage:
1) Replace your app.py with this app.py OR copy the helper blocks into your main app.py:
   - Writable data root helpers (_data_root/_data_path)
   - Profile/Carelog I/O functions using those helpers (no /mnt/data hardcode)
2) Ensure BLOODMAP_DATA_ROOT env var if you want a custom path (optional).
3) Run: streamlit run app.py
4) Press '프로필 저장' and confirm the saved path printed in the success message.

If your full app also writes graph CSV, replace its path with:
    path = _data_path("bloodmap_graph", f"{uid}.labs.csv")
