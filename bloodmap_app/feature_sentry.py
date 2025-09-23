# feature_sentry.py
# -*- coding: utf-8 -*-
"""
배포 전 '기존 기능 보존' 자동 점검 (필수 누락 시 배포 차단):
- (필수) 닉네임/프로필
- (필수) PIN
- (필수) 구토
- (필수) 설사
- (필수) APAP
- (필수) IBU
- (필수) 그래프 외부저장: /mnt/data/bloodmap_graph + (json, .labs.csv) 저장 패턴
- (선택) care_log, profile 경로 존재

모든 .py 파일을 스캔하여 하나라도 포함되면 '존재'로 간주.
문법(AST) 검사 포함.
"""
import re, ast, sys
from pathlib import Path

ROOT = Path(".")
py_files = sorted([p for p in ROOT.rglob("*.py") if p.is_file()])

if not py_files:
    print("❌ 프로젝트 내 .py 파일을 찾을 수 없습니다.")
    sys.exit(2)

def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        try:
            return p.read_text(encoding="utf-8-sig")
        except Exception:
            return p.read_text(errors="ignore")

code_map = {str(p): read(p) for p in py_files}

# 1) 문법(AST) 검사: 각 파일별로 점검
for p, src in code_map.items():
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"❌ 문법 오류(AST 실패): {p}: {e}")
        sys.exit(3)

def found_any(pattern, flags=0):
    rgx = re.compile(pattern, flags)
    hit_files = [f for f, src in code_map.items() if rgx.search(src)]
    return (len(hit_files) > 0), hit_files

# 2) 필수 기능 플래그
checks_required = {
    "닉네임/프로필": r"(닉네임|별명|profile)",
    "PIN": r"\bPIN\b|pin_lock|pin",
    "구토": r"(구토|vomit)",
    "설사": r"(설사|diarrhea)",
    "APAP": r"(APAP|아세트아미노펜|acetaminophen|paracetamol)",
    "IBU": r"(\bIBU\b|이부프로펜|ibuprofen)",

    # 그래프 외부저장 (필수)
    "graph_dir": r"/mnt/data/bloodmap_graph",
    "graph_json": r"/mnt/data/bloodmap_graph[/\w\-\{\}\.]*\.json",
    "graph_labs_csv": r"/mnt/data/bloodmap_graph[/\w\-\{\}\.]*\.labs\.csv",
}

# (선택) 참고
checks_optional = {
    "care_log_dir(선택)": r"/mnt/data/care_log",
    "profile_dir(선택)": r"/mnt/data/profile",
}

missing = []
detail = {}

for name, pat in checks_required.items():
    ok, files = found_any(pat, flags=re.IGNORECASE)
    detail[name] = files
    if not ok:
        missing.append(name)

opt_missing = []
for name, pat in checks_optional.items():
    ok, files = found_any(pat, flags=re.IGNORECASE)
    detail[name] = files
    if not ok:
        opt_missing.append(name)

print("=== Feature Sentry Report ===")
for k, files in detail.items():
    if files:
        print(f"✔ {k}: {len(files)}개 파일에 존재")
        for f in files[:5]:
            print(f"   - {f}")
        if len(files) > 5:
            print(f"   ... (+{len(files)-5} more)")
    else:
        tag = "❌" if "(선택)" not in k else "⚠️"
        print(f"{tag} {k}: 발견 못함")

if missing:
    print("\n❌ 필수 항목 누락 → 배포 중단")
    print("누락 항목:", ", ".join(missing))
    sys.exit(4)

print("\n✅ 문법/기능 보존 점검 통과 (그래프 외부저장 포함)")
if opt_missing:
    print("ℹ️ 선택 항목 참고 누락:", ", ".join(opt_missing))
sys.exit(0)