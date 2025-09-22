
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date

from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml
from pdf_export import export_md_to_pdf




# === AUTO: visitor metrics helpers ===
import os as _os, json as _json, datetime as _dt, uuid as _uuid
def _metrics_visits_path():
    base = "/mnt/data/metrics"
    try: _os.makedirs(base, exist_ok=True)
    except Exception: pass
    return f"{base}/visits.json"
def _metrics_load():
    try:
        with open(_metrics_visits_path(), "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception: return {}
def _metrics_save(d: dict):
    p = _metrics_visits_path(); tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump(d, f, ensure_ascii=False, indent=2)
        _os.replace(tmp, p)
    except Exception: pass
def _metrics_bump(uid: str|None, session_id: str|None):
    data = _metrics_load() or {}
    today = _dt.date.today().isoformat()
    t = data.get("today") or {}
    if t.get("date") != today: t = {"date": today, "visits": 0, "unique": 0, "uids": []}
    data["today"] = t
    tot = data.get("totals") or {"visits": 0, "unique": 0, "uids": []}
    data["totals"] = tot
    key = str(uid or session_id or _uuid.uuid4().hex[:12])
    t["visits"] = int(t.get("visits", 0)) + 1; tot["visits"] = int(tot.get("visits", 0)) + 1
    if key not in t.get("uids", []):
        t["uids"].append(key); t["unique"] = int(t.get("unique", 0)) + 1
    if key not in tot.get("uids", []):
        tot["uids"].append(key); tot["unique"] = int(tot.get("unique", 0)) + 1
    _metrics_save(data)
def _metrics_today_totals():
    d = _metrics_load() or {}
    t = d.get("today") or {}
    T = d.get("totals") or {}
    return {
        "today_unique": int(t.get("unique", 0) or 0),
        "today_visits": int(t.get("visits", 0) or 0),
        "total_unique": int(T.get("unique", 0) or 0),
        "total_visits": int(T.get("visits", 0) or 0),
    }
# === /AUTO ===




# === AUTO: GI/FEVER tools (under Special Tests) with summary + log + filters/CSV ===
def _gi_block_render_and_log(context: dict):
    import streamlit as st, datetime as _dt, pandas as _pd, os as _os, json as _json, io as _io
    def _calc_severity(diarrhea_type, diarrhea_freq, vomit_type, vomit_freq, fever_temp):
        sev = "🟢 안정"; reasons = []
        try:
            if (fever_temp or 0) >= 39.0: sev = "🚨 위중"; reasons.append("고열 ≥39℃")
            elif (fever_temp or 0) >= 38.0: sev = "🟧 주의"; reasons.append("발열 ≥38℃")
            if (diarrhea_freq or 0) >= 4:
                if sev!="🚨 위중": sev = "🟧 주의"
                reasons.append("설사 ≥4회/일")
            if (vomit_freq or 0) >= 3:
                if sev!="🚨 위중": sev = "🟧 주의"
                reasons.append("구토 ≥3회/일")
            if ("혈변" in (diarrhea_type or "")) or ("혈성" in (vomit_type or "")):
                sev = "🚨 위중"; reasons.append("혈변/혈성 구토")
        except Exception:
            pass
        return sev, reasons
    def _gi_log_path(uid:str):
        base = "/mnt/data/care_log"
        try: _os.makedirs(base, exist_ok=True)
        except Exception: pass
        return f"{base}/{uid}_gi.jsonl"
    def _gi_log_append(uid:str, rec:dict):
        p = _gi_log_path(uid)
        try:
            with open(p, "a", encoding="utf-8") as f:
                f.write(_json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception: pass
    def _gi_log_read(uid:str, limit:int=1000):
        p = _gi_log_path(uid)
        rows = []
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    try: rows.append(_json.loads(line))
                    except Exception: continue
        except FileNotFoundError: pass
        rows = rows[-limit:]
        return _pd.DataFrame(rows) if rows else _pd.DataFrame(columns=["ts","설사","횟수","구토","횟수2","체온"])
    st.markdown("#### 🚽 설사 / 🤮 구토 / 🌡️ 해열제")
    with st.expander("기록/계산", expanded=False):
        c_d1, c_d2 = st.columns([2,1])
        with c_d1:
            diarrhea_type = st.selectbox("설사(구분표)", ["", "노란색 설사", "진한 노란색 설사", "거품 설사", "녹색 설사", "녹색 혈변", "혈변", "검은색 변"], index=0)
        with c_d2:
            diarrhea_freq = st.number_input("설사 횟수(회/일)", min_value=0, step=1, value=0)
        c_v1, c_v2 = st.columns([2,1])
        with c_v1:
            vomit_type = st.selectbox("구토(구분)", ["", "흰색/묽음", "노란색/담즙", "초록색/담즙", "혈성 의심"], index=0)
        with c_v2:
            vomit_freq = st.number_input("구토 횟수(회/일)", min_value=0, step=1, value=0)
        c_w1, c_w2, c_w3 = st.columns(3)
        with c_w1:
            body_weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=0.0, key="antipy_weight_gi")
        with c_w2:
            age_years = st.number_input("나이(년)", min_value=0, step=1, value=0, key="antipy_age_gi")
        with c_w3:
            fever_temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key="antipy_temp_gi")
        def _dose_apap(weight):
            if not weight or weight <= 0: return None
            low = round(10 * weight); high = round(15 * weight)
            return low, high
        def _dose_ibu(weight, age):
            if not weight or weight <= 0: return None
            if age is not None and age < 0.5: return None
            dose = round(10 * weight)
            return dose
        apap = _dose_apap(body_weight); ibu  = _dose_ibu(body_weight, age_years)
        sev_level, reasons = _calc_severity(diarrhea_type, diarrhea_freq, vomit_type, vomit_freq, fever_temp)
        summary_lines = []
        summary_lines.append(f"- 응급도: **{sev_level}**" + (f" ({' / '.join(reasons)})" if reasons else ""))
        if fever_temp: summary_lines.append(f"- 체온: {fever_temp:.1f}℃")
        if diarrhea_type or diarrhea_freq: summary_lines.append(f"- 설사: {diarrhea_type or '-'} / {int(diarrhea_freq or 0)}회/일")
        if vomit_type or vomit_freq: summary_lines.append(f"- 구토: {vomit_type or '-'} / {int(vomit_freq or 0)}회/일")
        if apap: summary_lines.append(f"- APAP 권장 1회: {apap[0]}–{apap[1]} mg (4–6h)")
        if ibu:  summary_lines.append(f"- IBU 권장 1회: {ibu} mg (6–8h)")
        context["gi_summary_md"] = "## 🚽/🤮/🌡️ 위장/발열 요약\n" + "\n".join(summary_lines)
        st.markdown(f"**응급도: {sev_level}**  " + (" / ".join(reasons) if reasons else ""))
        _uid = st.session_state.get("user_key")
        col_log_btn, _ = st.columns([1,3])
        clicked = col_log_btn.button("기록 추가", use_container_width=True)
        if clicked and _uid:
            rec = {"ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                   "설사": diarrhea_type, "횟수": int(diarrhea_freq or 0),
                   "구토": vomit_type, "횟수2": int(vomit_freq or 0),
                   "체온": float(fever_temp or 0.0)}
            _gi_log_append(_uid, rec); st.success("기록을 저장했어요.")
        if _uid:
            df_log = _gi_log_read(_uid, limit=2000)
            if not df_log.empty:
                def _parse_ts(s):
                    try: return _dt.datetime.strptime(str(s), "%Y-%m-%d %H:%M")
                    except Exception:
                        try: return _dt.datetime.fromisoformat(str(s))
                        except Exception: return None
                df_log["__dt"] = df_log["ts"].apply(_parse_ts); df_log = df_log.dropna(subset=["__dt"])
                def _sev_row(row):
                    sev,_ = _calc_severity(row.get("설사"), row.get("횟수"), row.get("구토"), row.get("횟수2"), row.get("체온"))
                    return sev
                df_log["응급도"] = df_log.apply(_sev_row, axis=1)
                min_d = df_log["__dt"].min().date(); max_d = df_log["__dt"].max().date()
                f1, f2, f3, f4 = st.columns([1.2, 1.2, 1.2, 1.4])
                with f1:
                    d_from = st.date_input("시작일", value=min_d, min_value=min_d, max_value=max_d, key="gi_filter_from")
                with f2:
                    d_to   = st.date_input("종료일", value=max_d, min_value=min_d, max_value=max_d, key="gi_filter_to")
                with f3:
                    sev_pick = st.multiselect("응급도", options=["🚨 위중","🟧 주의","🟢 안정"], default=[], key="gi_filter_sev")
                with f4:
                    kw = st.text_input("키워드(설사/구토/메모)", value="", key="gi_filter_kw", placeholder="예: 혈변, 담즙")
                mask = (df_log["__dt"].dt.date >= d_from) & (df_log["__dt"].dt.date <= d_to)
                if sev_pick: mask &= df_log["응급도"].isin(sev_pick)
                if kw:
                    kwl = kw.strip().lower()
                    def _has_kw(row):
                        blob = f"{row.get('설사','')} {row.get('구토','')}".lower()
                        return kwl in blob
                    mask &= df_log.apply(_has_kw, axis=1)
                df_f = df_log.loc[mask].copy().sort_values("__dt", ascending=False)
                view_cols = ["ts","응급도","설사","횟수","구토","횟수2","체온"]
                st.markdown("##### 최근 기록 (필터 적용)")
                st.dataframe(df_f[view_cols], use_container_width=True, hide_index=True)
                buf = _io.StringIO(); df_f[view_cols].to_csv(buf, index=False, encoding="utf-8")
                st.download_button("CSV 내보내기", data=buf.getvalue().encode("utf-8"),
                                   file_name=f"{_uid}_gi_log_filtered.csv", mime="text/csv",
                                   use_container_width=True)
# === /AUTO ===


# 세션 플래그(중복 방지)
if "summary_line_shown" not in st.session_state:
    st.session_state["summary_line_shown"] = False

def short_caption(label: str) -> str:
    """
    peds_profiles.peds_short_caption()가 있으면 우선 사용,
    없으면 기본 문구로 보조하는 안전 헬퍼.
    """
    try:
        from peds_profiles import peds_short_caption as _peds_short_caption  # type: ignore
        s = _peds_short_caption(label or "")
        if s:
            return s
    except Exception:
        pass
    defaults = {
        "로타바이러스 장염": "영유아 위장관염 — 물설사·구토, 탈수 주의",
        "노로바이러스 장염": "급성 구토/설사 급발현 — 겨울철 유행, 탈수 주의",
        "바이럴 장염(비특이)": "대개 바이러스성 — 수분·전해질 보충과 휴식",
        "감기/상기도바이러스": "콧물·기침 중심 — 수분·가습·휴식",
        "독감(인플루엔자) 의심": "고열+근육통 — 48시간 내 항바이러스제 상담",
        "코로나 가능": "고열·기침·권태 — 신속항원검사/격리 고려",
        "세균성 편도/부비동염 가능": "고열+농성 콧물/안면통 — 항생제 필요 여부 진료로 결정",
        "장염(바이러스) 의심": "물설사·복통 — 수분·전해질 보충",
        "세균성 결막염 가능": "농성 눈꼽·한쪽 시작 — 항생제 점안 상담",
        "아데노바이러스 결막염 가능": "고열+양측 결막염 — 전염성, 위생 철저",
        "알레르기성 결막염 가능": "맑은 눈물·가려움 — 냉찜질·항히스타민 점안",
        "급성기관지염 가능": "기침 중심 — 대개 바이러스성, 경과관찰",
        "폐렴 의심": "호흡곤란/흉통·고열 — 흉부 X-ray/항생제 평가",
        "RSV": "모세기관지염 — 끈적가래로 쌕쌕/호흡곤란 가능",
    }
    return defaults.get((label or "").strip(), "")


def render_predictions(preds, show_copy=True):
    """예측 리스트 렌더링(짧은 해석 + N/100 점수 + 중복 없는 한 줄 요약)."""
    if not preds:
        return
    summary_items = []
    for p in preds:
        label = p.get("label", "")
        score = int(max(0, min(100, int(p.get("score", 0)))))
        cap = short_caption(label)
        tail = f" — {cap}" if cap else ""
        st.write(f"- **{label}**{tail} · 신뢰도 {score}/100")
        if cap:
            st.caption(f"↳ {cap}")
        summary_items.append(f"{label}({score}/100)")
    if show_copy and not st.session_state.get("summary_line_shown"):
        st.caption("🧾 한 줄 요약 복사")
        st.code(" | ".join(summary_items), language="")
        st.session_state["summary_line_shown"] = True


def build_peds_symptoms(nasal=None, cough=None, diarrhea=None, vomit=None,
                        days_since_onset=None, temp=None, fever_cat=None, eye=None):
    """소아 증상 dict를 안전하게 생성(누락 변수 기본값 보정)."""
    if nasal is None: nasal = "없음"
    if cough is None: cough = "없음"
    if diarrhea is None: diarrhea = "없음"
    if vomit is None: vomit = "없음"
    if days_since_onset is None: days_since_onset = 0
    if temp is None: temp = 0.0
    if fever_cat is None: fever_cat = "정상"
    if eye is None: eye = "없음"
    return {
        "콧물": nasal, "기침": cough, "설사": diarrhea, "구토": vomit,
        "증상일수": days_since_onset, "체온": temp, "발열": fever_cat, "눈꼽": eye
    }


# ---------------- 초기화 ----------------
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="BloodMap — 피수치가이드", page_icon="🩸", layout="centered")

# === AUTO: sidebar visitor stats ===
try:
    _stats = _metrics_today_totals()
    st.sidebar.markdown("### 👥 오늘(고유/방문)")
    st.sidebar.write(f"{_stats['today_unique']} / {_stats['today_visits']}")
    st.sidebar.markdown("— 누적 고유")
    st.sidebar.write(f"{_stats['total_unique']}")
    st.sidebar.markdown("— 총 방문수")
    st.sidebar.write(f"{_stats['total_visits']}")
except Exception:
    st.sidebar.caption("방문자 통계 불러오기 오류")
# === /AUTO ===


st.title("BloodMap — 피수치가이드")

st.info(
    "이 앱은 의료행위가 아니며, **참고용**입니다. 진단·치료를 **대체하지 않습니다**.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
    "개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
st.markdown("문의/버그 제보: **[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)**")

nick, pin, key = nickname_pin()

# === AUTO: bump visits (once per session/day) ===
try:
    if "_session_id" not in st.session_state:
        import uuid as _uuid
        st.session_state["_session_id"] = _uuid.uuid4().hex[:12]
    _today_key = "metrics_bumped_" + str(__import__("datetime").date.today())
    if not st.session_state.get(_today_key):
        _metrics_bump(st.session_state.get("user_key"), st.session_state.get("_session_id"))
        st.session_state[_today_key] = True
except Exception:
    pass
# === /AUTO ===


st.divider()
has_key = bool(nick and pin and len(pin) == 4)

# ---------------- 유틸 ----------------
def _fever_bucket_from_temp(temp: float|None) -> str:
    if temp is None: return ""
    if temp < 37.5: return "정상"
    if temp < 38.0: return "37.5~38"
    if temp < 38.5: return "38.0~38.5"
    if temp < 39.0: return "38.5~39"
    return "39+"

def _safe_label(k):
    try:
        return display_label(k)
    except Exception:
        return str(k)

def _filter_known(keys):
    return [k for k in (keys or []) if k in DRUG_DB]

def _one_line_selection(ctx: dict) -> str:
    def names(keys):
        return ", ".join(display_label(k) for k in _filter_known(keys))
    parts = []
    a = names(ctx.get("user_chemo"))
    if a: parts.append(f"항암제: {a}")
    b = names(ctx.get("user_targeted"))
    if b: parts.append(f"표적/면역: {b}")
    c = names(ctx.get("user_abx"))
    if c: parts.append(f"항생제: {c}")
    return " · ".join(parts) if parts else "선택된 약물이 없습니다."

def _peds_diet_fallback(sym: dict, disease: str|None=None) -> list[str]:
    tips = []
    temp = float((sym or {}).get("체온") or 0)
    days = int((sym or {}).get("증상일수") or 0)
    diarrhea = (sym or {}).get("설사") or ""
    vomit = (sym or {}).get("구토") or ""
    nasal = (sym or {}).get("콧물") or ""
    cough = (sym or {}).get("기침") or ""

    if diarrhea in ["3~4회","4~6회","5~6회","7회 이상"] or vomit in ["3~4회","4~6회","7회 이상"]:
        tips.append("ORS(경구수액): 수시 소량. 설사/구토 1회마다 **체중당 10 mL/kg** 보충")
        tips.append("초기 4~6시간은 물/주스/스포츠음료 대신 **ORS 우선**")
        tips.append("연식(BRAT: 바나나·쌀죽·사과퓨레·토스트), 기름진 음식·매운 음식·카페인·탄산 회피")
    else:
        tips.append("수분을 자주 소량씩 제공(맑은 물/미온수). 구토 시 30분 휴식 후 재개")
    tips.append("구토가 있으면 **5분마다 5–10 mL**씩, 멎으면 점진 증량")

    if disease in ["로타","노로","장염"]:
        tips.append("유제품은 설사 멎을 때까지 일시 제한(개인차 고려)")

    if temp >= 38.5:
        tips.append("체온 38.5℃↑: 얇게 입히고 미온수 닦기, 필요 시 해열제(간격 준수)")
    if cough in ["가끔","자주","심함"] or nasal in ["투명","흰색","누런","노랑(초록)"]:
        tips.append("호흡기 증상: 실내 가습/비강 세척, 자극물(담배연기) 회피")

    if days >= 2:
        tips.append("증상 48시간 이상 지속 → 소아과 상담 권장")
    tips.append("탈수 징후(소변 감소/입마름/축 처짐) 시 즉시 진료")

    return tips

def _adult_diet_fallback(sym: dict) -> list[str]:
    tips = []
    temp = float((sym or {}).get("체온") or 0)
    diarrhea = (sym or {}).get("설사") or ""
    vomit = (sym or {}).get("구토") or ""
    nasal = (sym or {}).get("콧물") or ""
    cough = (sym or {}).get("기침") or ""

    if diarrhea in ["4~6회","7회 이상"] or vomit in ["3~4회","4~6회","7회 이상"]:
        tips.append("설사/구토 다회: **ORS** 수시 복용, 설사/구토 1회마다 **10 mL/kg** 보충")
        tips.append("초기 4~6시간은 물/커피/주스 대신 ORS 권장")
        tips.append("연식(BRAT) 위주, 기름진/매운 음식·알코올 회피")
    elif diarrhea in ["1~3회"]:
        tips.append("설사 소량: 수분 보충 + 자극적 음식 줄이기")

    if temp >= 38.5:
        tips.append("38.5℃↑: 미온수 샤워·가벼운 옷차림, 필요 시 해열제(간격 준수)")
    if cough in ["가끔","자주","심함"]:
        tips.append("기침: 따뜻한 수분·꿀차(소아 제외)")
    if nasal in ["투명","흰색"]:
        tips.append("맑은 콧물: 실내 가습·비강 세척")
    elif nasal in ["누런","노랑(초록)"]:
        tips.append("탁한 콧물: 수분섭취/세척, 악화 시 상담")

    tips.append("구토 시 30분 휴식 후 **맑은 수분**부터 재개, 한 번에 많이 마시지 말기")
    return tips

def _export_report(ctx: dict, lines_blocks=None):
    footer = (
        "\n\n---\n"
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경·복용 중단 등은 반드시 **주치의와 상담** 후 결정하십시오.\n"
        "개인정보를 수집하지 않습니다.\n"
        "버그/문의: 피수치 가이드 공식카페.\n"
    )
    title = f"# BloodMap 결과 ({ctx.get('mode','')})\n\n"
    body = []

    if ctx.get("mode") == "암":
        body.append(f"- 카테고리: {ctx.get('group')}")
        body.append(f"- 진단: {ctx.get('dx_label') or ctx.get('dx')}")
    if ctx.get("mode") in ["소아","일상"]:
        body.append(f"- 대상: {ctx.get('who','소아')}")
        if ctx.get("symptoms"):
            body.append("- 증상: " + ", ".join(f"{k}:{v}" for k,v in ctx["symptoms"].items()))
        if ctx.get("temp") is not None:
            body.append(f"- 체온: {ctx.get('temp')} ℃")
        if ctx.get("days_since_onset") is not None:
            body.append(f"- 경과일수: {ctx.get('days_since_onset')}일")
    if ctx.get("preds"):
        preds_text = "; ".join(f"{p['label']}({p['score']})" for p in ctx["preds"])
        body.append(f"- 자동 추정: {preds_text}")
    if ctx.get("triage"):
        body.append(f"- 트리아지: {ctx['triage']}")
    if ctx.get("labs"):
        labs_t = "; ".join(f"{k}:{v}" for k,v in ctx["labs"].items() if v is not None)
        if labs_t:
            body.append(f"- 주요 수치: {labs_t}")

    if lines_blocks:
        for title2, lines in lines_blocks:
            if lines:
                body.append(f"\n## {title2}\n" + "\n".join(f"- {L}" for L in lines))

    if ctx.get("diet_lines"):
        diet = [str(x) for x in ctx["diet_lines"] if x]
        if diet:
            body.append("\n## 🍽️ 식이가이드\n" + "\n".join(f"- {L}" for L in diet))

    if ctx.get("mode") == "암":
        summary = _one_line_selection(ctx)
        if summary:
            body.append("\n## 🗂️ 선택 요약\n- " + summary)

    # GI 요약/URL 포함


    try:


        if ctx.get('gi_summary_md'):


            body.append(ctx['gi_summary_md'])


    except Exception:


        pass


    body.append("\n\nBloodMap: https://bloodmap.streamlit.app/")


    md = title + "\n".join(body) + footer
    txt = md.replace("# ","").replace("## ","")
    return md, txt

# ---------------- 모드 선택 ----------------
mode = st.radio("모드 선택", ["암", "일상", "소아"], horizontal=True)

# ---------------- 암 모드 ----------------
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
    dx_options = list(ONCO_MAP.get(group, {}).keys())

    def _dx_fmt(opt: str) -> str:
        try: return dx_display(group, opt)
        except Exception: return f"{group} - {opt}"

    dx = st.selectbox("진단(영문+한글)", dx_options or ["직접 입력"], format_func=_dx_fmt)
    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="")
    if dx: st.caption(_dx_fmt(dx))

    st.markdown("### 2) 개인 선택")
    from drug_db import picklist, key_from_label
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
    chemo_opts    = picklist(rec_local.get("chemo", []))
    targeted_opts = picklist(rec_local.get("targeted", []))
    abx_opts      = picklist(rec_local.get("abx") or [
        "Piperacillin/Tazobactam","Cefepime","Meropenem","Imipenem/Cilastatin","Aztreonam",
        "Amikacin","Vancomycin","Linezolid","Daptomycin","Ceftazidime","Levofloxacin","TMP-SMX",
        "Metronidazole","Amoxicillin/Clavulanate"
    ])
    c1,c2,c3 = st.columns(3)
    with c1: user_chemo_labels = st.multiselect("항암제(개인)", chemo_opts, default=[])
    with c2: user_targeted_labels = st.multiselect("표적/면역(개인)", targeted_opts, default=[])
    with c3: user_abx_labels = st.multiselect("항생제(개인)", abx_opts, default=[])
    from drug_db import key_from_label
    user_chemo    = [key_from_label(x) for x in user_chemo_labels]
    user_targeted = [key_from_label(x) for x in user_targeted_labels]
    user_abx      = [key_from_label(x) for x in user_abx_labels]

    st.markdown("### 3) 피수치 입력 (숫자만)")
    LABS_ORDER = [
        ("WBC","WBC,백혈구"), ("Hb","Hb,혈색소"), ("PLT","PLT,혈소판"), ("ANC","ANC,호중구"),
        ("Ca","Ca,칼슘"), ("Na","Na,소디움"), ("K","K,칼륨"),
        ("Alb","Alb,알부민"), ("Glu","Glu,혈당"), ("TP","TP,총단백"),
        ("AST","AST"), ("ALT","ALT"), ("LDH","LDH"),
        ("CRP","CRP"), ("Cr","Cr,크레아티닌"), ("UA","UA,요산"), ("TB","TB,총빌리루빈"), ("BUN","BUN")
    ]
    labs = {code: clean_num(st.text_input(label, placeholder="예: 4500")) for code, label in LABS_ORDER}

    # 특수검사
    from special_tests import special_tests_ui
    sp_lines = special_tests_ui()

    # 특수검사 바로 아래 GI/FEVER 섹션
    if "ctx" not in globals():
        ctx = {}
    try:
        _gi_block_render_and_log(ctx)
    except Exception as _e:
        st.caption(f"GI 블록 오류: {_e}")

    lines_blocks = []
    if sp_lines: lines_blocks.append(("특수검사 해석", sp_lines))

    # 저장/그래프
    st.markdown("#### 💾 저장/그래프")
    when = st.date_input("측정일", value=date.today())
    if st.button("📈 피수치 저장/추가"):
        st.session_state.setdefault("lab_hist", {}).setdefault(key, pd.DataFrame())
        df_prev = st.session_state["lab_hist"][key]
        row = {"Date": when.strftime("%Y-%m-%d")}
        labels = [label for _, label in LABS_ORDER]
        for code, label in LABS_ORDER: row[label] = labs.get(code)
        newdf = pd.DataFrame([row])
        if df_prev is None or df_prev.empty: df = newdf
        else:
            df = pd.concat([df_prev, newdf], ignore_index=True).drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
        for col in (["Date"]+labels):
            if col not in df.columns: df[col] = pd.NA
        df = df.reindex(columns=(["Date"]+labels))
        st.session_state["lab_hist"][key] = df
        st.success("저장 완료!")

    dfh = st.session_state.get("lab_hist", {}).get(key)
    if has_key and isinstance(dfh, pd.DataFrame) and not dfh.empty:
        st.markdown("##### 📊 추이 그래프")
        nonnull = [c for c in dfh.columns if (c!="Date" and dfh[c].notna().any())]
        default_pick = [c for c in ["WBC,백혈구","Hb,혈색소","PLT,혈소판","CRP","ANC,호중구"] if c in nonnull]
        pick = st.multiselect("지표 선택", options=nonnull, default=default_pick)
        if pick: st.line_chart(dfh.set_index("Date")[pick], use_container_width=True)
        st.dataframe(dfh[["Date"]+nonnull], use_container_width=True, height=220)
    elif not has_key:
        st.info("그래프는 별명 + PIN(4자리) 저장 시 표시됩니다.")
    else:
        st.info("저장된 히스토리가 없습니다. 값을 입력하고 ‘피수치 저장/추가’를 눌러 보세요.")

    if st.button("🔎 해석하기", key="analyze_cancer"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암","group":group,"dx":dx,"dx_label": dx_display(group, dx),
            "labs": labs, "user_chemo": user_chemo, "user_targeted": user_targeted, "user_abx": user_abx,
            "lines_blocks": lines_blocks
        }
    schedule_block()

# ---------------- 일상 모드 ----------------
elif mode == "일상":
    st.markdown("### 1) 대상 선택")
    who = st.radio("대상", ["소아","성인"], horizontal=True)
    days_since_onset = st.number_input("증상 시작 후 경과일수(일)", min_value=0, step=1, value=0)

    if who == "소아":
        from peds_rules import predict_from_symptoms, triage_advise
        opts = get_symptom_options("기본")
        eye_opts = opts.get("눈꼽", ["없음","맑음","노랑-농성","가려움 동반","한쪽","양쪽"])

        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: nasal = st.selectbox("콧물", opts["콧물"])
        with c2: cough = st.selectbox("기침", opts["기침"])
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
        with c4: vomit = st.selectbox("구토(횟수/일)", ["없음","1~2회","3~4회","4~6회","7회 이상"])
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0)
        with c6: eye = st.selectbox("눈꼽", eye_opts)

        age_m = st.number_input("나이(개월)", min_value=0, step=1)
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

        apap_ml, _ = acetaminophen_ml(age_m, weight or None)
        ibu_ml,  _ = ibuprofen_ml(age_m, weight or None)
        d1,d2 = st.columns(2)
        with d1:
            st.metric("아세트아미노펜 시럽 (평균 1회분)", f"{apap_ml} ml")
            st.caption("간격 **4~6시간**, 하루 최대 4회(성분별 중복 금지)")
        with d2:
            st.metric("이부프로펜 시럽 (평균 1회분)", f"{ibu_ml} ml")
            st.caption("간격 **6~8시간**, 위장 자극 시 음식과 함께")
        st.warning("이 용량 정보는 **참고용**입니다. 반드시 **주치의와 상담**하십시오.")

        fever_cat = _fever_bucket_from_temp(temp)
        # 입력 누락 대비 기본값 보정
        if "days_since_onset" not in locals(): days_since_onset = 0
        if "temp" not in locals(): temp = 0.0
        if "fever_cat" not in locals(): fever_cat = "정상"
        if 'nasal' not in locals(): nasal = '없음'
        if 'cough' not in locals(): cough = '없음'
        if 'diarrhea' not in locals(): diarrhea = '없음'
        if 'vomit' not in locals(): vomit = '없음'
        if 'eye' not in locals(): eye = '없음'
        symptoms = build_peds_symptoms(
            nasal=locals().get('nasal'),
            cough=locals().get('cough'),
            diarrhea=locals().get('diarrhea'),
            vomit=locals().get('vomit'),
            days_since_onset=locals().get('days_since_onset'),
            temp=locals().get('temp'),
            fever_cat=locals().get('fever_cat'),
            eye=locals().get('eye'),
        )
        preds = predict_from_symptoms(symptoms, temp, age_m)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        render_predictions(preds, show_copy=True)

        triage = triage_advise(temp, age_m, diarrhea)
        st.info(triage)

        diet_lines = _peds_diet_fallback(symptoms)

        if st.button("🔎 해석하기", key="analyze_daily_child"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"소아","symptoms":symptoms,
                "temp":temp,"age_m":age_m,"weight":weight or None,
                "apap_ml":apap_ml,"ibu_ml":ibu_ml,"preds":preds,"triage":triage,
                "days_since_onset": days_since_onset, "diet_lines": diet_lines
            }

    else:  # 성인
        from adult_rules import predict_from_symptoms, triage_advise, get_adult_options
        opts = get_adult_options()
        eye_opts = opts.get("눈꼽", ["없음","맑음","노랑-농성","가려움 동반","한쪽","양쪽"])

        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: nasal = st.selectbox("콧물", opts["콧물"])
        with c2: cough = st.selectbox("기침", opts["기침"])
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
        with c4: vomit = st.selectbox("구토(횟수/일)", ["없음","1~3회","4~6회","7회 이상"])
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0)
        with c6: eye = st.selectbox("눈꼽", eye_opts)

        comorb = st.multiselect("주의 대상", ["임신 가능성","간질환 병력","신질환 병력","위장관 궤양/출혈력","항응고제 복용","고령(65+)"])

        fever_cat = _fever_bucket_from_temp(temp)
        symptoms = build_peds_symptoms(
            nasal=locals().get('nasal'),
            cough=locals().get('cough'),
            diarrhea=locals().get('diarrhea'),
            vomit=locals().get('vomit'),
            days_since_onset=locals().get('days_since_onset'),
            temp=locals().get('temp'),
            fever_cat=locals().get('fever_cat'),
            eye=locals().get('eye'),
        )

        preds = predict_from_symptoms(symptoms, temp, comorb)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        render_predictions(preds, show_copy=True)

        triage = triage_advise(temp, comorb)
        st.info(triage)

        diet_lines = _adult_diet_fallback(symptoms)

        if st.button("🔎 해석하기", key="analyze_daily_adult"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"성인","symptoms":symptoms,
                "temp":temp,"comorb":comorb,"preds":preds,"triage":triage,
                "days_since_onset": days_since_onset, "diet_lines": diet_lines
            }

# ---------------- 소아(질환) 모드 ----------------
else:
    ctop = st.columns(4)
    with ctop[0]: disease = st.selectbox("소아 질환", ["로타","독감","RSV","아데노","마이코","수족구","편도염","코로나","중이염"], index=0)
    st.caption(short_caption(disease))
    with ctop[1]: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
    with ctop[2]: age_m = st.number_input("나이(개월)", min_value=0, step=1)
    with ctop[3]: weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

    opts = get_symptom_options(disease)
    eye_opts = opts.get("눈꼽", ["없음","맑음","노랑-농성","가려움 동반","한쪽","양쪽"])
    st.markdown("### 증상 체크")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: nasal = st.selectbox("콧물", opts.get("콧물", ["없음","투명","흰색","누런","피섞임"]))
    with c2: cough = st.selectbox("기침", opts.get("기침", ["없음","조금","보통","심함"]))
    with c3: diarrhea = st.selectbox("설사(횟수/일)", opts.get("설사", ["없음","1~2회","3~4회","5~6회"]))
    with c4: vomit = st.selectbox("구토(횟수/일)", ["없음","1~2회","3~4회","4~6회","7회 이상"])
    with c5: eye = st.selectbox("눈꼽", eye_opts)
    with c6: symptom_days = st.number_input("**증상일수**(일)", min_value=0, step=1, value=0)

    apap_ml, _ = acetaminophen_ml(age_m, weight or None)
    ibu_ml,  _ = ibuprofen_ml(age_m, weight or None)
    dc = st.columns(2)
    with dc[0]:
        st.metric("아세트아미노펜 시럽 (평균 1회분)", f"{apap_ml} ml")
        st.caption("간격 **4~6시간**, 하루 최대 4회(성분별 중복 금지)")
    with dc[1]:
        st.metric("이부프로펜 시럽 (평균 1회분)", f"{ibu_ml} ml")
        st.caption("간격 **6~8시간**, 위장 자극 시 음식과 함께")
    st.warning("이 용량 정보는 **참고용**입니다. 반드시 **주치의와 상담**하십시오.")

    fever_cat = _fever_bucket_from_temp(temp)
    symptoms = build_peds_symptoms(
            nasal=locals().get('nasal'),
            cough=locals().get('cough'),
            diarrhea=locals().get('diarrhea'),
            vomit=locals().get('vomit'),
            days_since_onset=locals().get('days_since_onset'),
            temp=locals().get('temp'),
            fever_cat=locals().get('fever_cat'),
            eye=locals().get('eye'),
        )

    if st.button("🔎 해석하기", key="analyze_peds"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"소아", "disease": disease,
            "symptoms": symptoms,
            "temp": temp, "age_m": age_m, "weight": weight or None,
            "apap_ml": apap_ml, "ibu_ml": ibu_ml, "vals": {},
            "diet_lines": _peds_diet_fallback(symptoms, disease=disease)
        }

# ---------------- 결과 게이트 ----------------
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    m = ctx.get("mode")

    if m == "암":
        labs = ctx.get("labs", {})
        st.subheader("🧪 피수치 요약")
        if labs:
            rcols = st.columns(len(labs))
            for i, (k, v) in enumerate(labs.items()):
                with rcols[i]: st.metric(k, v)
        if ctx.get("dx_label"): st.caption(f"진단: **{ctx['dx_label']}**")

        alerts = collect_top_ae_alerts((_filter_known(ctx.get("user_chemo"))) + (_filter_known(ctx.get("user_abx"))), db=DRUG_DB)
        if alerts: st.error("\n".join(alerts))

        st.subheader("🗂️ 선택 요약")
        st.write(_one_line_selection(ctx))

        # 순서: 피수치 → 특수검사 → 식이가이드 → 부작용
        lines_blocks = ctx.get("lines_blocks") or []
        for title2, lines2 in lines_blocks:
            if lines2:
                st.subheader("🧬 " + title2)
                for L in lines2: st.write("- " + L)

        st.subheader("🍽️ 식이가이드")
        diet_lines = lab_diet_guides(labs or {}, heme_flag=(ctx.get("group")=="혈액암"))
        for L in diet_lines: st.write("- " + L)
        ctx["diet_lines"] = diet_lines

        st.subheader("💊 부작용")
        ckeys = _filter_known(ctx.get("user_chemo"))
        akeys = _filter_known(ctx.get("user_abx"))
        if ckeys:
            st.markdown("**항암제(세포독성)**")
            render_adverse_effects(st, ckeys, DRUG_DB)
        if akeys:
            st.markdown("**항생제**")
            render_adverse_effects(st, akeys, DRUG_DB)

        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, lines_blocks)
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")
        try:
            pdf_bytes = export_md_to_pdf(md)
            st.download_button("⬇️ PDF (.pdf)", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf")
        except Exception as e:
            st.caption(f"PDF 변환 중 오류: {e}")

    elif m == "일상":
        st.subheader("👪 증상 요약")
        sy = ctx.get("symptoms", {})
        sy_cols = st.columns(max(1, min(4, len(sy))))
        for i, k in enumerate(sy.keys()):
            with sy_cols[i % len(sy_cols)]: st.metric(k, sy[k])
        if ctx.get("days_since_onset") is not None:
            st.caption(f"경과일수: {ctx['days_since_onset']}일")
        if ctx.get("temp") is not None:
            st.caption(f"체온: {ctx['temp']} ℃")

        preds = ctx.get("preds") or []
        if preds:
            st.subheader("🤖 증상 기반 자동 추정")
            render_predictions(preds, show_copy=True)


        if ctx.get("who") == "소아":
            st.subheader("🌡️ 해열제 1회분(평균)")
            d1,d2 = st.columns(2)
            with d1:
                st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} ml")
                st.caption("간격 **4~6시간**, 하루 최대 4회(성분별 중복 금지)")
            with d2:
                st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} ml")
                st.caption("간격 **6~8시간**, 위장 자극 시 음식과 함께")
            st.warning("이 용량 정보는 **참고용**입니다. 반드시 **주치의와 상담**하십시오.")

        st.subheader("🍽️ 식이가이드")
        for L in (ctx.get("diet_lines") or []):
            st.write("- " + str(L))

        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, None)
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")
        try:
            pdf_bytes = export_md_to_pdf(md)
            st.download_button("⬇️ PDF (.pdf)", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf")
        except Exception as e:
            st.caption(f"PDF 변환 중 오류: {e}")

    else:  # 소아(질환)
        st.subheader("👶 증상 요약")
        sy = ctx.get("symptoms", {})
        sy_cols = st.columns(max(1, min(4, len(sy))))
        for i, k in enumerate(sy.keys()):
            with sy_cols[i % len(sy_cols)]: st.metric(k, sy[k])
        if ctx.get("temp") is not None:
            st.caption(f"체온: {ctx['temp']} ℃")

        st.subheader("🌡️ 해열제 1회분(평균)")
        d1,d2 = st.columns(2)
        with d1:
            st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} ml")
            st.caption("간격 **4~6시간**, 하루 최대 4회(성분별 중복 금지)")
        with d2:
            st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} ml")
            st.caption("간격 **6~8시간**, 위장 자극 시 음식과 함께")
        st.warning("이 용량 정보는 **참고용**입니다. 반드시 **주치의와 상담**하십시오.")

        st.subheader("🍽️ 식이가이드")
        for L in (ctx.get("diet_lines") or []):
            st.write("- " + str(L))

        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, None)
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")
        try:
            pdf_bytes = export_md_to_pdf(md)
            st.download_button("⬇️ PDF (.pdf)", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf")
        except Exception as e:
            st.caption(f"PDF 변환 중 오류: {e}")

    st.caption("본 도구는 참고용입니다. 의료진의 진단/치료를 대체하지 않습니다.")
    st.caption("문의/버그 제보: [피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)")
    st.stop()


# --- AUTO: sidebar visitor trend (14d) ---
try:
    import pandas as _pd
    import datetime as _dt
    data = _load_metrics() or {}
    by_date = data.get("by_date", {})
    # build last 14 days series
    today = _dt.date.today()
    rows = []
    for i in range(13, -1, -1):
        d = (today - _dt.timedelta(days=i)).isoformat()
        r = by_date.get(d, {"unique": 0, "visits": 0})
        rows.append({"date": d, "unique": r.get("unique", 0), "visits": r.get("visits", 0)})
    _dfm = _pd.DataFrame(rows)
    with st.sidebar:
        st.markdown("###### 📈 최근 14일 추이")
        st.line_chart(_dfm.set_index("date")[["unique","visits"]])
except Exception as _e:
    pass
# --- /AUTO ---



# --- AUTO: labs friendly chart ---
def _render_labs_friendly_chart(uid: str):
    try:
        import pandas as _pd
        import numpy as _np
        import altair as alt
        # load from session_state persist (if available)
        hist = (st.session_state.get("lab_hist") or {}).get(uid)
        if hist is None or len(getattr(hist, "index", [])) == 0:
            return
        df = hist.copy()
        # Try to parse a 'date' column or index to datetime
        date_col = None
        for c in df.columns:
            if c.lower() in ("date","날짜","검사일"):
                date_col = c; break
        if date_col is None:
            # if index is datetime-like, move to column
            try:
                df = df.reset_index().rename(columns={"index": "date"})
                date_col = "date"
            except Exception:
                pass
        if date_col is None:
            return
        df[date_col] = _pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        # numeric columns only for chart
        num_cols = [c for c in df.columns if c != date_col and _pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            return

        with st.expander("🩸 그래프 옵션", expanded=False):
            cols_pick = st.multiselect("보기 항목", options=num_cols, default=num_cols[: min(5, len(num_cols))])
            smooth = st.checkbox("이동평균(3포인트)", value=False)
            y_min, y_max = st.slider("Y축 범위", value=(float(df[cols_pick].min(numeric_only=True).min()) if cols_pick else 0.0,
                                                    float(df[cols_pick].max(numeric_only=True).max()) if cols_pick else 1.0))
        if not cols_pick:
            return
        plot_df = df[[date_col] + cols_pick].copy()
        if smooth:
            for c in cols_pick:
                plot_df[c] = plot_df[c].rolling(window=3, min_periods=1, center=True).mean()

        # Melt for multi-series Altair
        m = plot_df.melt(date_col, var_name="항목", value_name="값")
        base = alt.Chart(m).mark_line(point=True).encode(
            x=alt.X(f"{date_col}:T", title="날짜"),
            y=alt.Y("값:Q", title="", scale=alt.Scale(domain=[y_min, y_max])),
            color="항목:N",
            tooltip=[alt.Tooltip(f"{date_col}:T", title="날짜"), "항목:N", alt.Tooltip("값:Q", format=".2f")]
        ).properties(height=260, use_container_width=True)
        st.altair_chart(base, use_container_width=True)
    except Exception as _e:
        st.caption(f"그래프 표시 오류: {_e}")

# 메인 영역 어딘가에서 현재 uid가 있으면 표시
try:
    _uid_preview = st.session_state.get("user_key")
    if _uid_preview:
        _render_labs_friendly_chart(_uid_preview)
except Exception:
    pass
# --- /AUTO ---



# === AUTO (safe): sidebar visitor metrics cards ===
try:
    import datetime as _dt, json as _json, os as _os, streamlit as st
    def _metrics_path():
        return "/mnt/data/metrics/visits.json"
    def _load_metrics_safe():
        try:
            with open(_metrics_path(), "r", encoding="utf-8") as f:
                return _json.load(f)
        except Exception:
            return {}
    with st.sidebar:
        st.markdown("### 👥 방문자 통계")
        _m = _load_metrics_safe() or {}
        td = _m.get("today", {})
        tt = _m.get("totals", {})
        c1,c2 = st.columns(2)
        with c1:
            st.metric("오늘(고유)", td.get("unique", 0))
            st.metric("누적 고유", tt.get("unique", 0))
        with c2:
            st.metric("오늘(방문)", td.get("visits", 0))
            st.metric("총 방문수", tt.get("visits", 0))
except Exception:
    pass
# === /AUTO ===



# === AUTO (safe): GI/FEVER tools with log ===
try:
    import streamlit as st, datetime as _dt, pandas as _pd, os as _os, json as _json
    st.markdown("#### 🚽 설사 / 🤮 구토 / 🌡️ 해열제")
    with st.expander("기록/계산", expanded=False):
        c_d1, c_d2 = st.columns([2,1])
        with c_d1:
            diarrhea_type = st.selectbox(
                "설사(구분표)", ["", "노란색 설사", "진한 노란색 설사", "거품 설사", "녹색 설사", "녹색 혈변", "혈변", "검은색 변"], index=0
            )
        with c_d2:
            diarrhea_freq = st.number_input("설사 횟수(회/일)", min_value=0, step=1, value=0)

        c_v1, c_v2 = st.columns([2,1])
        with c_v1:
            vomit_type = st.selectbox("구토(구분)", ["", "흰색/묽음", "노란색/담즙", "초록색/담즙", "혈성 의심"], index=0)
        with c_v2:
            vomit_freq = st.number_input("구토 횟수(회/일)", min_value=0, step=1, value=0)

        c_w1, c_w2, c_w3 = st.columns(3)
        with c_w1:
            body_weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=0.0, key="antipy_weight3")
        with c_w2:
            age_years = st.number_input("나이(년)", min_value=0, step=1, value=0, key="antipy_age3")
        with c_w3:
            fever_temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key="antipy_temp3")

        def _dose_apap(weight):
            if not weight or weight <= 0: return None
            low = round(10 * weight); high = round(15 * weight)
            return low, high
        def _dose_ibu(weight, age):
            if not weight or weight <= 0: return None
            if age is not None and age < 0.5: return None
            dose = round(10 * weight)
            return dose
        apap = _dose_apap(body_weight)
        ibu  = _dose_ibu(body_weight, age_years)

        sev_level = "🟢 안정"; reasons = []
        try:
            if (fever_temp or 0) >= 39.0: sev_level = "🚨 위중"; reasons.append("고열 ≥39℃")
            elif (fever_temp or 0) >= 38.0: sev_level = "🟧 주의"; reasons.append("발열 ≥38℃")
            if (diarrhea_freq or 0) >= 4: 
                if sev_level!="🚨 위중": sev_level = "🟧 주의"
                reasons.append("설사 ≥4회/일")
            if (vomit_freq or 0) >= 3:
                if sev_level!="🚨 위중": sev_level = "🟧 주의"
                reasons.append("구토 ≥3회/일")
            if ("혈변" in (diarrhea_type or "")) or ("혈성" in (vomit_type or "")):
                sev_level = "🚨 위중"; reasons.append("혈변/혈성 구토")
        except Exception:
            pass
        st.markdown(f"**응급도: {sev_level}**  " + (" / ".join(reasons) if reasons else ""))

        colA, colB = st.columns(2)
        with colA:
            st.subheader("APAP(아세트아미노펜)")
            if apap:
                st.write(f"권장 1회: **{apap[0]}–{apap[1]} mg** (4–6h 간격)")
                st.caption("소아 60–75 mg/kg/day, 성인 보수 3,000 mg/day 이하. 간질환/과음 시 의료진 상의.")
            else:
                st.caption("체중을 입력하면 계산됩니다.")
        with colB:
            st.subheader("IBU(이부프로펜)")
            if ibu:
                st.write(f"권장 1회: **{ibu} mg** (6–8h 간격)")
                st.caption("6개월 미만 금기. 위장관/신장질환·탈수 시 복용 전 의료진 상의.")
            else:
                st.caption("체중/나이를 입력하면 계산됩니다.")

        # 기록 저장 & 표
        def _gi_log_path(uid:str):
            base = "/mnt/data/care_log"
            try: _os.makedirs(base, exist_ok=True)
            except Exception: pass
            return f"{base}/{uid}_gi.jsonl"
        def _gi_log_append(uid:str, rec:dict):
            p = _gi_log_path(uid)
            try:
                with open(p, "a", encoding="utf-8") as f:
                    f.write(_json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception:
                pass
        def _gi_log_read(uid:str, limit:int=100):
            p = _gi_log_path(uid)
            rows = []
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        try: rows.append(_json.loads(line))
                        except Exception: continue
            except FileNotFoundError:
                pass
            rows = rows[-limit:]
            return _pd.DataFrame(rows) if rows else _pd.DataFrame(columns=["ts","설사","횟수","구토","횟수2","체온"])

        _uid = st.session_state.get("user_key")
        col_log_btn, _ = st.columns([1,3])
        clicked = col_log_btn.button("기록 추가", use_container_width=True)
        if clicked and _uid:
            rec = {
                "ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "설사": diarrhea_type, "횟수": int(diarrhea_freq or 0),
                "구토": vomit_type, "횟수2": int(vomit_freq or 0),
                "체온": float(fever_temp or 0.0)
            }
            _gi_log_append(_uid, rec)
            st.success("기록을 저장했어요.")
        if _uid:
            df_log = _gi_log_read(_uid, limit=200)
            if not df_log.empty:
                st.markdown("##### 최근 기록")
                st.dataframe(df_log.sort_values("ts", ascending=False), use_container_width=True, hide_index=True)
except Exception:
    pass
# === /AUTO ===

