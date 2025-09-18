
# 해열제 스케줄표(소아·일상·질환 전용) — 사용법
생성일: 2025-09-18 02:20:44 KST

## 끼워넣기
`app.py`에서 기존의 공용 미니 스케줄표 호출을 아래로 교체하세요.

### 일상 모드(소아/성인 공용)
```python
from mini_antipyretic_schedule import render_antipyretic_schedule_ui
with st.expander("⏱️ 해열제 스케줄표", expanded=False):
    render_antipyretic_schedule_ui(storage_key="sched_daily")
```

### 소아(질환) 모드
```python
from mini_antipyretic_schedule import render_antipyretic_schedule_ui
with st.expander("⏱️ 해열제 스케줄표", expanded=False):
    render_antipyretic_schedule_ui(storage_key="sched_peds")
```

※ 암 모드는 기존 항암 스케줄 유지 (이 모듈은 암 모드엔 자동으로 안 붙입니다).
