BloodMap Onco — Integrated Final (2025-09-18 03:48:38 KST)
포함:
- app.py — 해열제 스케줄러(한국시간 KST, 설사 시간대 기록 포함) 바로 실행용
- antipyretic_schedule.py — 스케줄러 모듈
- onco_antipyretic_log.py, cancer_support_panel.py — (선택) 기존 패널 사용 시 참고

실행:
  unzip -o bloodmap_onco_integrated_final.zip
  bash run_final.sh

기존 본섭 폴더에서 덮어쓰기 후:
  cd /mount/src/hoya12/bloodmap_app
  unzip -o /mnt/data/bloodmap_onco_integrated_final.zip
  bash run_final.sh
