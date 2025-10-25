Stub Preview — 안전 미리보기 진입점
---------------------------------
목적
- app.py를 수정하지 않고, 레거시 대블록(무거운 렌더)을 호출하지 않는 상태로
  모듈 라우터만 실행해 실제 "용량 감소 효과"를 체감해 보는 모드입니다.

실행
  streamlit run app_stub_preview.py

필요 모듈
- features/app_shell.py
- features/app_deprecator.py
- features/app_router.py
- (선택) features/dev/diag_panel.py  또는 features_dev/diag_panel.py

참고
- 문제가 없고 체감 개선이 충분하면, 다음 단계로 app.py 내부의 AE/특수/소아/내보내기 대블록을
  "주석 스텁화"하여 실제 줄 수를 감소시키는 패치를 진행합니다. (원본 백업+문법검사 포함)
