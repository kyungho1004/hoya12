피수치 홈페이지 — 통합 주입 패키지 (Unified Injection)
생성: 2025-09-22 08:55 KST

한 줄 적용:
    unzip BM_unified_inject.zip
    python inject_unified.py               # 같은 폴더의 app.py 대상으로
  또는
    python inject_unified.py /path/to/app.py

포함 파일:
  - inject_unified.py        : 이 한 파일로 백업→패치→교체까지 자동 수행
  - apply_patch_po_p1.py     : 패처 본체 (idempotent)
  - peds_age_refs.py         : 연령(개월/세) 기준치 테이블/평가
  - safety_gate.py           : Medication Safety Gate
  - backup_utils.py          : 스냅샷 백업/복구 UI

적용 후 즉시 확인:
  [암 모드] '연령 기준치 평가' 리스트 (🟩/🟨 + ref)
  [소아] '🌡 해열제 1회분(평균)' 아래 Safety Gate 경고/차단(🚫/⚠️/✅)
  [사이드바] 👤 프로필 / 🧷 백업·복구
  [내보내기] 연령 기준치 평가 + Safety Gate 요약 + 24h 케어로그