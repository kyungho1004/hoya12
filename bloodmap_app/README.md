# App Split Full Pack — Phase 3-A (Safe Patch)

포함 내용
- app.py (안전 위임 패치 적용본)
- features/
  - explainers.py (키워드 칩/스타일/예시 — ui_results 재노출)
  - chemo_examples.py (예시 블록/MD 재노출)
  - wireups.py (한 줄 연결: apply_keyword_chips)
  - adverse_effects.py (부작용 렌더 위임: ui_results 구현 호출)
  - egfr.py (eGFR 계산: CKD-EPI/Schwartz + mini UI 익스펜더)
  - __init__.py
- utils/
  - db_access.py (DRUG_DB AE 텍스트 합치기)
  - session.py (세션 가드/키)
  - plotting.py (그래프 PNG 외부저장 /mnt/data/*.png)
  - pdf_utils.py (pdf_export 래퍼)
  - __init__.py

적용 포인트
- 항암제 부작용 렌더 진입 전: features.adverse_effects로 우선 위임(실패/빈 구현이면 통과)
- 공통 경로: keyword 칩/예시(한 줄 호출), eGFR mini UI (로컬 임포트)
- 상단 import 추가 없음, /mnt/data 경로 유지

롤백
- app.py의 PATCH 블록 제거로 원상복구 가능
- 분리 모듈 삭제 시 기존 ui_results 기반 동작 유지