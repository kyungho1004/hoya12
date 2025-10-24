# App Split Full Pack — Phase 3-B (eGFR + Carelog, Safe Patch)

포함 내용
- app.py (안전 위임 패치 적용본)
- features/
  - explainers.py · chemo_examples.py · wireups.py
  - adverse_effects.py (부작용 렌더 위임)
  - egfr.py (CKD-EPI/Schwartz + eGFR 미니 UI)
  - carelog.py (케어로그: CSV, 최근50 보기, CSV/PDF 내보내기)
  - __init__.py
- utils/
  - db_access.py · session.py · plotting.py · pdf_utils.py
  - __init__.py

적용 포인트
- 항암제 부작용 렌더 공통 경로에서:
  - keyword 칩/예시(한 줄 호출, wireups)
  - eGFR UI (local import)
  - carelog UI (local import)

롤백
- app.py의 해당 PATCH 블록만 제거하면 원상복구됩니다.