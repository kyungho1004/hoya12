BloodMap Hotfix — selectbox(format_func) TypeError
=================================================
문제:
  Streamlit selectbox의 format_func는 인자를 1개만 받는 함수여야 합니다.
  기존 코드에서 local_dx_display(group, dx)처럼 2개 인자를 요구하는 함수를 그대로 넘겨
  TypeError가 발생했습니다.

해결:
  group을 클로저로 캡처하는 래퍼(_dx_fmt)를 만든 뒤 format_func에 전달하세요.

적용 위치 (app.py, 암 모드 카테고리/진단 선택 구간):
  1) 먼저 group을 선택한 다음,
  2) 아래의 _dx_fmt 함수를 추가하고,
  3) selectbox 호출에서 format_func=_dx_fmt 로 교체합니다.

코드 스니펫:
  # 카테고리 먼저
  group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
  dx_options = list(ONCO_MAP.get(group, {}).keys())

  # ✅ group을 캡처하는 래퍼
  def _dx_fmt(opt: str) -> str:
      try:
          return local_dx_display(group, opt)
      except Exception:
          return str(opt)

  # ✅ 변경된 selectbox
  dx = st.selectbox("진단(영문+한글)", dx_options or ["직접 입력"], format_func=_dx_fmt)

참고:
  - format_func는 내부적으로 format_func(option) 한 번만 호출됩니다.
  - local_dx_display는 (group, option) 형태이므로, group을 캡처한 _dx_fmt로 감싸야 합니다.
  - 안전을 위해 try/except로 문자열 강제 반환을 넣었습니다.

빠른 체크:
  - 림프종 선택 → DLBCL 등 항목에 한글 병기가 함께 표시되는지 확인
  - 혈액암 → '직접 입력' 선택 후 아래 보조 표기에서 한글 병기 정상 표시 확인
  - dx_options가 비어도 ["직접 입력"] 덕분에 크래시 없음

