
# -*- coding: utf-8 -*-
"""
sanity_check.py
Run: python sanity_check.py
Checks app.py for:
1) AST syntax validity
2) KST schedule block presence
3) No deprecated 'use_column_width'
4) Graph panel existence and unique widget keys (simple static scan)
"""

from pathlib import Path
import re, ast, sys, json

APP = "app.py"
text = Path(APP).read_text(encoding="utf-8")

report = {"file": APP, "ok": True, "issues": []}

# 1) AST parse
try:
    ast.parse(text)
except SyntaxError as e:
    report["ok"] = False
    report["issues"].append({"type":"syntax", "line": e.lineno, "msg": str(e)})

# 2) KST schedule block
if '해열제 스케줄(KST' not in text or '시작시간(한국시간)' not in text or '≥ 6시간' not in text:
    report["ok"] = False
    report["issues"].append({"type":"schedule", "msg":"KST 스케줄러 문구/간격 안내가 누락된 것 같습니다."})

# 3) Deprecated image arg
if 'use_column_width=' in text:
    report["ok"] = False
    report["issues"].append({"type":"deprecated", "msg":"use_column_width 사용 감지 → use_container_width 로 교체 필요"})

# 4) Graph panel function and keys
if 'def render_graph_panel()' not in text:
    report["ok"] = False
    report["issues"].append({"type":"graph", "msg":"render_graph_panel() 없음"})
if 'with t_graph:' not in text:
    report["ok"] = False
    report["issues"].append({"type":"graph", "msg":"with t_graph: 블록 없음"})

# 4-1) naive duplicate widget key scan (key=wkey("..."))
keys = re.findall(r'key\s*=\s*wkey\("([^"]+)"\)', text)
dups = {}
for k in keys:
    dups[k] = dups.get(k, 0) + 1
dup_list = [k for k,c in dups.items() if c > 1]
# It's okay to intentionally reuse keys for same widget in same place, but frequent cause of Streamlit errors.
if dup_list:
    report["issues"].append({"type":"keys", "msg":"중복 가능성이 있는 key 감지", "keys": dup_list[:50]})
    # If they appear more than 2 times, flag as likely problematic
    if any(dups[k] > 2 for k in dup_list):
        report["ok"] = False

print(json.dumps(report, ensure_ascii=False, indent=2))
if not report["ok"]:
    sys.exit(1)
