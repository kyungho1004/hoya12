# App Split Pack — Phase 2 (Safe Patch)

이번 패키지는 다음을 포함합니다.
- features/adverse_effects.py : 부작용 렌더를 기존 ui_results 구현으로 위임 (추후 단계적 이관)
- utils/plotting.py : 그래프 PNG 외부저장 (기본 /mnt/data/fig_YYYYMMDD_HHMMSS.png)
- utils/pdf_utils.py : pdf_export 래퍼 (기본 폰트 후보 포함)

## 참고
- 기존 app.py는 이미 Phase 1에서 안전 위임 블록이 들어가 있어 추가 작업 없이 동작합니다.
- 실제 렌더 구현을 옮길 때는 features/adverse_effects.py 내부에 한 섹션씩 이동하면 됩니다.