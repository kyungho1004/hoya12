# BloodMap — FULL Monday Pack
## 포함
- graph_store.py: /mnt/data/bloodmap_graph 저장/불러오기
- carelog_ext.py: 케어로그(암/일상/소아) 추가/삭제/24h TXT/ICS/PDF
- csv_importer.py: CSV Import Wizard
- unit_guard.py: 단위 가드
- er_onepage.py: ER One-Page PDF 생성용 MD 빌더
- apply_full_patch.py: idempotent app.py 패처
- install_full_update.py: 자동 설치 스크립트
- app_full_patched.py: 참고용 완성본(app.py 대체 가능)
## 사용
    unzip full_monday_pack.zip
    python install_full_update.py
## 확인
- 별명+PIN 있어야 고정 그래프 보임
- 그래프 저장/불러오기 버튼 동작 & 파일 생성(/mnt/data/bloodmap_graph)
- 케어로그 탭에서 추가/삭제 + TXT/ICS/PDF 내보내기
- 피수치 요약 섹션에 '단위 가드' 경고 표시
- 피수치 입력에서 CSV Import Wizard 동작
