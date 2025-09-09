# BloodMap utils shim pack
이 폴더의 파일들을 **레포 루트 기준** 아래 경로로 그대로 복사하세요.

```
bloodmap_app/
  __init__.py
  utils/
    __init__.py
    inputs.py
    interpret.py
    reports.py
    graphs.py
    schedule.py
```

그다음 Streamlit Cloud에서:
1) Manage app → Rerun (또는 Restart)
2) ...여전히 캐시가 남아 있으면 Clear cache도 눌러주세요.

이 쉼(Shim) 모듈은 최소 동작만 제공합니다. 이후 실제 구현 파일로 하나씩 교체하면 됩니다.
