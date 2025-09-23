# server_hotfix.py
# -*- coding: utf-8 -*-
"""
배포 서버 경로의 app.py를 '부분 패치'로 즉시 치유:
- key=_k("A", _k("B"...)) 형태의 중첩 키 → 단일 문자열 key로 평탄화
- st.number_input에서 min_value/step이 float면, value=0.0 강제(없을 때만)
- (특정 라인 보정) 체온 입력 key를 안전 문자열로 치환
- 원본은 .bak로 백업, AST 문법 검사 후 적용
사용법 예시:
    python server_hotfix.py --path /mount/src/hoya12/bloodmap_app/app.py
"""
import re, ast, sys, argparse, shutil
from pathlib import Path

def patch_code(src: str) -> (str, dict):
    report = {"nested_key_collapses": 0, "float_value_injections": 0, "specific_fixes": 0}

    # 1) key=_k("AA", _k("BB"...)) 또는 key=_k("AA", key=_k("BB"...)) → key="AA__BB__..."
    def join_all_strings(inner: str):
        parts = re.findall(r'["\']([^"\']+)["\']', inner)
        return "__".join(parts) if parts else None

    def repl_nested_key(m: re.Match):
        inner = m.group(1)
        joined = join_all_strings(inner)
        if not joined:
            return m.group(0)
        report["nested_key_collapses"] += 1
        return f'key="{joined}"'

    code = re.sub(r'key\s*=\s*_k\(\s*(.*?)\s*\)', repl_nested_key, src, flags=re.DOTALL)

    # 2) number_input: float 파라미터면 value=0.0 보강(없을 때만)
    def add_value_float(match: re.Match):
        call = match.group(1)
        if "value=" in call:
            return call
        if re.search(r'\b(min_value|step)\s*=\s*\d+\.\d+', call):
            report["float_value_injections"] += 1
            return call[:-1] + ", value=0.0)"
        return call

    code = re.sub(r'(st\.number_input\((?:[^)(]|\([^)(]*\))*\))', add_value_float, code, flags=re.DOTALL)

    # 3) 특정 라인(체온 입력) 보정: 남아있다면 안전 키로 강제
    before = code
    code = re.sub(
        r'with\s+ctop\[1\]:\s*\n\s*temp\s*=\s*st\.number_input\([^)]*\)',
        'with ctop[1]:\n    temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key="peds_disease_temp__auto")',
        code, flags=re.DOTALL
    )
    code = re.sub(
        r'with\s+c5:\s*\n\s*temp\s*=\s*st\.number_input\([^)]*\)',
        'with c5:\n    temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key="daily_child_temp__adult__auto")',
        code, flags=re.DOTALL
    )
    if code != before:
        report["specific_fixes"] += 1

    return code, report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="배포 중 app.py 실제 경로 (예: /mount/src/.../app.py)")
    args = ap.parse_args()
    target = Path(args.path)
    if not target.exists():
        print(f"❌ 파일 없음: {target}")
        sys.exit(2)

    original = target.read_text(encoding="utf-8")
    patched, rep = patch_code(original)

    # 변경 없으면 안내만
    if patched == original:
        print("ℹ️ 변경 사항 없음(이미 패치되어 있을 수 있음). 문법만 검사합니다.")

    # 문법 검사
    try:
        ast.parse(patched)
    except SyntaxError as e:
        print(f"❌ 패치 결과 문법 오류: {e}")
        sys.exit(3)

    # 백업 후 쓰기
    backup = target.with_suffix(target.suffix + ".bak")
    shutil.copyfile(target, backup)
    target.write_text(patched, encoding="utf-8")

    print("✅ 패치 적용 완료")
    print(f"   백업: {backup}")
    print(f"   대상: {target}")
    print("   리포트:", rep)

if __name__ == "__main__":
    main()