BloodMap Patch Bundle
Generated: 2025-09-25 23:16:42 (server time)

Entrypoint:
- streamlit_app.py  (Cloud 스타트 파일)
- app.py            (메인 UI/로직)

검증 결과:
- Python syntax OK: app.py, streamlit_app.py, branding.py, pdf_export.py, peds_dose.py, peds_profiles.py, special_tests.py, adult_rules.py, onco_map.py, ui_results.py, drug_db.py, core_utils.py, lab_diet.py
- Python syntax ERR: None
- JSON load OK: final_drug_coverage.json
- JSON load ERR: None

사용법:
1) 저장소 루트에 모든 파일 배치
2) Streamlit Cloud에서 entrypoint를 streamlit_app.py로 두고 배포
3) 기존 기능은 app.py 기준으로 동작
