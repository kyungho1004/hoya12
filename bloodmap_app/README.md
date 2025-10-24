# App Split Full Pack — Phase 4 (Peds Fallbacks Included, Safe Patch)

포함 내용
- app.py (안전 위임 패치 적용본)
- features/
  - explainers.py · chemo_examples.py · wireups.py · adverse_effects.py
  - egfr.py (CKD-EPI/Schwartz + mini UI)
  - carelog.py (CSV/PDF, 최근50 보기)
  - peds/
    - wireups.py (우선 기존 peds_dose/peds_guide UI 호출, 없으면 폴백 미니 UI 제공)
    - __init__.py
  - __init__.py
- utils/
  - db_access.py · session.py · plotting.py · pdf_utils.py
  - __init__.py

적용 포인트
- 공통 경로에서: 키워드 칩/예시, eGFR UI, 케어로그 UI, 소아 도구(우선 기존 UI → 폴백)
- 상단 import 추가 없음, /mnt/data 경로 유지

롤백
- app.py의 PATCH 블록 제거로 원상복구 가능