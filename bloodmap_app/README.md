# Light Split Pack (Safe, Patch-First)

이 패키지는 **app.py를 얇게 유지**하면서, 기존 구현은 그대로 두고
새 모듈을 **래퍼(re-export)** 형태로 추가하는 가장 안전한 분리 세트입니다.
기존 기능을 삭제하지 않으며, 언제든 import만 원복하면 롤백 가능합니다.

## 포함 파일
- features/explainers.py : ui_results의 키워드 칩/스타일/예시를 재노출
- features/chemo_examples.py : 항암제 요약 예시 + MD 버전 재노출
- utils/db_access.py : DRUG_DB에서 부작용 텍스트를 합쳐주는 헬퍼
- (패키지 초기화) features/__init__.py, utils/__init__.py

## app.py에 추가할 것 (두 군데)
1) 상단 import 근처
```python
from features.explainers import ensure_keyword_explainer_style, render_keyword_explainers
from features.chemo_examples import render_chemo_summary_example
from utils.db_access import concat_ae_text
```

2) 항암제 부작용 렌더 **직후**
```python
ensure_keyword_explainer_style(st)                  # CSS 1회 주입(중복 호출 안전)
_ae_source_text = concat_ae_text(DRUG_DB, picked_keys)
render_keyword_explainers(st, _ae_source_text)      # “특정 단어 있을 때만” 칩 노출
render_chemo_summary_example(st)                    # 시연용 예시 블록
```