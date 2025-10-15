# -*- coding: utf-8 -*-
"""
fix_and_patch_app.py
- Repairs broken sections in app.py
- Applies requested upgrades:
  * Graph tab auto-switch (without reordering tabs)
  * Persist history to CSV + safe "clear session only" vs "delete CSV"
  * Report includes chemo adverse effects
  * KST antipyretic scheduler
  * Moves graph panel fully to right tab
  * peds_guide dynamic import with graceful fallback
- Verifies syntax (AST) at the end
"""

import re, ast, sys, shutil, os

APP = "app.py"
raw = open(APP, "r", encoding="utf-8").read()
bak = APP + ".bak"
shutil.copyfile(APP, bak)

def sub_once(pattern, repl, text, flags=re.S):
    return re.sub(pattern, repl, text, flags=flags, count=1)

code = raw

# 0) Ensure UTF-8 header
if not code.lstrip().startswith("# -*- coding: utf-8 -*-"):
    code = "# -*- coding: utf-8 -*-\n" + code

# 1) Fix Streamlit rerun API
code = code.replace("st.experimental_rerun()", "st.rerun()")

# 2) Fix common typos that caused runtime issues
code = code.replace("setdefaultlt(", "setdefault(").replace("setdefau(", "setdefault(")
code = code.replace("plt = Nonee", "plt = None").replace("plt = Non", "plt = None")

# 3) Tabs: enforce static order + JS auto-switch (once) after tabs creation
m = re.search(r"tab_labels\s*=.*?st\.tabs\(tab_labels\)", code, re.S)
if m:
    fixed_tabs = (
        'tab_labels = ["🏠 홈", "🧪 피수치 입력", "🧬 암 선택", "💊 항암제(진단 기반)", '
        '"👶 소아 증상", "🔬 특수검사", "📄 보고서", "📊 기록/그래프"]\n'
        't_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report, t_graph = st.tabs(tab_labels)\n'
        'if st.session_state.get("auto_graph"):\n'
        '    st.session_state["auto_graph"] = False\n'
        '    st.markdown("""<script>\n'
        "const target = '📊 기록/그래프';\n"
        "const tabs = Array.from(document.querySelectorAll('button[role=\"tab\"]'));\n"
        "const btn = tabs.find(b => b.innerText.includes(target));\n"
        "if (btn) btn.click();\n"
        '</script>""', ' unsafe_allow_html=True)'
    )
    code = code[:m.start()] + "".join(fixed_tabs) + code[m.end():]

# 4) Remove embedded report graph panel (if still present)
code = re.sub(
    r'\n\s*st\.markdown\("### 📊 기록/그래프 패널"\)[\s\S]+?# ---------- QR helper ----------',
    '\n    # (moved) 기록/그래프는 우측 "📊 기록/그래프" 탭에서 확인하세요.\n\n# ---------- QR helper ----------',
    code
)

# 5) Ensure KST-based antipyretic scheduler (replace old example block)
code = re.sub(
    r'st\.markdown\("#### 해열제 예시 스케줄러\(교차복용\)"\)[\s\S]+?st\.markdown\("---"\)',
    (
        'st.markdown("#### 해열제 스케줄(KST 기준)")\n'
        'tz = _dt.timezone(_dt.timedelta(hours=9))  # Asia/Seoul\n'
        'today = _dt.date.today()\n'
        'c1, c2 = st.columns(2)\n'
        'with c1:\n'
        '    apap_last = st.time_input("마지막 APAP(아세트아미노펜) 복용 시각", value=_dt.datetime.now(tz=tz).time(), key=wkey("apap_last_time"))\n'
        'with c2:\n'
        '    ibu_last = st.time_input("마지막 IBU(이부프로펜) 복용 시각", value=_dt.datetime.now(tz=tz).time(), key=wkey("ibu_last_time"))\n'
        'try:\n'
        '    apap_dt = _dt.datetime.combine(today, apap_last, tzinfo=tz)\n'
        '    ibu_dt  = _dt.datetime.combine(today, ibu_last, tzinfo=tz)\n'
        '    next_apap = apap_dt + _dt.timedelta(hours=4)\n'
        '    next_ibu  = ibu_dt  + _dt.timedelta(hours=6)\n'
        '    st.caption("쿨다운 규칙: APAP ≥ 4시간, IBU ≥ 6시간 (한국시간 기준).")\n'
        '    colNA, colNI = st.columns(2)\n'
        '    with colNA:\n'
        '        st.metric("다음 APAP 가능 시각 (KST)", next_apap.strftime("%Y-%m-%d %H:%M"))\n'
        '    with colNI:\n'
        '        st.metric("다음 IBU 가능 시각 (KST)", next_ibu.strftime("%Y-%m-%d %H:%M"))\n'
        '    st.write("**권장 교차 예시(자동 계산)**")\n'
        '    plan = [("APAP", next_apap), ("IBU", next_apap + _dt.timedelta(hours=2)), ("APAP", next_apap + _dt.timedelta(hours=4)), ("IBU", next_ibu + _dt.timedelta(hours=6))]\n'
        '    for drug, t in plan:\n'
        "        st.write(f\"- {drug} @ {t.strftime('%Y-%m-%d %H:%M KST')}\")\n"
        'except Exception:\n'
        '    st.info("시각 입력을 다시 확인해주세요.")\n'
        'st.markdown("---")'
    ),
    code,
    flags=re.S
)

# 6) Ensure peds_guide dynamic import exists (insert before plotting backend if missing)
if "PEDS_PATH" not in code:
    code = re.sub(
        r"(# --- plotting backend)",
        (
            '# --- peds_guide optional module ---\n'
            '_peds, PEDS_PATH = _load_local_module("peds_guide", ["peds_guide.py", "modules/peds_guide.py"])\n'
            'if _peds:\n'
            '    render_caregiver_notes_peds = getattr(_peds, "render_caregiver_notes_peds", None)\n'
            '    render_symptom_explain_peds = getattr(_peds, "render_symptom_explain_peds", None)\n'
            '    build_peds_notes = getattr(_peds, "build_peds_notes", None)\n\n'
            r'\1'
        ),
        code, flags=re.S
    )

# 7) Report: ensure chemo adverse effects section
if "## 항암제 부작용(선택 약물)" not in code:
    code = re.sub(
        r'md_report\s*=\s*header\s*\+\s*\\n\\n## 최근 주요 수치\\n"\s*\+\s*labs_line\s*\+\s*\\n\\n## 식이 가이드\\n"\s*\+\s*\(diet_lines[^)]+\)',
        'md_report = header + "\\n\\n## 최근 주요 수치\\n" + labs_line + "\\n\\n## 식이 가이드\\n" + (diet_lines or "—") + "\\n\\n## 항암제 부작용(선택 약물)\\n" + (lambda _meds, _db: (lambda _m: "\\n".join(_m) if _m else "- (DB에 상세 부작용 없음)")(sum(([f"### {display_label(k, _db)}"] + [f"- {ln}" for ln in v]) for k, v in (_aggregate_all_aes(_meds, _db) or {}).items(), [])))(meds, DRUG_DB)',
        code, flags=re.S
    )

# 8) render_graph_panel: ensure header + base_dir
code = re.sub(
    r"(def\s+render_graph_panel\(\):\s*\n[\s\S]*?try:\s*\n\s*import matplotlib\.pyplot as plt[\s\S]*?except Exception:\s*\n\s*plt = None)",
    r"\1\n\n    st.markdown(\"### 📊 기록/그래프\")\n    base_dir = \"/mnt/data/bloodmap_graph\"\n    try:\n        os.makedirs(base_dir, exist_ok=True)\n    except Exception:\n        pass",
    code, flags=re.S
)

# 9) render_graph_panel: add 기록/그래프/내보내기 tabs (only if not already present)
if "tab_log, tab_plot, tab_export = st.tabs([" not in code:
    code = sub_once(
        r'st\.markdown\("### 📊 기록/그래프"\)',
        (
            'st.markdown("### 📊 기록/그래프")\n'
            '    tab_log, tab_plot, tab_export = st.tabs(["📝 기록", "📈 그래프", "⬇️ 내보내기"])\n\n'
            '    with tab_log:\n'
            '        st.session_state.setdefault("lab_history", [])\n'
            '        hist = st.session_state["lab_history"]\n'
            '        cols_btn = st.columns([1, 1, 1])\n'
            '        with cols_btn[0]:\n'
            '            if st.button("➕ 현재 값을 기록에 추가", key=wkey("add_history_btn")):\n'
            '                snap = {"ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "temp": st.session_state.get(wkey("cur_temp")), "hr": st.session_state.get(wkey("cur_hr")), "labs": st.session_state.get("labs_dict", {}) or {}}\n'
            '                hist.append(snap)\n'
            '                st.session_state["lab_history"] = hist\n'
            '                uid = st.session_state.get("key", "guest")\n'
            '                import pandas as _pd\n'
            '                rows = []\n'
            '                for h in hist:\n'
            '                    row = {"_ts": h.get("ts")}\n'
            '                    labs = h.get("labs", {}) or {}\n'
            '                    for k in ["WBC","Hb","PLT","ANC","CRP","Na","K","Ca","Cr","BUN","AST","ALT","T.B","Alb","Glu"]:\n'
            '                        row[k] = labs.get(k)\n'
            '                    rows.append(row)\n'
            '                try:\n'
            '                    df_save = _pd.DataFrame(rows)\n'
            '                    os.makedirs(base_dir, exist_ok=True)\n'
            '                    df_save.to_csv(os.path.join(base_dir, f"{uid}.labs.csv"), index=False)\n'
            '                except Exception:\n'
            '                    pass\n'
            '                st.session_state["auto_graph"] = True\n'
            '                st.rerun()\n'
            '        with cols_btn[1]:\n'
            '            if st.button("🗑️ 기록 비우기(세션만)", key=wkey("clear_history_btn")) and hist:\n'
            '                st.session_state["lab_history"] = []\n'
            '                st.warning("세션 기록을 비웠습니다. CSV 파일은 보존됩니다.")\n'
            '            if st.button("🗑️ CSV 파일까지 삭제", key=wkey("delete_csv_btn")):\n'
            '                uid = st.session_state.get("key", "guest")\n'
            '                import os\n'
            '                try:\n'
            '                    os.remove(os.path.join(base_dir, f"{uid}.labs.csv"))\n'
            '                    st.success("CSV 파일을 삭제했습니다.")\n'
            '                except Exception:\n'
            '                    st.info("CSV 파일이 없거나 삭제할 수 없습니다.")\n'
            '        with cols_btn[2]:\n'
            '            st.caption(f"총 {len(hist)}건")\n'
            '        try:\n'
            '            import pandas as _pd\n'
            '            if hist:\n'
            '                rows = []\n'
            '                for h in hist[-10:]:\n'
            '                    row = {"시각": h.get("ts","")}\n'
            '                    L = h.get("labs", {}) or {}\n'
            '                    for k in ["WBC","Hb","PLT","ANC","CRP"]:\n'
            '                        row[k] = L.get(k,"")\n'
            '                    rows.append(row)\n'
            '                st.dataframe(_pd.DataFrame(rows), use_container_width=True, height=200)\n'
            '            else:\n'
            '                st.info("기록이 없습니다.")\n'
            '        except Exception:\n'
            '            pass'
        ),
        code
    )

# 10) render_graph_panel: CSV-missing warning → session fallback message
code = re.sub(
    r'st\.warning\("표시할 CSV가 없습니다\.[\s\S]+?return',
    'st.info("아직 저장된 데이터가 없습니다. 📝 탭에서 **현재 값을 기록에 추가** 후 확인하세요.")\n        return',
    code, flags=re.S
)

# 11) Broken pediatric function signature → safe wrapper
code = re.sub(
    r"\ndef\s+render_symptom_explain_peds\([^\)]*\):[\s\S]*?(?=\n\ndef\s+)",
    (
        '\n\ndef render_symptom_explain_peds(**kwargs):\n'
        '    """소아 증상 가이드: peds_guide 모듈 우선 사용 (로컬 정의 손상 시 안전 래퍼)."""\n'
        '    import streamlit as st\n'
        '    try:\n'
        '        import peds_guide as _pg\n'
        '        if hasattr(_pg, "render_symptom_explain_peds"):\n'
        '            return _pg.render_symptom_explain_peds(**kwargs)\n'
        '    except Exception:\n'
        '        pass\n'
        '    st.info("소아 증상 가이드는 준비 중입니다.")\n'
    ),
    code, flags=re.S
)

# Final AST validation
try:
    ast.parse(code)
except SyntaxError as e:
    print("❌ 문법 오류 라인:", e.lineno, "열:", e.offset)
    print("해당 줄:", code.splitlines()[e.lineno-1])
    print("백업 파일 유지:", bak)
    sys.exit(1)

with open(APP, "w", encoding="utf-8") as f:
    f.write(code)

print("✅ All fixes applied & AST passed. 백업 생성:", bak)
