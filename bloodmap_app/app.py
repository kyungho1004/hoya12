# app.py — BloodMap
# (업데이트) 피수치 기반 식이가이드(예시) 추가 · 소아/암 연동 · 혈액암 철분+비타민C 경고 유지
# - 소아 질환: 로타/노로/파라/마이코 포함, 증상 최소항목 + 식이가이드(예시)
# - 암: 카테고리/진단 → 자동 예시 추천(항암/표적·면역/항생제) + 개별 선택
# - 피수치: 단일 컬럼(모바일 섞임 방지), 고정 컬럼 순서로 저장/그래프, 특수검사 토글
# - 식이가이드(예시): Alb/K/Hb/Na/Ca/혈당/AST·ALT/Cr·BUN/UA/CRP/ANC/PLT 조건별 5개 내외 예시 + 주의 문구
# 실행: streamlit run app.py

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

st.set_page_config(page_title="블러드맵 피수치가이드", page_icon="🩸", layout="centered")

# ------------------------- 공통 유틸 -------------------------
def _clean_num(s):
    if s is None: return None
    try:
        x = str(s).strip().replace("±","").replace("+","").replace(",","")
        if x in {"","-"}: return None
        return float(x)
    except: return None

def round_half(x):
    try: return round(float(x)*2)/2
    except: return None

def temp_band(t):
    try: t = float(t)
    except: return None
    if t < 37: return "36~37℃"
    if t < 38: return "37~38℃"
    if t < 39: return "38~39℃"
    return "≥39℃"

def rr_thr_by_age_m(m):
    try: m = float(m)
    except: return None
    if m < 2: return 60
    if m < 12: return 50
    if m < 60: return 40
    return 30

# ------------------------- 약물 DB -------------------------
CHEMO = {
    "ATRA (Tretinoin)": {"alias":"트레티노인(ATRA)", "moa":"RARα 작용·분화유도", "ae":"두통, 분화증후군"},
    "Arsenic Trioxide": {"alias":"삼산화비소(ATO)", "moa":"PML-RARα 분해", "ae":"QT 연장, 분화증후군"},
    "Daunorubicin": {"alias":"다우노루비신", "moa":"Topo II 억제/프리라디칼", "ae":"심독성"},
    "Idarubicin": {"alias":"이다루비신", "moa":"Topo II 억제", "ae":"심독성"},
    "Cytarabine": {"alias":"시타라빈(ARA-C)", "moa":"피리미딘 유사체", "ae":"골수억제, 결막염"},
    "MTX": {"alias":"메토트렉세이트", "moa":"DHFR 억제", "ae":"간독성, 골수억제"},
    "Methotrexate": {"alias":"메토트렉세이트", "moa":"DHFR 억제", "ae":"간독성, 골수억제"},
    "6-Mercaptopurine": {"alias":"6-머캅토퓨린(6-MP)", "moa":"푸린 합성 저해", "ae":"골수억제, 간독성"},
    "Thioguanine": {"alias":"티오구아닌(6-TG)", "moa":"푸린 유사체", "ae":"골수억제, 간독성"},
    "Vincristine": {"alias":"빈크리스틴", "moa":"미세소관 억제", "ae":"말초신경병증, 변비"},
    "Vinblastine": {"alias":"빈블라스틴", "moa":"미세소관 억제", "ae":"골수억제"},
    "Cyclophosphamide": {"alias":"사이클로포스파미드", "moa":"알킬화제", "ae":"출혈성 방광염"},
    "Etoposide": {"alias":"에토포시드", "moa":"Topo II 억제", "ae":"골수억제"},
    "Doxorubicin": {"alias":"독소루비신", "moa":"Topo II 억제/프리라디칼", "ae":"심독성"},
    "Prednisone": {"alias":"프레드니손", "moa":"글루코코르티코이드", "ae":"고혈당, 감염위험"},
    # 고형암/기타
    "Cisplatin": {"alias":"시스플라틴", "moa":"DNA 가닥 교차결합(백금제)", "ae":"신독성, 이독성, 오심"},
    "Carboplatin": {"alias":"카보플라틴", "moa":"백금제", "ae":"골수억제"},
    "Oxaliplatin": {"alias":"옥살리플라틴", "moa":"백금제", "ae":"말초신경병증"},
    "5-FU": {"alias":"5-플루오로우라실", "moa":"피리미딘 유사체", "ae":"점막염, 설사"},
    "Capecitabine": {"alias":"카페시타빈", "moa":"5-FU 전구약물", "ae":"수족증후군"},
    "Irinotecan": {"alias":"이리노테칸", "moa":"Topo I 억제", "ae":"설사, 골수억제"},
    "Docetaxel": {"alias":"도세탁셀", "moa":"미세소관 안정화", "ae":"무과립구열, 체액저류"},
    "Paclitaxel": {"alias":"파클리탁셀", "moa":"미세소관 안정화", "ae":"말초신경병증"},
    "Gemcitabine": {"alias":"젬시타빈", "moa":"핵산합성 억제", "ae":"골수억제"},
    "Pemetrexed": {"alias":"페메트렉시드", "moa":"엽산길 억제", "ae":"피로, 골수억제"},
    "Ifosfamide": {"alias":"이포스파미드", "moa":"알킬화제", "ae":"신경독성, 방광염"},
    "Bleomycin": {"alias":"블레오마이신", "moa":"DNA 절단", "ae":"폐독성"},
    "Hydroxyurea": {"alias":"하이드록시우레아", "moa":"리보뉴클레오타이드 환원효소 억제", "ae":"골수억제"},
    "Temozolomide": {"alias":"테모졸로마이드", "moa":"알킬화제", "ae":"골수억제"},
}

TARGETED = {
    "Rituximab": {"alias":"리툭시맙", "moa":"CD20 단일클론항체", "ae":"수액반응, 감염"},
    "Brentuximab vedotin": {"alias":"브렌툭시맙 베도틴", "moa":"CD30 ADC", "ae":"말초신경병증"},
    "Blinatumomab": {"alias":"블리나투모맙", "moa":"CD19 BiTE", "ae":"CRS, 신경독성"},
    "Inotuzumab ozogamicin": {"alias":"이노투주맙", "moa":"CD22 ADC", "ae":"간정맥폐쇄"},
    "Daratumumab": {"alias":"다라투무맙", "moa":"CD38 단일클론항체", "ae":"수액반응"},
    "Imatinib": {"alias":"이마티닙", "moa":"BCR-ABL TKI/GIST", "ae":"부종, 근육통"},
    "Dasatinib": {"alias":"다사티닙", "moa":"BCR-ABL TKI", "ae":"혈소판감소, 흉막삼출"},
    "Nilotinib": {"alias":"닐로티닙", "moa":"BCR-ABL TKI", "ae":"QT 연장"},
    "Osimertinib": {"alias":"오시머티닙", "moa":"EGFR TKI", "ae":"발진, 설사, QT 연장"},
    "Gefitinib": {"alias":"게피티닙", "moa":"EGFR TKI", "ae":"발진, 간수치상승"},
    "Erlotinib": {"alias":"얼로티닙", "moa":"EGFR TKI", "ae":"발진, 설사"},
    "Alectinib": {"alias":"알렉티닙", "moa":"ALK 억제", "ae":"근병증, 변비"},
    "Crizotinib": {"alias":"크리조티닙", "moa":"ALK/ROS1 억제", "ae":"시야장애, 오심"},
    "Larotrectinib": {"alias":"라로트렉티닙", "moa":"TRK 억제", "ae":"어지러움"},
    "Entrectinib": {"alias":"엔트렉티닙", "moa":"TRK/ROS1/ALK 억제", "ae":"체중증가"},
    "Trastuzumab": {"alias":"트라스투주맙", "moa":"HER2 단일클론항체", "ae":"심기능저하"},
    "Bevacizumab": {"alias":"베바시주맙", "moa":"VEGF 억제", "ae":"출혈/혈전, 단백뇨"},
    "Pembrolizumab": {"alias":"펨브롤리주맙", "moa":"PD-1 억제", "ae":"면역이상반응"},
    "Nivolumab": {"alias":"니볼루맙", "moa":"PD-1 억제", "ae":"면역이상반응"},
    "Atezolizumab": {"alias":"아테졸리주맙", "moa":"PD-L1 억제", "ae":"면역이상반응"},
    "Sorafenib": {"alias":"소라페닙", "moa":"다중 키나아제 억제(HCC/RCC)", "ae":"수족증후군, 고혈압"},
    "Lenvatinib": {"alias":"렌바티닙", "moa":"다중 키나아제 억제(HCC/갑상선)", "ae":"고혈압, 피로"},
    "Olaparib": {"alias":"올라파립", "moa":"PARP 억제", "ae":"빈혈, 피로"},
    "Sotorasib": {"alias":"소토라십", "moa":"KRAS G12C 억제", "ae":"간수치상승"},
}

ABX_ONCO = {
    "Piperacillin/Tazobactam": {"alias":"피페라실린/타조박탐", "note":"광범위 G(-)/혐기"},
    "Cefepime": {"alias":"세페핌", "note":"항녹농균 4세대"},
    "Ceftazidime": {"alias":"세프타지딤", "note":"항녹농균 3세대"},
    "Ceftriaxone": {"alias":"세프트리악손", "note":"3세대 세팔로"},
    "Cefazolin": {"alias":"세파졸린", "note":"1세대 세팔로"},
    "Meropenem": {"alias":"메로페넴", "note":"광범위 카바페넴"},
    "Vancomycin": {"alias":"반코마이신", "note":"G(+)/MRSA"},
    "Linezolid": {"alias":"라인졸리드", "note":"MRSA/VRE"},
    "Levofloxacin": {"alias":"레보플록사신", "note":"호흡기 FQ"},
    "Amikacin": {"alias":"아미카신", "note":"아미노글리코사이드"},
    "Metronidazole": {"alias":"메트로니다졸", "note":"혐기성"},
    "Fluconazole": {"alias":"플루코나졸", "note":"항진균"},
}

PEDS_MEDS = {
    "Dexamethasone": {"alias":"덱사메타손(스테로이드)", "note":"상기도염/크룹 등"},
    "Oseltamivir": {"alias":"오셀타미비르(항바이러스)", "note":"독감 의심/확진"},
    "Amoxicillin": {"alias":"아목시실린(항생제)", "note":"중이염/인두염"},
    "Amoxicillin/Clavulanate": {"alias":"아목시/클라불(항생제)", "note":"광범위"},
    "Azithromycin": {"alias":"아지스로마이신(항생제)", "note":"비정형"},
    "Cetirizine": {"alias":"세티리진(항히스타민)", "note":"알레르기 비염"},
    "Budesonide neb.": {"alias":"부데소니드(흡입)", "note":"천명/기관지염"},
    "Salbutamol neb.": {"alias":"살부타몰(네뷸)", "note":"기관지확장"},
    "Prednisolone": {"alias":"프레드니솔론", "note":"염증/쌕쌕거림"},
    "Ondansetron": {"alias":"온단세트론", "note":"구토 조절(의사 지시)"},
    "ORS": {"alias":"경구수분(ORS)", "note":"설사·구토 수분보충"},
    "Zinc": {"alias":"아연", "note":"설사 완화 보조"},
    "Palivizumab": {"alias":"팔리비주맙", "note":"RSV 예방(특수군)"},
}

# ------------------------- 암 카테고리/진단 -------------------------
# 진단명 표기: 영어/약어 + (한글 병기)
HEME = [
    "AML(급성 골수성 백혈병)", "APL(급성 전골수성 백혈병)", "ALL(급성 림프모구성 백혈병)",
    "CML(만성 골수성 백혈병)", "CLL(만성 림프구성 백혈병)",
    "MDS(골수형성이상증후군)", "MPN(골수증식성 질환)",
    "MM(다발골수종)", "AA(재생불량성 빈혈)", "HLH(혈구탐식성 림프조직구증)"
]
LYMPHOMA = [
    "Hodgkin(호지킨 림프종)",
    "DLBCL(미만성 거대 B세포 림프종)", "PMBCL(원발 종격동 B세포 림프종)",
    "FL1-2(여포성 1-2등급)", "FL3A(여포성 3A)", "FL3B(여포성 3B)",
    "MCL(외투세포 림프종)", "MZL(변연대 림프종)", "HGBL(고등급 B세포 림프종)",
    "BL(버킷 림프종)", "T-PLL(성인 T-림프모구성)",
    "PTCL-NOS(말초 T세포 림프종 NOS)", "AITL(혈관면역모세포성 T세포 림프종)",
    "ENKTL(NK/T 세포 림프종, 비강형)",
    "ALCL ALK+(역형성 대세포 림프종 ALK+)", "ALCL ALK-(역형성 대세포 림프종 ALK-)",
    "CTCL(MF/SS, 피부 T세포 림프종)"
]
SOLID = [
    "폐선암(Lung adenocarcinoma)", "폐편평(Lung squamous carcinoma)", "소세포폐암(SCLC)",
    "유방암(Breast cancer)", "위암(Gastric cancer)", "대장암(Colorectal cancer)",
    "간암(HCC)", "췌장암(Pancreatic cancer)", "담도암(Cholangiocarcinoma)",
    "자궁내막암(Endometrial cancer)", "자궁경부암(Cervical cancer)", "난소암(Ovarian cancer)",
    "전립선암(Prostate cancer)", "신장암(RCC)", "방광암(Bladder cancer)",
    "갑상선암(Thyroid cancer)", "흑색종(Melanoma)",
    "뇌종양(Glioma/Glioblastoma)", "식도암(Esophageal cancer)",
    "구강/후두암(Head & Neck)", "GIST(Gastrointestinal stromal tumor)"
]
SARCOMA = [
    "연부조직육종(Soft tissue sarcoma)", "골육종(Osteosarcoma)", "유잉육종(Ewing sarcoma)",
    "평활근육종(Leiomyosarcoma)", "지방육종(Liposarcoma)", "UPS/MFH(미분화형 다형성 육종)"
]
RARE = [
    "담낭암(Gallbladder cancer)", "부신피질암(Adrenocortical carcinoma)",
    "갈색세포종/부신경절종(Pheochromocytoma/Paraganglioma)",
    "흉선종/흉선암(Thymoma/Thymic carcinoma)", "신경내분비종양(NET)",
    "간모세포종(Hepatoblastoma)", "망막모세포종(Retinoblastoma)",
    "비인두암(Nasopharyngeal carcinoma)", "중피종(Mesothelioma)",
    "침샘암(Salivary gland carcinoma)", "소장암(Small bowel adenocarcinoma)",
    "척삭종(Chordoma)", "메르켈세포암(Merkel cell carcinoma)",
    "포도막 흑색종(Uveal melanoma)"
]# ------------------------- 피수치 라벨(한글 병기) -------------------------
LABS_ORDER = [
    ("WBC","WBC(백혈구)"),
    ("Hb","Hb(혈색소)"),
    ("PLT","PLT(혈소판)"),
    ("ANC","ANC(절대호중구,면역력)"),
    ("Ca","Ca(칼슘)"),
    ("Na","Na(나트륨,소디움)"),
    ("K","K(칼륨)"),
    ("Alb","Alb(알부민)"),
    ("Glu","Glu(혈당)"),
    ("TP","TP(총단백)"),
    ("AST","AST(간수치)"),
    ("ALT","ALT(간세포)"),
    ("LD","LD(유산탈수효소)"),
    ("CRP","CRP(C-반응성단백,염증)"),
    ("Cr","Cr(크레아티닌,신장)"),
    ("BUN","BUN(요소질소)"),
    ("UA","UA(요산)"),
    ("Tbili","Tbili(총빌리루빈)"),
]
LAB_LABELS = [label for _, label in LABS_ORDER]
LAB_COLS_FIXED = ["Date"] + LAB_LABELS

# ------------------------- 해열제 (평균값 ml, 0.5 반올림) -------------------------
ACET_MG_PER_ML = 160/5  # 32 mg/mL
IBU_MG_PER_ML  = 100/5  # 20 mg/mL

def apap_ml(weight_kg, mg_per_ml=ACET_MG_PER_ML):
    if not weight_kg: return None
    mg = 12.5 * float(weight_kg)
    return round_half(mg / mg_per_ml)

def ibu_ml(weight_kg, mg_per_ml=IBU_MG_PER_ML):
    if not weight_kg: return None
    mg = 10.0 * float(weight_kg)
    return round_half(mg / mg_per_ml)

def antipyretic_card():
    st.markdown("#### 🔥 해열제 (1회 평균 용량 기준)")
    c1, c2, c3 = st.columns([1.1,1,1])
    with c1: wt = st.number_input("체중(kg)", min_value=0.0, step=0.5)
    with c2: drug = st.selectbox("약제", ["아세트아미노펜", "이부프로펜"])
    with c3: conc = st.selectbox("시럽 농도", ["권장(기본)", "사용자 지정"])
    if drug=="아세트아미노펜":
        mgml = ACET_MG_PER_ML
        if conc=="사용자 지정":
            mg = st.number_input("아세트아미노펜 mg", min_value=1, step=1, value=160)
            ml = st.number_input("용량 mL", min_value=1.0, step=0.5, value=5.0)
            mgml = mg/ml
        one = apap_ml(wt, mgml)
        if one:
            st.success(f"**1회 용량: {one:.1f} mL**")
            st.caption("같은 약 간격 4–6시간 · 교차 사용은 보통 4시간 간격")
    else:
        mgml = IBU_MG_PER_ML
        if conc=="사용자 지정":
            mg = st.number_input("이부프로펜 mg", min_value=1, step=1, value=100)
            ml = st.number_input("용량 mL", min_value=1.0, step=0.5, value=5.0)
            mgml = mg/ml
        one = ibu_ml(wt, mgml)
        if one:
            st.success(f"**1회 용량: {one:.1f} mL**")
            st.caption("같은 약 간격 6–8시간 · 교차 사용은 보통 4시간 간격")

# ------------------------- 특수검사 (토글) -------------------------
QUAL = ["없음", "+", "++", "+++"]

def special_tests_ui():
    lines = []
    with st.expander("🧪 특수검사 (토글)", expanded=False):

        # 🔹 소변 검사
        st.markdown("### 🔹 소변 검사")
        col1 = st.columns(2)
        with col1[0]:
            alb = st.selectbox("알부민뇨", QUAL)
            hem = st.selectbox("혈뇨", QUAL)
        with col1[1]:
            sug = st.selectbox("요당", QUAL)
            ket = st.selectbox("케톤뇨", QUAL)

        # 🔸 면역·보체 검사
        st.markdown("### 🔸 면역 · 보체 검사")
        col2 = st.columns(2)
        with col2[0]:
            c3 = st.text_input("C3 (mg/dL)")
        with col2[1]:
            c4 = st.text_input("C4 (mg/dL)")

        # 🧬 지질 검사
        st.markdown("### 🧬 지질 검사")
        col3 = st.columns(2)
        with col3[0]:
            tg = st.text_input("TG (mg/dL)")
            hdl = st.text_input("HDL (mg/dL)")
        with col3[1]:
            ldl = st.text_input("LDL (mg/dL)")
            tc  = st.text_input("총콜레스테롤 (mg/dL)")

        # 🫀 신장/심장 기능
        st.markdown("### 🫀 신장 / 심장 기능")
        col4 = st.columns(2)
        with col4[0]:
            bun = st.text_input("BUN (mg/dL)")
            bnp = st.text_input("BNP (pg/mL)")
        with col4[1]:
            ckmb = st.text_input("CK-MB (ng/mL)")
            trop = st.text_input("Troponin-I (ng/mL)")
            myo  = st.text_input("Myoglobin (ng/mL)")

        # 🔍 해석 버튼 및 로직
        if st.button("🔎 특수검사 해석"):
            if alb!="없음": lines.append("알부민뇨 " + ("+"*QUAL.index(alb)) + " → 🟡~🔴 신장 이상 가능")
            if hem!="없음": lines.append("혈뇨 " + ("+"*QUAL.index(hem)) + " → 🟡 요로 염증/결석 등")
            if sug!="없음": lines.append("요당 " + ("+"*QUAL.index(sug)) + " → 🟡 고혈당/당뇨 의심")
            if ket!="없음": lines.append("케톤뇨 " + ("+"*QUAL.index(ket)) + " → 🟡 탈수/케톤증 가능")

            C3 = _clean_num(c3); C4 = _clean_num(c4)
            if C3 is not None: lines.append("C3 낮음 → 🟡 면역계 이상 가능" if C3 < 90 else "C3 정상/상승")
            if C4 is not None: lines.append("C4 낮음 → 🟡 면역계 이상 가능" if C4 < 10 else "C4 정상/상승")

            TG = _clean_num(tg); HDL = _clean_num(hdl); LDL = _clean_num(ldl); TC = _clean_num(tc)
            if TG is not None:
                lines.append("🔴 TG≥200: 고중성지방혈증 가능" if TG >= 200 else ("🟡 TG 150~199 경계" if TG >= 150 else "🟢 TG 양호"))
            if HDL is not None:
                lines.append("🟠 HDL<40: 심혈관 위험" if HDL < 40 else "🟢 HDL 양호")
            if LDL is not None:
                lines.append("🔴 LDL≥160: 고LDL콜" if LDL >= 160 else ("🟡 LDL 130~159 경계" if LDL >= 130 else "🟢 LDL 양호"))
            if TC is not None:
                lines.append("🔴 총콜≥240: 고지혈증" if TC >= 240 else ("🟡 총콜 200~239 경계" if TC >= 200 else "🟢 총콜 양호"))

            BUN = _clean_num(bun)
            if BUN is not None:
                lines.append("🔴 BUN≥25: 탈수/신장기능 저하 의심" if BUN >= 25 else "🟢 BUN 정상")
            BNP = _clean_num(bnp)
            if BNP is not None:
                lines.append("🔴 BNP≥100: 심부전 의심" if BNP >= 100 else "🟢 BNP 정상")

            CKMB = _clean_num(ckmb)
            TROP = _clean_num(trop)
            MYO = _clean_num(myo)

            if CKMB is not None:
                lines.append("🔴 CK-MB>5: 심장 손상 가능성" if CKMB > 5 else "🟢 CK-MB 정상")
            if TROP is not None:
                lines.append("🔴 Troponin-I>0.04: 심근경색 의심" if TROP > 0.04 else "🟢 Troponin-I 정상")
            if MYO is not None:
                lines.append("🟡 Myoglobin>85: 근육/심장 손상 가능성" if MYO > 85 else "🟢 Myoglobin 정상")

            if not lines:
                lines.append("입력값이 없어 해석할 내용이 없습니다.")
                
    return lines

# ------------------------- 별명+PIN -------------------------
def nickname_pin():
    c1,c2 = st.columns([2,1])
    with c1: n = st.text_input("별명", placeholder="예: 홍길동")
    with c2: p = st.text_input("PIN(4자리 숫자)", max_chars=4, placeholder="0000")
    p2 = "".join([c for c in (p or "") if c.isdigit()])[:4]
    if p and p2!=p: st.warning("PIN은 숫자 4자리만 허용됩니다.")
    key = (n.strip()+"#"+p2) if (n and p2) else (n or "guest")
    st.session_state["key"] = key
    return n, p2, key

# ------------------------- 항암 스케줄(간단 생성) -------------------------
def schedule_block():
    st.markdown("#### 📅 항암 스케줄(간단)")
    c1,c2,c3 = st.columns(3)
    with c1: start = st.date_input("시작일", value=date.today())
    with c2: cycle = st.number_input("주기(일)", min_value=1, step=1, value=21)
    with c3: ncyc = st.number_input("사이클 수", min_value=1, step=1, value=6)
    if st.button("스케줄 생성/추가"):
        rows = [{"Cycle": i+1, "Date": (start + timedelta(days=i*int(cycle))).strftime("%Y-%m-%d")} for i in range(int(ncyc))]
        df = pd.DataFrame(rows)
        st.session_state.setdefault("schedules", {})
        st.session_state["schedules"][st.session_state["key"]] = df
        st.success("스케줄이 저장되었습니다.")
    df = st.session_state.get("schedules", {}).get(st.session_state.get("key","guest"))
    if isinstance(df, pd.DataFrame) and not df.empty:
        st.dataframe(df, use_container_width=True, height=180)

# ------------------------- 암 자동 추천 -------------------------
def _labelize(db_keys, db):
    return [f"{k} ({db[k]['alias']})" for k in db_keys if k in db]

def auto_recs(dx_text: str):
    dx = (dx_text or "").lower()
    rec = {"chemo":[], "targeted":[], "abx":[]}

    # 혈액암
    if "apl" in dx:
        rec["chemo"] = ["ATRA (Tretinoin)","Arsenic Trioxide","Idarubicin","MTX","6-Mercaptopurine"]
        rec["abx"] = ["Piperacillin/Tazobactam","Cefepime"]
    elif "aml" in dx:
        rec["chemo"] = ["Cytarabine","Daunorubicin","Idarubicin"]
        rec["abx"] = ["Piperacillin/Tazobactam","Cefepime"]
    elif "all" in dx:
        rec["chemo"] = ["Vincristine","Daunorubicin","Cytarabine","MTX","6-Mercaptopurine","Cyclophosphamide","Prednisone"]
        rec["abx"] = ["Piperacillin/Tazobactam","Cefepime","Levofloxacin"]
    elif "cml" in dx:
        rec["targeted"] = ["Imatinib","Dasatinib","Nilotinib"]
    elif "cll" in dx:
        rec["targeted"] = ["Rituximab"]; rec["chemo"] = ["Cyclophosphamide","Prednisone"]

    # 림프종
    if "dlbcl" in dx or "pmbcl" in dx:
        rec["targeted"] += ["Rituximab"]
        rec["chemo"] += ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"]  # R-CHOP
    elif "mcl" in dx:
        rec["targeted"] += ["Rituximab"]; rec["chemo"] += ["Cytarabine","Cyclophosphamide"]
    elif "fl" in dx or "follicular" in dx:
        rec["targeted"] += ["Rituximab"]

    # 고형암
    if "폐암" in dx or "lung" in dx:
        rec["chemo"] += ["Cisplatin","Pemetrexed"]
        rec["targeted"] += ["Osimertinib","Alectinib","Crizotinib","Larotrectinib","Entrectinib"]
    if "유방암" in dx or "breast" in dx:
        rec["chemo"] += ["Doxorubicin","Cyclophosphamide","Paclitaxel"]; rec["targeted"] += ["Trastuzumab"]
    if "대장암" in dx or "colorectal" in dx:
        rec["chemo"] += ["Oxaliplatin","5-FU","Irinotecan","Capecitabine"]
    if "위암" in dx or "gastric" in dx:
        rec["chemo"] += ["Cisplatin","5-FU","Capecitabine"]; rec["targeted"] += ["Trastuzumab"]
    if "췌장암" in dx or "pancreatic" in dx:
        rec["chemo"] += ["Oxaliplatin","Irinotecan","5-FU","Gemcitabine"]
    if "간암" in dx or "hcc" in dx:
        rec["targeted"] += ["Sorafenib","Lenvatinib"]
    if "ovarian" in dx or "난소암" in dx:
        rec["chemo"] += ["Carboplatin","Paclitaxel"]; rec["targeted"] += ["Bevacizumab"]
    if "자궁경부암" in dx or "cervical" in dx:
        rec["chemo"] += ["Cisplatin"]; rec["targeted"] += ["Bevacizumab"]
    if "melanoma" in dx or "흑색종" in dx:
        rec["targeted"] += ["Pembrolizumab","Nivolumab"]
    if "rcc" in dx or "신장암" in dx:
        rec["targeted"] += ["Sorafenib"]
    if "glioma" in dx or "뇌종양" in dx:
        rec["chemo"] += ["Temozolomide"]

    if "담도암" in dx or "cholangiocarcinoma" in dx:
        rec["chemo"] += ["Gemcitabine","Cisplatin"]
    if "방광암" in dx or "bladder" in dx:
        rec["chemo"] += ["Gemcitabine","Cisplatin"]
    if "식도암" in dx or "esophageal" in dx:
        rec["chemo"] += ["Cisplatin","5-FU"]
    if "gist" in dx:
        rec["targeted"] += ["Imatinib"]

    # 중복 제거
    rec["chemo"] = list(dict.fromkeys(rec["chemo"]))
    rec["targeted"] = list(dict.fromkeys(rec["targeted"]))
    rec["abx"] = list(dict.fromkeys(rec["abx"]))
    return rec

# ------------------------- 피수치 기반 식이가이드(예시) -------------------------
def lab_diet_guides(labs: dict, heme_flag: bool = False):
    """
    labs: {'Alb':3.1, 'K':3.2, ...} 형태
    heme_flag: 혈액암 카테고리 여부(철분제+비타민C 경고 문구 추가)
    """
    L = []

    def add(title, foods, caution=None):
        if foods:
            L.append(f"{title} → 권장 예시: {', '.join(foods)}")
        if caution:
            L.append(f"주의: {caution}")

    Alb = labs.get("Alb"); K = labs.get("K"); Hb = labs.get("Hb"); Na = labs.get("Na"); Ca = labs.get("Ca")
    Glu = labs.get("Glu"); AST=labs.get("AST"); ALT=labs.get("ALT"); Cr=labs.get("Cr"); BUN=labs.get("BUN")
    UA=labs.get("UA"); CRP=labs.get("CRP"); ANC=labs.get("ANC"); PLT=labs.get("PLT")

    # ↓ 메모 기준 고정 리스트(5개, 음식 위주, '예시' 표기)
    if Alb is not None and Alb < 3.5:
        add("알부민 낮음", ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"])
    if K is not None and K < 3.5:
        add("칼륨 낮음", ["바나나","감자","호박죽","고구마","오렌지"])
    if Hb is not None and Hb < 10:
        add("Hb 낮음(빈혈)", ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
            caution="보충제는 식품이 아닙니다. (혈액암인 경우 철분제+비타민C 복용은 반드시 주치의와 상의)")
        if heme_flag:
            L.append("⚠️ 혈액암 환자: 철분제 + 비타민C 병용은 흡수 촉진 → 반드시 주치의와 상의 후 결정")
    if Na is not None and Na < 135:
        add("나트륨 낮음", ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"])
    if Ca is not None and Ca < 8.5:
        add("칼슘 낮음", ["연어통조림","두부","케일","브로콜리"], caution="참깨는 제외")
    if Glu is not None and Glu >= 140:
        add("혈당 높음", ["현미/귀리","두부 샐러드","채소 수프","닭가슴살","사과(소과)"],
            caution="당분 많은 간식/음료 피하기")
    if (Cr is not None and Cr > 1.2) or (BUN is not None and BUN > 20):
        add("신장 수치 상승", ["물/보리차 자주 조금씩","애호박/오이 수프","양배추찜","흰쌀죽","배/사과(소량)"],
            caution="단백질 과다 섭취·짠 음식 피하고, 탈수 주의")
    if (AST is not None and AST >= 50) or (ALT is not None and ALT >= 55):
        add("간수치 상승(AST/ALT)", ["구운 흰살생선","두부","삶은 야채","현미죽(소량)","올리브오일 드레싱 샐러드"],
            caution="기름진/튀김/술 피하기")
    if UA is not None and UA > 7:
        add("요산 높음", ["우유/요거트","달걀","감자","채소류","과일(체리 등)"],
            caution="내장·멸치·맥주 등 퓨린 높은 음식 제한")
    if CRP is not None and CRP >= 3:
        add("CRP 상승(염증)", ["토마토","브로콜리","블루베리","연어(완전 익히기)","올리브오일"],
            caution="생식 금지, 충분한 수분")
    if ANC is not None and ANC < 500:
        add("ANC<500 (호중구감소)", ["흰죽","계란찜(완숙)","연두부","잘 익힌 고기/생선","통조림 과일(시럽 제거)"],
            caution="생채소 금지 · 모든 음식은 완전히 익히기 또는 전자레인지 30초↑ · 멸균/살균 식품 권장 · 남은 음식은 2시간 지나면 폐기 · 껍질 있는 과일은 주치의와 상의")
    if PLT is not None and PLT < 20000:
        add("혈소판 낮음(PLT<20k)", ["계란찜","두부","바나나","오트밀죽","미역국"],
            caution="딱딱/자극 음식·술 피하고, 양치 시 부드러운 칫솔 사용")

    return L

# ------------------------- 메인 -------------------------
def main():
    # 헤더
    st.markdown("### 제작 Hoya/GPT · 자문 Hoya/GPT")
    st.info(
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
        "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
    )
    st.markdown("## 🩸 피수치가이드")
    st.caption("모바일 최적화 · 치료단계 UI 제외")
    nick, pin, key = nickname_pin()
    st.divider()

    mode = st.radio("모드 선택", ["암", "소아 가이드(질환 선택)"], horizontal=True)
    antipyretic_card()
    st.divider()

    report_sections = []

    if mode == "암":
        st.markdown("### 1) 암 선택")
        group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
        if group=="혈액암":
            dx = st.selectbox("혈액암(진단명)", HEME)
        elif group=="림프종":
            dx = st.selectbox("림프종(진단명)", LYMPHOMA)
        elif group=="고형암":
            dx = st.selectbox("고형암(진단명)", SOLID)
        elif group=="육종":
            dx = st.selectbox("육종(진단명)", SARCOMA)
        else:
            dx = st.selectbox("희귀암(긴 목록 일부)", RARE)

        # 혈액암 보충제 경고
        if group == "혈액암":
            msg = "혈액암 환자에서 **철분제 + 비타민 C** 복용은 흡수 촉진 가능성이 있어, **반드시 주치의와 상의 후** 복용 여부를 결정하세요."
            st.warning(msg); report_sections.append(("영양/보충제 주의", [msg]))

        # 자동 예시 추천
        st.markdown("### 2) 암 선택시(예시)")
        rec = auto_recs(dx)
        if any([rec["chemo"], rec["targeted"], rec["abx"]]):
            colr = st.columns(3)
            with colr[0]:
                st.markdown("**항암제 예시**")
                for lab in _labelize(rec["chemo"], CHEMO): st.write("- " + lab)
            with colr[1]:
                st.markdown("**표적/면역 예시**")
                for lab in _labelize(rec["targeted"], TARGETED): st.write("- " + lab)
            with colr[2]:
                st.markdown("**항생제(발열/호중구감소 시)**")
                for lab in _labelize(rec["abx"], ABX_ONCO): st.write("- " + lab)
            st.caption("※ 실제 치료는 환자 상태/바이오마커/가이드라인/의료진 판단에 따릅니다.")
            report_sections.append(("암 자동 예시", [f"진단: {dx}",
                                     f"항암제: {', '.join(rec['chemo']) or '-'}",
                                     f"표적/면역: {', '.join(rec['targeted']) or '-'}",
                                     f"항생제: {', '.join(rec['abx']) or '-'}"]))

        # 개별 선택
        st.markdown("### 3) 약물 개별 선택")
        chemo_opts = [f"{k} ({v['alias']})" for k,v in CHEMO.items()]
        targ_opts  = [f"{k} ({v['alias']})" for k,v in TARGETED.items()]
        abx_opts   = [f"{k} ({v['alias']})" for k,v in ABX_ONCO.items()]
        pick_chemo = st.multiselect("💊 항암제 선택", chemo_opts)
        pick_targ  = st.multiselect("🎯 표적/면역치료제 선택", targ_opts)
        pick_abx   = st.multiselect("🧪 항생제/항진균 선택", abx_opts)

        def _drug_lines(picks, db):
            out=[]
            for lab in picks:
                en = lab.split(" (")[0]
                info = db.get(en)
                if info:
                    moa = info.get('moa', info.get('note','')); ae  = info.get('ae','')
                    out.append(f"- **{en} ({info['alias']})** · 기전/특징: {moa}" + (f" · 주의: {ae}" if ae else ""))
            return out

        picked_lines = _drug_lines(pick_chemo, CHEMO) + _drug_lines(pick_targ, TARGETED) + _drug_lines(pick_abx, ABX_ONCO)
        if picked_lines:
            st.markdown("#### 선택 약물 요약")
            for L in picked_lines: st.write(L)
            report_sections.append(("선택 약물", [l.replace("**","") for l in picked_lines]))

        # 피수치 입력 — 단일 컬럼(모바일 안정)
        st.markdown("### 4) 암 피수치 (숫자만)")
        labs = {}
        for code, label in LABS_ORDER:
            v = st.text_input(label, placeholder="예: 4500")
            labs[code] = _clean_num(v)

        # 저장 & 그래프(고정 컬럼 순서)
        st.markdown("#### 💾 저장/그래프")
        when = st.date_input("측정일", value=date.today())
        if st.button("📈 피수치 저장/추가"):
            st.session_state.setdefault("lab_hist", {}).setdefault(key, pd.DataFrame())
            df_prev = st.session_state["lab_hist"][key]
            row = {"Date": when.strftime("%Y-%m-%d")}
            for code, label in LABS_ORDER:
                row[label] = labs.get(code)
            newdf = pd.DataFrame([row])
            if df_prev is None or df_prev.empty:
                df = newdf
            else:
                df = pd.concat([df_prev, newdf], ignore_index=True)
                df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
            for col in LAB_COLS_FIXED:
                if col not in df.columns: df[col] = pd.NA
            df = df.reindex(columns=LAB_COLS_FIXED)
            st.session_state["lab_hist"][key] = df
            st.success("저장 완료!")

        dfh = st.session_state.get("lab_hist", {}).get(key)
        if isinstance(dfh, pd.DataFrame) and not dfh.empty:
            st.markdown("##### 📊 추이 그래프")
            nonnull_cols = [c for c in LAB_LABELS if (c in dfh.columns and dfh[c].notna().any())]
            default_pick = [c for c in ["WBC(백혈구)","Hb(혈색소)","PLT(혈소판)","CRP(C-반응성단백,염증)","ANC(절대호중구,면역력)"] if c in nonnull_cols]
            pick = st.multiselect("지표 선택", options=nonnull_cols, default=default_pick)
            if pick: st.line_chart(dfh.set_index("Date")[pick], use_container_width=True)
            show_cols = ["Date"] + nonnull_cols
            st.dataframe(dfh[show_cols], use_container_width=True, height=220)
        else:
            st.info("저장된 히스토리가 없습니다. 값을 입력하고 ‘피수치 저장/추가’를 눌러 보세요.")

        # 특수검사
        sp_lines = special_tests_ui()
        if sp_lines:
            st.markdown("#### 🧬 특수검사 해석")
            for L in sp_lines: st.write("- "+L)
            report_sections.append(("특수검사 해석", sp_lines))

        # 주의 알림
        alerts=[]
        if labs.get("ANC") is not None and labs["ANC"]<500: alerts.append("🚨 ANC<500: 저균식/익힌 음식, 외부 노출 최소화")
        if labs.get("PLT") is not None and labs["PLT"]<20000: alerts.append("🩹 PLT<20k: 출혈 주의")
        if labs.get("CRP") is not None and labs["CRP"]>=3: alerts.append("🔥 CRP 상승: 감염평가 필요 가능")
        if labs.get("AST") is not None and labs["AST"]>=50: alerts.append("🟠 AST≥50: 간기능 저하 가능")
        if labs.get("ALT") is not None and labs["ALT"]>=55: alerts.append("🟠 ALT≥55: 간세포 손상 의심")
        if alerts:
            st.markdown("#### ⚠️ 주의 알림")
            for a in alerts: st.write("- "+a)
            report_sections.append(("주의 알림", alerts))

        # 🥗 피수치 기반 식이가이드(예시)
        diet_lines = lab_diet_guides(labs, heme_flag=(group=="혈액암"))
        if diet_lines:
            st.markdown("#### 🥗 피수치 기반 식이가이드 (예시)")
            for L in diet_lines: st.write("- " + L)
            report_sections.append(("피수치 기반 식이가이드(예시)", diet_lines))

        schedule_block()

        if st.button("🔎 해석하기"):
            shown = [f"{label}: {labs.get(code)}" for code,label in LABS_ORDER if labs.get(code) is not None]
            if shown:
                st.markdown("### 📋 암 피수치 요약")
                for s in shown: st.write("- "+s)
            if picked_lines: st.markdown("위 선택 약물 및 특수검사 해석을 참조하세요.")
            report_sections.append(("암 피수치 요약", shown if shown else ["입력값 없음"]))

    else:
        # 소아 가이드
        st.markdown("### 소아 질환 선택")
        disease = st.selectbox("질환", [
            "코로나","코로나(무증상)","수족구","장염(비특이적)","편도염","열감기(상기도염)",
            "RSV(호흡기세포융합바이러스)","아데노바이러스","독감(인플루엔자)",
            "로타바이러스(로타)","노로바이러스(노로)","파라인플루엔자(파라)","마이코플라즈마(비정형 폐렴)"
        ])

        st.markdown("#### 🧒 기본 계측")
        col = st.columns(3)
        with col[0]: age_m = st.number_input("나이(개월)", min_value=0, step=1)
        with col[1]: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
        with col[2]: spo2_have = st.checkbox("산소포화도 측정기 있음")
        rr = None; spo2 = None
        c2 = st.columns(2)
        with c2[0]: rr = st.number_input("호흡수(/분)", min_value=0, step=1)
        with c2[1]:
            if spo2_have: spo2 = st.number_input("SpO₂(%)", min_value=0, step=1)

        # 질환별 필요한 증상만
        st.markdown("#### 증상 입력(질환별 최소항목만)")
        vals = {}
        if disease=="수족구":
            c = st.columns(3)
            with c[0]: vals["분포"] = st.selectbox("수족구 분포", ["없음","입안","손발","전신"])
            with c[1]: vals["삼킴통증"] = st.selectbox("삼킴통증", ["없음","조금","보통","심함"])
            with c[2]: vals["타액증가"] = st.selectbox("타액 증가", ["없음","조금","보통","심함"])
        elif disease in ["장염(비특이적)","로타바이러스(로타)","노로바이러스(노로)"]:
            c = st.columns(2)
            with c[0]: vals["설사"] = st.selectbox("설사", ["없음","1~2회","3~4회","5~6회","7회 이상"])
            with c[1]: vals["구토"] = st.selectbox("구토", ["없음","1~2회","3~4회","5회 이상"])
        elif disease=="편도염":
            c = st.columns(2)
            with c[0]: vals["삼킴통증"] = st.selectbox("삼킴통증", ["없음","조금","보통","심함"])
            with c[1]: vals["타액증가"] = st.selectbox("타액 증가", ["없음","조금","보통","심함"])
        elif disease.startswith("코로나"):
            c = st.columns(3)
            with c[0]: vals["기침(주간)"] = st.selectbox("기침(주간)", ["없음","조금","보통","심함"])
            with c[1]: vals["기침(야간)"] = st.selectbox("기침(야간)", ["밤에 없음","보통","심함"])
            with c[2]: vals["콧물"] = st.selectbox("콧물", ["없음","투명","흰색","누런색","피섞임"])
        elif disease=="RSV(호흡기세포융합바이러스)":
            c = st.columns(3)
            with c[0]: vals["천명(쌕쌕)"] = st.selectbox("천명(쌕쌕)", ["없음","조금","보통","심함"])
            with c[1]: vals["함몰호흡"] = st.selectbox("함몰호흡(가슴/갈비)", ["없음","조금","보통","심함"])
            with c[2]: vals["수유감소"] = st.selectbox("수유/식이 감소", ["없음","조금","보통","심함"])
        elif disease=="아데노바이러스":
            c = st.columns(3)
            with c[0]: vals["결막충혈"] = st.selectbox("결막충혈/눈물", ["없음","조금","보통","심함"])
            with c[1]: vals["목통증"] = st.selectbox("목통증", ["없음","조금","보통","심함"])
            with c[2]: vals["설사/구토"] = st.selectbox("설사/구토", ["없음","1~2회","3~4회","5회 이상"])
        elif disease=="독감(인플루엔자)":
            c = st.columns(3)
            with c[0]: vals["근육통"] = st.selectbox("근육통", ["없음","조금","보통","심함"])
            with c[1]: vals["오한"] = st.selectbox("오한", ["없음","조금","보통","심함"])
            with c[2]: vals["기침"] = st.selectbox("기침", ["없음","조금","보통","심함"])
        elif disease=="파라인플루엔자(파라)":
            c = st.columns(3)
            with c[0]: vals["거친기침/크룹"] = st.selectbox("거친기침/크룹", ["없음","조금","보통","심함"])
            with c[1]: vals["쉰목소리"] = st.selectbox("쉰목소리", ["없음","조금","보통","심함"])
            with c[2]: vals["야간 악화"] = st.selectbox("야간 악화", ["없음","약간","자주","매우 잦음"])
        elif disease=="마이코플라즈마(비정형 폐렴)":
            c = st.columns(3)
            with c[0]: vals["마른기침"] = st.selectbox("마른기침", ["없음","조금","보통","심함"])
            with c[1]: vals["흉통/가슴불편"] = st.selectbox("흉통/가슴불편", ["없음","조금","보통","심함"])
            with c[2]: vals["피로/권태"] = st.selectbox("피로/권태", ["없음","조금","보통","심함"])
        else:
            c = st.columns(3)
            with c[0]: vals["콧물"] = st.selectbox("콧물", ["없음","투명","흰색","누런색","피섞임"])
            with c[1]: vals["기침(주간)"] = st.selectbox("기침(주간)", ["없음","조금","보통","심함"])
            with c[2]: vals["기침(야간)"] = st.selectbox("기침(야간)", ["밤에 없음","보통","심함"])

        # 소아 약(정보성)
        with st.expander("💊 소아 약(정보성) 선택 — 영어(한글)", expanded=False):
            q = st.text_input("검색(소아 약)")
            opts = [f"{k} ({v['alias']})" for k,v in PEDS_MEDS.items() if (not q) or q.lower() in k.lower() or q.lower() in v["alias"].lower()]
            pick = st.multiselect("선택", opts)
            if pick:
                st.caption("※ 처방/용량은 반드시 의료진 지시를 따르세요.")
                for lab in pick:
                    en = lab.split(" (")[0]
                    info = PEDS_MEDS.get(en, {})
                    st.write(f"- **{en} ({info.get('alias','')})** · 참고: {info.get('note','')}")

        # 소아 피수치(선택) — 단일 컬럼
        with st.expander("🧪 소아 피수치(선택 입력/토글)", expanded=False):
            p_wbc = st.text_input("WBC(백혈구)")
            p_hb  = st.text_input("Hb(혈색소)")
            p_plt = st.text_input("PLT(혈소판)")
            p_crp = st.text_input("CRP(염증지표)")
            if st.checkbox("간단 해석 보기"):
                info=[]
                W=_clean_num(p_wbc); H=_clean_num(p_hb); P=_clean_num(p_plt); C=_clean_num(p_crp)
                if W is not None and (W<4000 or W>11000): info.append("WBC 범위 밖 → 감염/바이러스/탈수 등 감별")
                if H is not None and H<10: info.append("Hb 낮음 → 빈혈 가능")
                if P is not None and P<150000: info.append("PLT 낮음 → 출혈 주의")
                if C is not None and C>=3: info.append("CRP 상승 → 염증/감염 가능")
                st.info("\n".join(["• "+m for m in (info or ["입력 없음"]) ]))
                # 소아도 해당 시 식이가이드(간단)
                labs_p = {"Hb":H, "PLT":P, "CRP":C}
                pdiet = []
                if H is not None and H<10:
                    pdiet += lab_diet_guides(labs_p)  # Hb 낮음 예시 재사용
                if P is not None and P<150000:
                    pdiet += [x for x in lab_diet_guides({"PLT":P})]
                if C is not None and C>=3:
                    pdiet += [x for x in lab_diet_guides({"CRP":C})]
                if pdiet:
                    st.markdown("**소아 피수치 기반 식이가이드 (예시)**")
                    for x in pdiet: st.write("- " + x)

        # 🥗 소아 식이가이드(질환별 예시)
        with st.expander("🥗 식이가이드 (예시)", expanded=True):
            foods, avoid, tips = peds_diet_guide(disease={}, vals={})
            # (호환성) disease/vals는 아래의 실제 구현에서 사용하므로 간단 wrapper:
        # 실제 가이드
        def peds_diet_guide(disease: str, vals: dict):
            d = (disease or "").lower()
            foods = []; avoid = []; tips  = []
            if "로타" in d or "장염" in d or "노로" in d:
                foods = ["쌀미음/야채죽","바나나","삶은 감자·당근","구운 식빵/크래커","연두부"]
                avoid = ["과일 주스·탄산","튀김/매운 음식","생채소/껍질 있는 과일","유당 많은 음식(설사 악화 시)"]
                tips  = ["소량씩 자주 ORS 보충","구토 후 10분 쉬고 한 모금씩","모유 수유 중이면 지속"]
            elif "독감" in d:
                foods = ["닭고기·야채죽","계란찜","연두부","사과퓨레/배숙","미지근한 국물"]
                avoid = ["매운/자극적인 음식","튀김/기름진 음식","카페인 음료"]
                tips  = ["고열·근육통 완화되면 빠르게 평소 식사로 회복","수분 충분히"]
            elif "rsv" in d or "상기도염" in d or "파라" in d:
                foods = ["미지근한 물/보리차","맑은 국/미음","연두부","계란찜","바나나/사과퓨레"]
                avoid = ["차갑고 자극적인 간식 과다","기름진 음식","질식 위험 작은 알갱이(견과류 등)"]
                tips  = ["작게·자주 먹이기","가습/코세척, 밤 기침 대비 베개 높이기"]
            elif "아데노" in d:
                foods = ["부드러운 죽","계란찜","연두부","사과퓨레","감자/당근 삶은 것"]
                avoid = ["매운/자극","튀김","과도한 단 음료"]
                tips  = ["결막염 동반 시 위생 철저(수건 분리)"]
            elif "마이코" in d:
                foods = ["닭가슴살죽","계란찜","연두부","흰살생선 죽","담백한 국"]
                avoid = ["매운/자극","튀김/기름진 음식","카페인 음료"]
                tips  = ["기침 심하면 자극 음식 피하고 수분 늘리기"]
            elif "수족구" in d:
                foods = ["차갑지 않은 부드러운 음식","바나나","요거트(자극 적음)","연두부","계란찜"]
                avoid = ["뜨겁고 매운 음식","산성 강한 과일(오렌지/파인애플 등)","튀김"]
                tips  = ["삼킴 통증 시 온도/질감 조절, 탈수 주의"]
            elif "편도염" in d:
                foods = ["부드러운 죽/미음","계란찜","연두부","따뜻한 국물","바나나"]
                avoid = ["매운/딱딱한 음식","튀김"]
                tips  = ["통증 조절하며 수분 충분히"]
            elif "코로나" in d:
                foods = ["부드러운 죽","연두부/계란찜","사과퓨레","바나나","맑은 국"]
                avoid = ["매운/자극","튀김/기름진 음식"]
                tips  = ["가족 간 전파 예방, 수분 충분히"]
            else:
                foods = ["부드러운 죽/미음","계란찜","연두부","사과퓨레","따뜻한 국물"]
                avoid = ["매운/자극","튀김"]
                tips  = ["3일 이상 고열 지속/악화 시 진료"]
            return foods, avoid, tips

        foods, avoid, tips = peds_diet_guide(disease, vals)
        st.markdown("**권장 예시**");  [st.write("- "+f) for f in foods]
        st.markdown("**피해야 할 예시**"); [st.write("- "+a) for a in avoid]
        if tips:
            st.markdown("**케어 팁**");   [st.write("- "+t) for t in tips]
        report_sections.append((f"소아 식이가이드 — {disease}",
                                [f"권장: {', '.join(foods)}", f"회피: {', '.join(avoid)}"] + ([f"팁: {', '.join(tips)}"] if tips else [])))

        # 해석하기
        if st.button("🔎 소아 해석하기"):
            out=[]
            if temp:
                band=temp_band(temp)
                if temp>=39.0: out.append(f"🚨 고열({temp:.1f}℃, {band}): **응급실/병원 내원 권고**")
                elif temp>=38.0: out.append(f"🌡️ 발열({temp:.1f}℃, {band}): 경과 관찰 + 해열제 고려")
                else: out.append(f"🌡️ 체온 {temp:.1f}℃ ({band})")
            thr = rr_thr_by_age_m(age_m)
            if rr and thr:
                out.append(f"🫁 호흡 빠름(RR {int(rr)}>{thr}/분): 악화 시 진료" if rr>thr else f"🫁 호흡수 {int(rr)}/분: 연령 기준 내(기준 {thr}/분)")
            if spo2_have and (spo2 is not None):
                if spo2<92: out.append(f"🧯 SpO₂ {int(spo2)}%: 저산소 → 즉시 진료")
                elif spo2<95: out.append(f"⚠️ SpO₂ {int(spo2)}%: 경계")
                else: out.append(f"🫧 SpO₂ {int(spo2)}%: 안정")
            dl=disease.lower(); tips2=[]
            if "코로나" in dl: tips2+=["🤒 코로나 의심: 보건소/PCR 문의, 동거가족 전파 주의"] if "무증상" not in dl else ["😷 무증상 노출: 자가 관찰, 필요 시 신속항원/PCR"]
            if "수족구" in dl: tips2+=["✋ 손발 수포·입안 통증 → 수분/통증 조절, 탈수 주의"]
            if "장염" in dl or "로타" in dl or "노로" in dl: tips2+=["💧 묽은 설사·구토 → ORS 소량씩 자주, 전해질 관리"]
            if "편도염" in dl: tips2+=["🧊 삼킴 통증·침 증가 → 부드러운 음식·해열제 반응 관찰"]
            if "rsv" in dl: tips2+=["🍼 수유 감소/함몰호흡·청색증 시 즉시 진료"]
            if "아데노" in dl: tips2+=["👁️ 결막염 동반 가능 → 손위생·수건 분리"]
            if "독감" in dl: tips2+=["⏱️ 48시간 내 항바이러스제 고려(의사 판단)"]
            if "파라" in dl: tips2+=["🗣️ 크룹 야간 악화 시 병원 상담, 습도/온도 관리"]
            out += tips2
            for L in out: st.write("- "+L)
            report_sections.append((f"소아 해석 — {disease}", out))

    # 보고서 저장
    st.divider()
    if report_sections:
        nicktag = f"{nick}#{pin}" if (nick and pin) else (nick or "guest")
        md = f"# BloodMap 보고서\n\n- 사용자: {nicktag}\n- 모드: {mode}\n\n"
        for title, lines in report_sections:
            md += f"## {title}\n"
            for L in lines: md += f"- {L}\n"
            md += "\n"
        md += (
            "---\n"
            "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
            "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
            "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.\n"
            "문의사항이나 버그 제보는 네이버까페에 제보해주시면 감사합니다.\n"
        )
        st.download_button("📥 보고서(.md) 다운로드", data=md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown", use_container_width=True)
        st.download_button("📄 보고서(.txt) 다운로드", data=md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain", use_container_width=True)

    # 하단 고지
    st.caption(
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다. "
        "약 변경/복용 중단 등은 반드시 주치의와 상의하세요. "
        "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다. "
        "문의사항이나 버그 제보는 네이버까페에 제보해주시면 감사합니다."
    )

if __name__ == "__main__":
    main()
