
# Onco Antipyretic Log — Drop-in
한국시간: 2025-09-18 01:53:45 KST

## 기능
- 항암 스케줄 **바로 아래**에 붙여 사용할 해열제 복용 기록 패널
- 성인/소아, 나이/체중, 설사 횟수
- **mL 통일**(APAP/IBU 농도 조절 가능), KST 기준 복용 시각 저장
- CSV 내보내기, 전체 삭제

## 끼워넣기
`app.py` (암 모드의 `schedule_block()` 호출 **바로 아래**)에 다음 두 줄:
```python
from onco_antipyretic_log import render_onco_antipyretic_log
render_onco_antipyretic_log(storage_key="onco_antipyretic_log")
```

Peds 계산은 `peds_dose_override.py`가 있으면 자동 사용합니다.
