# app.py — BloodMap
# - 소아 가이드: 질환 선택 가능 + 피수치 "토글(Expander)"로 노출
# - 암 피수치: 사용자 지정 라벨 그대로 (WBC(백혈구) … T,b(총빌리루빈))
# - 피수치 입력은 전부 text_input → +/- 스피너 완전 제거
# - 별명+PIN 저장 사용자는 그래프 표시(지표 선택 가능)

import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="BloodMap", page_icon="🩸", layout="centered")

# ------------------------- 공통 유틸 -------------------------
def round_half(x: float) -> float:
    try:
        return round(x * 2) / 2
    except Exception:
        return x

def num(v):
    """문자 → 숫자. 콤마/±/+ 공백 제거."""
    try:
        if v is None:
            return None
        s = str(v).strip().replace(",", "").replace("±", "").replace("+", "")
        if s == "":
            return None
        return float(s)
    except Exception:
        return None

def rr_threshold_by_age_months(m):
    if m is None:
        return None
    try:
        m = float(m)
    except:
        return None
    if m < 2:
        return 60
    if m < 12:
        return 50
    if m < 60:
        return 40
    return 30

def temp_band_label(t):
    if t is None:
        return None
    try:
        t = float(t)
    except:
        return None
    if t < 37.0:
        return "36~37℃"
    if t < 38.0:
        return "37~38℃"
    if t < 39.0:
        return "38~39℃"
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

# ------------------------- 해열제 -------------------------
ACET_DEFAULT_MG_PER_ML = 160/5  # 32 mg/mL
IBU_DEFAULT_MG_PER_ML  = 100/5  # 20 mg/mL

def dose_apap_ml(weight_kg: float, mg_per_ml: float = ACET_DEFAULT_MG_PER_ML):
    if not weight_kg or not mg_per_ml:
        return None, None
    mg = 12.5 * weight_kg  # 평균값 기준
    ml = mg / mg_per_ml
    return round_half(ml), 5  # 1일 최대 가능 횟수 표기만

def dose_ibu_ml(weight_kg: float, mg_per_ml: float = IBU_DEFAULT_MG_PER_ML):
    if not weight_kg or not mg_per_ml:
        return None, None
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
                mg_per_ml = mg / mL
            else:
                mg_per_ml = ACET_DEFAULT_MG_PER_ML
            ml_one, max_times = dose_apap_ml(wt, mg_per_ml)
        else:
            conc = st.selectbox("시럽 농도", ["100mg/5mL (권장)", "사용자 설정"], key="ibu_conc")
            if conc == "사용자 설정":
                mg = st.number_input("이부프로펜 mg", min_value=1, step=1, value=100, key="ibu_mg")
                mL = st.number_input("용량 mL", min_value=1.0, step=0.5, value=5.0, key="ibu_ml")
                mg_per_ml = mg / mL
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

# ------------------------- 소아 증상/해석 -------------------------
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
        if temp >= 39.0:
            lines.append(f"🚨 고열(≥39.0℃, {tb}): **응급실/병원 내원 권고**.")
            risk = "🔴 높음"
        elif temp >= 38.0:
            lines.append(f"🌡️ 발열(38.0–38.9℃, {tb}): 경과 관찰 + 해열제 고려.")
        else:
            lines.append(f"🌡️ 체온 {temp:.1f}℃({tb}).")

    thr = rr_threshold_by_age_months(age_m)
    if rr is not None and thr is not None:
        if rr > thr:
            lines.append(f"🫁 빠른 호흡(RR {int(rr)}>{thr}/분): 악화 시 진료.")
            if risk != "🔴 높음":
                risk = "🟠 중간"
        else:
            lines.append(f"🫁 호흡수 {int(rr)}/분: 연령 기준 내(기준 {thr}/분).")
    if spo2 is not None:
        if spo2 < 92:
            lines.append(f"🧯 산소포화도 {int(spo2)}%: 저산소 → 즉시 진료.")
            risk = "🔴 높음"
        elif spo2 < 95:
            lines.append(f"⚠️ 산소포화도 {int(spo2)}%: 경계.")
            if risk != "🔴 높음":
                risk = "🟠 중간"
        else:
            lines.append(f"🫧 산소포화도 {int(spo2)}%: 안정.")

    if nasal and nasal != SYM_NONE:
        if nasal in ["누런색", "피섞임"]:
            lines.append(f"👃 콧물({nasal}): 2~3일 지속·발열 동반 시 진료.")
            if risk == "🟢 낮음":
                risk = "🟠 중간"
        else:
            lines.append(f"👃 콧물({nasal}): 비강 세척/가습 도움.")
    if stool and stool != SYM_NONE:
        lines.append(f"🚰 설사 {stool}: ORS 소량씩 자주. 소변감소/무기력 시 진료.")
        if stool in ["5~6회", "7회 이상"] and risk != "🔴 높음":
            risk = "🟠 중간"
    if cough_day and cough_day != SYM_NONE:
        lines.append(f"🗣️ 기침(주간) {cough_day}: 가습·수분섭취.")
    if cough_night and cough_night != "밤에 없음":
        lines.append(f"🌙 기침(야간) {cough_night}: 야간 악화 시 진료.")
        if risk == "🟢 낮음":
            risk = "🟠 중간"
    if eye and eye != SYM_NONE:
        lines.append(f"👁️ 눈곱 {eye}: 결막염 의심 시 손위생·수건 분리.")
    if headache and headache != SYM_NONE:
        lines.append(f"🧠 두통 {headache}: 휴식/수분 보충.")
    if hfmd_area and hfmd_area != SYM_NONE:
        lines.append(f"✋ 수족구 분포: {hfmd_area}.")
    if activity == "조금 저하":
        lines.append("🛌 활동성 조금 저하: 휴식·수분, 악화 시 진료.")
    elif activity == "많이 저하":
        lines.append("🛌 활동성 많이 저하: **진료 권고**.")
        risk = "🔴 높음"
    if pv == "변화 있음":
        lines.append("📈 보호자 판단상 변화 있음 → 주의 관찰/진료 상담.")
        if risk == "🟢 낮음":
            risk = "🟠 중간"

    # 질환 선택에 따른 간단 가이드 (핵심만)
    dl = (disease or "").lower()
    tips = []
    if "코로나" in dl:
        if "무증상" in dl:
            tips += ["😷 코로나 무증상: 노출력 있으면 자가 관찰, 필요 시 신속항원/PCR.", "🤒 가족 간 전파 주의."]
        else:
            tips += ["🤒 코로나 의심: PCR 필요 시 보건소 문의."]
    if "수족구" in dl:
        tips += ["✋ 수족구: 손발 수포·입안 통증, 탈수 주의."]
    if "장염" in dl:
        tips += ["💩 장염: 묽은 설사·구토, 전해질 관리."]
    if "편도염" in dl:
        tips += ["🧊 편도염: 삼킴 통증·타액 증가, 해열제 반응 관찰."]
    if ("열감기" in dl) or ("상기도염" in dl):
        tips += ["🌡️ 열감기: 미열+콧물/기침, 3일 이상 고열 시 진료."]

    lines += tips
    return risk, lines

# ------------------------- 특수검사(공통) -------------------------
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
            if v == "+":
                lines.append(f"🟡 {k} {v} → 경미한 이상, 추적 권장.")
            elif v == "++":
                lines.append(f"🟠 {k} {v} → 의미 있는 이상, 원인 평가.")
            else:
                lines.append(f"🔴 {k} {v} → 🚨 신장/대사 이상 가능, 진료 권고.")
    C3_LOW, C4_LOW = 90, 10
    if quant.get("C3") is not None:
        lines.append("🟡 C3 낮음 → 면역계 이상 가능.") if quant["C3"] < C3_LOW else lines.append("🟢 C3 정상.")
    if quant.get("C4") is not None:
        lines.append("🟡 C4 낮음 → 면역계 이상 가능.") if quant["C4"] < C4_LOW else lines.append("🟢 C4 정상.")
    if quant.get("RBC") is not None:
        v = quant["RBC"]
        lines.append("🟡 RBC 낮음 → 빈혈 가능.") if v < 4.0 else lines.append("🟡 RBC 높음 → 탈수/진성 적혈구증 감별.") if v > 5.5 else lines.append("🟢 RBC 정상.")
    if quant.get("WBC") is not None:
        v = quant["WBC"]
        lines.append("🟠 WBC 낮음 → 감염 위험.") if v < 4.0 else lines.append("🟠 WBC 높음 → 감염/염증 가능.") if v > 11.0 else lines.append("🟢 WBC 정상.")
    if quant.get("TG") is not None:
        v = quant["TG"]
        lines.append("🔴 TG ≥200 → 고중성지방혈증 가능.") if v >= 200 else lines.append("🟡 TG 150~199 → 경계.") if v >= 150 else lines.append("🟢 TG 양호.")
    if quant.get("HDL") is not None and quant["HDL"] > 0:
        lines.append("🟠 HDL 낮음(<40) → 심혈관 위험.") if quant["HDL"] < 40 else lines.append("🟢 HDL 양호.")
    if quant.get("LDL") is not None:
        v = quant["LDL"]
        lines.append("🔴 LDL ≥160 → 고LDL콜레스테롤혈증.") if v >= 160 else lines.append("🟡 LDL 130~159 → 경계.") if v >= 130 else lines.append("🟢 LDL 양호.")
    if quant.get("TC") is not None:
        v = quant["TC"]
        lines.append("🔴 총콜 ≥240 → 고지혈증 가능.") if v >= 240 else lines.append("🟡 총콜 200~239 → 경계.") if v >= 200 else lines.append("🟢 총콜 양호.")
    if not lines:
        lines.append("입력값이 없어 해석할 내용이 없습니다.")
    return lines

# ------------------------- 암 피수치(요청 라벨 그대로) + 저장/그래프 -------------------------
# 내부 key → 화면 라벨(요청 문자열 그대로)
ONCO_LAB_LABEL = {
    "WBC": "WBC(백혈구)",
    "Hb": "Hb(혈색소)",
    "PLT": "PLT(혈소판)",
    "ANC": "ANC(절대호중구,면역력)",
    "Ca": "ca(칼슘)",
    "Na": "Na(나트륨,소디움)",
    "Alb": "Alb(알부민)",
    "Glu": "glu(혈당)",
    "TP": "t,p(총단백질)",
    "AST": "ast(간수치)",
    "ALT": "alt(간세포)",
    "LD": "LD(유산탈수효소)",
    "CRP": "CRP(C.반응성단백,염증)",
    "Cr": "C,R(크레아티닌,신장)",
    "UA": "U.A(요산)",
    "Tbili": "T,b(총빌리루빈)"
}
ONCO_ORDER = ["WBC","Hb","PLT","ANC","Ca","Na","Alb","Glu","TP","AST","ALT","LD","CRP","Cr","UA","Tbili"]

def onco_labs_block(nickname_key: str):
    st.markdown("#### 🧪 암 피수치 (텍스트 입력) — 스피너 제거")
    c1, c2 = st.columns(2)
    # 왼쪽
    with c1:
        WBC = st.text_input(ONCO_LAB_LABEL["WBC"], placeholder="예: 4500")
        Hb  = st.text_input(ONCO_LAB_LABEL["Hb"],  placeholder="예: 12.3")
        PLT = st.text_input(ONCO_LAB_LABEL["PLT"], placeholder="예: 150000")
        ANC = st.text_input(ONCO_LAB_LABEL["ANC"], placeholder="예: 1200")
        Ca  = st.text_input(ONCO_LAB_LABEL["Ca"],  placeholder="예: 9.2")
        Na  = st.text_input(ONCO_LAB_LABEL["Na"],  placeholder="예: 140")
        Alb = st.text_input(ONCO_LAB_LABEL["Alb"], placeholder="예: 4.1")
        Glu = st.text_input(ONCO_LAB_LABEL["Glu"], placeholder="예: 95")
    # 오른쪽
    with c2:
        TP    = st.text_input(ONCO_LAB_LABEL["TP"],    placeholder="예: 7.0")
        AST   = st.text_input(ONCO_LAB_LABEL["AST"],   placeholder="예: 30")
        ALT   = st.text_input(ONCO_LAB_LABEL["ALT"],   placeholder="예: 28")
        LD    = st.text_input(ONCO_LAB_LABEL["LD"],    placeholder="예: 180")
        CRP   = st.text_input(ONCO_LAB_LABEL["CRP"],   placeholder="예: 0.8")
        Cr    = st.text_input(ONCO_LAB_LABEL["Cr"],    placeholder="예: 0.8")
        UA    = st.text_input(ONCO_LAB_LABEL["UA"],    placeholder="예: 4.5")
        Tbili = st.text_input(ONCO_LAB_LABEL["Tbili"], placeholder="예: 0.8")

    vals = {
        "WBC": num(WBC), "Hb": num(Hb), "PLT": num(PLT), "ANC": num(ANC),
        "Ca": num(Ca), "Na": num(Na), "Alb": num(Alb), "Glu": num(Glu),
        "TP": num(TP), "AST": num(AST), "ALT": num(ALT), "LD": num(LD),
        "CRP": num(CRP), "Cr": num(Cr), "UA": num(UA), "Tbili": num(Tbili),
    }

    # 경고/가이드(간단)
    alerts = []
    if vals["ANC"] is not None and vals["ANC"] < 500:
        alerts.append("🚨 ANC<500: 생채소 금지·익힌 음식, 남은 음식 장시간 보관 금지, 멸균 식품 권장.")
    if vals["Hb"] is not None and vals["Hb"] < 8:
        alerts.append("🟥 Hb<8: 어지러움/호흡곤란 시 진료.")
    if vals["PLT"] is not None and vals["PLT"] < 20000:
        alerts.append("🩹 PLT<20k: 출혈 주의(양치/면도/넘어짐).")
    if vals["CRP"] is not None and vals["CRP"] >= 3:
        alerts.append("🔥 CRP 상승: 발열·통증 동반 시 진료.")
    if vals["AST"] is not None and vals["AST"] >= 50:
        alerts.append("🟠 AST≥50: 간기능 저하 가능.")
    if vals["ALT"] is not None and vals["ALT"] >= 55:
        alerts.append("🟠 ALT≥55: 간세포 손상 의심.")
    if vals["Na"] is not None and (vals["Na"] < 130 or vals["Na"] > 150):
        alerts.append("⚠️ Na 130 미만/150 초과: 전해질 이상 평가 필요.")
    if vals["Ca"] is not None and (vals["Ca"] < 7.5 or vals["Ca"] > 11.5):
        alerts.append("⚠️ 칼슘 이상: 저/고칼슘혈증 증상 주의.")
    if vals["Cr"] is not None and vals["Cr"] > 1.5:
        alerts.append("🧪 크레아티닌 상승: 신장 기능 저하 가능.")
    if vals["Tbili"] is not None and vals["Tbili"] > 2.0:
        alerts.append("🟠 총빌리루빈 상승: 황달/담도 문제 평가.")
    if vals["LD"] is not None and vals["LD"] > 250:
        alerts.append("🧬 LD 상승: 용혈/조직 손상/종양활성 등 비특이적 상승.")

    shown = [f"{ONCO_LAB_LABEL[k]}: {v}" for k, v in vals.items() if v is not None]

    # 저장/그래프
    st.markdown("##### 💾 저장 및 그래프")
    colg1, colg2 = st.columns([1, 1])
    with colg1:
        when = st.date_input("측정일", value=date.today(), key="onco_lab_date")
    with colg2:
        save_ok = st.button("📈 피수치 저장/추가", use_container_width=True, key="onco_save")

    if save_ok:
        if not nickname_key or "#" not in nickname_key:
            st.warning("별명 + PIN을 입력하면 개인 히스토리로 저장됩니다.")
        else:
            st.session_state.setdefault("lab_history", {})
            df = st.session_state["lab_history"].get(nickname_key)

            # 라벨을 컬럼명으로 저장
            row = {"Date": when.strftime("%Y-%m-%d")}
            for k in ONCO_ORDER:
                label = ONCO_LAB_LABEL[k]
                row[label] = vals.get(k)

            if isinstance(df, pd.DataFrame):
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            else:
                cols = ["Date"] + [ONCO_LAB_LABEL[k] for k in ONCO_ORDER]
                df = pd.DataFrame([row], columns=cols)
            df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
            st.session_state["lab_history"][nickname_key] = df
            st.success("저장 완료! 아래 그래프에서 추이를 확인하세요.")

    # 그래프
    df_hist = st.session_state.get("lab_history", {}).get(nickname_key)
    if isinstance(df_hist, pd.DataFrame) and not df_hist.empty:
        st.markdown("##### 📊 추이 그래프")
        default_graph = [
            ONCO_LAB_LABEL["WBC"], ONCO_LAB_LABEL["Hb"], ONCO_LAB_LABEL["PLT"],
            ONCO_LAB_LABEL["CRP"], ONCO_LAB_LABEL["ANC"]
        ]
        pick = st.multiselect(
            "지표 선택",
            options=[c for c in df_hist.columns if c != "Date"],
            default=[c for c in default_graph if c in df_hist.columns]
        )
        if pick:
            st.line_chart(df_hist.set_index("Date")[pick], use_container_width=True)
        st.dataframe(df_hist, use_container_width=True, height=240)
    else:
        st.info("저장된 히스토리가 없습니다. 값을 입력하고 ‘피수치 저장/추가’를 눌러 보세요.")

    return vals, alerts, shown

# ------------------------- 별명 + PIN -------------------------
def nickname_pin():
    c1, c2 = st.columns([2, 1])
    with c1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리 숫자)", max_chars=4, placeholder="0000")
    pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
    if pin and pin != pin_clean:
        st.warning("PIN은 숫자 4자리만 허용됩니다.")
    key = (nickname.strip() + "#" + pin_clean) if nickname and pin_clean else (nickname or "").strip()
    return nickname, pin_clean, key

# ------------------------- 메인 -------------------------
def main():
    st.markdown("## 🩸 BloodMap — 보호자용 미니 해석 도우미")
    st.caption("치료 단계 UI 제외 / 개인정보 미수집 / 피수치 입력은 모두 텍스트로 스피너 제거")
    nickname, pin, nickname_key = nickname_pin()
    st.divider()

    mode = st.radio("모드 선택", ["암", "소아 가이드(질환 선택)"], horizontal=True)

    # 해열제(공통)
    antipyretic_block()
    st.divider()

    report_sections = []

    if mode == "암":
        # 암 피수치 블록 + 저장/그래프
        vals, alerts, shown = onco_labs_block(nickname_key)

        # 특수검사(토글)
        with st.expander("🧪 특수검사 (토글)", expanded=False):
            qual, quant = special_tests_inputs(prefix="sp_onco")
            if st.button("🔎 특수검사 해석", use_container_width=True, key="sp_onco_btn"):
                sp_lines = interpret_special_tests(qual, quant)
                st.markdown("#### 해석 결과")
                for L in sp_lines:
                    st.write("- " + L)
                report_sections.append(("특수검사 해석", sp_lines))

        if st.button("🔎 암 피수치 해석하기", use_container_width=True):
            sec = []
            if shown:
                sec += shown
            if alerts:
                sec += alerts
            report_sections.append(("암 피수치 해석 요약", sec if sec else ["입력값이 없습니다."]))

    else:
        # 소아 가이드: 질환 선택 + 증상 입력
        disease = st.selectbox(
            "질환 선택",
            ["코로나", "코로나(무증상)", "수족구", "장염(비특이적)", "편도염", "열감기(상기도염)", "기타"],
            index=0
        )
        sym = pediatric_symptom_inputs(prefix="peds")
        # 피수치 토글(선택)
        with st.expander("🧒 소아 피수치 (선택 입력/토글)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                p_wbc = st.text_input("WBC(백혈구)", key="p_wbc")
                p_hb  = st.text_input("Hb(혈색소)", key="p_hb")
            with c2:
                p_plt = st.text_input("PLT(혈소판)", key="p_plt")
                p_crp = st.text_input("CRP(염증지표)", key="p_crp")
            # 간단 해석 미리보기
            if st.checkbox("피수치 간단 해석 보기", value=False, key="p_labs_preview"):
                pv = {"WBC": num(p_wbc), "Hb": num(p_hb), "PLT": num(p_plt), "CRP": num(p_crp)}
                msgs = []
                if pv["WBC"] is not None and (pv["WBC"] < 4000 or pv["WBC"] > 11000):
                    msgs.append("WBC 범위 밖 → 감염/바이러스/탈수 등 확인.")
                if pv["Hb"] is not None and pv["Hb"] < 10:
                    msgs.append("Hb 낮음 → 빈혈 가능.")
                if pv["PLT"] is not None and pv["PLT"] < 150000:
                    msgs.append("PLT 낮음 → 출혈 주의.")
                if pv["CRP"] is not None and pv["CRP"] >= 3:
                    msgs.append("CRP 상승 → 염증/감염 가능.")
                if not msgs:
                    msgs = ["입력값이 없어 해석할 내용이 없습니다."]
                st.info("\n".join(["• " + m for m in msgs]))

        if st.button("🔎 소아 해석하기", use_container_width=True):
            risk, lines = interpret_pediatric(sym, disease=disease)
            report_sections.append((f"소아 가이드 해석 - {disease}", [f"위험도: {risk}"] + lines))
            st.markdown(f"### 🧠 종합 위험도: **{risk}**")
            for L in lines:
                st.write("- " + L)

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

