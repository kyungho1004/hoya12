
# Fever Dose Panel — Drop-in Module

한국시간: 2025-09-18 01:07:31 KST

## 파일
- `fever_dose_ui.py` — 나이/체중, mg/kg, 시럽 농도 기반 자동 계산 패널

## 적용 방법
1) `fever_dose_ui.py`를 `app.py`와 같은 폴더에 둡니다.
2) `app.py` 상단에 임포트:
```python
from fever_dose_ui import render_fever_panel
```
3) 해열제 섹션에 삽입(나이/체중 입력 아래):
```python
dose_ctx = render_fever_panel(storage_key="fever_panel", default_age_m=36, default_weight=15.0)
apap_ml = dose_ctx["apap_ml"]
ibu_ml  = dose_ctx["ibu_ml"]
```
4) 기존 고정값 출력은 제거/주석 처리하세요.

## 참고
- APAP 기본 12.5 mg/kg (10–15 범위에서 조절 가능)
- IBU  기본 7.5 mg/kg  (5–10 범위에서 조절 가능)
- 시럽 농도: APAP 160 mg/5mL, IBU 100 mg/5mL (변경 가능)
- 계산은 소수 1자리 반올림, 수동 덮어쓰기 토글 제공
