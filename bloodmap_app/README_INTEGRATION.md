
# BloodMap Addons (2025‑09‑22)

이 폴더의 모듈들은 `app_onco_with_log.py`에서 **import** 해서 바로 쓸 수 있게 만든 드롭인입니다.

## 1) 케어로그 + 해열제(24h 한국어/유형/개인별 파일명)

```python
from onco_antipyretic_log import render_onco_antipyretic_log

# nickname_pin()으로 얻은 값 사용
nick, pin, key = nickname_pin()

# uid는 보통 key(별명+PIN 해시) 또는 그에 준하는 사용자 고유 식별자
uid = key

# (선택) 다음 복용 가능 시각 객체가 있으면 넘겨주세요. 없으면 None.
apap_next = None
ibu_next = None

# 원하는 위치에서 호출
render_onco_antipyretic_log(nick, uid, apap_next=apap_next, ibu_next=ibu_next)
```

동작:
- 구토/설사 **세부유형** 선택 후 기록
- 24h 목록을 **한국어 라벨 + 유형**으로 표시
- 내보내기 파일명이 **`{닉네임 or UID}`** 포함
- TXT/PDF/QR/ICS 모두 제공
- 저장은 쓰기 가능한 경로에 자동 보존 (환경변수 `BLOODMAP_DATA_ROOT` → `/mnt/data` → `/tmp`)

## 2) 소아 진단 로그 (복구 + 표시 + 내보내기)

```python
from peds_dx_log import render_peds_dx_section
render_peds_dx_section(nick, uid)
```

동작:
- 다양한 과거 위치에서 **레거시 자동 복구**
- 최근 10건 표시 + 빠른 추가
- TXT/PDF 내보내기 (파일명에 **닉/UID** 포함)

## 설치

```
pip install qrcode[pil]  # QR 내보내기 사용 시
```

> `pdf_export.export_md_to_pdf`가 있으면 PDF 내보내기도 자동 활성화됩니다.
