# qa_precheck.py — QA 스모크 체크 자동화 (패치 방식, 비파괴)
from __future__ import annotations
from pathlib import Path
import ast, re, datetime

REPORT_PATH = Path("/mnt/data/PRECHECK_REPORT.txt")

# 기본 스캔 대상(존재하는 것만 검사)
DEFAULT_FILES = [
    "/mnt/data/app.py",
    "/mnt/data/core_utils.py",
    "/mnt/data/ui_results.py",
    "/mnt/data/peds_guide.py",
    "/mnt/data/peds_dose.py",
    "/mnt/data/pdf_export.py",
    "/mnt/data/guards_smoke.py",
    "/mnt/data/branding.py",
    "/mnt/data/drug_db.py",
    "/mnt/data/pages_peds.py",
]

def _exists(p: str) -> bool:
    try:
        return Path(p).exists()
    except Exception:
        return False

def _read(p: str) -> str:
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""

def check_ast(files: list[str]) -> list[tuple[str, str]]:
    """(file, status) with 'OK' or 'SyntaxError: ...'"""
    out = []
    for f in files:
        if not _exists(f):
            out.append((f, "SKIP (missing)"))
            continue
        src = _read(f)
        try:
            ast.parse(src)
            out.append((f, "OK"))
        except SyntaxError as e:
            out.append((f, f"SyntaxError: line {e.lineno} {e.msg}"))
        except Exception as e:
            out.append((f, f"Error: {type(e).__name__}: {e}"))
    return out

_KEY_RE = re.compile(r"""key\s*=\s*(['"])(?P<k>.+?)\1""", re.S)

def check_widget_keys(files: list[str]) -> dict:
    """Heuristic scan for duplicated Streamlit keys."""
    keys = {}
    dups = {}
    for f in files:
        if not _exists(f):
            continue
        text = _read(f)
        for m in _KEY_RE.finditer(text):
            k = m.group("k").strip()
            if not k:
                continue
            keys.setdefault(k, []).append(f)
    for k, locs in keys.items():
        if len(locs) > 1:
            dups[k] = locs
    return {"total_keys": len(keys), "duplicates": dups}

def check_feature_markers() -> dict:
    """필수 기능 누락 점검 (마커 기반, 비침습)."""
    markers = {
        "eGFR": [
            r"eGFR", r"CKD[- ]?EPI", r"st\.metric\(.*eGFR"
        ],
        "graph_external_save": [
            r"/mnt/data/bloodmap_graph", r"\.to_csv\(", r"\.json"
        ],
        "ER_PDF": [
            r"pdf_export", r"export_er_pdf", r"\.pdf"
        ],
        "carelog_guardrails": [
            r"care_log", r"APAP", r"IBU", r"쿨다운", r"24h", r"24\s*시간", r">=\s*4", r">=\s*6"
        ],
    }
    files = [f for f in DEFAULT_FILES if _exists(f)]
    res = {}
    for name, pats in markers.items():
        found_any = False
        found_where = set()
        for f in files:
            text = _read(f)
            for pat in pats:
                if re.search(pat, text, flags=re.I):
                    found_any = True
                    found_where.add(Path(f).name)
        res[name] = {
            "ok": bool(found_any),
            "files": sorted(found_where)
        }
    return res

def run(files: list[str] | None = None, report_path: str | None = None) -> str:
    files = files or DEFAULT_FILES
    rpt = Path(report_path) if report_path else REPORT_PATH

    ts = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # KST
    lines = []
    lines.append(f"# PRECHECK REPORT (KST) — {ts.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1) AST
    lines.append("## 1) Syntax (ast.parse)\n")
    for f, status in check_ast(files):
        lines.append(f"- {f}: {status}")
    lines.append("")

    # 2) Widget key duplicates
    lines.append("## 2) Streamlit widget keys\n")
    kinfo = check_widget_keys(files)
    lines.append(f"- total_keys: {kinfo['total_keys']}")
    dups = kinfo["duplicates"]
    if dups:
        lines.append("- duplicates:")
        for k, locs in sorted(dups.items()):
            uniq = sorted(set(locs))
            lines.append(f"  - '{k}': used in {uniq}")
    else:
        lines.append("- duplicates: NONE")
    lines.append("")

    # 3) Required feature markers
    lines.append("## 3) Required features presence\n")
    feats = check_feature_markers()
    for name, info in feats.items():
        status = "OK" if info["ok"] else "MISSING"
        where = ", ".join(info["files"]) if info["files"] else "-"
        lines.append(f"- {name}: {status} (found in: {where})")

    content = "\n".join(lines).strip() + "\n"
    try:
        rpt.write_text(content, encoding="utf-8")
    except Exception:
        try:
            Path("PRECHECK_REPORT.txt").write_text(content, encoding="utf-8")
        except Exception:
            pass
    return content

if __name__ == "__main__":
    print(run())
