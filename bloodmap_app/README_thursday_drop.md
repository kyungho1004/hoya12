
# Thursday Drop #1 — Mini Bundle

한국시간 기준: 2025-09-18 00:59:09 KST

이 번들에는 다음이 포함됩니다.

- `onco_mini_toggle.py` — 암 미니 패널 토글(요약·복사 버튼 포함)
- `mini_schedule.py` — 소아·성인·질환 공용 미니 스케줄표
- `report_qr.py` — 보고서/앱 링크용 QR 유틸(외부 라이브러리 불요)
- `README_thursday_drop.md` — 적용 가이드
- `thursday_drop_1.zip` — 위 3개 소스+README 묶음

---

## 1) 설치/배치

모든 파일을 **앱 루트(= `app.py`가 있는 폴더)** 에 두세요.

구조 예시:
```
/mnt/data/
  app.py
  onco_mini_toggle.py
  mini_schedule.py
  report_qr.py
  README_thursday_drop.md
  ...
```

## 2) `app.py`에 끼워넣기

### (A) 상단 import
```python
from onco_mini_toggle import render_onco_mini
from mini_schedule import mini_schedule_ui
from report_qr import render_qr, qr_url
```

### (B) 암 모드 화면 상단에 미니 패널
```python
if mode == "암":
    # 기존 코드 위쪽/아래쪽 아무데나
    render_onco_mini(st.session_state.get("analysis_ctx"))
```

### (C) 공용 미니 스케줄표 섹션
- 암/일상/소아 아무 모드에나 다음 한 줄을 원하는 위치에 추가:
```python
mini_schedule_ui(storage_key="mini_sched")
```

### (D) 보고서 QR (예: 보고서 저장 섹션 아래)
```python
# 예시: 웹앱 공식 주소 또는 방금 생성된 다운로드 링크를 QR로
app_link = "https://bloodmap.streamlit.app/"
render_qr(st, app_link, size=220, caption="앱 바로가기")
```

## 3) 의존성
추가 파이썬 패키지 **없음**. (Streamlit/Pandas는 기존 `requirements.txt` 그대로 사용)

## 4) 동작 점검 체크리스트
- [x] 임포트 오류 없음 (경로 가드 필요 시 `app.py` 상단에 path guard 3줄 삽입 권장)
- [x] 암 미니 패널 토글 열리고 요약 표시됨
- [x] 미니 스케줄표 생성/추가/다운로드 동작
- [x] QR 표시(이미지 로드가 안 되면 네트워크 차단 여부 확인)

## 5) 문제 해결
- **ModuleNotFoundError**: 작업 폴더가 `app.py` 있는 위치인지 확인 (`cd /mnt/data`).
- **QR 안 보임**: 사내망/방화벽에서 `chart.googleapis.com` 차단 여부 확인.
- **스케줄 저장 안 됨**: Streamlit 세션 상태 초기화 여부 확인(새로고침 시 사라질 수 있음).

---

© BloodMap — caregiver-first UX
