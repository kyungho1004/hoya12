# app.py
import datetime as _dt
import os, sys, re, io, csv
from pathlib import Path
import importlib.util
import streamlit as st

def render_emerg_weights_pro():
    """전문가용: 슬라이더만 제공하는 응급도 가중치 패널.
    emerg_weights 세션 상태를 직접 조정합니다.
    """
    import streamlit as st
    st.subheader("전문가용: 응급도 가중치(슬라이더)")
    st.caption("의료진/숙련 보호자를 위한 세밀 조정 영역입니다.")

    # 기본 키 목록 (기존 슬라이더와 동일한 키셋 유지)
    keys = [
        ("anc_lt_500","ANC<500"),("anc_500_999","ANC 500–999"),("fever_38_0_38_4","발열 38.0–38.4"),
        ("fever_ge_38_5","고열 ≥38.5"),("hb_lt_7","중증빈혈 Hb<7"),("plt_lt_20k","혈소판 <20k"),
        ("crp_ge_10","CRP ≥10"),("hr_gt_130","HR>130"),("resp_distress","호흡곤란"),
        ("melena","흑색변"),("hematochezia","혈변"),("persistent_vomit","지속 구토"),
        ("oliguria","소변량 급감"),("loc_altered","의식저하"),("migraine_severe","번개두통")
    ]

    # 기본값 없을 때를 대비해 가벼운 초기화
    if "emerg_weights" not in st.session_state:
        st.session_state["emerg_weights"] = {k: 0.7 for k,_ in keys}

    cols = st.columns(3)
    for i, (k, label) in enumerate(keys):
        with cols[i % 3]:
            st.session_state["emerg_weights"][k] = st.slider(
                label, 0.0, 1.0, float(st.session_state["emerg_weights"].get(k, 0.7)), 0.05,
                help="가중치가 높을수록 긴급도 점수에 더 크게 반영됩니다.", key=f"pro_{k}"
            )

# --- Feature flag: show weights UI (hidden by default) ---
DEV_SHOW_WEIGHTS = False

def render_emerg_weights_ui():
    import streamlit as st


# LABS

def render_symptom_explain_peds(*, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd, max_temp=None):
    """선택된 증상에 대한 보호자 설명(가정 관리 팁 + 병원 방문 기준)을 상세 렌더."""
    import streamlit as st

    tips = {}

    fever_threshold = 38.5
    er_threshold = 39.0

    if fever != "없음":
        t = [
            "체온은 같은 부위에서 재세요(겨드랑이↔이마 혼용 금지).",
            "미온수(미지근한 물) 닦기, 얇은 옷 입히기.",
            "아세트아미노펜(APAP) 또는 이부프로펜(IBU) 복용 간격 준수(APAP ≥ 4시간, IBU ≥ 6시간).",
            "수분 섭취를 늘리고, 활동량은 줄여 휴식.",
        ]
        w = [
            f"체온이 **{fever_threshold}℃ 이상 지속**되거나, **{er_threshold}℃ 이상**이면 의료진 상담.",
            "경련, 지속 구토/의식저하, 발진 동반 고열이면 즉시 병원.",
            "3~5일 이상 발열 지속 시 진료 권장.",
        ]
        if max_temp is not None:
            try:
                mt = float(max_temp)
            except Exception:
                mt = None
            if mt is not None:
                if mt >= er_threshold:
                    w.insert(0, f"현재 최고 체온 **{mt:.1f}℃** → **즉시 병원 권고**.")
                elif mt >= fever_threshold:
                    w.insert(0, f"현재 최고 체온 **{mt:.1f}℃** → 해열/수분 보충 후 **면밀 관찰**.")
        tips["발열"] = (t, w)

    if cough != "없음" or nasal != "없음":
        t = [
            "가습·통풍·미온수 샤워 등으로 점액 배출을 돕기.",
            "코막힘 심하면 생리식염수 비강세척(소아는 분무형 권장).",
            "수면 시 머리 쪽을 약간 높여 주기.",
        ]
        w = [
            "숨이 차 보이거나, 입술이 퍼렇게 보이면 즉시 병원.",
            "기침이 2주 이상 지속되거나, 쌕쌕거림/흉통이 동반되면 진료.",
        ]
        tips["호흡기(기침/콧물)"] = (t, w)

    if stool != "없음" or persistent_vomit or oliguria:
        t = [
            "ORS 용액으로 5~10분마다 소량씩 자주 먹이기(토하면 10~15분 쉬고 재시도).",
            "기름진 음식·생야채·우유는 일시적으로 줄이기.",
            "항문 주위는 미온수 세정 후 완전 건조, 필요 시 보습막(연고) 얇게.",
        ]
        w = [
            "혈변/검은변, 심한 복통·지속 구토, **2시간 이상 소변 없음**이면 병원.",
            "탈수 의심(눈물 감소, 입마름, 축 처짐) 시 진료.",
        ]
        tips["장 증상(설사/구토/소변감소)"] = (t, w)

    if eye != "없음":
        t = [
            "눈곱은 끓였다 식힌 미온수로 안쪽→바깥쪽 방향 닦기(1회 1거즈).",
            "손 위생 철저, 수건/베개 공유 금지.",
        ]
        w = [
            "빛을 아파하거나, 눈이 붓고 통증 심할 때는 진료.",
            "농성 분비물과 고열 동반 시 병원.",
        ]
        tips["눈 증상"] = (t, w)

    if abd_pain:
        t = [
            "복부를 따뜻하게, 자극적인 음식(튀김/매운맛) 일시 제한.",
            "통증 위치/시간/연관성(식사/배변)을 기록해두기.",
        ]
        w = [
            "오른쪽 아랫배 지속 통증, 보행 시 악화, 구토·발열 동반 시 즉시 진료(충수염 감별).",
            "복부 팽만/혈변·검은변과 함께면 병원.",
        ]
        tips["복통"] = (t, w)

    if ear_pain:
        t = [
            "누우면 통증 악화 가능 → 머리 쪽 약간 높여 수면.",
            "코막힘 동반 시 비염 관리(생리식염수, 가습).",
        ]
        w = [
            "고열·구토 동반, 48시간 이상 통증 지속 시 진료.",
            "귀 뒤 붓고 심한 통증이면 즉시 병원.",
        ]
        tips["귀 통증"] = (t, w)

    if rash or hives:
        t = [
            "시원한 환경 유지, 땀/마찰 줄이기, 보습제 도포.",
            "알레르기 의심 음식·약물은 일시 중단 후 의료진과 상의.",
        ]
        w = [
            "얼굴·입술·혀 붓기, 호흡곤란, 전신 두드러기면 즉시 병원(아나필락시스 우려).",
            "수포/고열 동반 전신 발진은 진료.",
        ]
        tips["피부(발진/두드러기)"] = (t, w)

    if migraine:
        t = [
            "어두운 조용한 환경에서 휴식, 수분 보충.",
            "복용 중인 해열/진통제 간격 준수(중복 성분 주의).",
        ]
        w = [
            "갑작스런 '번개' 두통, 신경학적 이상(구음장애/편측마비/경련) 시 즉시 병원.",
            "두통이 점점 심해지고 구토/시야 이상이 동반되면 진료.",
        ]
        tips["두통/편두통"] = (t, w)

    if hfmd:
        t = [
            "입안 통증 시 차갑거나 미지근한 부드러운 음식 권장.",
            "수분 보충, 구강 위생(부드러운 양치) 유지.",
        ]
        w = [
            "침 흘림·음식·물 거부로 섭취 거의 못하면 병원.",
            "고열이 3일 이상 지속되거나 무기력 심하면 진료.",
        ]
        tips["수족구 의심"] = (t, w)

    try:
        anc_val = float(str(st.session_state.get("labs_dict", {}).get("ANC", "")).replace(",", "."))
    except Exception:
        anc_val = None
    if anc_val is not None and anc_val < 1000:
        t = [
            "생야채/껍질 과일은 피하고, **완전 가열** 후 섭취.",
            "남은 음식은 **2시간 이후 섭취 비권장**, 멸균·살균 식품 권장.",
        ]
        w = [
            "38.0℃ 이상 발열 시 바로 병원 연락, 38.5℃↑ 또는 39℃↑는 상위 조치.",
        ]
        tips["저호중구 음식 안전"] = (t, w)

    compiled = {}
    if tips:
        with st.expander("👪 증상별 보호자 설명", expanded=False):
            for k, (t, w) in tips.items():
                st.markdown(f"### {k}")
                if t:
                    st.markdown("**가정 관리 팁**")
                    for x in t:
                        st.markdown(f"- {x}")
                if w:
                    st.markdown("**병원 방문 기준**")
                    for x in w:
                        st.markdown(f"- {x}")
                st.markdown("---")
        compiled = tips

    st.session_state['peds_explain'] = compiled


def _normalize_abbr(k: str) -> str:
    k = (k or "").strip().upper().replace(" ", "")
    alias = {
        "TP": "T.P",
        "TB": "T.B",
        "WBC": "WBC",
        "HB": "Hb",
        "PLT": "PLT",
        "ANC": "ANC",
        "CRP": "CRP",
        "NA": "Na",
        "CR": "Cr",
        "GLU": "Glu",
        "CA": "Ca",
        "P": "P",
        "AST": "AST",
        "ALT": "ALT",
        "TBIL": "T.B",
        "ALB": "Alb",
        "BUN": "BUN",
    }
    return alias.get(k, k)

LAB_REF_ADULT = {
    "WBC": (4.0, 10.0),
    "Hb": (12.0, 16.0),
    "PLT": (150, 400),
    "ANC": (1500, 8000),
    "CRP": (0.0, 5.0),
    "Na": (135, 145),
    "Cr": (0.5, 1.2),
    "Glu": (70, 140),
    "Ca": (8.6, 10.2),
    "P": (2.5, 4.5),
    "T.P": (6.4, 8.3),
    "AST": (0, 40),
    "ALT": (0, 41),
    "T.B": (0.2, 1.2),
    "Alb": (3.5, 5.0),
    "BUN": (7, 20),
}
LAB_REF_PEDS = {
    "WBC": (5.0, 14.0),
    "Hb": (11.0, 15.0),
    "PLT": (150, 450),
    "ANC": (1500, 8000),
    "CRP": (0.0, 5.0),
    "Na": (135, 145),
    "Cr": (0.2, 0.8),
    "Glu": (70, 140),
    "Ca": (8.8, 10.8),
    "P": (4.0, 6.5),
    "T.P": (6.0, 8.0),
    "AST": (0, 50),
    "ALT": (0, 40),
    "T.B": (0.2, 1.2),
    "Alb": (3.8, 5.4),
    "BUN": (5, 18),
}
def lab_ref(is_peds: bool):
    return LAB_REF_PEDS if is_peds else LAB_REF_ADULT

def lab_validate(abbr: str, val, is_peds: bool):
    rng = lab_ref(is_peds).get(abbr)
    if rng is None or val in (None, ""):
        return None
    try:
        v = float(val)
    except Exception:
        return "형식 오류"
    lo, hi = rng
    if v < lo:
        return f"⬇️ 기준치 미만({lo}~{hi})"
    if v > hi:
        return f"⬆️ 기준치 초과({lo}~{hi})"
    return "정상범위"

with t_labs:
    st.subheader("피수치 입력 — 붙여넣기 지원 (견고)")
    st.caption("예: 'WBC: 4.5', 'Hb 12.3', 'PLT, 200', 'Na 140 mmol/L'…")

    auto_is_peds = bool(st.session_state.get(wkey("is_peds"), False))
    st.toggle("소아 기준 자동 적용(나이 기반)", value=True, key=wkey("labs_auto_mode"))
    if st.session_state.get(wkey("labs_auto_mode")):
        use_peds = auto_is_peds
    else:
        use_peds = st.checkbox("소아 기준(참조범위/검증)", value=auto_is_peds, key=wkey("labs_use_peds_manual"))

    order = [
        ("WBC", "백혈구"),
        ("Ca", "칼슘"),
        ("Glu", "혈당"),
        ("CRP", "CRP"),
        ("Hb", "혈색소"),
        ("P", "인(Phosphorus)"),
        ("T.P", "총단백"),
        ("Cr", "크레아티닌"),
        ("PLT", "혈소판"),
        ("Na", "나트륨"),
        ("AST", "AST"),
        ("T.B", "총빌리루빈"),
        ("ANC", "절대호중구"),
        ("Alb", "알부민"),
        ("ALT", "ALT"),
        ("BUN", "BUN"),
    ]
    with st.expander("📋 검사값 붙여넣기(자동 인식)", expanded=False):
        pasted = st.text_area("예: WBC: 4.5\nHb 12.3\nPLT, 200\nNa 140 mmol/L", height=120, key=wkey("labs_paste"))
        if st.button("붙여넣기 파싱 → 적용", key=wkey("parse_paste")):
            parsed = {}
            try:
                if pasted:
                    for line in str(pasted).splitlines():
                        s = line.strip()
                        if not s:
                            continue
                        parts = re.split(r'[:;,\t\-=\u00b7\u2022]| {2,}', s)
                        parts = [p for p in parts if p.strip()]
                        if len(parts) >= 2:
                            k = _normalize_abbr(parts[0])
                            v = _try_float(parts[1])
                            if k and (v is not None):
                                parsed[k] = v
                                continue
                        toks = s.split()
                        if len(toks) >= 2:
                            k = _normalize_abbr(toks[0])
                            v = _try_float(" ".join(toks[1:]))
                            if k and (v is not None):
                                parsed[k] = v
                if parsed:
                    for abbr, _ in order:
                        if abbr in parsed:
                            st.session_state[wkey(abbr)] = parsed[abbr]
                    st.success(f"적용됨: {', '.join(list(parsed.keys())[:12])} ...")
                else:
                    st.info("인식 가능한 수치를 찾지 못했습니다. 줄마다 '항목 값' 형태인지 확인해주세요.")
            except Exception:
                st.error("파싱 중 예외가 발생했지만 앱은 계속 동작합니다. 입력 형식을 다시 확인하세요.")

    cols = st.columns(4)
    values = {}
    for i, (abbr, kor) in enumerate(order):
        with cols[i % 4]:
            val = st.text_input(f"{abbr} — {kor}", value=str(st.session_state.get(wkey(abbr), "")), key=wkey(abbr))
            values[abbr] = _try_float(val)
            msg = lab_validate(abbr, values[abbr], use_peds)
            if msg:
                st.caption(("✅ " if msg == "정상범위" else "⚠️ ") + msg)
    labs_dict = st.session_state.get("labs_dict", {})
    labs_dict.update(values)
    st.session_state["labs_dict"] = labs_dict
    st.markdown(f"**참조범위 기준:** {'소아' if use_peds else '성인'} / **ANC 분류:** {anc_band(values.get('ANC'))}")

# DX
with t_dx:
    st.subheader("암 선택")
    if not ONCO:
        st.warning("onco_map 이 로드되지 않아 기본 목록이 비어있습니다. onco_map.py를 같은 폴더나 modules/ 에 두세요.")
    groups = sorted(ONCO.keys()) if ONCO else ["혈액암", "고형암"]
    group = st.selectbox("암 그룹", options=groups, index=0, key=wkey("onco_group_sel"))
    diseases = sorted(ONCO.get(group, {}).keys()) if ONCO else ["ALL", "AML", "Lymphoma", "Breast", "Colon", "Lung"]
    disease = st.selectbox("의심/진단명", options=diseases, index=0, key=wkey("onco_disease_sel"))
    disp = dx_display(group, disease)
    st.session_state["onco_group"] = group
    st.session_state["onco_disease"] = disease
    st.session_state["dx_disp"] = disp
    st.info(f"선택: {disp}")

    recs = auto_recs_by_dx(group, disease, DRUG_DB) or {}
    if any(recs.values()):
        st.markdown("**자동 추천 요약**")
        for cat, arr in recs.items():
            if not arr:
                continue
            st.write(f"- {cat}: " + ", ".join(arr))
    st.session_state["recs_by_dx"] = recs

# ---------- Chemo helpers ----------
def _to_set_or_empty(x):
    s = set()
    if not x:
        return s
    if isinstance(x, str):
        for p in re.split(r"[;,/]|\s+", x):
            p = p.strip().lower()
            if p:
                s.add(p)
    elif isinstance(x, (list, tuple, set)):
        for p in x:
            p = str(p).strip().lower()
            if p:
                s.add(p)
    elif isinstance(x, dict):
        for k, v in x.items():
            s.add(str(k).strip().lower())
            if isinstance(v, (list, tuple, set)):
                s |= {str(t).strip().lower() for t in v}
    return s

def _meta_for_drug(key):
    rec = DRUG_DB.get(key, {}) if isinstance(DRUG_DB, dict) else {}
    klass = str(rec.get("class", "")).strip().lower()
    tags = _to_set_or_empty(rec.get("tags")) | _to_set_or_empty(rec.get("tag")) | _to_set_or_empty(rec.get("properties"))
    if "qt" in tags or "qt_prolong" in tags or "qt-prolong" in tags:
        tags.add("qt_prolong")
    if "myelo" in tags or "myelosuppression" in tags:
        tags.add("myelosuppression")
    if "io" in tags or "immunotherapy" in tags or "pd-1" in tags or "pd-l1" in tags or "ctla-4" in tags:
        tags.add("immunotherapy")
    if "steroid" in tags or "corticosteroid" in tags:
        tags.add("steroid")
    inter = rec.get("interactions") or rec.get("ddi") or rec.get("drug_interactions")
    inter_list = []
    if isinstance(inter, str):
        inter_list = [s.strip() for s in re.split(r"[\n;,]", inter) if s.strip()]
    elif isinstance(inter, (list, tuple)):
        inter_list = [str(s).strip() for s in inter if str(s).strip()]
    warning = rec.get("warnings") or rec.get("warning") or rec.get("boxed_warning") or ""
    return {"class": klass, "tags": tags, "interactions": inter_list, "warning": warning, "raw": rec}

def check_chemo_interactions(keys):
    warns = []
    notes = []
    if not keys:
        return warns, notes
    metas = {k: _meta_for_drug(k) for k in keys}
    classes = {}
    for k, m in metas.items():
        if not m["class"]:
            continue
        classes.setdefault(m["class"], []).append(k)
    for klass, arr in classes.items():
        if len(arr) >= 2 and klass not in ("antiemetic", "hydration"):
            warns.append(f"동일 계열 **{klass}** 약물 중복({', '.join(arr)}) — 누적 독성 주의")
    qt_list = [k for k, m in metas.items() if "qt_prolong" in m["tags"]]
    if len(qt_list) >= 2:
        warns.append(f"**QT 연장 위험** 약물 다수 병용({', '.join(qt_list)}) — EKG/전해질 모니터링")
    myelo_list = [k for k, m in metas.items() if "myelosuppression" in m["tags"]]
    if len(myelo_list) >= 2:
        warns.append(f"**강한 골수억제 병용**({', '.join(myelo_list)}) — 감염/출혈 위험 ↑")
    if any("immunotherapy" in m["tags"] for m in metas.values()) and any("steroid" in m["tags"] for m in metas.values()):
        warns.append("**면역항암제 + 스테로이드** 병용 — 면역반응 저하 가능 (임상적 필요 시 예외)")
    for k, m in metas.items():
        for it in m["interactions"]:
            notes.append(f"- {k}: {it}")
        if m["warning"]:
            notes.append(f"- {k} [경고]: {m['warning']}")
    return warns, notes

def _aggregate_all_aes(meds, db):
    result = {}
    if not isinstance(meds, (list, tuple)) or not meds:
        return result
    ae_fields = [
        "ae",
        "ae_ko",
        "adverse_effects",
        "adverse",
        "side_effects",
        "side_effect",
        "warnings",
        "warning",
        "black_box",
        "boxed_warning",
        "toxicity",
        "precautions",
        "safety",
        "safety_profile",
        "notes",
    ]
    for k in meds:
        rec = db.get(k) if isinstance(db, dict) else None
        lines = []
        if isinstance(rec, dict):
            for field in ae_fields:
                v = rec.get(field)
                if not v:
                    continue
                if isinstance(v, str):
                    parts = []
                    for chunk in v.split("\n"):
                        for semi in chunk.split(";"):
                            parts.extend([p.strip() for p in semi.split(",")])
                    lines += [p for p in parts if p]
                elif isinstance(v, (list, tuple)):
                    tmp = []
                    for s in v:
                        for p in str(s).split(","):
                            q = p.strip()
                            if q:
                                tmp.append(q)
                    lines += tmp
        seen = set()
        uniq = []
        for s in lines:
            if s not in seen:
                uniq.append(s)
                seen.add(s)
        if uniq:
            result[k] = uniq
    return result

# CHEMO
with t_chemo:
    st.subheader("항암제(진단 기반)")
    group = st.session_state.get("onco_group")
    disease = st.session_state.get("onco_disease")
    recs = st.session_state.get("recs_by_dx", {}) or {}

    rec_chemo = list(dict.fromkeys(recs.get("chemo", []))) if recs else []
    rec_target = list(dict.fromkeys(recs.get("targeted", []))) if recs else []
    recommended = rec_chemo + [x for x in rec_target if x not in rec_chemo]

    def _indicates(rec: dict, disease_name: str):
        if not isinstance(rec, dict) or not disease_name:
            return False
        keys = ["indications", "indication", "for", "dx", "uses"]
        s = " ".join([str(rec.get(k, "")) for k in keys])
        return (disease_name.lower() in s.lower()) if s else False

    if (not recommended) and DRUG_DB and disease:
        for k, rec in DRUG_DB.items():
            try:
                if _indicates(rec, disease):
                    recommended.append(k)
            except Exception:
                pass

    label_map = {k: display_label(k, DRUG_DB) for k in DRUG_DB.keys()} if DRUG_DB else {}

    show_all = st.toggle("전체 보기(추천 외 약물 포함)", value=False, key=wkey("chemo_show_all"))
    if show_all or not recommended:
        pool_keys = sorted(label_map.keys())
        st.caption("현재: 전체 약물 목록에서 선택")
    else:
        pool_keys = recommended
        st.caption("현재: 진단 기반 추천 목록에서 선택")

    # 4) DB 누락 경고 + 임시 등록
    missing = [k for k in pool_keys if k not in DRUG_DB]
    if missing:
        st.warning("DB에 없는 추천/목록 약물이 있습니다: " + ", ".join(missing))
        if st.button("누락 약물 임시 등록(세션)", key=wkey("tmp_reg_missing")):
            for k in missing:
                if k not in DRUG_DB:
                    DRUG_DB[k] = {"class": "", "ae": ["(보강 필요)"], "tags": []}
            st.success("임시 등록 완료(세션 한정). 부작용/태그는 추후 보강하세요.")

    pool_labels = [label_map.get(k, str(k)) for k in pool_keys]
    unique_pairs = sorted(set(zip(pool_labels, pool_keys)), key=lambda x: x[0].lower())
    pool_labels_sorted = [p[0] for p in unique_pairs]
    picked_labels = st.multiselect("투여/계획 약물 선택", options=pool_labels_sorted, key=wkey("drug_pick"))
    label_to_key = {lbl: key for lbl, key in unique_pairs}
    picked_keys = [label_to_key.get(lbl) for lbl in picked_labels if lbl in label_to_key]
    st.session_state["chemo_keys"] = picked_keys

    if picked_keys:
        # 선택한 약물 DB 비어있으면 경고
        empty = [k for k in picked_keys if not isinstance(DRUG_DB.get(k), dict) or len(DRUG_DB.get(k)) == 0]
        if empty:
            st.error("선택 약물 중 DB 정보가 빈 값입니다: " + ", ".join(empty) + " — 부작용/경고 확인 불가.")

        st.markdown("### 선택 약물")
        for k in picked_keys:
            st.write("- " + label_map.get(k, str(k)))

        warns, notes = check_chemo_interactions(picked_keys)
        if warns:
            st.markdown("### ⚠️ 병용 주의/경고")
            for w in warns:
                st.error(w)
        if notes:
            st.markdown("### ℹ️ 참고(데이터베이스 기재)")
            for n in notes:
                st.info(n)

        ae_map = _aggregate_all_aes(picked_keys, DRUG_DB)
        st.markdown("### 항암제 부작용(전체)")
        if ae_map:
            for k, arr in ae_map.items():
                st.write(f"- **{label_map.get(k, str(k))}**")
                for ln in arr:
                    st.write(f"  - {ln}")
        else:
            st.write("- (DB에 상세 부작용 없음)")

# PEDS
with t_peds:
    st.subheader("소아 증상 기반 점수 + 보호자 설명 + 해열제 계산")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        nasal = st.selectbox("콧물", ["없음", "투명", "진득", "누런"], key=wkey("p_nasal"))
    with c2:
        cough = st.selectbox("기침", ["없음", "조금", "보통", "심함"], key=wkey("p_cough"))
    with c3:
        stool = st.selectbox("설사", ["없음", "1~2회", "3~4회", "5~6회", "7회 이상"], key=wkey("p_stool"))
    with c4:
        fever = st.selectbox("발열", ["없음", "37~37.5 (미열)", "37.5~38", "38~38.5", "38.5~39", "39 이상"], key=wkey("p_fever"))
    with c5:
        eye = st.selectbox("눈꼽/결막", ["없음", "맑음", "노랑-농성", "양쪽"], key=wkey("p_eye"))

    d1, d2, d3 = st.columns(3)
    with d1:
        oliguria = st.checkbox("소변량 급감", key=wkey("p_oliguria"))
    with d2:
        persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("p_pvomit"))
    with d3:
        petechiae = st.checkbox("점상출혈", key=wkey("p_petechiae"))

    e1, e2, e3 = st.columns(3)
    with e1:
        abd_pain = st.checkbox("복통/배마사지 거부", key=wkey("p_abd_pain"))
    with e2:
        ear_pain = st.checkbox("귀 통증/만지면 울음", key=wkey("p_ear_pain"))
    with e3:
        rash = st.checkbox("가벼운 발진/두드러기", key=wkey("p_rash"))

    f1, f2, f3 = st.columns(3)
    with f1:
        hives = st.checkbox("두드러기·알레르기 의심(전신/입술부종 등)", key=wkey("p_hives"))
    with f2:
        migraine = st.checkbox("편두통 의심(한쪽·박동성·빛/소리 민감)", key=wkey("p_migraine"))
    with f3:
        hfmd = st.checkbox("수족구 의심(손발·입 병변)", key=wkey("p_hfmd"))
    # 추가: 증상 지속 기간(보고서/로직 활용 가능)
    duration = st.selectbox("증상 지속일수", ["선택 안 함", "1일", "2일", "3일 이상"], key=wkey("p_duration"), help="대략적인 기간만 선택해도 괜찮아요.")
    if duration == "선택 안 함":
        duration_val = None
    else:
        duration_val = duration

    # ANC 기반 음식 안전 가이드(저호중구 시)
    try:
        anc_val = float(str(st.session_state.get("labs_dict", {}).get("ANC", "")).replace(",", "."))
    except Exception:
        anc_val = None
    if anc_val is not None and anc_val < 1000:
        st.warning("🍽️ 저호중구 시 음식 안전: **생야채/생과일 껍질**은 피하고, **완전 가열** 후 섭취하세요. 남은 음식은 **2시간 이후 섭취 비권장**. 멸균·살균 식품 권장.")

    # 추가: 최고 체온(°C)와 레드 플래그 체크
    max_temp = st.number_input("최고 체온(°C)", min_value=34.0, max_value=43.5, step=0.1, format="%.1f", key=wkey("p_max_temp"), help="하루 중 가장 높았던 체온을 입력해 주세요. 대략값도 괜찮습니다.")
    col_rf1, col_rf2, col_rf3, col_rf4 = st.columns(4)
    with col_rf1:
        red_seizure = st.checkbox("경련/의식저하", key=wkey("p_red_seizure"), help="발작처럼 몸이 뻣뻣해지거나 의식이 흐려지는 경우")
    with col_rf2:
        red_bloodstool = st.checkbox("혈변/검은변", key=wkey("p_red_blood"), help="붉은 피가 섞이거나, 타르처럼 검은 변")
    with col_rf3:
        red_night = st.checkbox("야간/새벽 악화", key=wkey("p_red_night"), help="밤에 더 아파하거나 잠을 못 잘 정도의 악화")
    with col_rf4:
        red_dehydration = st.checkbox("탈수 의심(눈물↓·입마름)", key=wkey("p_red_dehyd"), help="눈물이 잘 안 나오거나 입안이 바싹 마르는 경우")

    # 간단 위험 배지 산정
    fever_flag = (max_temp is not None and max_temp >= 38.5)
    danger_count = sum([1 if x else 0 for x in [red_seizure, red_bloodstool, red_night, red_dehydration, fever_flag]])
    if red_seizure or red_bloodstool or (max_temp is not None and max_temp >= 39.0):
        risk_badge = "🚨"
        st.error("🚨 고위험 신호가 있습니다. 즉시 병원(응급실) 평가를 권합니다.")
    elif danger_count >= 2:
        risk_badge = "🟡"
        st.warning("🟡 주의가 필요합니다. 수분 보충/해열제 가이드 준수하며 경과를 면밀히 관찰하세요.")
    else:
        risk_badge = "🟢"
        st.info("🟢 현재는 비교적 안정 신호입니다. 악화 시 바로 상위 단계 조치를 따르세요.")

    # 작은 위로와 안내
    if st.session_state.get("friendly_mode", True):
        from datetime import datetime, timedelta, timezone
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst).strftime("%Y-%m-%d %H:%M")
        st.caption(f"지금 시간을 기준으로 정리했어요(KST: {now_kst}). 보호자님, 혼자 아니에요. 작은 변화도 도움이 됩니다.")

    # ORS(경구수분보충) 가이드 — 설사/지속구토/소변감소 시 노출
    if (stool != "없음") or persistent_vomit or oliguria or red_dehydration:
        with st.expander("🥤 ORS 경구 수분 보충 가이드", expanded=False):
            st.markdown("- 5~10분마다 소량씩, 구토가 멎으면 양을 서서히 늘립니다.")
            st.markdown("- 차가운 온도보다는 **미지근한 온도**가 흡수에 유리할 수 있습니다.")
            st.markdown("- 2시간 내 소변이 없거나, 입이 마르고 눈물이 잘 나오지 않으면 의료진과 상의하세요.")
            st.markdown("- 스포츠음료는 보충에 한계가 있으니, 가능하면 **ORS 용액**을 사용하세요.")


    score = {
        "장염 의심": 0,
        "상기도/독감 계열": 0,
        "결막염 의심": 0,
        "탈수/신장 문제": 0,
        "출혈성 경향": 0,
        "중이염/귀질환": 0,
        "피부발진/경미한 알레르기": 0,
        "복통 평가": 0,
        "알레르기 주의": 0,
        "편두통 의심": 0,
        "수족구 의심": 0,
    }
    if stool in ["3~4회", "5~6회", "7회 이상"]:
        score["장염 의심"] += {"3~4회": 40, "5~6회": 55, "7회 이상": 70}[stool]
    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        score["상기도/독감 계열"] += 25
    if cough in ["조금", "보통", "심함"]:
        score["상기도/독감 계열"] += 20
    if eye in ["노랑-농성", "양쪽"]:
        score["결막염 의심"] += 30
    if oliguria:
        score["탈수/신장 문제"] += 40
        score["장염 의심"] += 10
    if persistent_vomit:
        score["장염 의심"] += 25
        score["탈수/신장 문제"] += 15
        score["복통 평가"] += 10
    if petechiae:
        score["출혈성 경향"] += 60
    if ear_pain:
        score["중이염/귀질환"] += 35
    if rash:
        score["피부발진/경미한 알레르기"] += 25
    if abd_pain:
        score["복통 평가"] += 25
    if hives:
        score["알레르기 주의"] += 60
    if migraine:
        score["편두통 의심"] += 35
    if hfmd:
        score["수족구 의심"] += 40

    ordered = sorted(score.items(), key=lambda x: x[1], reverse=True)
    st.write("• " + " / ".join([f"{k}: {v}" for k, v in ordered if v > 0]) if any(v > 0 for _, v in ordered) else "• 특이 점수 없음")
    # 보호자 설명 렌더 + peds_notes 저장
    render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd
    )
    try:
        notes = build_peds_notes(
            stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
            cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
            rash=rash, hives=hives, migraine=migraine, hfmd=hfmd, duration=duration_val, score=score, max_temp=max_temp, red_seizure=red_seizure, red_bloodstool=red_bloodstool, red_night=red_night, red_dehydration=red_dehydration
        )
    except Exception:
        notes = ""
    st.session_state["peds_notes"] = notes
    with st.expander(f"{risk_badge} 소아 증상 요약(보고서용 저장됨)", expanded=False):
        st.text_area("요약 내용", value=notes, height=160, key=wkey("peds_notes_preview"))


    st.markdown("---")
    
    if st.session_state.get("friendly_mode", True):
        st.caption("이 도구는 참고용 안내이며, 최종 진단은 의료진의 판단을 따릅니다. 증상이 빠르게 악화되면 즉시 병원을 방문하세요.")
    

    st.subheader("해열제 계산기")
    prev_wt = st.session_state.get(wkey("wt_peds"), 0.0)
    default_wt = _safe_float(prev_wt, 0.0)
    wt = st.number_input("체중(kg)", min_value=0.0, max_value=200.0, value=default_wt, step=0.1, key=wkey("wt_peds_num"))
    st.session_state[wkey("wt_peds")] = wt
    try:
        ap_ml_1, ap_ml_max = acetaminophen_ml(wt)
        ib_ml_1, ib_ml_max = ibuprofen_ml(wt)
    except Exception:
        ap_ml_1, ap_ml_max, ib_ml_1, ib_ml_max = (0.0, 0.0, 0.0, 0.0)
    colA, colB = st.columns(2)
    with colA:
        st.write(f"아세트아미노펜 1회 권장량: **{ap_ml_1:.1f} mL** (최대 {ap_ml_max:.1f} mL)")
    with colB:
        st.write(f"이부프로펜 1회 권장량: **{ib_ml_1:.1f} mL** (최대 {ib_ml_max:.1f} mL)")
    st.caption("쿨다운: APAP ≥4h, IBU ≥6h. 중복 복용 주의.")

    # 3) 해열제 예시 스케줄러
    st.markdown("#### 해열제 예시 스케줄러(교차복용)")
    start = st.time_input("시작시간", value=_dt.datetime.now().time(), key=wkey("peds_sched_start"))
    try:
        base = _dt.datetime.combine(_dt.date.today(), start)
        plan = [
            ("APAP", base),
            ("IBU", base + _dt.timedelta(hours=3)),
            ("APAP", base + _dt.timedelta(hours=6)),
            ("IBU", base + _dt.timedelta(hours=9)),
        ]
        st.caption("※ 실제 복용 간격: APAP≥4h, IBU≥6h. 예시는 간단 참고용.")
        for drug, t in plan:
            st.write(f"- {drug} @ {t.strftime('%H:%M')}")
    except Exception:
        st.info("시간 형식을 확인하세요.")

    st.markdown("---")
    st.subheader("보호자 체크리스트")
    show_ck = st.toggle("체크리스트 열기", value=False, key=wkey("peds_ck"))
    if show_ck:
        colL, colR = st.columns(2)
        with colL:
            st.markdown("**🟢 집에서 해볼 수 있는 것**")
            st.write("- 충분한 수분 섭취(ORS/미온수)")
            st.write("- 해열제 올바른 간격 준수")
            st.write("- 생리식염수 비강 세척/흡인(콧물)")
            st.write("- 가벼운 옷/시원한 환경")
        with colR:
            st.markdown("**🔴 즉시 진료가 필요한 신호**")
            st.write("- 번개치는 두통, 시야 이상, 경련, 의식저하")
            st.write("- 호흡곤란/청색증/입술부종")
            st.write("- 소변량 급감·축 늘어짐(탈수)")
            st.write("- 피 섞인 변/검은 변, 점상출혈 지속")

# SPECIAL (notes + pitfalls)
def _annotate_special_notes(lines):
    if not lines:
        return []
    notes_map = {
        r"procalcitonin|pct": "세균성 감염 지표 — 초기 6–24h, 신장기능/패혈증 단계 고려",
        r"d[- ]?dimer": "혈전/색전 의심 시 상승 — 고령·수술 후·임신 등에서 비특이적 상승",
        r"ferritin": "염증/HLH/철대사 이상 — 간질환·감염에서도 상승 가능",
        r"troponin": "심근 손상 — 신장기능 저하/빈맥/수술·패혈증에서도 경도 상승 가능",
        r"bnp|nt[- ]?pro[- ]?bnp": "심부전 가능성 — 연령·비만·신장기능·폐고혈압 영향",
        r"crp": "염증 비특이 — 절대치보다 **추세**가 중요",
        r"esr": "만성 염증성 지표 — 빈혈/임신/고령에서 상승",
        r"ldh": "용혈/종양부하/조직손상 — 비특이 지표",
        r"haptoglobin": "용혈 시 감소 — 간질환/급성기반응으로 변화",
        r"fibrinogen": "급성기 반응성으로 상승 — DIC 말기에 감소",
    }
    pitfalls = "※ 해석은 임상 맥락·시간축(발현 경과)·신장/간기능 영향을 반드시 함께 보세요."
    out = []
    for ln in lines:
        tagged = False
        for pat, note in notes_map.items():
            if re.search(pat, ln, flags=re.I):
                out.append(f"{ln} — [참고] {note}")
                tagged = True
                break
        if not tagged:
            out.append(ln)
    out.append(pitfalls)
    return out

with t_special:
    st.subheader("특수검사 해석")
    if SPECIAL_PATH:
        st.caption(f"special_tests 로드: {SPECIAL_PATH}")
    lines = special_tests_ui()
    lines = _annotate_special_notes(lines or [])
    st.session_state["special_interpretations"] = lines
    if lines:
        for ln in lines:
            st.write("- " + ln)
    else:
        st.info("아직 입력/선택이 없습니다.")

# ---------- QR helper ----------
def _build_hospital_summary():
    key_id = st.session_state.get("key", "(미설정)")
    labs = st.session_state.get("labs_dict", {}) or {}
    temp = st.session_state.get(wkey("cur_temp")) or "—"
    hr = st.session_state.get(wkey("cur_hr")) or "—"
    group = st.session_state.get("onco_group", "") or "—"
    disease = st.session_state.get("onco_disease", "") or "—"
    meds = st.session_state.get("chemo_keys", []) or []
    sym_keys = [
        "sym_hematuria",
        "sym_melena",
        "sym_hematochezia",
        "sym_chest",
        "sym_dyspnea",
        "sym_confusion",
        "sym_oliguria",
        "sym_pvomit",
        "sym_petechiae",
        "sym_thunderclap",
        "sym_visual_change",
    ]
    sym_kor = ["혈뇨", "흑색변", "혈변", "흉통", "호흡곤란", "의식저하", "소변량 급감", "지속 구토", "점상출혈", "번개두통", "시야 이상"]
    sym_line = ", ".join([nm for nm, kk in zip(sym_kor, sym_keys) if st.session_state.get(wkey(kk), False)]) or "해당 없음"
    pick = ["WBC", "Hb", "PLT", "ANC", "CRP", "Na", "K", "Ca", "Cr", "BUN", "AST", "ALT", "T.B", "Alb", "Glu"]
    lab_parts = []
    for k in pick:
        v = labs.get(k)
        if v not in (None, ""):
            lab_parts.append(f"{k}:{v}")
    labs_line = ", ".join(lab_parts) if lab_parts else "—"
    meds_line = ", ".join(meds) if meds else "—"
    return f"[PIN]{key_id} | T:{temp}℃ HR:{hr} | Dx:{group}/{disease} | Sx:{sym_line} | Labs:{labs_line} | Chemo:{meds_line}"

def _qr_image_bytes(text: str) -> bytes:
    try:
        import qrcode
        img = qrcode.make(text)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return b""

# REPORT with side panel (tabs)
with t_report:
    st.subheader("보고서 (.md/.txt/.pdf) — 모든 항목 포함")

    key_id = st.session_state.get("key", "(미설정)")
    labs = st.session_state.get("labs_dict", {}) or {}
    group = st.session_state.get("onco_group", "")
    disease = st.session_state.get("onco_disease", "")
    meds = st.session_state.get("chemo_keys", [])
    diets = lab_diet_guides(labs, heme_flag=(group == "혈액암"))
    temp = st.session_state.get(wkey("cur_temp"))
    hr = st.session_state.get(wkey("cur_hr"))
    age_years = _safe_float(st.session_state.get(wkey("age_years")), 0.0)
    is_peds = bool(st.session_state.get(wkey("is_peds"), False))

    sym_map = {
        "혈뇨": st.session_state.get(wkey("sym_hematuria"), False),
        "흑색변": st.session_state.get(wkey("sym_melena"), False),
        "혈변": st.session_state.get(wkey("sym_hematochezia"), False),
        "흉통": st.session_state.get(wkey("sym_chest"), False),
        "호흡곤란": st.session_state.get(wkey("sym_dyspnea"), False),
        "의식저하": st.session_state.get(wkey("sym_confusion"), False),
        "소변량 급감": st.session_state.get(wkey("sym_oliguria"), False),
        "지속 구토": st.session_state.get(wkey("sym_pvomit"), False),
        "점상출혈": st.session_state.get(wkey("sym_petechiae"), False),
        "번개치는 듯한 두통": st.session_state.get(wkey("sym_thunderclap"), False),
        "시야 이상/복시/암점": st.session_state.get(wkey("sym_visual_change"), False),
    }
    level, reasons, contrib = emergency_level(
        labs or {},
        temp,
        hr,
        {
            "hematuria": sym_map["혈뇨"],
            "melena": sym_map["흑색변"],
            "hematochezia": sym_map["혈변"],
            "chest_pain": sym_map["흉통"],
            "dyspnea": sym_map["호흡곤란"],
            "confusion": sym_map["의식저하"],
            "oliguria": sym_map["소변량 급감"],
            "persistent_vomit": sym_map["지속 구토"],
            "petechiae": sym_map["점상출혈"],
            "thunderclap": sym_map["번개치는 듯한 두통"],
            "visual_change": sym_map["시야 이상/복시/암점"],
        },
    )

    col_report, col_side = st.columns([2, 1])

    # ---------- 오른쪽: 기록/그래프/내보내기 ----------
    with col_side:
        st.markdown("### 📊 기록/그래프 패널")

        st.session_state.setdefault("lab_history", [])
        hist = st.session_state["lab_history"]

        tab_log, tab_plot, tab_export = st.tabs(["📝 기록", "📈 그래프", "⬇️ 내보내기"])

        with tab_log:
            cols_btn = st.columns([1, 1, 1])
            with cols_btn[0]:
                if st.button("➕ 현재 값을 기록에 추가", key=wkey("add_history_tab")):
                    snap = {
                        "ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "temp": temp or "",
                        "hr": hr or "",
                        "labs": {k: ("" if labs.get(k) in (None, "") else labs.get(k)) for k in labs.keys()},
                        "mode": "peds" if bool(st.session_state.get(wkey("is_peds"), False)) else "adult",
                        "ref": lab_ref(bool(st.session_state.get(wkey("is_peds"), False))),
                    }
                    weird = []
                    for k, v in (snap["labs"] or {}).items():
                        try:
                            fv = float(v)
                            if k == "Na" and not (110 <= fv <= 170):
                                weird.append(f"Na {fv}")
                            if k == "K" and not (1.0 <= fv <= 8.0):
                                weird.append(f"K {fv}")
                            if k == "Hb" and not (3.0 <= fv <= 25.0):
                                weird.append(f"Hb {fv}")
                            if k == "PLT" and fv > 0 and fv < 1:
                                weird.append(f"PLT {fv} (단위 확인)")
                        except Exception:
                            pass
                    hist.append(snap)
                    st.success("현재 값이 기록에 추가되었습니다.")
                    if weird:
                        st.warning("비정상적으로 보이는 값 감지: " + ", ".join(weird) + " — 단위/오타를 확인하세요.")
            with cols_btn[1]:
                if st.button("🗑️ 기록 비우기", key=wkey("clear_history")) and hist:
                    st.session_state["lab_history"] = []
                    hist = st.session_state["lab_history"]
                    st.warning("기록을 모두 비웠습니다.")
            with cols_btn[2]:
                st.caption(f"총 {len(hist)}건")

            if not hist:
                st.info("기록이 없습니다.")
            else:
                try:
                    import pandas as pd
                    rows = []
                    for h in hist[-10:]:
                        row = {
                            "시각": h.get("ts", ""),
                            "T(℃)": h.get("temp", ""),
                            "HR": h.get("hr", ""),
                            "WBC": (h.get("labs", {}) or {}).get("WBC", ""),
                            "Hb": (h.get("labs", {}) or {}).get("Hb", ""),
                            "PLT": (h.get("labs", {}) or {}).get("PLT", ""),
                            "ANC": (h.get("labs", {}) or {}).get("ANC", ""),
                            "CRP": (h.get("labs", {}) or {}).get("CRP", ""),
                        }
                        rows.append(row)
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, height=280)
                except Exception:
                    st.write(hist[-5:])

        with tab_plot:
            default_metrics = ["WBC", "Hb", "PLT", "ANC", "CRP", "Na", "Cr", "BUN", "AST", "ALT", "Glu"]
            all_metrics = sorted({*default_metrics, *list(labs.keys())})
            pick = st.multiselect("그래프 항목 선택", options=all_metrics, default=default_metrics[:4], key=wkey("chart_metrics_tab"))

            if not hist:
                st.info("기록이 없습니다. 먼저 '기록' 탭에서 추가하세요.")
            elif not pick:
                st.info("표시할 항목을 선택하세요.")
            else:
                x = [h.get("ts", "") for h in hist]
                if _HAS_MPL:
                    for m in pick:
                        y, band = [], None
                        for h in hist:
                            v = (h.get("labs", {}) or {}).get(m, "")
                            try:
                                v = float(str(v).replace(",", "."))
                            except Exception:
                                v = None
                            y.append(v)
                        for h in reversed(hist):
                            ref = (h.get("ref") or {})
                            if m in ref:
                                band = ref[m]
                                break
                        if all(v is None for v in y):
                            continue
                        fig = plt.figure()
                        plt.plot(x, [vv if vv is not None else float("nan") for vv in y], marker="o")
                        plt.title(m)
                        plt.xlabel("기록 시각")
                        plt.ylabel(m)
                        plt.xticks(rotation=45, ha="right")
                        if band and isinstance(band, (tuple, list)) and len(band) == 2:
                            lo, hi = band
                            try:
                                plt.axhspan(lo, hi, alpha=0.15)
                            except Exception:
                                pass
                        plt.tight_layout()
                        st.pyplot(fig)
                else:
                    try:
                        import pandas as pd
                        df_rows = []
                        for i, h in enumerate(hist):
                            row = {"ts": x[i]}
                            for m in pick:
                                v = (h.get("labs", {}) or {}).get(m, None)
                                try:
                                    v = float(str(v).replace(",", "."))
                                except Exception:
                                    v = None
                                row[m] = v
                            df_rows.append(row)
                        if df_rows:
                            df = pd.DataFrame(df_rows).set_index("ts")
                            for m in pick:
                                st.line_chart(df[[m]])
                        else:
                            st.info("표시할 데이터가 없습니다.")
                    except Exception:
                        st.warning("matplotlib/pandas 미설치 → 간단 표로 폴백합니다.")
                        for m in pick:
                            st.write(m, [(x[i], (hist[i].get("labs", {}) or {}).get(m, None)) for i in range(len(hist))])

        with tab_export:
            if not hist:
                st.info("기록이 없습니다.")
            else:
                since = st.text_input("시작 시각(YYYY-MM-DD)", value="")
                until = st.text_input("종료 시각(YYYY-MM-DD)", value="")

                def _in_range(ts):
                    if not ts:
                        return False
                    d = ts[:10]
                    if since and d < since:
                        return False
                    if until and d > until:
                        return False
                    return True

                sel = [h for h in hist if _in_range(h.get("ts", ""))] if (since or until) else hist

                output = io.StringIO()
                writer = csv.writer(output)
                all_keys = set()
                for h in sel:
                    all_keys |= set((h.get("labs", {}) or {}).keys())
                all_keys = sorted(all_keys)
                headers = ["ts", "temp", "hr"] + all_keys
                writer.writerow(headers)
                for h in sel:
                    row = [h.get("ts", ""), h.get("temp", ""), h.get("hr", "")]
                    for m in all_keys:
                        row.append((h.get("labs", {}) or {}).get(m, ""))
                    writer.writerow(row)
                st.download_button("CSV 다운로드", data=output.getvalue().encode("utf-8"), file_name="bloodmap_history.csv", mime="text/csv")
                st.caption("팁: 기간 필터를 지정해 필요한 구간만 내보낼 수 있습니다.")

    # ---------- 왼쪽: 보고서 본문 ----------
    with col_report:
        use_dflt = st.checkbox("기본(모두 포함)", True, key=wkey("rep_all"))
        colp1, colp2 = st.columns(2)
        with colp1:
            sec_profile = st.checkbox("프로필/활력/모드", True if use_dflt else False, key=wkey("sec_profile"))
            sec_symptom = st.checkbox("증상 체크(홈)", True if use_dflt else False, key=wkey("sec_symptom"))
            sec_emerg = st.checkbox("응급도 평가(기여도/가중치 포함)", True if use_dflt else False, key=wkey("sec_emerg"))
            sec_dx = st.checkbox("진단명(암 선택)", True if use_dflt else False, key=wkey("sec_dx"))
        with colp2:
            sec_meds = st.checkbox("항암제 요약/부작용/병용경고", True if use_dflt else False, key=wkey("sec_meds"))
            sec_labs = st.checkbox("피수치 전항목", True if use_dflt else False, key=wkey("sec_labs"))
            sec_diet = st.checkbox("식이가이드", True if use_dflt else False, key=wkey("sec_diet"))
            sec_special = st.checkbox("특수검사 해석(각주)", True if use_dflt else False, key=wkey("sec_special"))

        st.markdown("### 🏥 병원 전달용 요약 + QR")
        qr_text = _build_hospital_summary()
        st.code(qr_text, language="text")
        qr_png = _qr_image_bytes(qr_text)
        if qr_png:
            st.image(qr_png, caption="이 QR을 스캔하면 위 요약 텍스트가 표시됩니다.", use_column_width=False)
            st.download_button("QR 이미지(.png) 다운로드", data=qr_png, file_name="bloodmap_hospital_qr.png", mime="image/png")
        else:
            st.info("QR 라이브러리를 찾지 못했습니다. 위 텍스트를 그대로 공유하세요. (선택: requirements에 `qrcode` 추가)")

        lines = []
        lines.append("# Bloodmap Report (Full)")
        lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        lines.append("")
        lines.append("> In memory of Eunseo, a little star now shining in the sky.")
        lines.append("> This app is made with the hope that she is no longer in pain,")
        lines.append("> and resting peacefully in a world free from all hardships.")
        lines.append("")
        lines.append("---")
        lines.append("")

        if sec_profile:
            lines.append("## 프로필/활력/모드")
            lines.append(f"- 키(별명#PIN): {key_id}")
            lines.append(f"- 나이(년): {age_years}")
            lines.append(f"- 모드: {'소아' if is_peds else '성인'}")
            lines.append(f"- 체온(℃): {temp if temp not in (None, '') else '—'}")
            lines.append(f"- 심박수(bpm): {hr if hr not in (None, '') else '—'}")
            lines.append("")

        if sec_symptom:
            lines.append("## 증상 체크(홈)")
            for k, v in sym_map.items():
                lines.append(f"- {k}: {'예' if v else '아니오'}")
            lines.append("")

        if sec_emerg:
            lines.append("## 응급도 평가")
            lines.append(f"- 현재 응급도: {level}")
            if reasons:
                for r in reasons:
                    lines.append(f"  - {r}")
            if contrib:
                lines.append("### 응급도 기여도(Why)")
                total = sum(x["score"] for x in contrib) or 1.0
                for it in sorted(contrib, key=lambda x: -x["score"]):
                    pct = round(100.0 * it["score"] / total, 1)
                    lines.append(f"- {it['factor']}: 점수 {round(it['score'], 2)} (기본{it['base']}×가중치{it['weight']}, {pct}%)")
            lines.append("")
            lines.append("### 사용한 가중치")
            for k, v in get_weights().items():
                lines.append(f"- {k}: {v}")
            lines.append("")

        if sec_dx:
            lines.append("## 진단명(암)")
            lines.append(f"- 그룹: {group or '(미선택)'}")
            lines.append(f"- 질환: {disease or '(미선택)'}")
            lines.append("")

        if sec_meds:
            lines.append("## 항암제 요약")
            if meds:
                for m in meds:
                    try:
                        lines.append(f"- {display_label(m, DRUG_DB)}")
                    except Exception:
                        lines.append(f"- {m}")
            else:
                lines.append("- (없음)")
            lines.append("")

            warns, notes = check_chemo_interactions(meds)
            if warns:
                lines.append("### ⚠️ 병용 주의/경고")
                for w in warns:
                    lines.append(f"- {w}")
                lines.append("")
            if notes:
                lines.append("### ℹ️ 참고(데이터베이스 기재)")
                for n in notes:
                    lines.append(n)
                lines.append("")

            if meds:
                ae_map = _aggregate_all_aes(meds, DRUG_DB)
                if ae_map:
                    lines.append("## 항암제 부작용(전체)")
                    for k, arr in ae_map.items():
                        try:
                            nm = display_label(k, DRUG_DB)
                        except Exception:
                            nm = k
                        lines.append(f"- {nm}")
                        for ln in arr:
                            lines.append(f"  - {ln}")
                    lines.append("")

        if sec_labs:
            lines.append("## 피수치 (모든 항목)")
            all_labs = [
                ("WBC", "백혈구"),
                ("Ca", "칼슘"),
                ("Glu", "혈당"),
                ("CRP", "CRP"),
                ("Hb", "혈색소"),
                ("P", "인(Phosphorus)"),
                ("T.P", "총단백"),
                ("Cr", "크레아티닌"),
                ("PLT", "혈소판"),
                ("Na", "나트륨"),
                ("AST", "AST"),
                ("T.B", "총빌리루빈"),
                ("ANC", "절대호중구"),
                ("Alb", "알부민"),
                ("ALT", "ALT"),
                ("BUN", "BUN"),
            ]
            for abbr, kor in all_labs:
                v = labs.get(abbr) if isinstance(labs, dict) else None
                lines.append(f"- {abbr} ({kor}): {v if v not in (None, '') else '—'}")
            lines.append(f"- ANC 분류: {anc_band(labs.get('ANC') if isinstance(labs, dict) else None)}")
            lines.append("")

        if sec_diet:
            dlist = diets or []
            if dlist:
                lines.append("## 식이가이드(자동)")
                for d in dlist:
                    lines.append(f"- {d}")
                lines.append("")

        if sec_special:
            spec_lines = st.session_state.get("special_interpretations", [])
            if spec_lines:
                lines.append("## 특수검사 해석(각주 포함)")
                for ln in spec_lines:
                    lines.append(f"- {ln}")
                lines.append("")

        lines.append("---")
        lines.append("### 🏥 병원 전달용 텍스트 (QR 동일 내용)")
        lines.append(_build_hospital_summary())
        lines.append("")

        md = "\n".join(lines)
        st.code(md, language="markdown")
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"), file_name="bloodmap_report.md", mime="text/markdown")
        txt_data = md.replace("**", "")
        st.download_button("📝 보고서 .txt 다운로드", data=txt_data.encode("utf-8"), file_name="bloodmap_report.txt", mime="text/plain")
        try:
            pdf_bytes = export_md_to_pdf(md)
            st.download_button("📄 보고서 .pdf 다운로드", data=pdf_bytes, file_name="bloodmap_report.pdf", mime="application/pdf")
        except Exception:
            st.caption("PDF 변환 모듈을 불러오지 못했습니다. .md 또는 .txt를 사용해주세요.")
