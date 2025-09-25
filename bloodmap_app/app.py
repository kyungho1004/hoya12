# app.py — Bloodmap patched with preflight(), external JSON, weight-based guardrails, report labs
import datetime as _dt
import os as _os, json as _json, typing as _t, ast as _ast, inspect as _inspect
import streamlit as st

# ---------- Safe banner import ----------
BANNER_OK = False
try:
    from branding import render_deploy_banner  # flat
    BANNER_OK = True
except Exception:
    try:
        from .branding import render_deploy_banner  # package
        BANNER_OK = True
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

# ---------- Key registry & helpers ----------
_KEY_REG = set()
def wkey(name: str) -> str:
    who = st.session_state.get("key", "guest")
    mode_now = st.session_state.get("mode", "main")
    k = f"{mode_now}:{who}:{name}"
    _KEY_REG.add(k)
    return k

def enko(en: str, ko: str) -> str:
    return f"{en} / {ko}" if ko else en

def save_labs_csv(df, key: str):
    save_dir = "/mnt/data/bloodmap_graph"
    try:
        _os.makedirs(save_dir, exist_ok=True)
        path = _os.path.join(save_dir, f"{key}.labs.csv")
        df.to_csv(path, index=False, encoding="utf-8")
        st.caption(f"외부 저장 완료: {path}")
        st.session_state["_CSV_OK"] = True
    except Exception as e:
        st.warning("CSV 저장 실패: " + str(e))
        st.session_state["_CSV_OK"] = False

# eGFR CKD-EPI 2009 (fallback)
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
    st.session_state["_EGRF_OK"] = True
except Exception:
    egfr_fn = _egfr_local
    st.session_state["_EGRF_OK"] = True  # fallback available

# ---------- Load external GROUPS & CHEMO_MAP ----------
def _load_json(path: str, fallback: _t.Any) -> _t.Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return fallback

DATA_DIR = "/mnt/data/data"
GROUPS = _load_json(f"{DATA_DIR}/groups.json", {})
if not GROUPS:
    GROUPS = {
        "🩸 혈액암 (Leukemia)": [["Acute Lymphoblastic Leukemia (ALL)","급성 림프모구 백혈병"]],
    }
CHEMO_MAP = _load_json(f"{DATA_DIR}/chemo_map.json", {})

# ---------- Preflight ----------
def preflight():
    problems = []

    # 1) ast.parse self
    try:
        src = _inspect.getsource(preflight.__globals__['preflight'].__code__)  # dummy to access module
        # Actually parse this file content via __file__
        with open(__file__, "r", encoding="utf-8") as f:
            _ast.parse(f.read())
    except Exception as e:
        problems.append(f"[AST] 파싱 실패: {e}")

    # 2) widget-key duplicates
    if len(_KEY_REG) != len(set(_KEY_REG)):
        problems.append("[KEY] 위젯 키 중복 감지")

    # 3) feature toggles
    if not BANNER_OK:
        problems.append("[TOGGLE] 배너 render 불가")
    if not st.session_state.get("_EGRF_OK", False):
        problems.append("[TOGGLE] eGFR 사용 불가")
    if "care_log" not in st.session_state:
        problems.append("[TOGGLE] 가드레일 로그 미초기화")
    if not st.session_state.get("_CSV_OK", None):
        problems.append("[TOGGLE] CSV 저장 미검증")

    if problems:
        st.warning("🧪 Preflight 경고:\n- " + "\n- ".join(problems))
    else:
        st.success("✅ Preflight 통과")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key", "guest"), key=wkey("user_key"))
    st.session_state["mode"] = st.radio("모드", ["일반", "암", "소아"], index=1, key=wkey("mode_sel"))
    st.button("Preflight 실행", on_click=preflight, key=wkey("run_preflight"))

# ---------- Tabs ----------
tab_home, tab_labs, tab_dx, tab_meds, tab_report = st.tabs(["🏠 홈", "🧪 검사/지표", "🧬 진단/항암제", "💊 가드레일", "📄 보고서"])

with tab_home:
    st.success("Bloodmap가 동작 중입니다. 좌측에서 프로필을 설정하고 상단 탭을 이용하세요.")
    st.caption("※ 본 도구는 의학적 조언이 아닙니다. 실제 투약은 반드시 담당 의료진과 상의하세요.")

with tab_labs:
    st.subheader("기본 수치 입력")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with c2:
        age = st.number_input("나이(세)", min_value=1, max_value=110, step=1, value=40, key=wkey("age"))
    with c3:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=0.0, key=wkey("wt"))
    with c4:
        cr = st.number_input("Cr (mg/dL)", min_value=0.0, step=0.1, value=0.8, key=wkey("cr"))
    with c5:
        today = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    st.caption("※ eGFR(CKD-EPI 2009)은 성별/나이/Cr만 사용합니다. 체중은 표/CSV에 함께 저장됩니다.")
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
            save_labs_csv(df, st.session_state.get("key","guest"))
    else:
        st.info("pandas 미탑재: 표/CSV 저장 기능 비활성화")

def render_dx_once():
    if st.session_state.get("dx_rendered"):
        return
    st.session_state["dx_rendered"] = True
    tabs = st.tabs(list(GROUPS.keys()))
    for i, (grp, dx_list) in enumerate(GROUPS.items()):
        with tabs[i]:
            st.subheader(grp)
            labels = [enko(en, ko) for en, ko in dx_list]
            dx_choice = st.selectbox("진단명을 선택하세요", labels, key=wkey(f"dx_sel_{i}"))
            idx = labels.index(dx_choice)
            en_dx, ko_dx = dx_list[idx]

            st.caption("자동 추천 항암제(수정/추가 가능)")
            suggestions = CHEMO_MAP.get(en_dx, [])
            picked = st.multiselect("항암제를 선택/추가하세요 (영문/한글 병기)", suggestions, default=suggestions, key=wkey(f"meds_{i}"))
            extra = st.text_input("추가 항암제(쉼표로 구분)", key=wkey(f"extra_{i}"))
            if extra.strip():
                more = [x.strip() for x in extra.split(",") if x.strip()]
                seen, merged = set(), []
                for x in picked + more:
                    if x not in seen:
                        seen.add(x); merged.append(x)
                picked = merged

            if st.button("이 선택을 보고서에 사용", key=wkey(f"use_{i}")):
                st.session_state["report_group"] = grp
                st.session_state["report_dx_en"] = en_dx
                st.session_state["report_dx_ko"] = ko_dx
                st.session_state["report_meds"] = picked
                st.success("보고서에 반영되었습니다.")

with tab_dx:
    render_dx_once()

with tab_meds:
    st.subheader("해열제 가드레일 (APAP/IBU)")
    from datetime import datetime as _dtpy, timedelta as _td
    try:
        from pytz import timezone
        def _now_kst(): return _dtpy.now(timezone("Asia/Seoul"))
    except Exception:
        def _now_kst(): return _dtpy.now()

    st.session_state.setdefault("care_log", {}).setdefault(st.session_state.get("key","guest"), [])
    log = st.session_state["care_log"][st.session_state.get("key","guest")]

    c0, c1, c2, c3 = st.columns(4)
    liver = c0.checkbox("간기능 장애", value=False, key=wkey("flag_liver"))
    renal = c0.checkbox("신기능 장애", value=False, key=wkey("flag_renal"))
    limit_apap_base = c1.number_input("APAP 24h 한계 기본(mg)", min_value=0, value=4000, step=100, key=wkey("apap_limit_base"))
    limit_ibu_base  = c2.number_input("IBU  24h 한계 기본(mg)", min_value=0, value=1200, step=100, key=wkey("ibu_limit_base"))
    wt_for_dose     = c3.number_input("체중(kg, 권장량 계산)", min_value=0.0, value=0.0, step=0.5, key=wkey("wt_dose"))

    # 권장량(가이드 참고치, 의료적 조언 아님)
    apap_mgkg_day = st.number_input("APAP 권장 상한 (mg/kg/24h)", min_value=0, value=75, step=5, key=wkey("apap_mgkg"))
    ibu_mgkg_day  = st.number_input("IBU  권장 상한 (mg/kg/24h)", min_value=0, value=40, step=5, key=wkey("ibu_mgkg"))

    # 플래그에 따른 제한 보정 (보수적)
    factor = 1.0
    if liver: factor *= 0.5
    if renal: factor *= 0.5

    limit_apap = int(limit_apap_base * factor)
    limit_ibu  = int(limit_ibu_base  * factor)
    if wt_for_dose > 0:
        limit_apap = min(limit_apap, int(apap_mgkg_day * wt_for_dose))
        limit_ibu  = min(limit_ibu,  int(ibu_mgkg_day  * wt_for_dose))

    st.info(f"계산된 24h 상한: APAP {limit_apap} mg, IBU {limit_ibu} mg (※ 참고용)")

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

    now = _now_kst()
    apap_24h = sum(x["dose"] for x in log if x.get("drug")=="APAP" and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds() <= 24*3600)
    ibu_24h  = sum(x["dose"] for x in log if x.get("drug")=="IBU"  and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds() <= 24*3600)
    if apap_24h > limit_apap:
        st.error(f"APAP 24h 총 {apap_24h} mg (한계 {limit_apap} mg) 초과")
    if ibu_24h > limit_ibu:
        st.error(f"IBU 24h 총 {ibu_24h} mg (한계 {limit_ibu} mg) 초과")

    def _ics(title, when):
        dt = when.strftime("%Y%m%dT%H%M%S")
        return f"BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:{title}\nDTSTART:{dt}\nEND:VEVENT\nEND:VCALENDAR\n".encode("utf-8")

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

with tab_report:
    st.subheader("보고서 (.md)")
    def build_report_md() -> str:
        grp = st.session_state.get("report_group")
        en_dx = st.session_state.get("report_dx_en")
        ko_dx = st.session_state.get("report_dx_ko")
        meds = st.session_state.get("report_meds", [])
        egfr = st.session_state.get("_last_egfr")
        rows = st.session_state.get("lab_rows", [])

        lines = []
        lines.append("# Bloodmap Report")
        if grp and en_dx:
            lines.append(f"**암종 그룹**: {grp}")
            lines.append(f"**진단명**: {enko(en_dx, ko_dx)}")
        else:
            lines.append("**진단명**: (선택되지 않음)")
        if egfr is not None:
            lines.append(f"**최근 eGFR**: {egfr} mL/min/1.73㎡")
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

    md_text = build_report_md()
    st.code(md_text, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md_text.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))