# app.py — Bloodmap split tabs (암 선택/항암제/피수치/특수검사)
import datetime as _dt
import os as _os, json as _json, typing as _t
import streamlit as st

# ---------- Safe banner import ----------
try:
    from branding import render_deploy_banner  # flat
except Exception:
    try:
        from .branding import render_deploy_banner  # package
    except Exception:
        def render_deploy_banner(*args, **kwargs):
            return None

# ---------- Optional pandas ----------
try:
    import pandas as pd
except Exception:
    pd = None

st.set_page_config(page_title="Bloodmap", layout="wide")
st.title("Bloodmap")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# ---------- Helpers ----------
_KEY_REG = set()
def wkey(name: str) -> str:
    who = st.session_state.get("key", "guest")
    mode_now = st.session_state.get("mode", "main")
    k = f"{mode_now}:{who}:{name}"
    _KEY_REG.add(k)
    return k
def enko(en: str, ko: str) -> str:
    return f"{en} / {ko}" if ko else en

# Load external data
DATA_DIR = "/mnt/data/data"
def _load_json(path, fallback): 
    try:
        with open(path,"r",encoding="utf-8") as f: return _json.load(f)
    except Exception: return fallback
GROUPS = _load_json(f"{DATA_DIR}/groups.json", {})
CHEMO_MAP = _load_json(f"{DATA_DIR}/chemo_map.json", {})

# eGFR CKD-EPI 2009
def _egfr_local(scr_mgdl: float, age_y: int, sex: str) -> _t.Optional[float]:
    try:
        sex_f = (sex == "여")
        k = 0.7 if sex_f else 0.9
        a = -0.329 if sex_f else -0.411
        min_cr = min(scr_mgdl / k, 1)
        max_cr = max(scr_mgdl / k, 1)
        sex_fac = 1.018 if sex_f else 1.0
        val = 141 * (min_cr ** a) * (max_cr ** -1.209) * (0.993 ** int(age_y)) * sex_fac
        return round(val, 1)
    except Exception:
        return None
try:
    from core_utils import egfr_ckd_epi_2009 as egfr_fn  # type: ignore
except Exception:
    egfr_fn = _egfr_local

# ---------- Sidebar ----------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key", "guest"), key=wkey("user_key"))
    st.session_state["mode"] = st.radio("모드", ["일반", "암", "소아"], index=1, key=wkey("mode_sel"))

# ---------- Tabs ----------
t_home, t_labs, t_dx_only, t_chemo, t_special, t_guard, t_report = st.tabs(
    ["🏠 홈","🧪 피수치","🧬 암 선택","💊 항암제","🔬 특수검사","🛡 가드레일","📄 보고서"]
)

with t_home:
    st.success("필요한 항목이 탭으로 분리되었습니다: 피수치 · 암 선택 · 항암제 · 특수검사 · 가드레일 · 보고서")

with t_labs:
    st.subheader("피수치 (Labs)")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with c2:
        age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with c3:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=0.0, key=wkey("wt"))
    with c4:
        cr = st.number_input("Cr (mg/dL)", min_value=0.0, step=0.1, value=0.8, key=wkey("cr"))
    with c5:
        today = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    egfr = egfr_fn(cr, int(age), sex)
    if egfr is not None:
        st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")
        st.session_state["_last_egfr"] = egfr
    if pd is not None:
        row = {"date": str(today), "sex": sex, "age": int(age), "weight(kg)": weight, "Cr(mg/dL)": cr, "eGFR": egfr}
        st.session_state.setdefault("lab_rows", [])
        if st.button("➕ 현재 값 추가", key=wkey("add_row")):
            st.session_state["lab_rows"].append(row)
        df = pd.DataFrame(st.session_state["lab_rows"] or [row])
        st.dataframe(df, use_container_width=True)
        if st.button("📁 외부 저장(.csv)", key=wkey("save_csv_btn")):
            try:
                _os.makedirs("/mnt/data/bloodmap_graph", exist_ok=True)
                path = f"/mnt/data/bloodmap_graph/{st.session_state.get('key','guest')}.labs.csv"
                df.to_csv(path, index=False, encoding="utf-8"); st.caption(f"외부 저장: {path}")
            except Exception as e:
                st.warning("CSV 저장 실패: "+str(e))

with t_dx_only:
    st.subheader("암 선택 (Diagnosis)")
    tabs = st.tabs(list(GROUPS.keys()))
    for i,(grp, dx_list) in enumerate(GROUPS.items()):
        with tabs[i]:
            labels = [enko(en, ko) for en,ko in dx_list]
            sel = st.selectbox("진단명을 선택하세요", labels, key=wkey(f"dx_sel_{i}"))
            idx = labels.index(sel)
            en_dx, ko_dx = dx_list[idx]
            if st.button("선택 저장", key=wkey(f"dx_save_{i}")):
                st.session_state["selected_dx_en"] = en_dx
                st.session_state["selected_dx_ko"] = ko_dx
                st.success(f"선택됨: {enko(en_dx, ko_dx)}")

with t_chemo:
    st.subheader("항암제 (Chemo)")
    en_dx = st.session_state.get("selected_dx_en")
    ko_dx = st.session_state.get("selected_dx_ko","")
    if not en_dx:
        st.info("먼저 '암 선택' 탭에서 진단명을 저장하세요.")
    else:
        st.write(f"현재 진단: **{enko(en_dx, ko_dx)}**")
        suggestions = CHEMO_MAP.get(en_dx, [])
        picked = st.multiselect("항암제를 선택/추가하세요 (영문/한글 병기)", suggestions, default=suggestions, key=wkey("chemo_ms"))
        extra = st.text_input("추가 항암제(쉼표로 구분)", key=wkey("chemo_extra"))
        if extra.strip():
            more = [x.strip() for x in extra.split(",") if x.strip()]
            seen, merged = set(), []
            for x in picked + more:
                if x not in seen: seen.add(x); merged.append(x)
            picked = merged
        if st.button("항암제 선택 저장", key=wkey("chemo_save")):
            st.session_state["report_group"] = "—"
            st.session_state["report_dx_en"] = en_dx
            st.session_state["report_dx_ko"] = ko_dx
            st.session_state["report_meds"] = picked
            st.success("저장되었습니다. '보고서' 탭에서 확인하세요.")

with t_special:
    st.subheader("특수검사 (Special Tests)")
    try:
        from special_tests import render_special_tests  # expecting a function
        render_special_tests(st, key_prefix=wkey("special"))  # type: ignore
    except Exception:
        st.info("특수검사 모듈이 없거나 호환되지 않습니다. special_tests.py의 render_special_tests(st, key_prefix=...) 함수를 제공하면 자동 표시됩니다.")

with t_guard:
    st.subheader("가드레일 (APAP/IBU)")
    # 간단 버전: 총량/쿨다운만
    from datetime import datetime as _dtpy
    try:
        from pytz import timezone
        def _now_kst(): return _dtpy.now(timezone("Asia/Seoul"))
    except Exception:
        def _now_kst(): return _dtpy.now()

    st.session_state.setdefault("care_log", {}).setdefault(st.session_state.get("key","guest"), [])
    log = st.session_state["care_log"][st.session_state.get("key","guest")]
    c1,c2 = st.columns(2)
    limit_apap = c1.number_input("APAP 24h 한계(mg)", 0, 10000, 4000, 100, key=wkey("apap_lim"))
    limit_ibu  = c2.number_input("IBU  24h 한계(mg)",  0, 10000, 1200, 100, key=wkey("ibu_lim"))
    d1,d2 = st.columns(2)
    apap = d1.number_input("APAP 복용량(mg)", 0, 10000, 0, 50, key=wkey("apap_now"))
    ibu  = d2.number_input("IBU  복용량(mg)",  0, 10000, 0, 50, key=wkey("ibu_now"))
    if d1.button("APAP 기록", key=wkey("apap_btn")):
        log.append({"t": _now_kst().isoformat(), "drug":"APAP", "dose": apap})
    if d2.button("IBU 기록", key=wkey("ibu_btn")):
        log.append({"t": _now_kst().isoformat(), "drug":"IBU", "dose": ibu})
    now = _now_kst()
    apap_24h = sum(x["dose"] for x in log if x["drug"]=="APAP" and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds()<=24*3600)
    ibu_24h  = sum(x["dose"] for x in log if x["drug"]=="IBU"  and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds()<=24*3600)
    if apap_24h > limit_apap: st.error(f"APAP 24h 총 {apap_24h} mg 초과")
    if ibu_24h  > limit_ibu : st.error(f"IBU 24h 총 {ibu_24h} mg 초과")

with t_report:
    st.subheader("보고서 (.md)")
    def build_report_md() -> str:
        en_dx = st.session_state.get("report_dx_en")
        ko_dx = st.session_state.get("report_dx_ko","")
        meds  = st.session_state.get("report_meds", [])
        egfr  = st.session_state.get("_last_egfr")
        rows  = st.session_state.get("lab_rows", [])
        lines = []
        lines.append("# Bloodmap Report")
        lines.append(f"**진단명**: {enko(en_dx, ko_dx) if en_dx else '(선택되지 않음)'}")
        if egfr is not None: lines.append(f"**최근 eGFR**: {egfr} mL/min/1.73㎡")
        lines.append("")
        lines.append("## 항암제 요약")
        if meds: 
            for m in meds: lines.append(f"- {m}")
        else:
            lines.append("- (선택 항암제 없음)")
        if rows:
            lines.append("")
            lines.append("## 최근 검사 요약")
            head = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR"]
            lines.append("| " + " | ".join(head) + " |")
            lines.append("|" + "|".join(["---"]*len(head)) + "|")
            for r in rows[-5:]:
                lines.append("| " + " | ".join(str(r.get(k,"")) for k in head) + " |")
        lines.append("")
        lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        return "\n".join(lines)
    md = build_report_md()
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))