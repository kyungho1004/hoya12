# BloodMap — 3패키지 통합 패치 (bundle V1)

## 포함 파일
- `interactions.py` — 상호작용/금기 룰 엔진(암 모드)
- `bundle_addons.py` — 해열제 24시간 시간표 카드, 증상 일지 카드, 톤 프리셋, 보고서 블록
- `pdf_export.py` — QR 코드 포함 PDF 변환 (교체용)
- `README_bundle.md` — 설치/적용 가이드

## 의존성
`requirements.txt`에 아래 2줄 추가 후 설치:
```
qrcode[pil]>=7.4
pillow>=10.0
```
(ReportLab은 기존 requirements에 있다고 가정)

## 적용 순서 (요약)
1) 위 3개 파이썬 파일을 프로젝트 루트에 복사(기존 `pdf_export.py`는 덮어쓰기).
2) `requirements.txt` 업데이트 및 설치.
3) `app.py`에 아래 패치 스니펫을 검색 붙여넣기.

## app.py 패치 요점
- **import 추가**
```python
from bundle_addons import (
    ui_sidebar_settings, toneize_line, toneize_lines,
    ui_antipyretic_card, ui_symptom_diary_card,
    render_interactions_box, md_block_antipy_schedule, md_block_diary,
)
from interactions import compute_interactions
```

- **사이드바 톤 프리셋 호출**
```python
ui_sidebar_settings()
```

- **암 모드: 기타 복용 약 입력**
```python
other_meds_text = st.text_input("기타 복용 약 (자유 입력)", placeholder="예: 타이레놀, 플루옥세틴, 나프록센 등")
```

- **소아/일상 입력 하단: 카드 2종**
```python
sched_today = ui_antipyretic_card(age_m, weight or None, temp, key)
diary_df = ui_symptom_diary_card(key)
```

- **암 모드 결과 상단: 상호작용/금기 박스 + 보고서 요약**
```python
sel_drugs = (_filter_known(ctx.get("user_chemo"))) + (_filter_known(ctx.get("user_abx"))) + (_filter_known(ctx.get("user_targeted")))
warn_lines = render_interactions_box(sel_drugs, ctx.get("labs", {}), ctx.get("other_meds_text"))
```

- **보고서에 시간표/일지/QR 자동 포함**
```python
extra_blocks = []
extra_blocks.extend([("🕒 해열제 시간표", md_block_antipy_schedule(sched_today))])
extra_blocks.extend([("📈 증상 일지(오늘/최근7일 요약)", md_block_diary(diary_df))])
md += "\n\n[[QR:https://cafe.naver.com/bloodmap]]\n"
```

## 체크리스트
- 해열제 카드: 스케줄 생성/복사/저장, “이미 먹었어요” 즉시 반영
- 상호작용: 6‑MP×알로푸리놀, MTX×NSAIDs/신기능, linezolid×SSRI, ATO×QT·저K/저Mg
- 증상 일지: 라인/막대 미니차트, JSON 내보내기/불러오기(PIN 해시 포함은 앱 쪽 로직 연동 시)
- 보고서: 시간표/일지/상호작용 요약/QR 포함
- 톤 프리셋: 기본/더-친절/초-간결 즉시 반영
```
