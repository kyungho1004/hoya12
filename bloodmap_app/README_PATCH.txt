# bloodmap_metrics_permfix_patch

이 패치는 `FileNotFoundError`/`PermissionError`로 **방문자 통계 파일**을 못 쓰는 문제를 해결합니다.

## 적용 방법 (app.py에 3줄 교체)

1) **상단 import 근처**에 추가:
```python
from pathsafe import resolve_data_dirs, safe_json_read, safe_json_write
```

2) 기존 경로 상수 정의 부분을 **아래로 교체**:
```python
SAVE_DIR, CARE_DIR, PROF_DIR, MET_DIR = resolve_data_dirs()
```

3) 방문자 통계 저장 코드에서 `json.dump(... open(met_path,"w") ...)` 를 **아래로 교체**:
```python
D = safe_json_read(met_path, {"unique": [], "visits": []})
# ... D 업데이트 후
safe_json_write(met_path, D)
```

> 배포 환경이 `/mnt/data`에 쓰기 불가하더라도, 이 패치는 자동으로 쓰기 가능한 폴더를 선택합니다.
> (우선순위: `BLOODMAP_DATA_DIR` → /mnt/data → /mount/data → ~/.local/share/bloodmap → ./data → 시스템 임시폴더)

## 옵션
- 특정 폴더를 강제하려면 환경변수 `BLOODMAP_DATA_DIR=/mount/data` 처럼 지정하세요.