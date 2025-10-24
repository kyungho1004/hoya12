# App Split Full Pack — Phase 6 (DB Harden + Debug + AE Fallback)

포함 내용
- app.py (안전 위임/로컬 임포트 패치 적용본)
- features/
  - explainers.py (기본: ui_results 위임, 폴백: explainer_rules로 로컬 렌더)
  - explainer_rules.py (키워드 칩 규칙 집합)
  - chemo_examples.py · wireups.py
  - adverse_effects.py (**업그레이드**: 기본 ui_results 위임, 폴백 시 간단 요약 테이블 렌더)
  - egfr.py (CKD-EPI/Schwartz + mini UI)
  - carelog.py (CSV/PDF 내보내기 + 최근50 보기)
  - debug_tools.py (디버그: 매칭 소스 텍스트/선택 키)
  - peds/wireups.py (기존 UI 우선, 없으면 해열제/발열 **폴백 미니 UI**)
  - __init__.py
- utils/
  - db_access.py (**업그레이드**: 필드 alias + 중첩 수집)
  - session.py · plotting.py · pdf_utils.py
  - __init__.py

동작 요약
- AE 렌더: ui_results.render_adverse_effects 우선 호출 → 실패/부재 시 fallback 테이블 표시
- 공통 경로: 키워드 칩/예시, eGFR, 케어로그, 소아 도구, 디버그 패널
- 상단 import 추가 없음, /mnt/data 경로 유지, try/except 가드로 UI 안정성 보장

롤백
- app.py의 PATCH 블록 제거 or features/* 모듈 제거해도 기존 동작 유지(ui_results 기반).