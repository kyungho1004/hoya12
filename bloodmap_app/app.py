# app.py — rebuilt minimal but complete Bloodmap app
import datetime as _dt
import io as _io
import os as _os
import typing as _t

import streamlit as st

# ---- Safe banner import (package/flat/no-op) ----
try:
    from branding import render_deploy_banner  # flat
except Exception:
    try:
        from .branding import render_deploy_banner  # package
    except Exception:
        def render_deploy_banner(*args, **kwargs):
            return None

# ---- Optional deps ----
try:
    import pandas as pd  # type: ignore
except Exception:  # graceful degradation
    pd = None

# ---- Page setup ----
st.set_page_config(page_title="Bloodmap", layout="wide")
st.title("Bloodmap")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# ---- Style (optional) ----
try:
    with open("style.css", "r", encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

# ---- Helpers ----
def wkey(name: str) -> str:
    try:
        who = st.session_state.get("key", "guest")
        mode_now = st.session_state.get("mode", "main")
        return f"{mode_now}:{who}:{name}"
    except Exception:
        return name

def init_care_log(user_key: str):
    st.session_state.setdefault("care_log", {})
    st.session_state["care_log"].setdefault(user_key, [])
    return st.session_state["care_log"][user_key]

def save_labs_csv(df, key: str):
    try:
        save_dir = "/mnt/data/bloodmap_graph"
        _os.makedirs(save_dir, exist_ok=True)
        csv_path = _os.path.join(save_dir, f"{key}.labs.csv")
        if pd is None:
            raise RuntimeError("pandas not available")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        st.caption(f"외부 저장 완료: {csv_path}")
    except Exception as _e:
        st.warning("외부 저장 실패: " + str(_e))

# eGFR util (prefer core_utils if available)
def _egfr_local(scr_mgdl: float, age_y: int, sex: str) -> _t.Optional[float]:
    try:
        if scr_mgdl is None or age_y is None:
            return None
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

# ---- Sidebar basic profile ----
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key", "guest"), key=wkey("user_key"))
    st.session_state["mode"] = st.radio("모드", ["일반", "암", "소아"], index=0, key=wkey("mode_sel"))

# ---- Tabs ----
tab_home, tab_labs, tab_meds = st.tabs(["🏠 홈", "🧪 검사/지표", "💊 해열제 가드"])

with tab_home:
    st.success("앱이 재구성되어 정상 동작 중입니다.")
    if False:
    # 개발용 점검 패널 비활성화
    with st.expander("모듈 임포트 상태"):
        import importlib
        for mod in ["core_utils","drug_db","onco_map","ui_results","lab_diet","peds_profiles","peds_dose","adult_rules","special_tests","pdf_export"]:
            try:
                importlib.import_module(mod)
                st.write(f"✅ import {mod}")
            except Exception as e:
                st.write(f"❌ import {mod}: {e}")

with tab_labs:
    st.subheader("기본 수치 입력")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with c2:
        age = st.number_input("나이(세)", min_value=1, max_value=110, step=1, value=40, key=wkey("age"))
    with c3:
        cr = st.number_input("Cr (mg/dL)", min_value=0.0, step=0.1, value=0.8, key=wkey("cr"))
    with c4:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=0.0, key=wkey("wt"))
    with c5:
        today = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    st.caption("※ 참고: CKD-EPI 2009 eGFR 계산에는 체중이 직접적으로 사용되지 않습니다.")
    # eGFR
    egfr = egfr_fn(cr, int(age), sex)
    if egfr is not None:
        st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")
    # Dataframe preview + save
    if pd is not None:
        df = pd.DataFrame([{"date": str(today), "sex": sex, "age": int(age), "weight(kg)": weight, "Cr(mg/dL)": cr, "eGFR": egfr}])
        st.dataframe(df, use_container_width=True)
        if st.button("📁 외부 저장(.csv)", key=wkey("save_csv_btn")):
            save_labs_csv(df, st.session_state.get("key","guest"))
    else:
        st.info("pandas 미탑재: 표/CSV 저장 기능 비활성화")

with tab_meds:
    st.subheader("해열제 가드레일 (APAP/IBU)")
    from datetime import datetime, timedelta
    try:
        from pytz import timezone
        def _now_kst(): return datetime.now(timezone("Asia/Seoul"))
    except Exception:
        def _now_kst(): return datetime.now()

    def _ics(title: str, when: datetime) -> bytes:
        dt = when.strftime("%Y%m%dT%H%M%S")
        ics = f"BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:{title}\nDTSTART:{dt}\nEND:VEVENT\nEND:VCALENDAR\n"
        return ics.encode("utf-8")

    log = init_care_log(st.session_state.get("key","guest"))

    c1, c2, c3 = st.columns(3)
    limit_apap = c1.number_input("APAP 24h 한계(mg)", min_value=0, value=4000, step=100, key=wkey("apap_limit"))
    limit_ibu  = c2.number_input("IBU  24h 한계(mg)", min_value=0, value=1200, step=100, key=wkey("ibu_limit"))
    _ = c3.number_input("체중(kg, 선택)", min_value=0.0, value=0.0, step=0.5, key=wkey("wt_opt"))

    d1, d2 = st.columns(2)
    apap_now = d1.number_input("APAP 복용량(mg)", min_value=0, value=0, step=50, key=wkey("apap_now"))
    ibu_now  = d2.number_input("IBU 복용량(mg)",  min_value=0, value=0, step=50, key=wkey("ibu_now"))

    if d1.button("APAP 복용 기록", key=wkey("apap_take_btn")):
        last = next((x for x in reversed(log) if x.get("drug")=="APAP"), None)
        now = _now_kst()
        if last:
            last_t = _dt.datetime.fromisoformat(last["t"])
            if (now - last_t).total_seconds() < 4*3600:
                st.error("APAP 쿨다운 4시간 미만입니다.")
            else:
                log.append({"t": now.isoformat(), "drug":"APAP", "dose": apap_now})
        else:
            log.append({"t": now.isoformat(), "drug":"APAP", "dose": apap_now})

    if d2.button("IBU 복용 기록", key=wkey("ibu_take_btn")):
        last = next((x for x in reversed(log) if x.get("drug")=="IBU"), None)
        now = _now_kst()
        if last:
            last_t = _dt.datetime.fromisoformat(last["t"])
            if (now - last_t).total_seconds() < 6*3600:
                st.error("IBU 쿨다운 6시간 미만입니다.")
            else:
                log.append({"t": now.isoformat(), "drug":"IBU", "dose": ibu_now})
        else:
            log.append({"t": now.isoformat(), "drug":"IBU", "dose": ibu_now})

    # Rollup + next-dose ICS
    now = _now_kst()
    apap_24h = sum(x["dose"] for x in log if x.get("drug")=="APAP" and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds() <= 24*3600)
    ibu_24h  = sum(x["dose"] for x in log if x.get("drug")=="IBU"  and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds() <= 24*3600)
    if apap_24h > limit_apap:
        st.error(f"APAP 24h 총 {apap_24h} mg (한계 {limit_apap} mg) 초과")
    if ibu_24h > limit_ibu:
        st.error(f"IBU 24h 총 {ibu_24h} mg (한계 {limit_ibu} mg) 초과")

    last_apap = next((x for x in reversed(log) if x.get("drug")=="APAP"), None)
    if last_apap:
        next_t = _dt.datetime.fromisoformat(last_apap["t"]) + _dt.timedelta(hours=4)
        st.download_button("APAP 다음 복용 .ics", data=_ics("APAP next dose", next_t),
                           file_name="apap_next.ics", mime="text/calendar", key=wkey("apap_ics"))
    last_ibu = next((x for x in reversed(log) if x.get("drug")=="IBU"), None)
    if last_ibu:
        next_t = _dt.datetime.fromisoformat(last_ibu["t"]) + _dt.timedelta(hours=6)
        st.download_button("IBU 다음 복용 .ics", data=_ics("IBU next dose", next_t),
                           file_name="ibu_next.ics", mime="text/calendar", key=wkey("ibu_ics"))