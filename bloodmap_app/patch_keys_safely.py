# patch_keys_safely.py
# -*- coding: utf-8 -*-
"""
- key=_k("A", _k("B", _k("C"))) → key="A__B__C"
- st.number_input(...): min_value/step에 float(소수점) 있으면 value=0.0 보강(없을 때만)
- 저장은 app.patched.py로 (원본 보존)
- 적용 후 AST(문법) 확인
"""
import re, ast, sys
from pathlib import Path

SRC = Path("app.py")
if not SRC.exists():
    print("❌ app.py를 찾을 수 없습니다.")
    sys.exit(2)

orig = SRC.read_text(encoding="utf-8")

def _join_strs(inner: str):
    # 따옴표 안의 문자열들만 뽑아 "__"로 결합
    parts = re.findall(r'["\']([^"\']+)["\']', inner)
    return "__".join(parts) if parts else None

def _repl_key(m: re.Match):
    inner = m.group(1)
    joined = _join_strs(inner)
    return f'key="{joined}"' if joined else m.group(0)

# 1) key=_k(...) 어떤 중첩 형태든 단일 문자열로
text = re.sub(r'key\s*=\s*_k\(\s*(.*?)\s*\)', _repl_key, orig, flags=re.DOTALL)

# 2) number_input: float 파라미터면 value=0.0 보강
def _add_value_float(code: str) -> str:
    def repl(m: re.Match):
        call = m.group(1)
        if "value=" in call:
            return call
        if re.search(r'\b(min_value|step)\s*=\s*\d+\.\d+', call):
            return call[:-1] + ", value=0.0)"
        return call
    return re.sub(r'(st\.number_input\((?:[^)(]|\([^)(]*\))*\))', repl, code, flags=re.DOTALL)

text = _add_value_float(text)

DST = Path("app.patched.py")
DST.write_text(text, encoding="utf-8")

# 3) 문법 체크
try:
    ast.parse(text)
except SyntaxError as e:
    print(f"❌ 패치본 문법 오류: {e}")
    sys.exit(3)

print("✅ 패치 완료: app.patched.py 생성 (원본은 그대로)")
print("TIP) 배포 전: python feature_sentry.py 로 기능 보존 재확인하세요.")