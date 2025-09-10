# app.py — BloodMap (self-contained, mobile-first)
# 포함:
# - 별명+PIN / 개인정보 미수집 고지
# - 해열제: 1회 평균 용량(ml)만, 0.5mL 반올림, (최대 가능 횟수), 교차 시간 안내
# - 소아 증상 입력/해석: 코로나(무증상 포함)/수족구/장염/편도염/열감기 + RSV/아데노/로타·노로/인플루/파라인플루엔자
# - 일반/암: 피수치(모바일 최소), 항암 스케줄(저장/표/CSV),
#   암 카테고리/진단 선택 → 항암제(영어+한글 병기)·표적치료제·항생제 요약
# - 혈액암/림프종: **진단명 한글 병기 UI 표기**
# - 특수검사(정성/정량) 토글 + 입력 + 자동 해석(🟢/🟡/🔴) — 암 선택 시 노출
# - 보고서: 화면 요약 → .md/.txt 다운로드
#
# ⚠️의료 고지: 본 해석은 참고용입니다. 모든 의학적 판단·약 변경/중단은 반드시 주치의와 상의하세요.

import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="BloodMap", page_icon="🩸", layout="centered")

# -------------------------
# 공통 유틸
# -------------------------
def round_half(x: float) -> float:
    try:
        return round(x * 2) / 2
    except Exception:
        return x

def num(v):
    try:
        if v is None or str(v).strip()=="":
            return None
        return float(v)
    except Exception:
        return None

def rr_threshold_by_age_months(m):
    if m is None:
        return None
    try:
        m = float(m)
    except:
        return None
    if m < 2:   return 60
    if m < 12:  return 50
    if m < 60:  return 40
    return 30  # ≥5y

def temp_band_label(t):
    if t is None:
        return None
    try:
        t = float(t)
    except:
        return None
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
    # 평균 12.5 mg/kg, q4-6h, 최대 5회/일
    if not weight_kg or not mg_per_ml:
        return None, None
    mg = 12.5 * weight_kg
    ml = mg / mg_per_ml
    return round_half(ml), 5

def dose_ibu_ml(weight_kg: float, mg_per_ml: float = IBU_DEFAULT_MG_PER_ML):
    # 평균 10 mg/kg, q6-8h, 최대 4회/일
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
            st.caption("같은 약 간격: **최소 4~6시간** (4시간 이내 재투여 금지)")
        else:
            st.caption("같은 약 간격: **최소 6~8시간** (6시간 이내 재투여 금지)")
        st.info("교차 사용: 일반적으로 **4시간 간격**을 두고 교차하세요. 같은 약의 최소 간격은 반드시 지키세요.")
    else:
        st.info("체중과 시럽 농도를 입력하면 **1회 평균 용량(ml)**이 계산됩니다. (0.5mL 단위 반올림)")

# -------------------------
# 소아 증상 UI + 해석
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
        "age_m": num(age_m),
        "temp": num(temp),
        "rr": num(rr),
        "spo2": num(spo2),
        "nasal": nasal,
        "stool": stool,
        "cough_day": cough_day,
        "cough_night": cough_night,
        "eye": eye,
        "activity": activity,
        "headache": headache,
        "hfmd_area": hfmd_area,
        "parent_vitals": parent_vitals,
    }

def interpret_pediatric(sym: dict, disease: str = ""):
    lines = []
    risk = "🟢 낮음"

    age_m = sym.get("age_m")
    temp = sym.get("temp")
    rr = sym.get("rr")
    spo2 = sym.get("spo2")
    nasal = sym.get("nasal")
    stool = sym.get("stool")
    cough_day = sym.get("cough_day")
    cough_night = sym.get("cough_night")
    eye = sym.get("eye")
    activity = sym.get("activity")
    headache = sym.get("headache")
    hfmd_area = sym.get("hfmd_area")
    pv = sym.get("parent_vitals")

    tb = temp_band_label(temp)
    if temp is not None:
        if temp >= 39.0:
            lines.append(f"🚨 고열(≥39.0℃, {tb}): **응급실/병원 내원 권고**.")
            risk = "🔴 높음"
        elif temp >= 38.0:
            lines.append(f"🌡️ 발열(38.0–38.9℃, {tb}): 경과 관찰 + 해열제 고려.")
        else:
            lines.append(f"🌡️ 체온 {temp:.1f}℃({tb}): 고열 소견은 없습니다.")

    thr = rr_threshold_by_age_months(age_m)
    if rr is not None and thr is not None:
        if rr > thr:
            lines.append(f"🫁 빠른 호흡(RR {int(rr)}>{thr}/분): 호흡기 증상 악화 시 진료 권고.")
            if risk != "🔴 높음":
                risk = "🟠 중간"
        else:
            lines.append(f"🫁 호흡수 {int(rr)}/분: 연령 기준 내(기준 {thr}/분).")

    if spo2 is not None:
        if spo2 < 92:
            lines.append(f"🧯 산소포화도 {int(spo2)}%: 저산소 범위 → 즉시 진료/응급 고려.")
            risk = "🔴 높음"
        elif spo2 < 95:
            lines.append(f"⚠️ 산소포화도 {int(spo2)}%: 경계 범위 → 악화 시 진료.")
            if risk != "🔴 높음":
                risk = "🟠 중간"
        else:
            lines.append(f"🫧 산소포화도 {int(spo2)}%: 안정.")

    if nasal and nasal != SYM_NONE:
        if nasal in ["누런색", "피섞임"]:
            lines.append(f"👃 콧물({nasal}): 2~3일 이상 지속·발열 동반 시 진료 상담.")
            if risk == "🟢 낮음":
                risk = "🟠 중간"
        else:
            lines.append(f"👃 콧물({nasal}): 비강 세척·가습 도움.")

    if stool and stool != SYM_NONE:
        lines.append(f"🚰 설사 {stool}: ORS 소량씩 자주. 소변 감소·무기력 시 진료 고려.")
        if stool in ["5~6회", "7회 이상"] and risk != "🔴 높음":
            risk = "🟠 중간"

    if cough_day and cough_day != SYM_NONE:
        lines.append(f"🗣️ 기침(주간) {cough_day}: 가습·수분섭취 권장.")
    if cough_night and cough_night != "밤에 없음":
        lines.append(f"🌙 기침(야간) {cough_night}: 야간 악화 시 진료 상담.")
        if risk == "🟢 낮음":
            risk = "🟠 중간"

    if eye and eye != SYM_NONE:
        lines.append(f"👁️ 눈곱 {eye}: 결막염 의심 시 손위생·수건 개별 사용.")

    if headache and headache != SYM_NONE:
        lines.append(f"🧠 두통 {headache}: 탈수·발열 시 악화 가능, 휴식/수분 보충.")

    if hfmd_area and hfmd_area != SYM_NONE:
        lines.append(f"✋ 수족구 분포: {hfmd_area} 병변 관찰 필요.")

    if activity == "조금 저하":
        lines.append("🛌 활동성 조금 저하: 휴식·수분 보충, 악화 시 진료.")
    elif activity == "많이 저하":
        lines.append("🛌 활동성 많이 저하: **진료 권고**.")
        risk = "🔴 높음"
    if pv == "변화 있음":
        lines.append("📈 보호자 판단상 '활력징후 변화 있음' → 주의 관찰/진료 상담 권고.")
        if risk == "🟢 낮음":
            risk = "🟠 중간"

    dl = (disease or "").lower()
    disease_tips = []
    if "rsv" in dl:
        disease_tips.append("🫁 RSV 의심: 영아·야간 악화 주의, 호흡곤란·함몰 시 즉시 진료.")
    if ("로타" in dl) or ("노로" in dl):
        disease_tips.append("🚰 로타/노로 의심: ORS 소량씩 자주, 지사제 임의복용 지양.")
    if ("아데노" in dl) or ("adeno" in dl):
        disease_tips.append("👁️ 아데노 의심: 결막염 동반 가능, 손위생·수건 분리.")
    if ("인플루" in dl) or ("독감" in dl):
        disease_tips.append("🦠 인플루엔자 의심: 고열·근육통 동반 시 항바이러스제 상담.")
    if ("파라" in dl) or ("parainfluenza" in dl):
        disease_tips.append("🗣️ 파라인플루엔자: 후두염/크룹 주의, 찬 공기/가습 도움.")
    if "코로나(무증상)" in disease or ("코로나" in disease and "무증상" in disease):
        disease_tips.append("😷 코로나 무증상: 노출력 있으면 자가 관찰, 필요 시 신속항원/PCR 상담.")
        disease_tips.append("🤒 가족 간 전파 주의, 격리 수칙 준수.")
    elif "코로나" in disease:
        disease_tips.append("🤒 코로나 의심: 가족 간 전파 주의, PCR 필요 시 보건소 문의.")
    if "수족구" in disease:
        disease_tips.append("✋ 수족구 의심: 손발 수포·입안 통증 동반, 탈수 주의.")
        if hfmd_area and hfmd_area != SYM_NONE:
            disease_tips.append(f"✋ 병변 위치: {hfmd_area} — 통증 시 시원한 유동식 권장.")
    if "장염" in disease:
        disease_tips.append("💩 장염 의심: 묽은 설사·구토 동반, 전해질 관리 중요.")
    if "편도염" in disease:
        disease_tips.append("🧊 편도염 의심: 삼킴 통증·침 분비 증가, 해열제 반응 관찰.")
    if ("열감기" in disease) or ("상기도염" in disease):
        disease_tips.append("🌡️ 열감기 의심: 미열 + 콧물/기침, 3일 이상 고열 지속 시 진료.")

    lines.extend(disease_tips)
    return risk, lines

# -------------------------
# (NEW) 특수검사 입력 + 해석
# -------------------------
QUAL_CHOICES = ["없음", "+", "++", "+++"]

def special_tests_inputs(prefix="sp"):
    st.markdown("##### 🧪 특수검사 입력")
    c1, c2 = st.columns(2)
    with c1:
        alb = st.selectbox("알부민뇨/단백뇨", QUAL_CHOICES, key=f"{prefix}_alb")
        hema = st.selectbox("혈뇨", QUAL_CHOICES, key=f"{prefix}_hema")
        glu = st.selectbox("요당", QUAL_CHOICES, key=f"{prefix}_glu")
        ket = st.selectbox("케톤뇨", QUAL_CHOICES, key=f"{prefix}_ket")
        occult = st.selectbox("잠혈(요/대변)", QUAL_CHOICES, key=f"{prefix}_occ")
    with c2:
        c3 = st.number_input("C3 (mg/dL)", min_value=0.0, step=1.0, key=f"{prefix}_c3")
        c4 = st.number_input("C4 (mg/dL)", min_value=0.0, step=1.0, key=f"{prefix}_c4")
        rbc = st.number_input("적혈구 RBC (×10⁶/μL)", min_value=0.0, step=0.1, key=f"{prefix}_rbc")
        wbc = st.number_input("백혈구 WBC (×10³/μL)", min_value=0.0, step=0.1, key=f"{prefix}_wbc")
        tg  = st.number_input("TG (중성지방, mg/dL)", min_value=0.0, step=1.0, key=f"{prefix}_tg")
        hdl = st.number_input("HDL (mg/dL)", min_value=0.0, step=1.0, key=f"{prefix}_hdl")
        ldl = st.number_input("LDL (mg/dL)", min_value=0.0, step=1.0, key=f"{prefix}_ldl")
        tc  = st.number_input("총콜레스테롤 (mg/dL)", min_value=0.0, step=1.0, key=f"{prefix}_tc")

    qual = {"알부민뇨": alb, "혈뇨": hema, "요당": glu, "케톤뇨": ket, "잠혈": occult}
    quant = {"C3": num(c3), "C4": num(c4), "RBC": num(rbc), "WBC": num(wbc),
             "TG": num(tg), "HDL": num(hdl), "LDL": num(ldl), "TC": num(tc)}
    return qual, quant

def interpret_special_tests(qual: dict, quant: dict):
    lines = []

    # 정성 검사
    for k, v in qual.items():
        if v and v != "없음":
            if v == "+":
                lines.append(f"🟡 {k} {v} → 경미한 이상, 추적 관찰 권장.")
            elif v == "++":
                lines.append(f"🟠 {k} {v} → 의미 있는 이상, 원인 평가 필요.")
            else:  # "+++"
                tip = "🚨 신장 기능 이상 가능성" if k in ["알부민뇨","혈뇨"] else "🚨 대사/염증 이상 가능성"
                lines.append(f"🔴 {k} {v} → {tip}, 진료 권고.")

    # 정량 검사
    C3_LOW, C4_LOW = 90, 10
    if quant.get("C3") is not None:
        if quant["C3"] < C3_LOW:
            lines.append("🟡 C3 낮음 → 면역계 이상(루푸스 등) 가능성, 경과/재검 권장.")
        else:
            lines.append("🟢 C3 정상 범위로 보입니다.")
    if quant.get("C4") is not None:
        if quant["C4"] < C4_LOW:
            lines.append("🟡 C4 낮음 → 면역계 이상 가능성, 임상 맥락 확인.")
        else:
            lines.append("🟢 C4 정상 범위로 보입니다.")

    if quant.get("RBC") is not None:
        if quant["RBC"] < 4.0:
            lines.append("🟡 RBC 낮음 → 빈혈 가능성, 철분/영양 상태 확인.")
        elif quant["RBC"] > 5.5:
            lines.append("🟡 RBC 높음 → 탈수/진성적혈구증 등 감별 필요.")
        else:
            lines.append("🟢 RBC 대체로 정상 범위.")
    if quant.get("WBC") is not None:
        if quant["WBC"] < 4.0:
            lines.append("🟠 WBC 낮음(백혈구 감소) → 감염 위험, 발열 시 즉시 평가.")
        elif quant["WBC"] > 11.0:
            lines.append("🟠 WBC 높음 → 감염/염증 가능성.")
        else:
            lines.append("🟢 WBC 정상 범위.")

    if quant.get("TG") is not None:
        if quant["TG"] >= 200:
            lines.append("🔴 TG ≥200 → 고중성지방혈증 가능, 식이/운동/약물 상담.")
        elif quant["TG"] >= 150:
            lines.append("🟡 TG 150~199 → 경계 영역.")
        else:
            lines.append("🟢 TG 양호.")
    if quant.get("HDL") is not None and quant["HDL"] > 0:
        if quant["HDL"] < 40:
            lines.append("🟠 HDL 낮음(<40) → 심혈관 위험 증가 가능.")
        else:
            lines.append("🟢 HDL 양호.")
    if quant.get("LDL") is not None:
        if quant["LDL"] >= 160:
            lines.append("🔴 LDL ≥160 → 고LDL콜레스테롤혈증 가능.")
        elif quant["LDL"] >= 130:
            lines.append("🟡 LDL 130~159 → 경계 위험.")
        else:
            lines.append("🟢 LDL 양호.")
    if quant.get("TC") is not None:
        if quant["TC"] >= 240:
            lines.append("🔴 총콜레스테롤 ≥240 → 고지혈증 가능.")
        elif quant["TC"] >= 200:
            lines.append("🟡 총콜레스테롤 200~239 → 경계.")
        else:
            lines.append("🟢 총콜레스테롤 양호.")

    if not lines:
        lines.append("입력값이 없어 해석할 내용이 없습니다.")
    return lines

# -------------------------
# 항암제/표적치료/항생제 데이터
# -------------------------
drug_info = {
    # Cytotoxics
    "Cytarabine": {"ko":"시타라빈(ARA-C)", "mech":"핵산 합성 억제(S-phase).", "se":"골수억제, 발열, 고용량 시 신경독성/결막염."},
    "Daunorubicin": {"ko":"다우노루비신", "mech":"Topo II 억제.", "se":"심독성, 골수억제, 점막염."},
    "Idarubicin": {"ko":"이다루비신", "mech":"Topo II 억제.", "se":"심독성, 골수억제."},
    "Cyclophosphamide": {"ko":"사이클로포스파미드", "mech":"알킬화제.", "se":"골수억제, 출혈성 방광염(메스나)."},
    "Etoposide": {"ko":"에토포사이드", "mech":"Topo II 억제.", "se":"골수억제, 저혈압(주입속도)."},
    "Fludarabine": {"ko":"플루다라빈", "mech":"푸린 유사체.", "se":"면역억제/감염 위험, 골수억제."},
    "Hydroxyurea": {"ko":"하이드록시유레아", "mech":"RNR 억제.", "se":"골수억제, 피부변화."},
    "Methotrexate": {"ko":"메토트렉세이트(MTX)", "mech":"DHFR 억제.", "se":"간독성, 골수억제, 구내염(폴린산)."},
    "ATRA": {"ko":"트레티노인(ATRA)", "mech":"분화 유도.", "se":"분화증후군, 간수치 상승, 피부/점막 자극."},
    "G-CSF": {"ko":"필그라스팀(그라신 계열)", "mech":"호중구 생성 자극.", "se":"골통, 드물게 비장비대."},
    "Asparaginase": {"ko":"아스파라기나제", "mech":"아스파라긴 고갈.", "se":"췌장염, 알레르기, 혈전."},
    "Vincristine": {"ko":"빈크리스틴", "mech":"미세소관 억제.", "se":"말초신경병증, 변비."},
    "Doxorubicin": {"ko":"독소루비신", "mech":"Topo II 억제.", "se":"심독성, 탈모, 점막염."},
    "Ifosfamide": {"ko":"이포스파미드", "mech":"알킬화제.", "se":"신경/신독성, 출혈성 방광염(메스나)."},
    "Gemcitabine": {"ko":"젬시타빈", "mech":"핵산 합성 억제.", "se":"골수억제, 발열감, 간수치 상승."},
    "Oxaliplatin": {"ko":"옥살리플라틴", "mech":"백금계 DNA 교차결합.", "se":"말초신경병증(한랭 유발)."},
    "Irinotecan": {"ko":"이리노테칸", "mech":"Topo I 억제.", "se":"설사(급성/지연), 골수억제."},
    "5-FU": {"ko":"플루오로우라실(5-FU)", "mech":"피리미딘 대사 교란.", "se":"구내염, 설사, 수족증후군."},
    "Capecitabine": {"ko":"카페시타빈", "mech":"경구 5-FU 전구약.", "se":"수족증후군, 설사."},
    "Paclitaxel": {"ko":"파클리탁셀", "mech":"미세소관 안정화.", "se":"알레르기, 골수억제, 말초신경병증."},
    "Docetaxel": {"ko":"도세탁셀", "mech":"미세소관 안정화.", "se":"부종, 골수억제, 점막염."},
    "Cisplatin": {"ko":"시스플라틴", "mech":"백금계 DNA 결합.", "se":"신독성, 이독성, 구역/구토."},
    "Carboplatin": {"ko":"카보플라틴", "mech":"백금계 DNA 결합.", "se":"골수억제, 구역/구토."},
    "Trabectedin": {"ko":"트라벡테딘", "mech":"DNA 결합/전사 억제.", "se":"간독성, 골수억제."},
    "Temozolomide": {"ko":"테모졸로마이드", "mech":"알킬화제.", "se":"골수억제, 오심."},
    "Pemetrexed": {"ko":"페메트렉시드", "mech":"엽산 길항제.", "se":"골수억제, 피로(엽산/비12 보충)."},
    "Cabazitaxel": {"ko":"카바지탁셀", "mech":"미세소관 안정화.", "se":"호중구감소, 설사."},

    # Targeted / IO
    "Imatinib": {"ko":"이마티닙", "mech":"BCR-ABL/PDGFR/c-KIT TKI.", "se":"부종, 근육통, 발진."},
    "Dasatinib": {"ko":"다사티닙", "mech":"BCR-ABL TKI.", "se":"흉막삼출, 혈소판감소."},
    "Nilotinib": {"ko":"닐로티닙", "mech":"BCR-ABL TKI.", "se":"QT 연장, 고혈당."},
    "Gefitinib": {"ko":"게피티닙", "mech":"EGFR TKI.", "se":"발진, 설사, 간수치 상승."},
    "Erlotinib": {"ko":"엘로티닙", "mech":"EGFR TKI.", "se":"발진, 설사."},
    "Osimertinib": {"ko":"오시머티닙", "mech":"EGFR T790M/Ex19/L858R TKI.", "se":"QT 연장, 간질성폐질환(드묾)."},
    "Alectinib": {"ko":"알렉티닙", "mech":"ALK TKI.", "se":"근육효소 상승, 변비."},
    "Sunitinib": {"ko":"수니티닙", "mech":"VEGFR/PDGFR TKI.", "se":"핸드풋, 고혈압, 피로."},
    "Pazopanib": {"ko":"파조파닙", "mech":"VEGFR TKI.", "se":"간독성, 고혈압."},
    "Regorafenib": {"ko":"레고라페닙", "mech":"다중키나아제 억제.", "se":"핸드풋, 고혈압."},
    "Bevacizumab": {"ko":"베바시주맙", "mech":"VEGF-A 항체.", "se":"고혈압, 출혈/천공(드묾)."},
    "Trastuzumab": {"ko":"트라스투주맙", "mech":"HER2 항체.", "se":"심기능 저하, 주입반응."},
    "Pembrolizumab": {"ko":"펨브롤리주맙", "mech":"PD-1 면역관문 억제.", "se":"면역관련 부작용(피부/간/폐/내분비)."},
    "Nivolumab": {"ko":"니볼루맙", "mech":"PD-1 면역관문 억제.", "se":"면역관련 부작용."},
    "Rituximab": {"ko":"리툭시맙", "mech":"CD20 항체.", "se":"B형간염 재활성화, 주입반응."},
    "Polatuzumab vedotin": {"ko":"폴라투주맙 베도틴", "mech":"CD79b ADC.", "se":"말초신경병증, 골수억제."},
    "Brentuximab vedotin": {"ko":"브렌툭시맙 베도틴", "mech":"CD30 ADC.", "se":"말초신경병증."},
    "Lenvatinib": {"ko":"렌바티닙", "mech":"VEGFR 등 TKI.", "se":"고혈압, 단백뇨, 피로."},
    "Ibrutinib": {"ko":"이브루티닙", "mech":"BTK 억제제.", "se":"출혈, 부정맥, 고혈압."},
}

# 암 카테고리 → 진단 라벨/키
heme_label_map = {
    "AML": "AML (급성골수성백혈병)",
    "APL": "APL (급성전골수구백혈병)",
    "ALL": "ALL (급성림프모구백혈병)",
    "CML": "CML (만성골수성백혈병)",
    "CLL": "CLL (만성림프구성백혈병)",
}
lymphoma_label_map = {
    "DLBCL": "DLBCL (미만성 거대 B세포 림프종)",
    "PMBCL": "PMBCL (원발성 종격동 B세포 림프종)",
    "FL12":  "FL grade1-2 (여포성 림프종 1-2등급)",
    "FL3A":  "FL grade3A (여포성 림프종 3A)",
    "FL3B":  "FL grade3B (여포성 림프종 3B)",
    "MCL":   "MCL (외투세포 림프종)",
    "MZL":   "MZL (변연부 림프종)",
    "HGBL":  "HGBL (고등급 B세포 림프종)",
    "BL":    "BL (버킷 림프종)",
}
heme_codes = list(heme_label_map.keys())
lymphoma_codes = list(lymphoma_label_map.keys())

solid_cancers = [
    "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)","대장암(Colorectal cancer)",
    "간암(HCC)","췌장암(Pancreatic cancer)","담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
    "구강/후두암(Head&Neck)","피부암(흑색종)","신장암(RCC)","갑상선암(Thyroid)","난소암(Ovarian)",
    "자궁경부암(Cervical)","전립선암(Prostate)","뇌종양(Glioma)","식도암(Esophageal)","방광암(Bladder)"
]
sarcoma_dx = ["연부조직육종(Soft tissue sarcoma)","골육종(Osteosarcoma)","유잉육종(Ewing sarcoma)",
              "평활근육종(Leiomyosarcoma)","지방육종(Liposarcoma)","악성 섬유성 조직구종(UPS/MFH)"]
rare_cancers = ["담낭암(Gallbladder)","부신암(Adrenal)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)","간모세포종(Hepatoblastoma)",
                "비인두암(NPC)","GIST"]

# 진단 → (항암제, 표적/면역, 대표 요법)
heme_by_cancer = {
    "AML": (["Cytarabine","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","Methotrexate","ATRA","G-CSF"], [] , []),
    "APL": (["ATRA","Idarubicin","Daunorubicin","Cytarabine","Methotrexate","G-CSF"], [], []),
    "ALL": (["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","Methotrexate","Cytarabine","Etoposide"], [], []),
    "CML": (["Hydroxyurea"], ["Imatinib","Dasatinib","Nilotinib"], []),
    "CLL": (["Fludarabine","Cyclophosphamide"], [], []),
}
solid_by_cancer = {
    "폐암(Lung cancer)": (["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed"], ["Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"], []),
    "유방암(Breast cancer)": (["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel"], ["Trastuzumab","Bevacizumab","Pembrolizumab"], []),
    "위암(Gastric cancer)": (["Cisplatin","Oxaliplatin","5-FU","Capecitabine","Paclitaxel"], ["Trastuzumab","Pembrolizumab"], []),
    "대장암(Colorectal cancer)": (["5-FU","Capecitabine","Oxaliplatin","Irinotecan"], ["Bevacizumab","Regorafenib"], []),
    "간암(HCC)": ([], ["Sunitinib","Lenvatinib","Bevacizumab","Pembrolizumab","Nivolumab"], []),
    "췌장암(Pancreatic cancer)": (["Gemcitabine","Oxaliplatin","Irinotecan","5-FU"], [], []),
    "담도암(Cholangiocarcinoma)": (["Gemcitabine","Cisplatin"], ["Bevacizumab"], []),
    "자궁내막암(Endometrial cancer)": (["Carboplatin","Paclitaxel"], [], []),
    "구강/후두암(Head&Neck)": (["Cisplatin","5-FU","Docetaxel"], [], []),
    "피부암(흑색종)": (["Paclitaxel"], ["Nivolumab","Pembrolizumab"], []),
    "신장암(RCC)": ([], ["Sunitinib","Pazopanib","Bevacizumab","Nivolumab","Pembrolizumab"], []),
    "갑상선암(Thyroid)": ([], ["Lenvatinib","Sorafenib"], []),
    "난소암(Ovarian)": (["Carboplatin","Paclitaxel"], ["Bevacizumab"], []),
    "자궁경부암(Cervical)": (["Cisplatin","Paclitaxel"], ["Bevacizumab"], []),
    "전립선암(Prostate)": (["Docetaxel","Cabazitaxel"], [], []),
    "뇌종양(Glioma)": (["Temozolomide"], ["Bevacizumab"], []),
    "식도암(Esophageal)": (["Cisplatin","5-FU","Paclitaxel"], ["Nivolumab","Pembrolizumab"], []),
    "방광암(Bladder)": (["Cisplatin","Gemcitabine"], ["Bevacizumab","Pembrolizumab","Nivolumab"], []),
}
sarcoma_by_dx = {
    "연부조직육종(Soft tissue sarcoma)": (["Doxorubicin","Ifosfamide","Pazopanib","Gemcitabine","Docetaxel"], [], []),
    "골육종(Osteosarcoma)": (["Doxorubicin","Cisplatin","Ifosfamide","Methotrexate"], [], []),
    "유잉육종(Ewing sarcoma)": (["Vincristine","Doxorubicin","Cyclophosphamide","Ifosfamide","Etoposide"], [], []),
    "평활근육종(Leiomyosarcoma)": (["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel","Pazopanib"], [], []),
    "지방육종(Liposarcoma)": (["Doxorubicin","Ifosfamide","Trabectedin"], [], []),
    "악성 섬유성 조직구종(UPS/MFH)": (["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel"], [], []),
}
rare_by_cancer = {
    "담낭암(Gallbladder)": (["Gemcitabine","Cisplatin"], [], []),
    "부신암(Adrenal)": (["Mitotane","Etoposide","Doxorubicin","Cisplatin"], [], []),
    "망막모세포종(Retinoblastoma)": (["Vincristine","Etoposide","Carboplatin"], [], []),
    "흉선종/흉선암(Thymoma/Thymic carcinoma)": (["Cyclophosphamide","Doxorubicin","Cisplatin"], [], []),
    "신경내분비종양(NET)": (["Etoposide","Cisplatin","Sunitinib"], [], []),
    "간모세포종(Hepatoblastoma)": (["Cisplatin","Doxorubicin"], [], []),
    "비인두암(NPC)": (["Cisplatin","5-FU","Gemcitabine"], ["Bevacizumab","Nivolumab","Pembrolizumab"], []),
    "GIST": ([], ["Imatinib","Sunitinib","Regorafenib"], []),
}
lymphoma_regimens = {
    "DLBCL": ["R-CHOP","Pola-R-CHP","DA-EPOCH-R","R-ICE","R-DHAP","R-GDP","R-GemOx","R-ESHAP","Pola-BR"],
    "PMBCL": ["DA-EPOCH-R","R-ICE","R-DHAP","R-GDP","R-GemOx"],
    "FL12":  ["BR","R-CVP","R-CHOP","Obinutuzumab+BR","Lenalidomide+R"],
    "FL3A":  ["R-CHOP","Pola-R-CHP","BR"],
    "FL3B":  ["R-CHOP","Pola-R-CHP","DA-EPOCH-R"],
    "MCL":   ["BR","R-CHOP","R-ICE","R-DHAP"],
    "MZL":   ["BR","R-CVP","R-CHOP"],
    "HGBL":  ["R-CHOP","Pola-R-CHP","DA-EPOCH-R","R-ICE","R-DHAP","R-GDP"],
    "BL":    ["CODOX-M/IVAC-R","Hyper-CVAD-R","R-ICE"],
}
lymphoma_targets = {
    "DLBCL": ["Polatuzumab vedotin","Rituximab","Lenalidomide"],
    "PMBCL": ["Pembrolizumab","Nivolumab"],
    "FL12":  ["Rituximab","Lenalidomide"],
    "FL3A":  ["Rituximab","Polatuzumab vedotin"],
    "FL3B":  ["Rituximab","Polatuzumab vedotin"],
    "MCL":   ["Ibrutinib","Lenalidomide","Rituximab"],
    "MZL":   ["Rituximab"],
    "HGBL":  ["Polatuzumab vedotin","Rituximab"],
    "BL":    ["Rituximab"],
}

common_abx = [
    "Piperacillin/Tazobactam (피페라실린/타조박탐): 광범위, 호중구감소성 발열 1차 옵션 중.",
    "Cefepime (세페핌): 항녹농균 4세대 세팔로스포린.",
    "Meropenem (메로페넴): ESBL/중증 패혈증 고려.",
    "Vancomycin (반코마이신): MRSA 커버, 신장·농도 모니터.",
    "Levofloxacin (레보플록사신): 경구 가능, QT 연장 주의.",
    "TMP/SMX (트리메토프림/설파메톡사졸): PCP 예방/치료, 전해질·혈구감소 주의.",
]

def drug_display_lines(drug_names):
    out = []
    for en in drug_names:
        if en not in drug_info:
            out.append(f"{en} (정보 요약 준비 중)")
            continue
        ko = drug_info[en]["ko"]
        mech = drug_info[en]["mech"]
        se = drug_info[en]["se"]
        out.append(f"**{en} ({ko})** — 기전: {mech} / 부작용: {se}")
    return out

def render_cancer_drugs(group, cancer_key):
    lines, extra, regimens = [], [], []
    if group == "혈액암" and cancer_key in heme_by_cancer:
        chemo, targeted, regs = heme_by_cancer[cancer_key]
        lines += drug_display_lines(chemo)
        if targeted:
            extra.append("### 표적치료제")
            extra += drug_display_lines(targeted)
        regimens = regs
    elif group == "고형암" and cancer_key in solid_by_cancer:
        chemo, targeted, regs = solid_by_cancer[cancer_key]
        if chemo:
            lines.append("### 항암제(세포독성)")
            lines += drug_display_lines(chemo)
        if targeted:
            extra.append("### 표적/면역치료제")
            extra += drug_display_lines(targeted)
        regimens = regs
    elif group == "육종" and cancer_key in sarcoma_by_dx:
        chemo, targeted, regs = sarcoma_by_dx[cancer_key]
        lines += drug_display_lines(chemo)
        regimens = regs
    elif group == "희귀암" and cancer_key in rare_by_cancer:
        chemo, targeted, regs = rare_by_cancer[cancer_key]
        if chemo:
            lines.append("### 항암제")
            lines += drug_display_lines(chemo)
        if targeted:
            extra.append("### 표적치료제")
            extra += drug_display_lines(targeted)
        regimens = regs
    elif group == "림프종" and cancer_key in lymphoma_regimens:
        regimens = lymphoma_regimens.get(cancer_key, [])
        tg = lymphoma_targets.get(cancer_key, [])
        if tg:
            extra.append("### 표적/면역치료제")
            extra += drug_display_lines(tg)

    abx = ["### 자주 쓰는 항생제(요약)"] + [f"- {x}" for x in common_abx]
    return lines, extra, regimens, abx

# -------------------------
# 항암 스케줄
# -------------------------
def render_schedule(nickname_key: str):
    st.markdown("### 🗓️ 항암 스케줄")
    col1, col2 = st.columns(2)
    with col1:
        regimen = st.text_input("요법/레짐명", placeholder="예: R-CHOP / ATRA+IDA 등", key="sch_reg")
        start = st.date_input("사이클 시작일", value=date.today(), key="sch_start")
        cycles = st.number_input("총 사이클 수", min_value=1, max_value=12, value=6, step=1, key="sch_cycles")
    with col2:
        cycle_len = st.number_input("사이클 길이(일)", min_value=7, max_value=42, value=21, step=1, key="sch_len")
        days = st.multiselect("투여일(사이클 내 Day)", options=list(range(1, 29)), default=[1], key="sch_days")
        memo = st.text_input("메모 (선택)", placeholder="예: 외래/입원, 수액, 주사 등", key="sch_memo")

    if st.button("📌 스케줄 생성/업데이트", use_container_width=True):
        rows = []
        for c in range(1, int(cycles)+1):
            base = start + timedelta(days=(c-1)*int(cycle_len))
            for d in sorted(days):
                rows.append({
                    "Cycle": c,
                    "Day": d,
                    "Date": (base + timedelta(days=d-1)).strftime("%Y-%m-%d"),
                    "Regimen": regimen or "",
                    "Memo": memo or ""
                })
        df = pd.DataFrame(rows, columns=["Cycle","Day","Date","Regimen","Memo"])
        st.session_state.setdefault("schedule_store", {})
        st.session_state["schedule_store"][nickname_key] = df
        st.success("스케줄이 저장되었습니다.")

    store = st.session_state.get("schedule_store", {}).get(nickname_key)
    if isinstance(store, pd.DataFrame) and not store.empty:
        st.dataframe(store, use_container_width=True, height=240)
        csv = store.to_csv(index=False).encode("utf-8-sig")
        st.download_button("CSV 저장", data=csv, file_name=f"chemo_schedule_{nickname_key}.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("스케줄이 없습니다. 위에서 생성해 주세요.")

# -------------------------
# 별명 + PIN
# -------------------------
def nickname_pin():
    c1, c2 = st.columns([2,1])
    with c1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리 숫자)", max_chars=4, placeholder="0000")
    pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
    if pin and pin != pin_clean:
        st.warning("PIN은 숫자 4자리만 허용됩니다.")
    key = (nickname.strip() + "#" + pin_clean) if nickname and pin_clean else (nickname or "").strip()
    return nickname, pin_clean, key

# -------------------------
# 일반/암 — 간단 피수치 입력 (모바일 최소)
# -------------------------
def labs_block():
    st.markdown("#### 🧪 주요 수치 (선택 입력)")
    c1, c2 = st.columns(2)
    with c1:
        wbc = st.number_input("WBC(백/μL)", min_value=0.0, step=100.0, help="예: 4500 → 4,500")
        hb  = st.number_input("Hb(g/dL)", min_value=0.0, step=0.1)
        plt = st.number_input("혈소판(/μL)", min_value=0.0, step=1000.0)
        anc = st.number_input("ANC(/μL)", min_value=0.0, step=100.0)
        crp = st.number_input("CRP(mg/L)", min_value=0.0, step=0.1)
    with c2:
        ast = st.number_input("AST(U/L)", min_value=0.0, step=1.0)
        alt = st.number_input("ALT(U/L)", min_value=0.0, step=1.0)
        cr  = st.number_input("Cr(mg/dL)", min_value=0.0, step=0.1)
        alb = st.number_input("Albumin(g/dL)", min_value=0.0, step=0.1)
        glu = st.number_input("Glucose(mg/dL)", min_value=0.0, step=1.0)

    vals = {
        "WBC": num(wbc), "Hb": num(hb), "혈소판": num(plt), "ANC": num(anc), "CRP": num(crp),
        "AST": num(ast), "ALT": num(alt), "Cr": num(cr), "Albumin": num(alb), "Glucose": num(glu),
    }
    out = []
    if vals["ANC"] is not None and vals["ANC"] < 500:
        out.append("🚨 호중구 <500: 생채소 금지·익혀 먹기·남은 음식 2시간 이후 비권장·멸균식품 권장.")
    if vals["Hb"] is not None and vals["Hb"] < 8:
        out.append("🟥 빈혈 심화(Hb<8): 어지러움/호흡곤란 시 진료.")
    if vals["혈소판"] is not None and vals["혈소판"] < 20000:
        out.append("🩹 혈소판 <20k: 출혈 주의, 넘어짐·양치 출혈 관찰.")
    if vals["AST"] is not None and vals["AST"] >= 50:
        out.append("🟠 AST ≥50: 간기능 저하 가능.")
    if vals["ALT"] is not None and vals["ALT"] >= 55:
        out.append("🟠 ALT ≥55: 간세포 손상 의심.")
    if vals["CRP"] is not None and vals["CRP"] >= 3:
        out.append("🔥 염증 반응(CRP↑): 발열·통증 동반 시 진료.")
    if vals["Albumin"] is not None and vals["Albumin"] < 3.0:
        out.append("🥛 알부민 낮음: 부드러운 단백식 권장(달걀/연두부/흰살생선/닭가슴살/귀리죽).")

    shown = [f"{k}: {v}" for k, v in vals.items() if v is not None]
    return vals, out, shown

# -------------------------
# 메인
# -------------------------
def main():
    st.markdown("## 🩸 BloodMap — 보호자용 미니 해석 도우미")
    st.caption("혼돈 방지: **세포·면역 치료(CAR-T 등)는 표기하지 않습니다.** / 이 앱은 개인정보를 수집하지 않습니다.")
    nickname, pin, nickname_key = nickname_pin()
    st.divider()

    mode = st.radio("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"], horizontal=True)

    # 해열제(공통)
    antipyretic_block()
    st.divider()

    report_sections = []

    if mode == "일반/암":
        # 1) 피수치
        vals, alerts, shown = labs_block()
        if st.button("🔎 피수치 해석하기", use_container_width=True, key="labs_btn"):
            sec = []
            if shown: sec += [f"{s}" for s in shown]
            if alerts: sec += alerts
            report_sections.append(("피수치 해석 요약", sec if sec else ["입력값이 충분하지 않습니다."]))

        # 2) 암 카테고리/진단 → 약제 요약
        st.markdown("#### 🧬 암 카테고리/진단 선택")
        group = st.selectbox("암 카테고리", ["혈액암","고형암","육종","희귀암","림프종","미선택/일반"], index=0)

        header_label = ""
        cancer_key = None

        if group == "혈액암":
            options = [heme_label_map[k] for k in heme_codes]
            selected = st.selectbox("진단", options, index=0)
            rev = {v:k for k,v in heme_label_map.items()}
            cancer_key = rev[selected]
            header_label = selected
        elif group == "림프종":
            options = [lymphoma_label_map[k] for k in lymphoma_codes]
            selected = st.selectbox("진단", options, index=0)
            rev = {v:k for k,v in lymphoma_label_map.items()}
            cancer_key = rev[selected]
            header_label = selected
        elif group == "고형암":
            cancer_key = st.selectbox("진단", solid_cancers, index=0)
            header_label = cancer_key
        elif group == "육종":
            cancer_key = st.selectbox("진단", sarcoma_dx, index=0)
            header_label = cancer_key
        elif group == "희귀암":
            cancer_key = st.selectbox("진단", rare_cancers, index=0)
            header_label = cancer_key
        else:
            header_label = "[미선택/일반]"
            cancer_key = None

        if st.button("💊 항암제/표적치료 보기", use_container_width=True, key="drug_btn"):
            lines, extra, regs, abx = render_cancer_drugs(group, cancer_key)
            st.markdown(f"### [{group}] {header_label}")
            if regs:
                st.markdown("**대표 요법(레짐)**")
                for r in regs:
                    st.write(f"- {r}")
            if lines:
                for L in lines:
                    st.write(f"- {L}" if not L.startswith("###") else L)
            if extra:
                for L in extra:
                    st.write(f"- {L}" if not L.startswith("###") else L)
            st.markdown("### 감염 대비 참고")
            for L in abx:
                st.write(L)

            # 보고서 섹션
            rep = []
            if regs: rep.append("대표 요법: " + ", ".join(regs))
            if lines: rep += [L.replace("**","") for L in lines if not L.startswith("###")]
            if extra: rep += [L.replace("**","") for L in extra if not L.startswith("###")]
            rep += [x for x in abx]
            report_sections.append((f"암 진단: [{group}] {header_label}", rep if rep else ["해당 데이터 없음"]))

        # 3) (NEW) 특수검사 — 암 선택 시 토글
        if group in ["혈액암","고형암","육종","희귀암","림프종"]:
            with st.expander("🧪 특수검사 (암 선택 시)", expanded=False):
                qual, quant = special_tests_inputs(prefix="sp")
                if st.button("🔎 특수검사 해석하기", use_container_width=True, key="sp_btn"):
                    sp_lines = interpret_special_tests(qual, quant)
                    st.markdown("#### 해석 결과")
                    for L in sp_lines:
                        st.write("- " + L)
                    report_sections.append(("특수검사 해석", sp_lines))

        # 4) 항암 스케줄
        with st.expander("🗓️ 항암 스케줄 관리", expanded=True):
            if not nickname_key:
                st.info("별명 + PIN을 입력하면 스케줄을 개인별로 저장할 수 있습니다.")
            render_schedule(nickname_key or "guest")

    elif mode == "소아(일상/호흡기)":
        sym = pediatric_symptom_inputs(prefix="p1")
        if st.button("🔎 소아 해석하기", use_container_width=True):
            risk, lines = interpret_pediatric(sym, disease="")
            st.markdown(f"### 🧠 종합 위험도: **{risk}**")
            for L in lines:
                st.write("- " + L)
            st.markdown("### 🏠 가정 관리 팁")
            st.write("- 손위생·기침 예절, 비강 세척/가습")
            st.write("- 소량씩 자주 수분/식사, 부드러운 식감")
            st.write("- 충분한 휴식, 악화 시 진료")
            report_sections.append(("소아(일상/호흡기) 해석", [f"위험도: {risk}"] + lines))

    else:  # 소아(감염질환)
        disease = st.selectbox(
            "질환 선택",
            [
                "코로나", "코로나(무증상)",
                "수족구", "장염(비특이적)", "편도염", "열감기(상기도염)",
                "RSV", "아데노(PCF)", "로타/노로", "인플루엔자(독감)", "파라인플루엔자", "기타"
            ],
            index=0
        )
        sym = pediatric_symptom_inputs(prefix="p2")
        if st.button("🔎 소아 질환 해석하기", use_container_width=True):
            risk, lines = interpret_pediatric(sym, disease=disease)
            st.markdown(f"### 🧠 종합 위험도: **{risk}**")
            st.markdown(f"**질환 선택:** {disease}")
            for L in lines:
                st.write("- " + L)
            st.markdown("### 🏠 가정 관리 팁")
            st.write("- 손위생·기침 예절, 비강 세척/가습")
            st.write("- ORS 소량씩 자주(구토/설사 시), 지사제 임의 복용 지양")
            st.write("- 야간 악화/호흡곤란/탈수 소견 시 즉시 진료")
            report_sections.append((f"소아(감염질환) 해석 - {disease}", [f"위험도: {risk}"] + lines))

    # 보고서 저장
    st.divider()
    if report_sections:
        md = build_report_md(nickname, pin, mode, report_sections)
        st.download_button("📥 보고서(.md) 다운로드", data=md.encode("utf-8"), file_name="bloodmap_report.md", mime="text/markdown", use_container_width=True)
        st.download_button("📄 보고서(.txt) 다운로드", data=md.encode("utf-8"), file_name="bloodmap_report.txt", mime="text/plain", use_container_width=True)

    st.caption(
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다. "
        "약 변경/복용 중단 등은 반드시 주치의와 상의하세요. "
        "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
    )

if __name__ == "__main__":
    main()
