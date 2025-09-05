# BloodMap package (entry fix)
- Built: 2025-09-05 07:19
- Includes patched `bloodmap_app/app.py` (KR-first heme labels, AML/APL mapping).
- Root `streamlit_app.py` is clean (UTF-8, LF, no BOM).

## Streamlit Cloud (추천)
Settings → Main file path: `bloodmap_app/app.py`

## Local run
```
pip install -r requirements.txt
streamlit run bloodmap_app/app.py
```
