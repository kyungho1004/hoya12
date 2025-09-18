BloodMap — One-shot Deploy (20250918_033100)
- app.py 포함, 항암 스케줄 하단에 해열제 기록 패널 연결
- onco_antipyretic_log.py (간격/24h 경고 포함), cancer_support_panel.py (mL 표준, 전문가 설정 숨김)

서버에서 바로 적용:
  cd /mount/src/hoya12/bloodmap_app
  unzip -o /mnt/data/prod_one_shot_deploy.zip
  pkill -f "streamlit run" || true
  streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501
