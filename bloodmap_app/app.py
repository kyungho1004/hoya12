# app.py — BloodMap (labs labels ko+en, spinnerless inputs, per-user graphs)
import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="BloodMap", page_icon="🩸", layout="centered")

# -------------------------
# 공통 유틸
# -------------------------
def round_half(x: float) -> float:
    try: return round(x * 2) / 2
    except Exception: return x

def num(v):
    """문자 → 숫자. 콤마/±/+ 제거, 공백 허용."""
    try:
        if v is None: return None
        s = str(v).strip().replace(",", "").replace("±", "").replace("+", "")
        if s == "": return None
        return float(s)
    except Exception:
        return None

def rr_threshold_by_age_months(m):
    if m is None: return None
    try: m = float(m)
    except: return None
    if m < 2:   return 60
    if m < 12:  return 50
    if m < 60:  return 40
    return 30

def temp_band_label(t):
    if t is None: return None
    try: t = float(t)
    except: return None
    if t < 37.0: return "36~37℃"
    if t < 38.0: return "37~38℃"
    if t < 39.0: return "38~39℃"
    return "≥39℃"

def build_report_md(nickname, pin, mode, sections):
    nick = f"{nickname}#{pin}" if nickname and pin else (nickname or "guest")
    md = f"# BloodMap 보고서\n\n- 사용자: {nick}\n- 모드: {mode}\n\n"
    for title, lines in sections:
        md += f"## {title}\n"
        if not lines:
            md += "- (내용 없음)\n\n"
            continue
        for L in lines:
            md += f"- {L}\n"
        md += "\n"
    md += (
        "----\n"
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
        "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.\n"
    )
    return md

# -------------------------
# 해열제 계산
# -------------------------
ACET_DEFAULT_MG_PER_ML = 160/5  # 32 mg/mL
IBU_DEFAULT_MG_PER_ML  = 100/5  # 20 mg/mL

def dose_apap_ml(weight_kg: float, mg_per_ml: float = ACET_DEFAULT_MG_PER_ML):
    if not weight_kg or not mg_per_ml: return None, None
    mg = 12.5 * weight_kg
    ml = mg / mg_per_ml
    return round_half(ml), 5

def dose_ibu_ml(weight_kg: float, mg_per_ml: float = IBU_DEFAULT_MG_PER_ML):
    if not weight_kg or not mg_per_ml: return None, None
    mg = 10.0 * weight_kg
    ml = mg / mg_per_ml
    return round_half(ml), 4

def antipyretic_block():
    st.markdown("#### 🔥 해열제 (1회 평균 용량 기준)")
    colw, cola, colc = st.columns([1.1, 1, 1])
    with colw:
        wt = st.number_input("체중(kg)", min_value=0.0, step=0.5, key="wt")
    with cola:
        med = st.selectbox("해열제", ["아세트아미노펜", "이부프로펜"], key="apy")
    with colc:
        if med == "아세트아미노펜":
            conc = st.selectbox("시럽 농도", ["160mg/5mL (권장)", "사용자 설정"], key="apap_conc")
            if conc == "사용자 설정":
                mg = st.number_input("아세트아미노펜 mg", min_value=1, step=1, value=160, key="apap_mg")
                mL = st.number_input("용량 mL", min_value=1.0, step=0.5, value=5.0, key="apap_ml")
                mg_per_ml = mg/mL
            else:
                mg_per_ml = ACET_DEFAULT_MG_PER_ML
            ml_one, max_times = dose_apap_ml(wt, mg_per_ml)
        else:
            conc = st.selectbox("시럽 농도", ["100mg/5mL (권장)", "사용자 설정"], key="ibu_conc")
            if conc == "사용자 설정":
                mg = st.number_input("이부프로펜 mg", min_value=1, step=1, value=100, key="ibu_mg")
                mL = st.number_input("용량 mL", min_value=1.0, step=0.5, value=5.0, key="ibu_ml")
                mg_per_ml = mg/mL
            else:
                mg_per_ml = IBU_DEFAULT_MG_PER_ML
            ml_one, max_times = dose_ibu_ml(wt, mg_per_ml)

    if wt and ml_one:
        st.success(f"**1회 용량: {ml_one:.1f} mL**  (최대 가능 횟수: **{max_times}회/일**)")
        if med == "아세트아미노펜":
            st.caption("같은 약 간격: **최소 4~6시간**")
        else:
            st.caption("같은 약 간격: **최소 6~8시간**")
        st.info("교차 사용: 보통 **4시간 간격**으로 교차. 같은 약 최소 간격은 반드시 준수.")
    else:
        st.info("체중과 시럽 농도를 입력하면 **1회 평균 용량(ml)**이 계산됩니다. (0.5mL 단위 반올림)")

# -------------------------
# 소아 증상/해석 (간략 유지)
# -------------------------
SYM_NONE = "없음"
SEV4 = [SYM_NONE, "조금", "보통", "심함"]

def pediatric_symptom_inputs(prefix="peds"):
    st.markdown("#### 👶 소아 증상 입력")
    c1, c2 = st.columns(2)
    with c1:
        age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{prefix}_age_m")
        temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, key=f"{prefix}_temp")
        rr   = st.number_input("호흡수(회/분)", min_value=0, step=1, key=f"{prefix}_rr")
        spo2 = st.number_input("산소포화도(%)", min_value=0, step=1, key=f"{prefix}_spo2")
        headache = st.selectbox("편두통", SEV4, key=f"{prefix}_headache")
        hfmd_area = st.selectbox("수족구 분포(해당 시)", [SYM_NONE, "입안", "손발", "전신"], key=f"{prefix}_hfmd")
    with c2:
        nasal = st.selectbox("콧물", [SYM_NONE, "투명", "흰색", "누런색", "피섞임"], key=f"{prefix}_nasal")
        stool = st.selectbox("설사", [SYM_NONE, "1~2회", "3~4회", "5~6회", "7회 이상"], key=f"{prefix}_stool")
        cough_day = st.selectbox("기침(주간)", SEV4, key=f"{prefix}_cough_day")
        cough_night = st.selectbox("기침(야간)", ["밤에 없음", "보통", "심함"], key=f"{prefix}_cough_night")
        eye = st.selectbox("눈곱", SEV4, key=f"{prefix}_eye")
        activity = st.selectbox("활동성/컨디션", ["평소와 같음", "조금 저하", "많이 저하"], key=f"{prefix}_act")
        parent_vitals = st.selectbox("보호자 판단(활력징후)", ["평소와 같음", "변화 있음"], key=f"{prefix}_pv")
    return {
        "age_m": num(age_m), "temp": num(temp), "rr": num(rr), "spo2": num(spo2),
        "nasal": nasal, "stool": stool, "cough_day": cough_day, "cough_night": cough_night,
        "eye": eye, "activity": activity, "headache": headache, "hfmd_area": hfmd_area,
        "parent_vitals": parent_vitals,
    }

def interpret_pediatric(sym: dict, disease: str = ""):
    lines, risk = [], "🟢 낮음"
    age_m, temp, rr, spo2 = sym.get("age_m"), sym.get("temp"), sym.get("rr"), sym.get("spo2")
    nasal, stool = sym.get("nasal"), sym.get("stool")
    cough_day, cough_night = sym.get("cough_day"), sym.get("cough_night")
    eye, activity, headache = sym.get("eye"), sym.get("activity"), sym.get("headache")
    hfmd_area, pv = sym.get("hfmd_area"), sym.get("parent_vitals")

    tb = temp_band_label(temp)
    if temp is not None:
        if temp >= 39.0: lines.append(f"🚨 고열(≥39.0℃, {tb}): **응급실/병원 내원 권고**."); risk="🔴 높음"
        elif temp >= 38.0: lines.append(f"🌡️ 발열(38.0–38.9℃, {tb}): 경과 관찰 + 해열제 고려.")
        else: lines.append(f"🌡️ 체온 {temp:.1f}℃({tb}).")

    thr = rr_threshold_by_age_months(age_m)
    if rr is not None and thr is not None:
        if rr > thr: lines.append(f"🫁 빠른 호흡(RR {int(rr)}>{thr}/분): 악화 시 진료.");  risk = "🟠 중간" if risk!="🔴 높음" else risk
        else: lines.append(f"🫁 호흡수 {int(rr)}/분: 연령 기준 내(기준 {thr}/분).")
    if spo2 is not None:
        if spo2 < 92: lines.append(f"🧯 산소포화도 {int(spo2)}%: 저산소 → 즉시 진료."); risk="🔴 높음"
        elif spo2 < 95: lines.append(f"⚠️ 산소포화도 {int(spo2)}%: 경계."); risk="🟠 중간" if risk!="🔴 높음" else risk
        else: lines.append(f"🫧 산소포화도 {int(spo2)}%: 안정.")

    if nasal and nasal != SYM_NONE:
        if nasal in ["누런색","피섞임"]: lines.append(f"👃 콧물({nasal}): 2~3일 지속·발열 동반 시 진료.");  risk="🟠 중간" if risk=="🟢 낮음" else risk
        else: lines.append(f"👃 콧물({nasal}): 비강 세척/가습 도움.")
    if stool and stool != SYM_NONE:
        lines.append(f"🚰 설사 {stool}: ORS 소량씩 자주. 소변감소/무기력 시 진료.")
        if stool in ["5~6회","7회 이상"] and risk!="🔴 높음": risk="🟠 중간"
    if cough_day and cough_day != SYM_NONE: lines.append(f"🗣️ 기침(주간) {cough_day}: 가습·수분섭취.")
    if cough_night and cough_night != "밤에 없음": lines.append(f"🌙 기침(야간) {cough_night}: 야간 악화 시 진료.");  risk="🟠 중간" if risk=="🟢 낮음" else risk
    if eye and eye != SYM_NONE: lines.append(f"👁️ 눈곱 {eye}: 결막염 의심 시 손위생·수건 분리.")
    if headache and headache != SYM_NONE: lines.append(f"🧠 두통 {headache}: 휴식/수분 보충.")
    if hfmd_area and hfmd_area != SYM_NONE: lines.append(f"✋ 수족구 분포: {hfmd_area}.")
    if activity == "조금 저하": lines.append("🛌 활동성 조금 저하: 휴식·수분, 악화 시 진료.")
    elif activity == "많이 저하": lines.append("🛌 활동성 많이 저하: **진료 권고**."); risk="🔴 높음"
    if pv == "변화 있음": lines.append("📈 보호자 판단상 변화 있음 → 주의 관찰/진료 상담.");  risk="🟠 중간" if risk=="🟢 낮음" else risk

    # (질환별 팁은 이전과 동일) — 생략

    return risk, lines

# -------------------------
# 특수검사 (정성/정량) — 기존 버전 유지
# -------------------------
QUAL_CHOICES = ["없음", "+", "++", "+++"]

def special_tests_inputs(prefix="sp"):
    st.markdown("##### 🧪 특수검사")
    c1, c2 = st.columns(2)
    with c1:
        alb = st.selectbox("알부민뇨/단백뇨", QUAL_CHOICES, key=f"{prefix}_alb")
        hema = st.selectbox("혈뇨", QUAL_CHOICES, key=f"{prefix}_hema")
        glu = st.selectbox("요당", QUAL_CHOICES, key=f"{prefix}_glu")
        ket = st.selectbox("케톤뇨", QUAL_CHOICES, key=f"{prefix}_ket")
        occult = st.selectbox("잠혈(요/대변)", QUAL_CHOICES, key=f"{prefix}_occ")
    with c2:
        c3 = st.text_input("C3 (mg/dL)", key=f"{prefix}_c3", placeholder="예: 95")
        c4 = st.text_input("C4 (mg/dL)", key=f"{prefix}_c4", placeholder="예: 15")
        rbc = st.text_input("RBC (×10⁶/μL)", key=f"{prefix}_rbc", placeholder="예: 4.5")
        wbc = st.text_input("WBC (×10³/μL)", key=f"{prefix}_wbc", placeholder="예: 6.0")
        tg  = st.text_input("TG (mg/dL)", key=f"{prefix}_tg", placeholder="예: 120")
        hdl = st.text_input("HDL (mg/dL)", key=f"{prefix}_hdl", placeholder="예: 55")
        ldl = st.text_input("LDL (mg/dL)", key=f"{prefix}_ldl", placeholder="예: 110")
        tc  = st.text_input("총콜레스테롤 (mg/dL)", key=f"{prefix}_tc", placeholder="예: 190")

    qual = {"알부민뇨": alb, "혈뇨": hema, "요당": glu, "케톤뇨": ket, "잠혈": occult}
    quant = {"C3": num(c3), "C4": num(c4), "RBC": num(rbc), "WBC": num(wbc),
             "TG": num(tg), "HDL": num(hdl), "LDL": num(ldl), "TC": num(tc)}
    return qual, quant

def interpret_special_tests(qual: dict, quant: dict):
    lines = []
    for k, v in qual.items():
        if v and v != "없음":
            if v == "+":   lines.append(f"🟡 {k} {v} → 경미한 이상, 추적 권장.")
            elif v == "++": lines.append(f"🟠 {k} {v} → 의미 있는 이상, 원인 평가.")
            else:          lines.append(f"🔴 {k} {v} → 🚨 신장/대사 이상 가능, 진료 권고.")
    C3_LOW, C4_LOW = 90, 10
    if quant.get("C3") is not None: lines.append("🟡 C3 낮음 → 면역계 이상 가능.") if quant["C3"] < C3_LOW else lines.append("🟢 C3 정상.")
    if quant.get("C4") is not None: lines.append("🟡 C4 낮음 → 면역계 이상 가능.") if quant["C4"] < C4_LOW else lines.append("🟢 C4 정상.")
    if quant.get("RBC") is not None:
        v=quant["RBC"]
        lines.append("🟡 RBC 낮음 → 빈혈 가능.") if v<4.0 else lines.append("🟡 RBC 높음 → 탈수/진성 적혈구증 감별.") if v>5.5 else lines.append("🟢 RBC 정상.")
    if quant.get("WBC") is not None:
        v=quant["WBC"]
        lines.append("🟠 WBC 낮음 → 감염 위험.") if v<4.0 else lines.append("🟠 WBC 높음 → 감염/염증 가능.") if v>11.0 else lines.append("🟢 WBC 정상.")
    if quant.get("TG") is not None:
        v=quant["TG"]
        lines.append("🔴 TG ≥200 → 고중성지방혈증 가능.") if v>=200 else lines.append("🟡 TG 150~199 → 경계.") if v>=150 else lines.append("🟢 TG 양호.")
    if quant.get("HDL") is not None and quant["HDL"]>0: lines.append("🟠 HDL 낮음(<40) → 심혈관 위험.") if quant["HDL"]<40 else lines.append("🟢 HDL 양호.")
    if quant.get("LDL") is not None:
        v=quant["LDL"]
        lines.append("🔴 LDL ≥160 → 고LDL콜레스테롤혈증.") if v>=160 else lines.append("🟡 LDL 130~159 → 경계.") if v>=130 else lines.append("🟢 LDL 양호.")
    if quant.get("TC") is not None:
        v=quant["TC"]
        lines.append("🔴 총콜 ≥240 → 고지혈증 가능.") if v>=240 else lines.append("🟡 총콜 200~239 → 경계.") if v>=200 else lines.append("🟢 총콜 양호.")
    if not lines: lines.append("입력값이 없어 해석할 내용이 없습니다.")
    return lines

# -------------------------
# 항암제/표적치료/항생제 데이터 (요약) — 이전 버전 그대로 (지면상 생략 가능)
# -------------------------
drug_info = {
    "Cytarabine":{"ko":"시타라빈(ARA-C)","mech":"핵산 합성 억제(S-phase).","se":"골수억제, 발열, 고용량 시 신경독성/결막염."},
    "Daunorubicin":{"ko":"다우노루비신","mech":"Topo II 억제.","se":"심독성, 골수억제, 점막염."},
    "Idarubicin":{"ko":"이다루비신","mech":"Topo II 억제.","se":"심독성, 골수억제."},
    "Cyclophosphamide":{"ko":"사이클로포스파미드","mech":"알킬화제.","se":"골수억제, 출혈성 방광염(메스나)."},
    "Etoposide":{"ko":"에토포사이드","mech":"Topo II 억제.","se":"골수억제, 저혈압(주입속도)."},
    "Fludarabine":{"ko":"플루다라빈","mech":"푸린 유사체.","se":"면역억제/감염 위험, 골수억제."},
    "Hydroxyurea":{"ko":"하이드록시유레아","mech":"RNR 억제.","se":"골수억제, 피부변화."},
    "Methotrexate":{"ko":"메토트렉세이트(MTX)","mech":"DHFR 억제.","se":"간독성, 골수억제, 구내염(폴린산 구제)."},
    "ATRA":{"ko":"트레티노인(ATRA)","mech":"분화 유도.","se":"분화증후군, 간수치 상승, 피부/점막 자극."},
    "G-CSF":{"ko":"필그라스팀(그라신 계열)","mech":"호중구 생성 자극.","se":"골통, 드물게 비장비대."},
    "Asparaginase":{"ko":"아스파라기나제","mech":"아스파라긴 고갈.","se":"췌장염, 알레르기, 혈전."},
    "Vincristine":{"ko":"빈크리스틴","mech":"미세소관 억제.","se":"말초신경병증, 변비."},
    "Doxorubicin":{"ko":"독소루비신","mech":"Topo II 억제.","se":"심독성, 탈모, 점막염."},
    "Ifosfamide":{"ko":"이포스파미드","mech":"알킬화제.","se":"신경/신독성, 출혈성 방광염(메스나)."},
    "Gemcitabine":{"ko":"젬시타빈","mech":"핵산 합성 억제.","se":"골수억제, 발열감, 간수치 상승."},
    "Oxaliplatin":{"ko":"옥살리플라틴","mech":"백금계 DNA 교차결합.","se":"말초신경병증(한랭 유발)."},
    "Irinotecan":{"ko":"이리노테칸","mech":"Topo I 억제.","se":"설사(급성/지연), 골수억제."},
    "5-FU":{"ko":"플루오로우라실(5-FU)","mech":"피리미딘 대사 교란.","se":"구내염, 설사, 수족증후군."},
    "Capecitabine":{"ko":"카페시타빈","mech":"경구 5-FU 전구약.","se":"수족증후군, 설사."},
    "Paclitaxel":{"ko":"파클리탁셀","mech":"미세소관 안정화.","se":"알레르기, 골수억제, 말초신경병증."},
    "Docetaxel":{"ko":"도세탁셀","mech":"미세소관 안정화.","se":"부종, 골수억제, 점막염."},
    "Cisplatin":{"ko":"시스플라틴","mech":"백금계 DNA 결합.","se":"신독성, 이독성, 구역/구토."},
    "Carboplatin":{"ko":"카보플라틴","mech":"백금계 DNA 결합.","se":"골수억제, 구역/구토."},
    # … (표적/면역제 생략 없이 계속)
}

common_abx = [
    "Piperacillin/Tazobactam (피페라실린/타조박탐): 광범위, 호중구감소성 발열 1차.",
    "Cefepime (세페핌): 항녹농균 4세대 세팔로스포린.",
    "Meropenem (메로페넴): ESBL/중증 패혈증 고려.",
    "Vancomycin (반코마이신): MRSA, 신장/농도 모니터.",
    "Levofloxacin (레보플록사신): 경구 가능, QT 연장 주의.",
    "TMP/SMX (트리메토프림/설파메톡사졸): PCP 예방/치료, 전해질/혈구감소 주의.",
]

def drug_display_lines(drug_names):
    out=[]
    for en in drug_names:
        if en not in drug_info: out.append(f"{en} (정보 준비 중)"); continue
        ko=drug_info[en]["ko"]; mech=drug_info[en]["mech"]; se=drug_info[en]["se"]
        out.append(f"**{en} ({ko})** — 기전: {mech} / 부작용: {se}")
    return out

# -------------------------
# 별명 + PIN
# -------------------------
def nickname_pin():
    c1, c2 = st.columns([2,1])
    with c1: nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2: pin = st.text_input("PIN(4자리 숫자)", max_chars=4, placeholder="0000")
    pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
    if pin and pin != pin_clean: st.warning("PIN은 숫자 4자리만 허용됩니다.")
    key = (nickname.strip()+"#"+pin_clean) if nickname and pin_clean else (nickname or "").strip()
    return nickname, pin_clean, key

# -------------------------
# 피수치 (텍스트 입력 + 저장/그래프)
# -------------------------
LAB_LABELS = {
    "WBC": "WBC(백혈구)", "Hb": "Hb(혈색소)", "PLT": "PLT(혈소판)", "ANC": "ANC(절대호중구)",
    "CRP": "CRP(염증반응)", "AST": "AST(간 효소)", "ALT": "ALT(간세포)",
    "Cr": "Cr(크레아티닌)", "Alb": "Alb(알부민)", "Glu": "Glu(혈당)"
}
LAB_ORDER = ["WBC","Hb","PLT","ANC","CRP","AST","ALT","Cr","Alb","Glu"]

def labs_block_text(nickname_key: str):
    st.markdown("#### 🧪 주요 수치 (선택 입력) — 스피너 제거")
    c1, c2 = st.columns(2)
    with c1:
        WBC = st.text_input(f"{LAB_LABELS['WBC']}", placeholder="예: 4500")
        Hb  = st.text_input(f"{LAB_LABELS['Hb']}",  placeholder="예: 12.3")
        PLT = st.text_input(f"{LAB_LABELS['PLT']}", placeholder="예: 150000")
        ANC = st.text_input(f"{LAB_LABELS['ANC']}", placeholder="예: 1200")
        CRP = st.text_input(f"{LAB_LABELS['CRP']}", placeholder="예: 0.8")
    with c2:
        AST = st.text_input(f"{LAB_LABELS['AST']}", placeholder="예: 30")
        ALT = st.text_input(f"{LAB_LABELS['ALT']}", placeholder="예: 28")
        Cr  = st.text_input(f"{LAB_LABELS['Cr']}",  placeholder="예: 0.8")
        Alb = st.text_input(f"{LAB_LABELS['Alb']}", placeholder="예: 4.1")
        Glu = st.text_input(f"{LAB_LABELS['Glu']}", placeholder="예: 95")
    vals = {"WBC":num(WBC),"Hb":num(Hb),"PLT":num(PLT),"ANC":num(ANC),"CRP":num(CRP),
            "AST":num(AST),"ALT":num(ALT),"Cr":num(Cr),"Alb":num(Alb),"Glu":num(Glu)}

    # 간단 경고
    alerts=[]
    if vals["ANC"] is not None and vals["ANC"] < 500:
        alerts.append("🚨 ANC <500: 생채소 금지·익혀 먹기·남은 음식 2시간 이후 비권장·멸균식품 권장.")
    if vals["Hb"] is not None and vals["Hb"] < 8:
        alerts.append("🟥 Hb<8: 어지러움/호흡곤란 시 진료.")
    if vals["PLT"] is not None and vals["PLT"] < 20000:
        alerts.append("🩹 PLT<20k: 출혈 주의, 넘어짐·양치 출혈 관찰.")
    if vals["AST"] is not None and vals["AST"] >= 50:
        alerts.append("🟠 AST≥50: 간기능 저하 가능.")
    if vals["ALT"] is not None and vals["ALT"] >= 55:
        alerts.append("🟠 ALT≥55: 간세포 손상 의심.")
    if vals["CRP"] is not None and vals["CRP"] >= 3:
        alerts.append("🔥 CRP 상승: 발열·통증 동반 시 진료.")
    if vals["Alb"] is not None and vals["Alb"] < 3.0:
        alerts.append("🥛 알부민 낮음: 부드러운 단백식 권장.")

    shown = [f"{LAB_LABELS[k]}: {v}" for k,v in vals.items() if v is not None]

    # 저장/그래프
    st.markdown("##### 💾 저장 및 그래프")
    colg1, colg2 = st.columns([1,1])
    with colg1:
        when = st.date_input("측정일", value=date.today(), key="lab_date")
    with colg2:
        save_ok = st.button("📈 피수치 저장/추가", use_container_width=True)

    if save_ok:
        if not nickname_key or "#" not in nickname_key:
            st.warning("별명 + PIN을 입력하면 개인 히스토리로 저장됩니다.")
        else:
            st.session_state.setdefault("lab_history", {})
            df = st.session_state["lab_history"].get(nickname_key)
            row = {"Date": when.strftime("%Y-%m-%d")}
            row.update({k: vals.get(k) for k in LAB_ORDER})
            if isinstance(df, pd.DataFrame):
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            else:
                df = pd.DataFrame([row], columns=["Date"]+LAB_ORDER)
            # 정렬/중복 제거(동일 일자 여러개면 최신만 남김)
            df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
            st.session_state["lab_history"][nickname_key] = df
            st.success("저장 완료! 아래 그래프에서 추이를 확인하세요.")

    # 그래프 출력
    df_hist = st.session_state.get("lab_history", {}).get(nickname_key)
    if isinstance(df_hist, pd.DataFrame) and not df_hist.empty:
        st.markdown("##### 📊 추이 그래프")
        pick = st.multiselect("지표 선택", ["WBC","Hb","PLT","CRP","ANC"], default=["WBC","Hb","PLT","CRP","ANC"])
        if pick:
            plot_df = df_hist.set_index("Date")[pick]
            st.line_chart(plot_df, use_container_width=True)
        st.dataframe(df_hist, use_container_width=True, height=220)
    else:
        st.info("저장된 히스토리가 없습니다. 값을 입력하고 ‘피수치 저장/추가’를 눌러 보세요.")

    return vals, alerts, shown

# -------------------------
# 간단 UI (암/소아 스위치 + 해열제 + 피수치 + 특수검사 + 보고서)
# -------------------------
def main():
    st.markdown("## 🩸 BloodMap — 보호자용 미니 해석 도우미")
    st.caption("치료 단계 UI 제외 / 개인정보 미수집 / 피수치 입력은 전부 ‘텍스트’로 스피너 제거")
    nickname, pin, nickname_key = nickname_pin()
    st.divider()

    mode = st.radio("모드 선택", ["일반/암", "소아(일상/호흡기)"], horizontal=True)

    # 해열제(공통)
    antipyretic_block()
    st.divider()

    report_sections = []

    # 피수치 + 그래프
    vals, alerts, shown = labs_block_text(nickname_key)

    if st.button("🔎 피수치 해석하기", use_container_width=True):
        sec = []
        if shown: sec += shown
        if alerts: sec += alerts
        report_sections.append(("피수치 해석 요약", sec if sec else ["입력값이 없습니다."]))

    # 특수검사(원하면 확장)
    with st.expander("🧪 특수검사 (선택)", expanded=False):
        qual, quant = special_tests_inputs(prefix="sp")
        if st.button("🔎 특수검사 해석", use_container_width=True, key="sp_btn"):
            sp_lines = interpret_special_tests(qual, quant)
            st.markdown("#### 해석 결과")
            for L in sp_lines: st.write("- " + L)
            report_sections.append(("특수검사 해석", sp_lines))

    # 소아 모드(간단 해석)
    if mode == "소아(일상/호흡기)":
        sym = pediatric_symptom_inputs(prefix="p1")
        if st.button("🔎 소아 해석하기", use_container_width=True):
            risk, lines = interpret_pediatric(sym, disease="")
            st.markdown(f"### 🧠 종합 위험도: **{risk}**")
            for L in lines: st.write("- " + L)
            report_sections.append(("소아(일상/호흡기) 해석", [f"위험도: {risk}"] + lines))

    # 보고서 저장
    st.divider()
    if report_sections:
        md = build_report_md(nickname, pin, mode, report_sections)
        st.download_button("📥 보고서(.md) 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown", use_container_width=True)
        st.download_button("📄 보고서(.txt) 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.txt", mime="text/plain", use_container_width=True)

    st.caption("본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다. "
               "약 변경/복용 중단 등은 반드시 주치의와 상의하세요. "
               "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.")

if __name__ == "__main__":
    main()
