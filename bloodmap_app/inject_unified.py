#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 주입 스크립트 (Unified Injector)
- 현재 디렉토리의 app.py를 백업 후, Po‑P1 기능(연령기준/게이트/백업UI) 주입
사용:
    python inject_unified.py            # app.py 대상
    python inject_unified.py path/to/app.py
요구 파일(같은 폴더): apply_patch_po_p1.py, peds_age_refs.py, safety_gate.py, backup_utils.py
"""
import sys, shutil, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("app.py")
    if not target.exists():
        print(f"[오류] 대상 파일이 없습니다: {target}")
        sys.exit(1)

    # 필수 모듈 체크
    needed = ["apply_patch_po_p1.py","peds_age_refs.py","safety_gate.py","backup_utils.py"]
    for n in needed:
        if not Path(n).exists():
            print(f"[오류] 현재 폴더에 {n} 가 필요합니다.")
            sys.exit(2)

    # 백업
    KST = timezone(timedelta(hours=9))
    stamp = datetime.now(KST).strftime("%Y%m%d_%H%M")
    backup = target.with_suffix(target.suffix + f".bak_{stamp}")
    shutil.copy2(target, backup)
    print(f"[백업] {backup.name} 생성")

    # 패치 실행
    patched = target.with_name(target.stem + "_patched" + target.suffix)
    cmd = [sys.executable, "apply_patch_po_p1.py", str(target)]
    out = subprocess.check_output(cmd)
    patched.write_bytes(out)
    print(f"[패치] {patched.name} 생성")

    # 교체
    shutil.move(str(patched), str(target))
    print(f"[적용] app.py 교체 완료")

    print("\n✅ 완료! 앱을 재시작하고 다음을 확인하세요:")
    print(" - 암 모드: '연령 기준치 평가' 표시")
    print(" - 소아 해열제: Safety Gate(🚫/⚠️/✅) 표시")
    print(" - 사이드바: 👤 프로필 / 🧷 백업·복구")
    print(" - 내보내기: 연령 기준치 평가 + Safety Gate 요약 포함")

if __name__ == "__main__":
    main()