# -*- coding: utf-8 -*-
# === Standalone app.py: no dependency on utils/app_utils for critical bits ===
import os, sys, importlib
PKG_DIR = os.path.dirname(__file__)
PKG_NAME = os.path.basename(PKG_DIR)
PARENT_DIR = os.path.dirname(PKG_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def _imp(mod):
    return importlib.import_module(f"{PKG_NAME}.{mod}")

# Import package modules
cfg = _imp("config")
store = _imp("storage")
hp = _imp("helpers")
ctr = _imp("counter")
drug_data = _imp("drug_data")

# Re-export the names used below
APP_TITLE = cfg.APP_TITLE
PAGE_TITLE = cfg.PAGE_TITLE
MADE_BY = cfg.MADE_BY
CAFE_LINK_MD = cfg.CAFE_LINK_MD
FOOTER_CAFE = cfg.FOOTER_CAFE
DISCLAIMER = cfg.DISCLAIMER
ORDER = cfg.ORDER
FEVER_GUIDE = cfg.FEVER_GUIDE
get_user_key, load_session, append_history = store.get_user_key, store.load_session, store.append_history
compute_acr, compute_upcr = hp.compute_acr, hp.compute_upcr
interpret_acr, interpret_upcr = hp.interpret_acr, hp.interpret_upcr
interpret_ast, interpret_alt = hp.interpret_ast, hp.interpret_alt
interpret_na, interpret_k, interpret_ca = hp.interpret_na, hp.interpret_k, hp.interpret_ca
pediatric_guides = hp.pediatric_guides
build_report_md, build_report_txt, build_report_pdf_bytes = hp.build_report_md, hp.build_report_txt, hp.build_report_pdf_bytes
bump, count = ctr.bump, ctr.count

# --- Inline versions to avoid utils/app_utils conflicts ---
def user_key(nickname: str, pin: str) -> str:
    pin = (pin or "").strip()
    if len(pin) != 4 or not pin.isdigit():
        return ""
    nickname = (nickname or "").strip()
    return f"{nickname}#{pin}" if nickname else ""

def init_state(st=None):
    try:
        import streamlit as st_mod
    except Exception:
        return
    S = st_mod.session_state
    if "onco_prev_key" not in S: S["onco_prev_key"] = ""
    if "onco_selected" not in S: S["onco_selected"] = []

import streamlit as st
import pandas as pd
import datetime

# --- Cancer dictionaries (보호자 눈높이 샘플) ---
ONCO_CATEGORIES = ["혈액암", "림프종", "고형암", "육종", "희귀암"]

BLOOD_CANCERS = {
    "APL": ["베사노이드(트레티노인, ATRA)", "As2O3(아르세닉 트리옥사이드)", "6-MP(6-머캅토퓨린)", "MTX(메토트렉세이트)"],
    "ALL": ["6-MP", "MTX", "빈크리스틴", "덱사메타손"],
    "AML": ["시타라빈(ARA-C)", "다우노루비신/이다루비신"],
    "CML": ["이미티닙", "닐로티닙", "다사티닙"],
    "CLL": ["벤다무스틴", "리툭시맙"],
}

LYMPHOMA = {
    "B거대세포": ["R-CHOP(리툭시맙+CHOP)", "폴라투주맙", "브렌툭시맙(선택)"],
    "호지킨": ["ABVD", "브렌툭시맙 베도틴"],
}

SARCOMA = {
    "골육종": ["고용량 MTX", "도소루비신", "시스플라틴"],
    "유잉육종": ["VAC/IE", "이리노테칸(선택)"],
    "횡문근육종": ["빈크리스틴", "엑티노마이신", "사이클로포스파미드"],
}

RARE = {
    "GIST": ["이미티닙", "수니티닙", "리프레티닙"],
    "HLH(증후군)": ["덱사메타손", "에토포사이드"],
}

SOLID_OPTIONS = list(getattr(drug_data, "solid_targeted", {}).keys())

ABX_SIMPLE = {
    "세페핌": "광범위 베타락탐 — 발열 중성구감소증 1차 약제로 자주 사용.",
    "피페라실린/타조박탐": "그람+/그람-/혐기균 커버 — 복합감염에 널리 사용.",
    "메로페넴": "광범위 카바페넴 — 다제내성 위험 시 고려.",
    "반코마이신": "MRSA 등 그람+ 커버 — 신장기능/혈중농도 모니터.",
    "레보플록사신": "경구 가능 — QT연장/건병증 주의.",
}

def _css():
    try:
        st.markdown('<style>' + (open(os.path.join(PKG_DIR, "style.css"), "r", encoding="utf-8").read()) + '</style>', unsafe_allow_html=True)
    except Exception:
        pass

def _header():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered", page_icon="🩸")
    st.title(APP_TITLE)
    st.caption(MADE_BY + " · " + CAFE_LINK_MD)

def _fever_dose(weight_kg: float):
    if not weight_kg or weight_kg <= 0:
        return {}
    ac_min = round(weight_kg * 10)  # mg
    ac_max = round(weight_kg * 15)  # mg
    ibu = round(weight_kg * 10)     # mg
    return {
        "아세트아미노펜 1회": f"{ac_min}~{ac_max} mg (4~6시간 간격, 최대 5회/일)",
        "이부프로펜 1회": f"{ibu} mg (6~8시간 간격, 최대 4회/일)",
        "체온 가이드": FEVER_GUIDE
    }

def _food_suggestions(vals: dict) -> list:
    out = []
    alb = float(vals.get("Albumin(알부민)") or 0)
    k = float(vals.get("K(포타슘)") or 0)
    hb = float(vals.get("Hb(혈색소)") or 0)
    na = float(vals.get("Na(소디움)") or 0)
    ca = float(vals.get("Ca(칼슘)") or 0)
    if alb and alb < 3.5:
        out.append("알부민 낮음: 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽")
    if k and k < 3.5:
        out.append("칼륨 낮음: 바나나, 감자, 호박죽, 고구마, 오렌지")
    if hb and hb < 10:
        out.append("Hb 낮음: 소고기, 시금치, 두부, 달걀 노른자, 렌틸콩")
    if na and na < 135:
        out.append("나트륨 낮음: 전해질 음료, 미역국, 바나나, 오트밀죽, 삶은 감자")
    if ca and ca < 8.5:
        out.append("칼슘 낮음: 연어통조림, 두부, 케일, 브로콜리, (참깨 제외)")
    return out

def _interpret_core(vals: dict) -> list:
    msg = []
    for key, val in vals.items():
        if val in ("", None): continue
        if key.startswith("AST"):
            msg.append(("warn" if float(val)>80 else "ok", f"AST: {interpret_ast(float(val))}"))
        if key.startswith("ALT"):
            msg.append(("warn" if float(val)>80 else "ok", f"ALT: {interpret_alt(float(val))}"))
        if key.startswith("Na"):
            v=float(val); lev = "danger" if v<130 or v>150 else ("warn" if v<135 or v>145 else "ok")
            msg.append((lev, interpret_na(v)))
        if key.startswith("K("):
            v=float(val); lev = "danger" if v<3.0 or v>6.0 else ("warn" if v<3.5 or v>5.5 else "ok")
            msg.append((lev, interpret_k(v)))
        if key.startswith("Ca("):
            v=float(val); lev = "danger" if v<8.0 or v>11.5 else ("warn" if v<8.5 or v>10.5 else "ok")
            msg.append((lev, interpret_ca(v)))
    return msg

def _qual_interpret(qvals: dict) -> list:
    out = []
    for k,v in qvals.items():
        if not v or v=="-": continue
        if "단백뇨" in k:
            out.append(("danger" if v=="＋＋＋" else "warn", f"{k} {v} → 🚨 신장 기능 이상 가능성"))
        elif k in ("혈뇨","요당","잠혈"):
            out.append(("warn", f"{k} {v} → 추가 검사 권장"))
        else:
            out.append(("ok", f"{k} {v}"))
    return out

def _colored(line):
    level, text = line
    if level=="danger": return f"🟥 **{text}**"
    if level=="warn": return f"🟡 {text}"
    return f"🟢 {text}"

def main():
    bump()
    _header()
    _css()
    init_state()

    st.sidebar.subheader("사용자 식별 (별명 + 4자리 PIN)")
    alias = st.sidebar.text_input("별명", max_chars=20, placeholder="예: Hoya")
    pin = st.sidebar.text_input("PIN (4자리)", max_chars=4, type="password")
    key = user_key(alias, pin)
    if not key:
        st.warning("별명과 4자리 PIN을 모두 입력하세요. (예: Hoya · 1234)")

    mode = st.radio("진단 모드", ["소아 일상/질환 모드", "암 진단 모드"], horizontal=True)

    if mode == "소아 일상/질환 모드":
        st.markdown("### 소아 발열/감염")
        col1,col2,col3 = st.columns(3)
        with col1:
            weight = st.number_input("체중 (kg)", min_value=0.0, step=0.1)
        with col2:
            temp = st.number_input("현재 체온 (℃)", min_value=34.0, max_value=42.5, step=0.1)
        with col3:
            show_labs = st.checkbox("피수치 입력란 표시", value=False)

        if weight:
            st.markdown("**해열제 자동 계산**")
            for k,v in _fever_dose(weight).items():
                st.info(f"- {k}: {v}")

        vals = {}
        if show_labs:
            st.markdown("### 주요 혈액 수치")
            for label in ORDER:
                vals[label] = st.number_input(label, value=None, step=0.1, format="%.2f")

        st.markdown("### 특수검사")
        qcols = st.columns(4)
        qvals = {}
        ops = ["-","＋","＋＋","＋＋＋"]
        qvals["단백뇨"] = qcols[0].selectbox("단백뇨 (+)", ops, index=0)
        qvals["혈뇨"] = qcols[1].selectbox("혈뇨 (+)", ops, index=0)
        qvals["요당"] = qcols[2].selectbox("요당 (+)", ops, index=0)
        qvals["잠혈"] = qcols[3].selectbox("잠혈 (+)", ops, index=0)

        if st.button("해석하기"):
            derived = {}
            albumin_u = st.session_state.get("요 알부빈 (mg/L)") or st.session_state.get("요 알부민 (mg/L)")
            urine_cr = st.session_state.get("요 크레아티닌 (mg/dL)")
            if albumin_u and urine_cr:
                acr = round(compute_acr(float(albumin_u), float(urine_cr)), 1); derived["ACR(mg/g)"] = acr
                st.markdown(_colored(("warn" if acr>=30 else "ok", interpret_acr(acr))))

            for line in _interpret_core(vals):
                st.markdown(_colored(line))
            for line in _qual_interpret(qvals):
                st.markdown(_colored(line))

            guides = pediatric_guides(vals, group="소아-일상")
            foods = _food_suggestions(vals)
            if guides:
                st.markdown("### 소아/케어 가이드")
                for g in guides:
                    st.write("- " + g)
            if foods:
                st.markdown("### 음식 가이드 (수치 기반)")
                for f in foods:
                    st.write("- " + f)

            if key:
                payload = {
                    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    "mode": mode,
                    "vals": {k:v for k,v in vals.items() if v not in (None,"")},
                    "qvals": qvals,
                    "derived": derived,
                    "guides": guides,
                    "foods": foods,
                }
                doc = append_history(key, payload)
                st.success(f"저장 완료: {key}")
                hist = pd.DataFrame(doc.get("history", []))
                if not hist.empty:
                    rows = []
                    for r in doc["history"]:
                        t = r.get("ts"); row={"ts":t}
                        for lab in ["WBC(백혈구)","Hb(혈색소)","혈소판(PLT)","CRP","ANC(호중구)"]:
                            row[lab] = r.get("vals",{}).get(lab)
                        rows.append(row)
                    df = pd.DataFrame(rows).dropna(how="all", subset=["WBC(백혈구)","Hb(혈색소)","혈소판(PLT)","CRP","ANC(호중구)"])
                    if not df.empty:
                        df["ts"] = pd.to_datetime(df["ts"])
                        st.line_chart(df.set_index("ts"))

        st.markdown("---")
        if st.button("보고서 .md / .txt / .pdf 다운로드 준비"):
            meta = {"user_key": key or "-", "diagnosis": "-", "category": "소아-일상"}
            derived = {}
            md = build_report_md(meta, vals, derived, [])
            st.download_button("📄 MD 다운로드", md, file_name="bloodmap_report.md")
            st.download_button("📝 TXT 다운로드", build_report_txt(md), file_name="bloodmap_report.txt")
            st.download_button("🧾 PDF 다운로드", build_report_pdf_bytes(md), file_name="bloodmap_report.pdf")

    if mode == "암 진단 모드":
        st.markdown("### 암 카테고리 선택")
        cat = st.selectbox("암 카테고리", ONCO_CATEGORIES)
        dx = ""
        meds = []
        if cat == "고형암":
            dx = st.selectbox("고형암 진단명", SOLID_OPTIONS)
            meds = getattr(drug_data, "solid_targeted", {}).get(dx, [])
        elif cat == "혈액암":
            dx = st.selectbox("혈액암 진단명", list(BLOOD_CANCERS.keys()))
            meds = BLOOD_CANCERS.get(dx, [])
        elif cat == "림프종":
            dx = st.selectbox("림프종 진단명", list(LYMPHOMA.keys()))
            meds = LYMPHOMA.get(dx, [])
        elif cat == "육종":
            dx = st.selectbox("육종 진단명", list(SARCOMA.keys()))
            meds = SARCOMA.get(dx, [])
        else:
            dx = st.selectbox("희귀암 진단명", list(RARE.keys()))
            meds = RARE.get(dx, [])

        st.markdown("**자동 연결 항목**")
        st.write("- 항암제 목록")
        if meds:
            for m in meds:
                label = getattr(drug_data, "ko", lambda x:x)(m) if m in sum(getattr(drug_data, "solid_targeted", {}).values(), []) else m
                st.write(f"  • {label}")
        st.write("- 암환자에서 자주 쓰는 항생제")
        for k,v in {
            "세페핌": "광범위 베타락탐 — 발열 중성구감소증 1차 약제로 자주 사용.",
            "피페라실린/타조박탐": "그람+/그람-/혐기균 커버 — 복합감염에 널리 사용.",
            "메로페넴": "광범위 카바페넴 — 다제내성 위험 시 고려.",
            "반코마이신": "MRSA 등 그람+ 커버 — 신장기능/혈중농도 모니터.",
            "레보플록사신": "경구 가능 — QT연장/건병증 주의.",
        }.items():
            st.write(f"  • {k}: {v}")

        st.markdown("### 혈액 수치 입력")
        vals = {}
        for label in ORDER:
            vals[label] = st.number_input(label, value=None, step=0.1, format="%.2f")

        st.markdown("### 특수검사")
        qcols = st.columns(4)
        qvals = {}
        ops = ["-","＋","＋＋","＋＋＋"]
        qvals["단백뇨"] = qcols[0].selectbox("단백뇨 (+)", ops, index=0, key="onco_q1")
        qvals["혈뇨"] = qcols[1].selectbox("혈뇨 (+)", ops, index=0, key="onco_q2")
        qvals["요당"] = qcols[2].selectbox("요당 (+)", ops, index=0, key="onco_q3")
        qvals["잠혈"] = qcols[3].selectbox("잠혈 (+)", ops, index=0, key="onco_q4")

        if st.button("해석하기", key="onco_go"):
            derived = {}
            for line in _interpret_core(vals):
                st.markdown(_colored(line))
            for line in _qual_interpret(qvals):
                st.markdown(_colored(line))
            foods = _food_suggestions(vals)
            if foods:
                st.markdown("### 음식 가이드 (수치 기반)")
                for f in foods:
                    st.write("- " + f)

            if key:
                payload = {
                    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    "mode": mode, "category": cat, "diagnosis": dx,
                    "vals": {k:v for k,v in vals.items() if v not in (None,"")},
                    "qvals": qvals, "derived": derived,
                    "meds": meds,
                }
                doc = append_history(key, payload)
                st.success(f"저장 완료: {key}")
                hist = pd.DataFrame(doc.get("history", []))
                if not hist.empty:
                    rows = []
                    for r in doc["history"]:
                        t = r.get("ts"); row={"ts":t}
                        for lab in ["WBC(백혈구)","Hb(혈색소)","혈소판(PLT)","CRP","ANC(호중구)"]:
                            row[lab] = r.get("vals",{}).get(lab)
                        rows.append(row)
                    df = pd.DataFrame(rows).dropna(how="all", subset=["WBC(백혈구)","Hb(혈색소)","혈소판(PLT)","CRP","ANC(호중구)"])
                    if not df.empty:
                        df["ts"] = pd.to_datetime(df["ts"])
                        st.line_chart(df.set_index("ts"))

        st.markdown("---")
        if st.button("보고서 .md / .txt / .pdf 다운로드 준비", key="onco_exp"):
            meta = {"user_key": key or "-", "diagnosis": dx, "category": cat}
            derived = {}
            md = build_report_md(meta, vals, derived, [])
            st.download_button("📄 MD 다운로드", md, file_name="bloodmap_report.md")
            st.download_button("📝 TXT 다운로드", build_report_txt(md), file_name="bloodmap_report.txt")
            st.download_button("🧾 PDF 다운로드", build_report_pdf_bytes(md), file_name="bloodmap_report.pdf")

    st.markdown("---")
    st.caption(DISCLAIMER)
    st.caption(f"현재 세션 조회수: {count()} · {FOOTER_CAFE}")
