# app.py — Bloodmap SAFE CLASSIC (2025-11-02 KST)
# - 단일 파일 실행 가능 (외부 모듈 없어도 동작)
# - 홈으로 튀는 현상 방지, 중복 키 가드, 파일쓰기 폴백(/mnt/data → /mount/data → /tmp)
# - 특수모듈 없는 경우 스텁으로 안전 실행
# - 기존 탭 순서 유지: 홈 / 소아 증상 / 암 선택 / 항암제(진단 기반) / 피수치 입력 / 특수검사 / 보고서 / 기록/그래프

from __future__ import annotations
import os, re, sys, io, json, csv
import datetime as dt
from typing import Dict, Any, List, Tuple
from pathlib import Path

import streamlit as st
try:
    from zoneinfo import ZoneInfo
except Exception:
    # Py<3.9 환경 호환
    from backports.zoneinfo import ZoneInfo  # type: ignore

# =========================
# 0) TOP SAFETY GUARDS
# =========================
KST = ZoneInfo("Asia/Seoul")
def now_kst() -> dt.datetime:
    return dt.datetime.now(tz=KST)

# Streamlit 내부 위젯 패치가 남아있을 경우 원복
if not os.environ.get("BM_DISABLE_ST_PATCH"):
    try:
        if not hasattr(st, "_bm_text_input_orig"):
            st._bm_text_input_orig = st.text_input
        if not hasattr(st, "_bm_selectbox_orig"):
            st._bm_selectbox_orig = st.selectbox
        if not hasattr(st, "_bm_text_area_orig"):
            st._bm_text_area_orig = st.text_area
        st.text_input  = st._bm_text_input_orig
        st.selectbox   = st._bm_selectbox_orig
        st.text_area   = st._bm_text_area_orig
    except Exception:
        pass
    os.environ["BM_DISABLE_ST_PATCH"] = "1"  # 재패치 방지

# URL 쿼리 파라미터 호환 유틸
def _get_qp(name: str, default: str="") -> str:
    try:
        v = st.query_params.get(name)
        return v[0] if isinstance(v, list) else (v or default)
    except Exception:
        try:
            v = st.experimental_get_query_params().get(name, [default])
            return v[0] if v else default
        except Exception:
            return default

def _set_qp(**kwargs):
    try:
        # 최신 API
        st.query_params.update(**kwargs)  # type: ignore
    except Exception:
        try:
            st.experimental_set_query_params(**kwargs)
        except Exception:
            pass

# 라우팅 첫 로드/튐 방지
def _bootstrap_route():
    ss = st.session_state
    cur = ss.get("_route")
    url_r = _get_qp("route", "")
    if not cur:
        if url_r:
            ss["_route"] = url_r
            ss["_route_last"] = url_r
        else:
            # 첫 진입은 chemo(항암 탭) 쪽으로 고정(형 기존 흐름)
            ss["_route"] = "chemo"
            ss["_route_last"] = "chemo"
            _set_qp(route="chemo")

def _block_spurious_home():
    ss = st.session_state
    cur = ss.get("_route") or "home"
    last = ss.get("_route_last")
    intent_home = ss.get("_home_intent", False)
    if cur == "home" and last and last != "home" and not intent_home:
        ss["_route"] = last
        _set_qp(route=last)

def _pin_dx_route():
    ss = st.session_state
    ss["_home_intent"] = False
    if ss.get("_route") != "dx":
        ss["_route"] = "dx"
        if not ss.get("_route_last") or ss.get("_route_last") == "home":
            ss["_route_last"] = "dx"
        _set_qp(route="dx")
        st.rerun()

_bootstrap_route()

# =========================
# 1) PAGE SHELL
# =========================
APP_VERSION = "항상 여러분들의 힘이 되도록 노력하겠습니다. 여러분들의 피드백이 업데이트에 많은 도움이 됩니다"

st.set_page_config(page_title=f"Bloodmap {APP_VERSION}", layout="wide")
st.title(f"Bloodmap {APP_VERSION}")
st.markdown(
    """> In memory of Eunseo, a little star now shining in the sky.
> This app is made with the hope that she is no longer in pain,
> and resting peacefully in a world free from all hardships."""
)
st.markdown("---")

# 브랜딩: 외부 branding 모듈 없으면 문구만
def render_deploy_banner(url: str, credit: str):
    st.markdown(
        f'<div style="padding:.5rem 0;color:#666;">'
        f'<strong>배포 주소</strong>: <a href="{url}" target="_blank">{url}</a><br>'
        f'제작: Hoya/GPT · 자문: Hoya/GPT'
        f'</div>',
        unsafe_allow_html=True
    )
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# =========================
# 2) PATH/IO SAFETY
# =========================
DATA_BASE = None
for cand in ["/mnt/data", "/mount/data", "/tmp"]:
    try:
        p = Path(cand)
        p.mkdir(exist_ok=True)
        if os.access(str(p), os.W_OK):
            DATA_BASE = p
            break
    except Exception:
        continue
if DATA_BASE is None:
    DATA_BASE = Path("/tmp")
    DATA_BASE.mkdir(exist_ok=True)

# =========================
# 3) UTILITIES
# =========================
def wkey(name: str) -> str:
    who = st.session_state.get("key", "guest#PIN")
    return f"{who}:{name}"

def _try_float(s) -> float | None:
    if s in (None, ""):
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.search(r'([-+]?[0-9]*[.,]?[0-9]+)', str(s))
    if not m: return None
    num = m.group(1).replace(",", ".")
    try: return float(num)
    except Exception: return None

def _safe_float(v, default=0.0) -> float:
    try:
        if v in (None, ""): return default
        if isinstance(v, (int, float)): return float(v)
        return float(str(v).strip())
    except Exception:
        return default

# =========================
# 4) OPTIONAL MODULE STUBS
# =========================
# onco_map stub
DX_KO = {
    "ALL": "급성 림프구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "Lymphoma": "림프종",
    "Breast": "유방암",
    "Colon": "대장암",
    "Lung": "폐암",
}
def _dx_norm(s: str) -> str:
    return s

def build_onco_map() -> Dict[str, Dict[str, Any]]:
    return {
        "혈액암": {"ALL": {}, "AML": {}, "Lymphoma": {}},
        "고형암": {"Breast": {}, "Colon": {}, "Lung": {}},
    }

def dx_display(group: str, disease: str) -> str:
    ko = DX_KO.get(_dx_norm(disease)) or disease
    if re.search(r"[가-힣]", str(disease)):
        return f"{group} — {disease}"
    return f"{group} — {disease} ({ko})"

def auto_recs_by_dx(group: str, disease: str, db: Dict[str,Any]) -> Dict[str, List[str]]:
    # 간단 추천(스텁). 실제 onco_map 있으면 교체됨.
    rec = {"chemo": [], "targeted": [], "abx": []}
    d = (disease or "").lower()
    if d in ("all", "aml", "lymphoma"):
        rec["chemo"] = ["Cytarabine", "Daunorubicin", "6-MP", "MTX"]
    elif d in ("breast",):
        rec["chemo"] = ["Doxorubicin", "Cyclophosphamide", "Paclitaxel"]
        rec["targeted"] = ["Trastuzumab"]
    elif d in ("colon",):
        rec["chemo"] = ["5-FU", "Leucovorin", "Oxaliplatin"]
    elif d in ("lung",):
        rec["chemo"] = ["Cisplatin", "Pemetrexed"]
    return rec

# drug_db stub (최소 부작용/태그 포함)
DRUG_DB: Dict[str, Dict[str, Any]] = {
    "Cytarabine": {"class":"antimetabolite", "ae":["골수억제","오심/구토","구내염","발열"], "tags":["myelosuppression"]},
    "Daunorubicin": {"class":"anthracycline", "ae":["심근독성","골수억제","탈모"], "tags":["myelosuppression","qt_prolong"]},
    "6-MP": {"class":"antimetabolite", "ae":["간수치상승","골수억제"], "tags":["myelosuppression"]},
    "MTX": {"class":"antimetabolite", "ae":["간독성","구내염","신장독성"], "tags":["myelosuppression"]},
    "Doxorubicin": {"class":"anthracycline", "ae":["심근독성","골수억제","탈모"], "tags":["myelosuppression","qt_prolong"]},
    "Cyclophosphamide": {"class":"alkylating", "ae":["출혈성방광염","골수억제","오심"], "tags":["myelosuppression"]},
    "Paclitaxel": {"class":"taxane", "ae":["말초신경병증","골수억제","탈모"], "tags":["myelosuppression"]},
    "Trastuzumab": {"class":"targeted", "ae":["심기능저하","주입반응"], "tags":["immunotherapy"]},
    "5-FU": {"class":"antimetabolite", "ae":["설사","점막염","손발증후군","골수억제"], "tags":["myelosuppression"]},
    "Leucovorin": {"class":"rescue", "ae":["구역","발진"], "tags":[]},
    "Oxaliplatin": {"class":"platinum", "ae":["말초신경병증","구역/구토"], "tags":[]},
    "Cisplatin": {"class":"platinum", "ae":["신장독성","오심/구토","이독성"], "tags":[]},
    "Pemetrexed": {"class":"antifolate", "ae":["골수억제","피로","구내염"], "tags":["myelosuppression"]},
}

def display_label(key: str, db: Dict[str,Any] | None=None) -> str:
    db = db or DRUG_DB
    rec = db.get(key, {})
    kor = rec.get("name_ko")
    base = key
    if kor: return f"{base} ({kor})"
    # 일부 친숙한 표기
    alias = {"6-MP":"6-MP(6-머캅토퓨린)", "MTX":"MTX(메토트렉세이트)", "5-FU":"5-FU(5-플루오로우라실)"}
    return alias.get(base, base)

# special_tests stub
def special_tests_ui():
    st.info("특수검사 모듈이 아직 연결되지 않아, 임시 안내만 보여드립니다.")
    col = st.columns(3)
    with col[0]:
        st.checkbox("Albumin(뇨)+", key=wkey("sp_alb"))
    with col[1]:
        st.checkbox("WBC(뇨)+", key=wkey("sp_wbc"))
    with col[2]:
        st.checkbox("Nitrite+", key=wkey("sp_nit"))
    st.caption("※ 실제 특수검사 UI는 special_tests.py 연결 시 자동 대체됩니다.")

# pdf_export stub
def export_md_to_pdf(md_text: str) -> bytes:
    return md_text.encode("utf-8")

# =========================
# 5) EMERGENCY SCORE
# =========================
DEFAULT_WEIGHTS = {
    "w_anc_lt500": 1.0, "w_anc_500_999": 1.0,
    "w_temp_38_0_38_4": 1.0, "w_temp_ge_38_5": 1.0,
    "w_plt_lt20k": 1.0, "w_hb_lt7": 1.0, "w_crp_ge10": 1.0, "w_hr_gt130": 1.0,
    "w_hematuria": 1.0, "w_melena": 1.0, "w_hematochezia": 1.0,
    "w_chest_pain": 1.0, "w_dyspnea": 1.0, "w_confusion": 1.0,
    "w_oliguria": 1.0, "w_persistent_vomit": 1.0, "w_petechiae": 1.0,
    "w_thunderclap": 1.0, "w_visual_change": 1.0,
}
PRESETS = {
    "기본(Default)": DEFAULT_WEIGHTS,
    "발열·감염 민감": {**DEFAULT_WEIGHTS, "w_temp_ge_38_5": 2.0, "w_temp_38_0_38_4": 1.5, "w_crp_ge10": 1.5, "w_anc_lt500": 2.0, "w_anc_500_999": 1.5},
    "출혈 위험 민감": {**DEFAULT_WEIGHTS, "w_plt_lt20k": 2.5, "w_petechiae": 2.0, "w_hematochezia": 2.0, "w_melena": 2.0},
    "신경계 위중 민감": {**DEFAULT_WEIGHTS, "w_thunderclap": 3.0, "w_visual_change": 2.5, "w_confusion": 2.5, "w_chest_pain": 1.2},
}

def get_weights() -> Dict[str,float]:
    key = st.session_state.get("key", "guest#PIN")
    store = st.session_state.setdefault("weights", {})
    return store.setdefault(key, dict(DEFAULT_WEIGHTS))

def set_weights(new_w: Dict[str,float]):
    key = st.session_state.get("key", "guest#PIN")
    st.session_state.setdefault("weights", {})
    st.session_state["weights"][key] = dict(new_w)

def anc_band(anc: float | None) -> str:
    if anc is None: return "(미입력)"
    try: anc = float(anc)
    except Exception: return "(값 오류)"
    if anc < 500: return "🚨 중증 호중구감소(<500)"
    if anc < 1000: return "🟧 중등도 호중구감소(500~999)"
    if anc < 1500: return "🟡 경도 호중구감소(1000~1499)"
    return "🟢 정상(≥1500)"

def emergency_level(labs: dict, temp_c, hr, symptoms: dict):
    a = _try_float((labs or {}).get("ANC"))
    p = _try_float((labs or {}).get("PLT"))
    c = _try_float((labs or {}).get("CRP"))
    h = _try_float((labs or {}).get("Hb"))
    t = _try_float(temp_c)
    heart = _try_float(hr)
    W = get_weights()
    reasons, contrib = [], []
    def add(name, base, wkey):
        w = W.get(wkey, 1.0); s = base*w
        contrib.append({"factor":name,"base":base,"weight":w,"score":s})
        reasons.append(name)
    if a is not None and a < 500:   add("ANC<500",3,"w_anc_lt500")
    elif a is not None and a < 1000:add("ANC 500~999",2,"w_anc_500_999")
    if t is not None and t >= 38.5: add("고열 ≥38.5℃",2,"w_temp_ge_38_5")
    elif t is not None and t >= 38: add("발열 38.0~38.4℃",1,"w_temp_38_0_38_4")
    if p is not None and p < 20000: add("혈소판 <20k",2,"w_plt_lt20k")
    if h is not None and h < 7.0:   add("중증 빈혈(Hb<7)",1,"w_hb_lt7")
    if c is not None and c >= 10:   add("CRP ≥10",1,"w_crp_ge10")
    if heart and heart > 130:       add("빈맥(HR>130)",1,"w_hr_gt130")
    # symptoms
    for k,wk,base in [
        ("hematuria","w_hematuria",1), ("melena","w_melena",2), ("hematochezia","w_hematochezia",2),
        ("chest_pain","w_chest_pain",2), ("dyspnea","w_dyspnea",2), ("confusion","w_confusion",3),
        ("oliguria","w_oliguria",2), ("persistent_vomit","w_persistent_vomit",2),
        ("petechiae","w_petechiae",2), ("thunderclap","w_thunderclap",3), ("visual_change","w_visual_change",2),
    ]:
        if symptoms.get(k): add(k, base, wk)
    risk = sum(x["score"] for x in contrib)
    level = "🚨 응급" if risk >= 5 else ("🟧 주의" if risk >= 2 else "🟢 안심")
    return level, reasons, contrib

# =========================
# 6) SIDEBAR (프로필/활력징후/모드)
# =========================
with st.sidebar:
    st.header("프로필")
    raw_key = st.text_input("별명#PIN (또는 별명만)", value=st.session_state.get("key","guest#PIN"), key="user_key_raw")
    pin_field = st.text_input("PIN 숫자 (별명만 입력 시)", value=st.session_state.get("_pin_raw",""), key="_pin_raw", type="password")
    if "#" in raw_key:
        nickname, pin = raw_key.split("#",1)[0].strip(), raw_key.split("#",1)[1].strip()
    else:
        nickname, pin = raw_key.strip(), pin_field.strip()
    # 간단 PIN 규칙
    def _is_valid_pin(p): return p.isdigit() and 4 <= len(p) <= 8
    if not pin: pin = "0000"
    st.session_state["key"] = f"{nickname}#{pin}"

    st.subheader("활력징후")
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""), key=wkey("cur_temp"))
    hr   = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""), key=wkey("cur_hr"))

    st.subheader("연령/모드")
    age_years = st.number_input("나이(년)", min_value=0.0, max_value=120.0,
                                value=_safe_float(st.session_state.get(wkey("age_years"), 0.0), 0.0),
                                step=0.5, key=wkey("age_years_num"))
    st.session_state[wkey("age_years")] = age_years
    auto_peds = age_years < 18.0
    manual_override = st.checkbox("소아/성인 수동 선택", value=False, key=wkey("mode_override"))
    if manual_override:
        is_peds = st.toggle("소아 모드", value=bool(st.session_state.get(wkey("is_peds"), auto_peds)), key=wkey("is_peds_tgl"))
    else:
        is_peds = auto_peds
    st.session_state[wkey("is_peds")] = is_peds
    st.caption(("현재 모드: **소아**" if is_peds else "현재 모드: **성인**") + (" (자동)" if not manual_override else " (수동)"))

# =========================
# 7) TABS (형 기존 순서)
# =========================
tab_labels = ["🏠 홈", "👶 소아 증상", "🧬 암 선택", "💊 항암제(진단 기반)", "🧪 피수치 입력", "🔬 특수검사", "📄 보고서", "📊 기록/그래프"]
t_home, t_peds, t_dx, t_chemo, t_labs, t_special, t_report, t_graph = st.tabs(tab_labels)

# ---------- HOME ----------
with t_home:
    st.subheader("응급도 요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp, _ = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), {})
    if level_tmp.startswith("🚨"): st.error("현재 상태: " + level_tmp)
    elif level_tmp.startswith("🟧"): st.warning("현재 상태: " + level_tmp)
    else: st.info("현재 상태: " + level_tmp)
    st.markdown("---")

    with st.expander("💬 피드백(앱 개선 제안/오류 신고)", expanded=False):
        fb_store_key = wkey("home_feedback_store")
        fb_widget_key = wkey("home_feedback_input")
        _default_fb = st.session_state.get(fb_store_key, "")
        fb_txt = st.text_area("피드백을 남겨주세요", value=_default_fb, height=120, key=fb_widget_key)

        c1,c2 = st.columns(2)
        def _save_fb():
            st.session_state[fb_store_key] = st.session_state.get(fb_widget_key, "")
            st.success("피드백이 저장되었습니다(세션 기준).")
        def _clear_fb():
            st.session_state[fb_store_key] = ""
            st.session_state[fb_widget_key] = ""
        with c1: st.button("피드백 저장(세션)", key=wkey("btn_fb_save"), on_click=_save_fb)
        with c2: st.button("피드백 지우기", key=wkey("btn_fb_clear"), on_click=_clear_fb)

        st.divider()
        st.markdown("#### 🙌 도움이 되었나요? (1~5점)")
        _score_key = wkey("home_fb_score")
        _score = st.radio("도움 정도 선택", options=[5,4,3,2,1],
                          format_func=lambda x:{5:"👍 매우 도움됨",4:"🙂 도움됨",3:"😐 보통",2:"🙁 별로",1:"👎 도움이 안 됨"}[x],
                          horizontal=True, key=_score_key, index=0)
        st.markdown("##### 빠른 태그(선택)")
        _tag_key = wkey("home_fb_tags")
        _tags = st.multiselect("어떤 점이 좋았나요/아쉬웠나요?",
                               ["속도가 빨라요","설명이 명확해요","UI가 편해요","오류가 있어요","모바일이 불편해요","기능이 부족해요","응급도 판정이 정확해요"],
                               default=[], key=_tag_key)

        fb_dir = DATA_BASE / "feedback"
        fb_dir.mkdir(exist_ok=True)
        fb_file = fb_dir / "home_feedback_metrics.json"
        def _load_fb():
            if not fb_file.exists():
                return {"ratings": [], "counts":{"1":0,"2":0,"3":0,"4":0,"5":0}}
            try:
                return json.loads(fb_file.read_text("utf-8"))
            except Exception:
                return {"ratings": [], "counts":{"1":0,"2":0,"3":0,"4":0,"5":0}}

        def _save_fb_store(data: dict):
            try:
                tmp = fb_file.with_suffix(".tmp")
                tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(tmp, fb_file)
            except Exception:
                pass

        def _submit_rating():
            data = _load_fb()
            data["counts"][str(_score)] = int(data["counts"].get(str(_score),0)) + 1
            entry = {"ts_kst": now_kst().isoformat(), "score": int(_score), "tags": list(_tags), "text_len": len(st.session_state.get(fb_widget_key,""))}
            data["ratings"].append(entry)
            if len(data["ratings"])>1000: data["ratings"]=data["ratings"][-1000:]
            _save_fb_store(data)
            st.success("피드백 점수가 저장되었습니다. 고맙습니다!")
        st.button("점수 저장", key=wkey("btn_fb_rate_save"), on_click=_submit_rating)

    st.subheader("응급도 체크(증상 기반)")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: hematuria = st.checkbox("혈뇨", key=wkey("sym_hematuria"))
    with c2: melena = st.checkbox("흑색변", key=wkey("sym_melena"))
    with c3: hematochezia = st.checkbox("혈변", key=wkey("sym_hematochezia"))
    with c4: chest_pain = st.checkbox("흉통", key=wkey("sym_chest"))
    with c5: dyspnea = st.checkbox("호흡곤란", key=wkey("sym_dyspnea"))
    with c6: confusion = st.checkbox("의식저하", key=wkey("sym_confusion"))
    d1,d2,d3 = st.columns(3)
    with d1: oliguria = st.checkbox("소변량 급감", key=wkey("sym_oliguria"))
    with d2: persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("sym_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("sym_petechiae"))
    e1,e2 = st.columns(2)
    with e1: thunderclap = st.checkbox("번개치는 듯한 두통(Thunderclap)", key=wkey("sym_thunderclap"))
    with e2: visual_change = st.checkbox("시야 이상/복시/암점", key=wkey("sym_visual_change"))

    sym = dict(hematuria=hematuria, melena=melena, hematochezia=hematochezia, chest_pain=chest_pain,
               dyspnea=dyspnea, confusion=confusion, oliguria=oliguria, persistent_vomit=persistent_vomit,
               petechiae=petechiae, thunderclap=thunderclap, visual_change=visual_change)

    alerts = []
    a = _try_float(st.session_state.get("labs_dict", {}).get("ANC"))
    p = _try_float(st.session_state.get("labs_dict", {}).get("PLT"))
    if thunderclap or (visual_change and (confusion or chest_pain or dyspnea)):
        alerts.append("🧠 **신경계 위중 의심** — 즉시 응급평가")
    if (a is not None and a < 500) and (_try_float(st.session_state.get(wkey("cur_temp"))) and _try_float(st.session_state.get(wkey("cur_temp"))) >= 38.0):
        alerts.append("🔥 **발열성 호중구감소증 의심** — 즉시 항생제 평가")
    if (p is not None and p < 20000) and (melena or hematochezia or petechiae):
        alerts.append("🩸 **출혈 고위험** — 즉시 병원")
    if oliguria and persistent_vomit:
        alerts.append("💧 **중등~중증 탈수 가능** — 수액 고려")
    if chest_pain and dyspnea:
        alerts.append("❤️ **흉통+호흡곤란** — 응급평가 권장")
    for msg in alerts: st.error(msg) if alerts else st.info("위험 조합 경고 없음")

    level, reasons, _ = emergency_level(st.session_state.get("labs_dict", {}), st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), sym)
    if level.startswith("🚨"): st.error("응급도: " + level + (" — " + " · ".join(reasons) if reasons else ""))
    elif level.startswith("🟧"): st.warning("응급도: " + level + (" — " + " · ".join(reasons) if reasons else ""))
    else: st.info("응급도: " + level + (" — " + " · ".join(reasons) if reasons else ""))

# ---------- PEDS ----------
with t_peds:
    st.subheader("소아 증상 기반 점수 + 보호자 설명 + 해열제 계산")

    st.markdown("""
    <style>
      .peds-nav-md{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin:.25rem 0 .5rem;}
      .peds-nav-md a{display:block;text-align:center;padding:.6rem .8rem;border-radius:12px;border:1px solid #ddd;text-decoration:none;color:inherit;background:#fff}
      .peds-nav-md a:active{transform:scale(.98)}
    </style>
    <div class="peds-nav-md">
      <a href="#peds_constipation">🧻 변비</a>
      <a href="#peds_diarrhea">💦 설사</a>
      <a href="#peds_vomit">🤢 구토</a>
      <a href="#peds_antipyretic">🌡️ 해열제</a>
      <a href="#peds_ors">🥤 ORS·탈수</a>
      <a href="#peds_respiratory">🫁 가래·쌕쌕</a>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: nasal = st.selectbox("콧물", ["없음","투명","진득","누런"], key=wkey("p_nasal"))
    with c2: cough = st.selectbox("기침", ["없음","조금","보통","심함"], key=wkey("p_cough"))
    with c3: stool = st.selectbox("설사", ["없음","1~2회","3~4회","5~6회","7회 이상"], key=wkey("p_stool"))
    with c4: fever = st.selectbox("발열", ["없음","37~37.5 (미열)","37.5~38","38~38.5","38.5~39","39 이상"], key=wkey("p_fever"))
    with c5: eye = st.selectbox("눈꼽/결막", ["없음","맑음","노랑-농성","양쪽"], key=wkey("p_eye"))

    constipation = st.selectbox("변비", ["없음","의심","3일 이상","배변 시 통증"], key=wkey("p_constipation"))
    g1,g2 = st.columns(2)
    with g1: sputum = st.selectbox("가래", ["없음","조금","보통","많음"], key=wkey("p_sputum"))
    with g2: wheeze = st.selectbox("쌕쌕거림(천명)", ["없음","조금","보통","심함"], key=wkey("p_wheeze"))
    d1,d2,d3 = st.columns(3)
    with d1: oliguria = st.checkbox("소변량 급감", key=wkey("p_oliguria"))
    with d2: persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("p_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("p_petechiae"))
    e1,e2,e3 = st.columns(3)
    with e1: abd_pain = st.checkbox("복통/배마사지 거부", key=wkey("p_abd_pain"))
    with e2: ear_pain = st.checkbox("귀 통증/만지면 울음", key=wkey("p_ear_pain"))
    with e3: rash = st.checkbox("가벼운 발진/두드러기", key=wkey("p_rash"))
    f1,f2,f3 = st.columns(3)
    with f1: hives = st.checkbox("두드러기·알레르기 의심", key=wkey("p_hives"))
    with f2: migraine = st.checkbox("편두통 의심", key=wkey("p_migraine"))
    with f3: hfmd = st.checkbox("수족구 의심", key=wkey("p_hfmd"))

    duration = st.selectbox("증상 지속일수", ["선택 안 함","1일","2일","3일 이상"], key=wkey("p_duration"))
    duration_val = None if duration=="선택 안 함" else duration

    max_temp = st.number_input("최고 체온(°C)", min_value=34.0, max_value=43.5, step=0.1, format="%.1f", key=wkey("p_max_temp"))
    col_rf1,col_rf2,col_rf3,col_rf4 = st.columns(4)
    with col_rf1: red_seizure = st.checkbox("경련/의식저하", key=wkey("p_red_seizure"))
    with col_rf2: red_bloodstool = st.checkbox("혈변/검은변", key=wkey("p_red_blood"))
    with col_rf3: red_night = st.checkbox("야간/새벽 악화", key=wkey("p_red_night"))
    with col_rf4: red_dehydration = st.checkbox("탈수 의심(눈물↓·입마름)", key=wkey("p_red_dehyd"))

    fever_flag = (max_temp is not None and max_temp >= 38.5)
    danger_count = sum([1 if x else 0 for x in [red_seizure, red_bloodstool, red_night, red_dehydration, fever_flag]])
    if red_seizure or red_bloodstool or (max_temp is not None and max_temp >= 39.0):
        risk_badge = "🚨"; st.error("🚨 고위험 신호가 있습니다. 즉시 병원(응급실) 평가 권장")
    elif danger_count >= 2:
        risk_badge = "🟡"; st.warning("🟡 주의 필요 — 수분 보충/해열제 간격 준수하며 면밀 관찰")
    else:
        risk_badge = "🟢"; st.info("🟢 비교적 안정 신호 — 악화 시 상위 단계 조치")

    # ANC 기반 음식안전 경고
    try:
        anc_val = float(str(st.session_state.get("labs_dict",{}).get("ANC","")).replace(",", "."))
    except Exception:
        anc_val = None
    if anc_val is not None and anc_val < 1000:
        st.warning("🍽️ 저호중구 시: 생야채/껍질 과일 피하고, 완전 가열 섭취. 남은 음식은 2시간 이후 섭취 비권장. 멸균·살균 식품 권장.")

    # 간단 점수(요약 표시만)
    score = { "장염 의심":0, "상기도/독감 계열":0, "결막염 의심":0, "탈수/신장 문제":0,
              "출혈성 경향":0, "중이염/귀질환":0, "피부발진/경미한 알레르기":0,
              "복통 평가":0, "알레르기 주의":0, "편두통 의심":0, "수족구 의심":0,
              "하기도/천명 주의":0, "가래 동반 호흡기":0, "아데노바이러스 의심":0 }
    if stool in ["3~4회","5~6회","7회 이상"]: score["장염 의심"] += {"3~4회":40,"5~6회":55,"7회 이상":70}[stool]
    if fever in ["38~38.5","38.5~39","39 이상"]: score["상기도/독감 계열"] += 25
    if cough in ["조금","보통","심함"]: score["상기도/독감 계열"] += 20
    if sputum in ["조금","보통","많음"]: score["가래 동반 호흡기"] += {"조금":10,"보통":20,"많음":30}[sputum]
    if wheeze in ["조금","보통","심함"]: score["하기도/천명 주의"] += {"조금":25,"보통":40,"심함":60}[wheeze]
    if eye in ["노랑-농성","양쪽"]: score["결막염 의심"] += 30
    if oliguria: score["탈수/신장 문제"] += 40; score["장염 의심"] += 10
    if persistent_vomit: score["장염 의심"] += 25; score["탈수/신장 문제"] += 15; score["복통 평가"] += 10
    if petechiae: score["출혈성 경향"] += 60
    if ear_pain: score["중이염/귀질환"] += 35
    if rash: score["피부발진/경미한 알레르기"] += 25
    if abd_pain: score["복통 평가"] += 25
    if hives: score["알레르기 주의"] += 60
    if migraine: score["편두통 의심"] += 35
    if hfmd: score["수족구 의심"] += 40
    ordered = sorted(score.items(), key=lambda x: x[1], reverse=True)
    st.write("• " + " / ".join([f"{k}: {v}" for k,v in ordered if v>0]) if any(v>0 for _,v in ordered) else "• 특이 점수 없음")

    # 간단 보호자 설명(요약)
    with st.expander("👪 보호자 설명(요약)", expanded=False):
        if fever!="없음":
            st.markdown("- 발열: 얇은 옷, 미온수 닦기, **APAP ≥4h / IBU ≥6h**, 수분 보충")
            if max_temp and max_temp >= 39.0: st.markdown("  - **현재 39℃ 이상 → 즉시 병원 권고**")
        if (stool!="없음") or persistent_vomit or oliguria:
            st.markdown("- 장 증상: ORS 5~10분마다 소량, 기름진 음식·생야채·우유 일시 제한")
            st.markdown("  - 혈변/검은변, 심한 복통/지속 구토, 소변 없음 → 진료")
        if cough!="없음" or nasal!="없음":
            st.markdown("- 호흡기: 생리식염수 세척/가습, 수면 시 머리 높이기")
            if wheeze!="없음": st.markdown("  - 쌕쌕거림 동반 시 악화 주의, 호흡곤란 시 즉시 병원")
        if eye in ["노랑-농성","양쪽"]:
            st.markdown("- 눈: 분비물 위생(안쪽→바깥쪽), 통증/고열 시 진료")

    # 해열제 간단 계산(체중 기반 대략)
    st.markdown("---")
    st.subheader("해열제 계산기")
    wt = st.number_input("체중(kg)", min_value=0.0, max_value=200.0, value=_safe_float(st.session_state.get(wkey("wt_peds"),0.0),0.0), step=0.1, key=wkey("wt_peds_num"))
    st.session_state[wkey("wt_peds")] = wt
    # APAP 10-15 mg/kg → 160mg/5mL 시럽 환산 ≈ mL = (용량(mg) / 160)*5
    apap_mg = max(0.0, 12.5 * wt)
    apap_ml = apap_mg/160*5 if wt>0 else 0.0
    # IBU 10 mg/kg → 100mg/5mL 시럽 환산
    ibu_mg = max(0.0, 10.0 * wt)
    ibu_ml = ibu_mg/100*5 if wt>0 else 0.0
    colA,colB = st.columns(2)
    with colA: st.write(f"아세트아미노펜 시럽(160mg/5mL): **{apap_ml:.1f} mL** (≥4시간 간격)")
    with colB: st.write(f"이부프로펜 시럽(100mg/5mL): **{ibu_ml:.1f} mL** (≥6시간 간격)")
    st.caption("※ 금기/주의 질환에 따라 달라질 수 있으니, 반드시 의료진 지시에 따르세요.")

# ---------- DX ----------
with t_dx:
    st.subheader("암 선택")
    ONCO = build_onco_map() or {}
    groups = sorted(ONCO.keys()) if ONCO else ["혈액암","고형암"]
    group = st.selectbox("암 그룹", options=groups, index=0, key=wkey("onco_group_sel"))
    diseases = sorted(ONCO.get(group, {}).keys()) if ONCO else ["ALL","AML","Lymphoma","Breast","Colon","Lung"]
    disease = st.selectbox("의심/진단명", options=diseases, index=0, key=wkey("onco_disease_sel"),
                           format_func=lambda x: (f"{x} (" + (DX_KO.get(_dx_norm(x)) or DX_KO.get(x) or x) + ")") if not re.search(r"[가-힣]", str(x)) else str(x))
    _pin_dx_route()  # 홈 튐 방지

    try:
        disp = dx_display(group, disease)
    except Exception:
        disp = f"{group} - {disease}"
        st.warning("진단 정보 표시 중 문제가 발생했어요. 선택을 다시 확인해 주세요.")
    st.session_state["onco_group"] = group
    st.session_state["onco_disease"] = disease
    st.session_state["dx_disp"] = disp
    st.info(f"선택: {disp}")

    recs = auto_recs_by_dx(group, disease, DRUG_DB) or {}
    if any(recs.values()):
        st.markdown("**자동 추천 요약**")
        for cat, arr in recs.items():
            if arr: st.write(f"- {cat}: " + ", ".join(arr))
    st.session_state["recs_by_dx"] = recs

# ---------- CHEMO ----------
def _to_set_or_empty(x) -> set:
    s=set()
    if not x: return s
    if isinstance(x,str):
        for p in re.split(r"[;,/]|\s+", x):
            p=p.strip().lower()
            if p: s.add(p)
    elif isinstance(x,(list,tuple,set)):
        for p in x:
            p=str(p).strip().lower()
            if p: s.add(p)
    elif isinstance(x,dict):
        for k,v in x.items():
            s.add(str(k).strip().lower())
            if isinstance(v,(list,tuple,set)):
                s |= {str(t).strip().lower() for t in v}
    return s

def _meta_for_drug(key: str) -> Dict[str,Any]:
    rec = DRUG_DB.get(key, {})
    klass = str(rec.get("class","")).strip().lower()
    tags = _to_set_or_empty(rec.get("tags")) | _to_set_or_empty(rec.get("properties"))
    if "qt" in tags or "qt-prolong" in tags: tags.add("qt_prolong")
    if "myelo" in tags or "myelosuppression" in tags: tags.add("myelosuppression")
    return {"class":klass, "tags":tags, "raw":rec}

def check_chemo_interactions(keys: List[str]) -> Tuple[List[str], List[str]]:
    warns, notes = [], []
    if not keys: return warns, notes
    metas = {k:_meta_for_drug(k) for k in keys}
    classes={}
    for k,m in metas.items():
        if m["class"]:
            classes.setdefault(m["class"], []).append(k)
    for klass, arr in classes.items():
        if len(arr)>=2 and klass not in ("antiemetic","hydration"):
            warns.append(f"동일 계열 **{klass}** 중복({', '.join(arr)}) — 누적 독성 주의")
    qt_list = [k for k,m in metas.items() if "qt_prolong" in m["tags"]]
    if len(qt_list)>=2: warns.append(f"**QT 연장 위험** 약물 다수 병용({', '.join(qt_list)}) — EKG/전해질 모니터링")
    myelo_list = [k for k,m in metas.items() if "myelosuppression" in m["tags"]]
    if len(myelo_list)>=2: warns.append(f"**강한 골수억제 병용**({', '.join(myelo_list)}) — 감염/출혈 위험 ↑")
    return warns, notes

def _aggregate_all_aes(meds: List[str], db: Dict[str,Any]) -> Dict[str, List[str]]:
    result={}
    if not meds: return result
    fields=["ae","ae_ko","adverse_effects","warnings","toxicity","notes"]
    for k in meds:
        rec=db.get(k) or {}
        lines=[]
        for f in fields:
            v=rec.get(f)
            if not v: continue
            if isinstance(v,str):
                for chunk in v.split("\n"):
                    for semi in chunk.split(";"):
                        for p in semi.split(","):
                            q=p.strip()
                            if q: lines.append(q)
            elif isinstance(v,(list,tuple)):
                for s in v:
                    for p in str(s).split(","):
                        q=p.strip()
                        if q: lines.append(q)
        seen=set(); uniq=[]
        for s in lines:
            if s not in seen:
                uniq.append(s); seen.add(s)
        if uniq: result[k]=uniq
    return result

with t_chemo:
    st.subheader("항암제(진단 기반)")
    group = st.session_state.get("onco_group")
    disease = st.session_state.get("onco_disease")
    recs = st.session_state.get("recs_by_dx", {}) or {}

    rec_chemo = list(dict.fromkeys(recs.get("chemo", []))) if recs else []
    rec_target = list(dict.fromkeys(recs.get("targeted", []))) if recs else []
    recommended = rec_chemo + [x for x in rec_target if x not in rec_chemo]

    # 추천이 없으면 DB 전체 중 진단명 키워드로 간단 매칭
    if (not recommended) and DRUG_DB and disease:
        d = (disease or "").lower()
        for k in DRUG_DB.keys():
            if d in k.lower(): recommended.append(k)

    label_map = {k: display_label(k, DRUG_DB) for k in DRUG_DB.keys()}
    show_all = st.toggle("전체 보기(추천 외 약물 포함)", value=False, key=wkey("chemo_show_all"))
    pool_keys = sorted(label_map.keys()) if (show_all or not recommended) else recommended
    if show_all or not recommended: st.caption("현재: 전체 약물 목록에서 선택")
    else: st.caption("현재: 진단 기반 추천 목록에서 선택")

    pool_labels = [label_map.get(k, str(k)) for k in pool_keys]
    unique_pairs = sorted(set(zip(pool_labels, pool_keys)), key=lambda x: x[0].lower())
    pool_labels_sorted = [p[0] for p in unique_pairs]
    picked_labels = st.multiselect("투여/계획 약물 선택", options=pool_labels_sorted, default=pool_labels_sorted, key=wkey("drug_pick"))
    label_to_key = {lbl:key for (lbl,key) in unique_pairs}
    picked_keys = [label_to_key.get(lbl) for lbl in picked_labels if lbl in label_to_key]
    st.session_state["chemo_keys"] = picked_keys

    if not picked_keys:
        st.caption("선택된 항암제가 없어 기본값으로 복구했어요.")
        picked_keys = [label_to_key.get(lbl) for lbl in pool_labels_sorted]
        st.session_state["chemo_keys"] = picked_keys

    if picked_keys:
        st.markdown("### 선택 약물")
        for k in picked_keys:
            st.write("- " + label_map.get(k, str(k)))

        warns, notes = check_chemo_interactions(picked_keys)
        if warns:
            st.markdown("### ⚠️ 병용 주의/경고")
            for w in warns: st.error(w)

        ae_map = _aggregate_all_aes(picked_keys, DRUG_DB)
        st.markdown("### 항암제 부작용(전체)")
        if ae_map:
            for k, arr in ae_map.items():
                st.write(f"- **{label_map.get(k, str(k))}**")
                for ln in arr:
                    st.write(f"  - {ln}")
        else:
            st.write("- (DB에 상세 부작용 없음)")

# ---------- LABS ----------
LAB_REF_ADULT = {"WBC":(4.0,10.0),"Hb":(12.0,16.0),"PLT":(150,400),"ANC":(1500,8000),"CRP":(0.0,5.0),
                 "Na":(135,145),"Cr":(0.5,1.2),"Glu":(70,140),"Ca":(8.6,10.2),"P":(2.5,4.5),
                 "T.P":(6.4,8.3),"AST":(0,40),"ALT":(0,41),"T.B":(0.2,1.2),"Alb":(3.5,5.0),"BUN":(7,20)}
LAB_REF_PEDS = {"WBC":(5.0,14.0),"Hb":(11.0,15.0),"PLT":(150,450),"ANC":(1500,8000),"CRP":(0.0,5.0),
                "Na":(135,145),"Cr":(0.2,0.8),"Glu":(70,140),"Ca":(8.8,10.8),"P":(4.0,6.5),
                "T.P":(6.0,8.0),"AST":(0,50),"ALT":(0,40),"T.B":(0.2,1.2),"Alb":(3.8,5.4),"BUN":(5,18)}
def lab_ref(is_peds: bool): return LAB_REF_PEDS if is_peds else LAB_REF_ADULT
def lab_validate(abbr: str, val, is_peds: bool):
    rng = lab_ref(is_peds).get(abbr)
    if rng is None or val in (None,""): return None
    try: v=float(val)
    except Exception: return "형식 오류"
    lo,hi=rng
    if v<lo: return f"⬇️ 기준치 미만({lo}~{hi})"
    if v>hi: return f"⬆️ 기준치 초과({lo}~{hi})"
    return "정상범위"

with t_labs:
    st.subheader("피수치 입력 — 붙여넣기 지원")
    st.caption("예: 'WBC: 4.5', 'Hb 12.3', 'PLT, 200', 'Na 140 mmol/L'…")

    auto_is_peds = bool(st.session_state.get(wkey("is_peds"), False))
    st.toggle("소아 기준 자동 적용(나이 기반)", value=True, key=wkey("labs_auto_mode"))
    use_peds = auto_is_peds if st.session_state.get(wkey("labs_auto_mode")) else st.checkbox("소아 기준(참조범위/검증)", value=auto_is_peds, key=wkey("labs_use_peds_manual"))

    order=[("WBC","백혈구"),("Ca","칼슘"),("Glu","혈당"),("CRP","CRP"),("Hb","혈색소"),("P","인"),
           ("T.P","총단백"),("Cr","크레아티닌"),("PLT","혈소판"),("Na","나트륨"),("AST","AST"),
           ("T.B","총빌리루빈"),("ANC","절대호중구"),("Alb","알부민"),("ALT","ALT"),("BUN","BUN")]

    with st.expander("📋 검사값 붙여넣기(자동 인식)", expanded=False):
        pasted = st.text_area("예: WBC: 4.5\nHb 12.3\nPLT, 200\nNa 140 mmol/L", height=120, key=wkey("labs_paste"))
        if st.button("붙여넣기 파싱 → 적용", key=wkey("parse_paste")):
            parsed={}
            try:
                if pasted:
                    for line in str(pasted).splitlines():
                        s=line.strip()
                        if not s: continue
                        parts=re.split(r'[:;,\t\-=\u00b7\u2022]| {2,}', s)
                        parts=[p for p in parts if p.strip()]
                        if len(parts)>=2:
                            k=parts[0].strip()
                            v=_try_float(parts[1])
                            if k and (v is not None): parsed[k]=v; continue
                        toks=s.split()
                        if len(toks)>=2:
                            k=toks[0].strip(); v=_try_float(" ".join(toks[1:]))
                            if k and (v is not None): parsed[k]=v
                if parsed:
                    for abbr,_ in order:
                        if abbr in parsed: st.session_state[wkey(abbr)] = parsed[abbr]
                    st.success(f"적용됨: {', '.join(list(parsed.keys())[:12])} ...")
                else:
                    st.info("인식 가능한 수치를 찾지 못했습니다. 줄마다 '항목 값' 형태인지 확인해주세요.")
            except Exception:
                st.error("파싱 중 예외가 발생했지만 앱은 계속 동작합니다. 입력 형식을 다시 확인하세요.")

    cols = st.columns(4)
    values={}
    for i,(abbr,kor) in enumerate(order):
        with cols[i%4]:
            val = st.text_input(f"{abbr} — {kor}", value=str(st.session_state.get(wkey(abbr), "")), key=wkey(abbr))
            values[abbr] = _try_float(val)
            msg = lab_validate(abbr, values[abbr], use_peds)
            if msg: st.caption(("✅ " if msg=="정상범위" else "⚠️ ")+msg)
    labs_dict = st.session_state.get("labs_dict", {})
    labs_dict.update(values)
    st.session_state["labs_dict"] = labs_dict
    st.markdown(f"**참조범위 기준:** {'소아' if use_peds else '성인'} / **ANC 분류:** {anc_band(values.get('ANC'))}")

# ---------- SPECIAL TESTS ----------
with t_special:
    st.subheader("🔬 특수검사")
    special_tests_ui()

# ---------- REPORT ----------
with t_report:
    st.subheader("📄 보고서")
    dx_text = st.session_state.get("dx_disp", "(진단 선택 없음)")
    labs = st.session_state.get("labs_dict", {})
    lines = [f"# 보고서({now_kst().strftime('%Y-%m-%d %H:%M KST')})",
             f"- 진단: {dx_text}",
             "- 피수치:"]
    for k in ["WBC","Hb","PLT","ANC","CRP","Na","Cr","Glu","Ca","P","AST","ALT","T.B","Alb","BUN","T.P"]:
        v = labs.get(k)
        if v is not None: lines.append(f"  - {k}: {v}")
    md = "\n".join(lines)
    st.text_area("미리보기", value=md, height=240, key=wkey("report_md"))
    if st.button("PDF로 내보내기(간이)", key=wkey("btn_pdf")):
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("다운로드: report.pdf", data=pdf_bytes, file_name="report.pdf", mime="application/pdf", key=wkey("dl_pdf"))

# ---------- GRAPH ----------
with t_graph:
    st.subheader("📊 기록/그래프 (간이)")
    st.caption("※ 간이 스토리지(/mnt/data → /mount/data → /tmp) 사용")
    store_dir = DATA_BASE / "bloodmap_graph"
    store_dir.mkdir(exist_ok=True)
    uid = st.session_state.get("key","guest#PIN").replace("#","_")
    csv_path = store_dir / f"{uid}.labs.csv"

    labs = st.session_state.get("labs_dict", {})
    cols = st.columns(2)
    with cols[0]:
        if st.button("현재 수치 CSV에 추가", key=wkey("btn_save_csv")):
            row = {"ts": now_kst().isoformat()}
            row.update({k: labs.get(k) for k in ["WBC","Hb","PLT","ANC","CRP","Na","Cr","Glu"]})
            existed = csv_path.exists()
            with csv_path.open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not existed: w.writeheader()
                w.writerow(row)
            st.success(f"저장됨: {csv_path}")
    with cols[1]:
        if csv_path.exists():
            st.caption(f"파일: {csv_path}")
            try:
                import pandas as pd
                df = pd.read_csv(csv_path)
                st.dataframe(df.tail(20), use_container_width=True)
                # 간이 라인 차트
                for col in ["WBC","Hb","PLT","ANC","CRP"]:
                    if col in df.columns:
                        st.line_chart(df.set_index("ts")[col], height=160)
            except Exception:
                st.info("pandas를 사용할 수 없어 표/차트 미표시.")

# 마지막: 홈 튐 방지
_block_spurious_home()
