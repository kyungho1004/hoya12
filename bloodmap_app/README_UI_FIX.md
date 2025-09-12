# BloodMap — UI Fix & Special Tests

## 변경 요약
- `app.py`
  - 소아모드 발열 선택박스(라인 260대) **인덴트/식 수정** → 런타임 오류(IndentationError) 해결
  - **특수검사 토글 UI 호출 추가**: `special_tests_ui()`
  - **B세포 림프종 연령별 탭**(소아/성인) `render_bcell_age_tabs()` 추가 및 자동 호출
- `special_tests.py`
  - 카테고리 토글(소변/보체/지질/심부전/당) + 색상 배지 해석
  - 소변 RBC/WBC 평균 자동 계산(쉼표 구분 입력)

## 포함 파일
- app.py
- special_tests.py
- onco_map.py (최신 패치 반영본)
- drug_db.py (최신 패치 반영본)
- README_UI_FIX.md

## 참고
- 보고서(MD/TXT)에 특수검사 해석줄을 포함하고 싶으면, 결과 생성 시 `_spec_lines`를 합쳐서 출력하세요.