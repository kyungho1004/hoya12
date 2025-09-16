# 복구/정리 패키지
- `app.py`: 가장 긴(원본에 가까운) 버전으로 복구. 출처: /mnt/data/bloodmap_full_bundle_v1_fix_peds_helper.zip::bloodmap_full_bundle_v1/app.py
- `bundle_addons.py`: 현재 버전 + (필요 시) `ui_symptom_diary_card` 폴백 추가.

## 적용 방법
1) 현재 프로젝트의 `app.py`를 백업 후, 이 파일로 교체합니다.
2) `bundle_addons.py`도 함께 교체(또는 기존 파일에 폴백 함수만 복사).
3) 앱 재시작: `streamlit run app.py` (또는 폴더 구조에 맞게)
