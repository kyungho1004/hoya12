# App Split Pack (Phase 1, Safe Patch)

- 이 ZIP은 현재 **패치 완료된 app.py**와 분리된 모듈(features/utils)을 포함합니다.
- 기존 코드는 삭제하지 않고, 항암제 부작용 렌더 진입 직전에 **안전 위임 블록**을 삽입했습니다.
- 상단 임포트 추가 없이 **로컬 임포트**로 동작합니다.
- `/mnt/data/...` 경로 유지.

## 포함 파일
- app.py (현재 패치 적용본)
- features/
  - __init__.py
  - explainers.py (키워드 칩/스타일/예시 — ui_results 재노출)
  - chemo_examples.py (예시 블록/MD — 재노출)
  - wireups.py (한 줄 연결: apply_keyword_chips)
  - adverse_effects.py (부작용 렌더 본체 이관 대상, 스켈레톤)
- utils/
  - __init__.py
  - db_access.py (DRUG_DB AE 텍스트 합치기)
  - session.py (세션 가드/키)

## 동작 요약
- 항암제 부작용 렌더 시:
  1) features.adverse_effects.render_adverse_effects(...) 시도 (실패/비어있으면 통과)
  2) 기존 구현 흐름 유지
  3) 공통 경로에서 설명칩/예시 렌더는 wireups/실행 블록으로 동작

## 롤백
- app.py의 PATCH 블록을 제거하면 원상복구됩니다.