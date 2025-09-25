
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

try:
    # Case 1: flat files (branding.py beside app.py)
    from branding import render_deploy_banner  # type: ignore
except Exception:
    try:
        # Case 2: package layout (this file in a package directory)
        from .branding import render_deploy_banner  # type: ignore
    except Exception:
        # Fallback: no-op to prevent NameError; keeps app running
        def render_deploy_banner(*args, **kwargs):
            return None

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
st.title("BloodMap — 피수치가이드")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")


st.info(
    "이 앱은 의료행위가 아니며, **참고용**입니다. 진단·치료를 **대체하지 않습니다**.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
    "개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
st.markdown("문의/버그 제보: **[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)**")

nick, pin, key = nickname_pin()
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
from branding import render_deploy_banner


def wkey(name: str) -> str:
    try:
        who = st.session_state.get("key", "guest")
        mode_now = st.session_state.get("mode", "unknown")
        return f"{mode_now}:{who}:{name}"
    except Exception:
        return name

# === eGFR (CKD-EPI 2009) metric block ===
try:
    from core_utils import egfr_ckd_epi_2009
    _labs = locals().get("labs") or globals().get("labs")
    _cr = None
    if isinstance(_labs, dict):
        _cr = _labs.get("Cr") or _labs.get("creatinine") or _labs.get("CRE") or _labs.get("cr")
    sex_for_gfr = st.selectbox("성별(egfr)", ["여","남"], index=0, key=wkey("egfr_sex"))
    age_for_gfr = st.number_input("나이(세, egfr)", min_value=1, max_value=110, step=1, value=40, key=wkey("egfr_age"))
    _egfr_val = egfr_ckd_epi_2009(_cr, int(age_for_gfr), sex_for_gfr)
    if _egfr_val is not None:
        st.metric("eGFR (CKD-EPI 2009)", f"{_egfr_val} mL/min/1.73㎡")
except Exception:
    pass



def save_labs_csv(df, key: str):
    try:
        import os
        save_dir = "/mnt/data/bloodmap_graph"
        os.makedirs(save_dir, exist_ok=True)
        csv_path = os.path.join(save_dir, f"{key}.labs.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        st.caption(f"외부 저장 완료: {csv_path}")
    except Exception as _sv_err:
        st.warning("외부 저장 실패: " + str(_sv_err))


def init_care_log(user_key: str):
    st.session_state.setdefault("care_log", {})
    st.session_state["care_log"].setdefault(user_key, [])
    return st.session_state["care_log"][user_key]
