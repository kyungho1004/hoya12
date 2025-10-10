# -*- coding: utf-8 -*-
import streamlit as st

# ============================
# Basic Setup
# ============================
st.set_page_config(page_title="피수치 · 보호자 가이드", layout="wide")
st.info("이 앱의 안내는 참고용입니다. 응급이 의심되면 지체하지 말고 119 또는 가까운 응급실을 이용해 주세요.")

# ============================
# Utilities & State
# ============================
def wkey(s: str) -> str:
    return f"app_{s}"

def get_weights():
    if "weights" not in st.session_state:
        st.session_state["weights"] = {}
    return st.session_state["weights"]

def set_weights(newW):
    st.session_state["weights"] = dict(newW)

# 프리셋(원하면 계속 추가)
PRESETS = {
    "기본(Default)": {},
    "보수적(안전 우선)": {
        "w_temp_ge_38_5": 1.2, "w_dyspnea": 1.2, "w_confusion": 1.2,
        "w_oliguria": 1.2, "w_persistent_vomit": 1.2
    },
}

# ============================
# 암 종류(상단 분류 탭)
# ============================
CANCER_TYPES = [
    "위암", "대장암", "간암", "췌담도암", "폐암",
    "유방암", "자궁/난소암", "전립선/방광암",
    "두경부암", "뇌종양",
    "혈액암(백혈병/림프종/다발골수종)"
]

def get_onco_type_guides(cancer: str):
    base_diet = [
        "소량씩 자주 드세요(작은 접시, 2~3시간 간격).",
        "단백질 보충: 달걀/두부/살코기/생선/요거트 등.",
        "수분은 한 번에 많이 말고 **조금씩 자주**.",
        "매운/지나치게 기름진 음식, 강한 향은 일시적으로 줄이기."
    ]
    base_tests = ["CBC(혈액), 전해질, 간/신장 기능", "필요 시 CRP/PCT 등 염증지표"]
    base_notes = ["체중/섭취량/소변·배변 기록은 진료에 도움이 됩니다."]
    diet = list(base_diet); tests = list(base_tests); notes = list(base_notes)

    if cancer == "위암":
        diet += ["소화 쉬운 **연식/죽**으로 시작 후 점차 일반식으로.", "식후 바로 눕지 말고 20–30분 의자에 앉아 쉬기."]
        tests += ["철분/비타민 B12(수술 후 흡수장애 가능성)"]
        notes += ["덤핑증후군 의심 시 소량·저당식, 수분은 식간에."]
    elif cancer == "대장암":
        diet += ["배변 불편 시 **부드러운 저잔사식**부터, 호전되면 섬유소 서서히 증가.", "수분 충분히."]
        tests += ["CEA(진행/추적 시 의료진 판단)", "대변 잠혈(상황별)"]
        notes += ["설사 지속 시 수분·전해질 보충, 유제품은 일시 제한 가능."]
    elif cancer == "간암":
        diet += ["알코올은 **금지**.", "단백질은 과하지 않게 균형, 염분 과다 섭취 주의."]
        tests += ["AST/ALT/ALP, 빌리루빈, PT/INR", "AFP ± 영상(의료진 판단)"]
        notes += ["복수/부종 있으면 염분 제한과 체중·부종 관찰."]
    elif cancer == "췌담도암":
        diet += ["기름진 음식은 증상 악화 가능, **저지방식** 우선.", "담즙정체/흡수장애 시 **지용성 비타민 보충** 상담."]
        tests += ["Bil/ALP/GGT, 아밀레이스·리파아제", "CA 19-9(의료진 판단)"]
        notes += ["담즙 정체(황달/소양감) 시 즉시 상담."]
    elif cancer == "폐암":
        diet += ["숨참 시 한 번에 많이 먹지 말고 조금씩.", "단백질/열량 밀도 높은 간식 활용."]
        tests += ["흉부 X-ray/CT, 산소포화도, 필요 시 심전도"]
        notes += ["기침 심하면 따뜻한 음료·가습 도움."]
    elif cancer == "유방암":
        diet += ["균형식 기본, 체중 증가 예방.", "호르몬치료 중 알코올 제한 권고."]
        tests += ["유방 영상 추적, 골밀도(장기 호르몬치료 시)"]
        notes += ["림프부종 예방: 해당 팔 채혈/혈압 피하기, 무거운 물건 주의."]
    elif cancer == "자궁/난소암":
        diet += ["철분·단백질 보충, 변비 예방 위한 수분/섬유소 조절.", "수술 후 연식→일반식 단계 전환."]
        tests += ["CA-125/HE4 등(의료진 판단)", "골반 영상 추적"]
        notes += ["복부 팽만/통증·질출혈 변화 시 연락."]
    elif cancer == "전립선/방광암":
        diet += ["수분 충분히, 카페인·탄산은 방광 자극 시 줄이기.", "요실금 있으면 소량씩 자주 마시기."]
        tests += ["PSA(전립선), 요검사/요배양(방광)", "영상 추적(의료진 계획)"]
        notes += ["혈뇨/배뇨통 악화 시 진료 필요."]
    elif cancer == "두경부암":
        diet += ["삼킴 곤란 시 **걸쭉하게** 농도 조절, 고열량 음료 활용.", "구강 통증 시 차갑고 부드러운 음식."]
        tests += ["구강·후두 내시경/영상", "영양평가(연하평가 포함)"]
        notes += ["구강위생 강화, 구내염 시 자극 음식 회피."]
    elif cancer == "뇌종양":
        diet += ["스테로이드 복용 시 염분·당 조절.", "구역 시 소량씩 자주·생강/레몬 등 사용 가능."]
        tests += ["뇌 MRI/CT", "전해질·혈당(스테로이드·항경련제 영향)"]
        notes += ["두통/구토/신경학적 변화 시 즉시 평가."]
    elif cancer == "혈액암(백혈병/림프종/다발골수종)":
        diet += ["감염 위험 시 **익힌 음식 위주**, 날음식(회/반숙 등) 회피.", "단백질·열량 보충 중요."]
        tests += ["CBC, 말초도말, LDH ± 골수검사(의료진 판단)"]
        notes += ["발열·점상출혈·멍 증가·호흡곤란 등 변화에 민감히 관찰."]

    return diet, tests, notes

# ============================
# Hem-Onc 카테고리/서브타입(암환자 탭)
# ============================
ONCO_CATEGORIES = {
    "혈액암": [
        "APL (급성 전골수구성 백혈병)",
        "ALL (급성 림프모구 백혈병)",
        "AML (급성 골수성 백혈병)",
        "CPL (만성 골수증식성 질환; PV/ET/MF)",
        "CLL (만성 림프구성 백혈병)",
        "CML (만성 골수성 백혈병)",
        "MM (다발골수종)",
    ],
    "림프종": [
        "DLBCL (미만성 거대 B세포 림프종)",
        "cHL (고전적 호지킨 림프종)",
        "FL (여포성 림프종)",
        "MCL (외투세포 림프종)",
        "MZL (변연부 림프종)",
        "PTCL (말초 T세포 림프종)",
    ],
    "육종": [
        "OS (골육종)", "EWS (유잉 육종)", "RMS (횡문근육종)",
        "LMS (평활근육종)", "UPS (미분화 다형성 육종)", "GIST (위장관 기질종양)",
    ],
    "고형암": [
        "NSCLC (비소세포 폐암)", "SCLC (소세포 폐암)",
        "유방암(HR+/HER2-)", "유방암(HER2+)", "유방암(삼중음성)",
        "대장암", "위암", "췌장암", "간세포암(HCC)", "담도암",
        "전립선암", "방광암", "신장암(RCC)", "두경부암(HNSCC)", "뇌종양(교모세포종 등)",
    ],
    "희귀암": [
        "NET (신경내분비종양)", "흉선종/흉선암", "생식세포종양(GCT)", "소아고형암(신경모세포종 등)",
    ],
}

# 서브타입별 대표 요법(예시/교육용)
ONCO_REGIMENS = {
    # 혈액암
    "APL (급성 전골수구성 백혈병)": ["ATRA + ATO", "± 안트라사이클린(이다루비신/다우노루비신)", "유지: ATRA ± 6-MP, MTX"],
    "ALL (급성 림프모구 백혈병)": ["스테로이드 + 비크리스틴 + L-아스파라기나제 ± 안트라사이클린", "CNS 예방(IT MTX 등)", "Ph+ : TKI(이마티닙/다사티닙/포나티닙)"],
    "AML (급성 골수성 백혈병)": ["7+3(시타라빈+안트라사이클린)", "FLT3 변이: 미도스타우린", "고령/비적합: HMA(아자/데시) ± 베네토클락스"],
    "CPL (만성 골수증식성 질환; PV/ET/MF)": ["PV: 정맥절개·ASA·하이드록시우레아", "ET: 하이드록시우레아/IFN, 저용량 ASA", "MF: 룩솔리티닙 등 JAK 억제제"],
    "CLL (만성 림프구성 백혈병)": ["BTK 억제제(이브루티닙/아칼라/자누브루)", "베네토클락스 + 오비누투주맙/리툭시맙"],
    "CML (만성 골수성 백혈병)": ["TKI(이마티닙/다사티닙/닐로티닙/보수티닙/포나티닙)"],
    "MM (다발골수종)": ["PI + IMiD + 스테로이드(예: 보르테조밉+레날리도마이드+덱사)", "자·동종 이식 고려"],

    # 림프종
    "DLBCL (미만성 거대 B세포 림프종)": ["R-CHOP", "고위험시 R-DA-EPOCH 등"],
    "cHL (고전적 호지킨 림프종)": ["ABVD", "브렌툭시맙 베도틴 병용/구제요법 상황별"],
    "FL (여포성 림프종)": ["R-벤다무스틴", "R-CHOP/R-CVP 상황별"],
    "MCL (외투세포 림프종)": ["R-CHOP 변형 + 시타라빈 기반", "BTK 억제제(재발)"],
    "MZL (변연부 림프종)": ["R-치료(방사선/화학) 상황별", "헬리코박터 제균(위형)"],
    "PTCL (말초 T세포 림프종)": ["CHOP 변형", "브렌툭시맙(표적 CD30) 대상군"],

    # 육종
    "OS (골육종)": ["MAP(HD-MTX+독소루비신+시스플라틴)", "수술 ± 방사선"],
    "EWS (유잉 육종)": ["VDC/IE 교대", "수술/방사선 병용"],
    "RMS (횡문근육종)": ["VAC/VAI 등", "국소치료 병합"],
    "LMS (평활근육종)": ["독소루비신 ± 이포스파마이드/다카바진", "파조파닙 등 표적"],
    "UPS (미분화 다형성 육종)": ["독소루비신 기반", "트라베크테딘/에리불린(상황별)"],
    "GIST (위장관 기질종양)": ["이마티닙(키트/PDGFRA 변이)", "수술 ± TKI 유지"],

    # 고형암
    "NSCLC (비소세포 폐암)": ["PD-L1/변이 따라 면역/표적", "EGFR: 오시머티닙 / ALK: 알렉티닙 등"],
    "SCLC (소세포 폐암)": ["백금+에토포사이드 ± 면역(아테졸리주맙 등)"],
    "유방암(HR+/HER2-)": ["AI/탐옥시펜 ± CDK4/6 억제제"],
    "유방암(HER2+)": ["트라스투주맙 ± 퍼투주맙 + 택산", "T-DM1/T-DXd(상황별)"],
    "유방암(삼중음성)": ["면역 ± 택산/플라틴", "BRCA 변이: PARP 억제제"],
    "대장암": ["FOLFOX/FOLFIRI ± 항EGFR/항VEGF", "MSI-H: 면역"],
    "위암": ["플라틴+플루오로피리미딘 ± 트라스투주맙(HER2+)", "면역 병용(상황별)"],
    "췌장암": ["FOLFIRINOX 또는 젬/나브-파클리"],
    "간세포암(HCC)": ["아테졸리주맙+베바시주맙", "렌바티닙/소라페닙"],
    "담도암": ["젬시타빈+시스플라틴 ± 면역", "FGFR2/IDH1 표적(변이시)"],
    "전립선암": ["ADT ± AR 억제제(아팔/엔잘/아비) | 도세탁셀(상황별)"],
    "방광암": ["백금 ± 면역 | ADC(엔포투맙 등)"],
    "신장암(RCC)": ["IO/IO 또는 IO+TKI"],
    "두경부암(HNSCC)": ["백금+5-FU ± 항EGFR/면역", "국소는 수술/방사선"],
    "뇌종양(교모세포종 등)": ["테모졸로마이드+방사선(스투프)", "재발: 베바시주맙 등"],

    # 희귀암
    "NET (신경내분비종양)": ["소마토스타틴 유사체", "PRRT(루테튬-177)"],
    "흉선종/흉선암": ["백금 기반", "표적/면역(상황별)"],
    "생식세포종양(GCT)": ["BEP(블레오/에토포사이드/시스플라틴)"],
    "소아고형암(신경모세포종 등)": ["리스크 기반 다약제+수술/방사선", "항GD2(상황별)"],
}

# ============================
# 특수검사 파일 연동
# ============================
def load_special_tests_from_file(category: str, subtype: str):
    """
    special_tests.py가 있으면 다음 우선순위로 탐색:
    1) get_special_tests(category, subtype)
    2) get_tests_for(category, subtype)
    3) SPECIAL_TESTS[(category, subtype)], SPECIAL_TESTS[subtype], SPECIAL_TESTS[category]
    못 찾으면 [].
    """
    try:
        import special_tests as stx
    except Exception:
        return []
    for fname in ("get_special_tests", "get_tests_for"):
        fn = getattr(stx, fname, None)
        if callable(fn):
            try:
                res = fn(category, subtype)
                if isinstance(res, (list, tuple)):
                    return list(res)
            except Exception:
                pass
    data = getattr(stx, "SPECIAL_TESTS", {})
    for key in ((category, subtype), subtype, category):
        if isinstance(data, dict) and key in data:
            val = data[key]
            if isinstance(val, (list, tuple)):
                return list(val)
    return []

# ============================
# 항암제 부작용 매핑(태그) & 상세
# ============================
ONCO_REGIMEN_TAGS = {
    # 혈액암
    "APL (급성 전골수구성 백혈병)": ["ATRA", "ATO", "Anthracycline"],
    "ALL (급성 림프모구 백혈병)": ["Steroid", "Vincristine", "L-Asparaginase", "Anthracycline", "IT-MTX"],
    "AML (급성 골수성 백혈병)": ["Cytarabine", "Anthracycline", "FLT3i"],
    "CPL (만성 골수증식성 질환; PV/ET/MF)": ["Hydroxyurea", "Aspirin", "JAKi"],
    "CLL (만성 림프구성 백혈병)": ["BTKi", "Venetoclax", "Anti-CD20"],
    "CML (만성 골수성 백혈병)": ["TKI-BCRABL"],
    "MM (다발골수종)": ["Bortezomib", "IMiD", "Steroid"],

    # 림프종
    "DLBCL (미만성 거대 B세포 림프종)": ["Anthracycline", "Cyclophosphamide", "Vincristine", "Steroid", "Anti-CD20"],
    "cHL (고전적 호지킨 림프종)": ["Anthracycline", "Bleomycin"],
    "FL (여포성 림프종)": ["Alkylator", "Anti-CD20"],
    "MCL (외투세포 림프종)": ["Anthracycline", "Cytarabine", "BTKi"],
    "MZL (변연부 림프종)": ["Anti-CD20"],
    "PTCL (말초 T세포 림프종)": ["Anthracycline"],

    # 육종
    "OS (골육종)": ["High-MTX", "Anthracycline", "Cisplatin"],
    "EWS (유잉 육종)": ["Cyclophosphamide", "Ifosfamide", "Doxorubicin", "Etoposide"],
    "RMS (횡문근육종)": ["Vincristine", "Actinomycin-D", "Cyclophosphamide/Ifosfamide"],
    "LMS (평활근육종)": ["Doxorubicin", "Dacarbazine", "Pazopanib"],
    "UPS (미분화 다형성 육종)": ["Doxorubicin", "Trabectedin", "Eribulin"],
    "GIST (위장관 기질종양)": ["Imatinib"],

    # 고형암
    "NSCLC (비소세포 폐암)": ["IO(PD-1/PD-L1)", "EGFR-TKI", "ALK-TKI", "Platinum", "Taxane", "Bevacizumab"],
    "SCLC (소세포 폐암)": ["Platinum", "Etoposide", "IO(PD-1/PD-L1)"],
    "유방암(HR+/HER2-)": ["AI/SERM", "CDK4/6i"],
    "유방암(HER2+)": ["Trastuzumab", "Pertuzumab", "Taxane", "ADC(HER2)"],
    "유방암(삼중음성)": ["IO(PD-1/PD-L1)", "Platinum", "Taxane"],
    "대장암": ["Fluoropyrimidine", "Irinotecan", "Oxaliplatin", "Anti-EGFR", "Anti-VEGF"],
    "위암": ["Platinum", "Fluoropyrimidine", "Trastuzumab", "IO(PD-1/PD-L1)"],
    "췌장암": ["Irinotecan", "Oxaliplatin", "Fluoropyrimidine", "Gemcitabine", "Taxane"],
    "간세포암(HCC)": ["IO(PD-1/PD-L1)", "Bevacizumab", "TKI-VEGFR"],
    "담도암": ["Gemcitabine", "Platinum", "IO(PD-1/PD-L1)", "FGFR/IDH1i"],
    "전립선암": ["ADT", "ARi", "Docetaxel"],
    "방광암": ["Platinum", "IO(PD-1/PD-L1)", "ADC(Nectin-4)"],
    "신장암(RCC)": ["IO+IO", "IO+TKI-VEGFR"],
    "두경부암(HNSCC)": ["Platinum", "5-FU", "Anti-EGFR", "IO(PD-1/PD-L1)"],
    "뇌종양(교모세포종 등)": ["Temozolomide", "Bevacizumab"],

    # 희귀암
    "NET (신경내분비종양)": ["SSA", "PRRT"],
    "흉선종/흉선암": ["Platinum"],
    "생식세포종양(GCT)": ["BEP(블레오/에토포사이드/시스플라틴)"],
    "소아고형암(신경모세포종 등)": ["다약제(위험도기반)"],
}

CHEMO_AE = {
    "ATRA": {"common":["두통/피부건조","WBC 상승"],"monitor":["DS 징후: 발열·호흡곤란·부종·저혈압"],"red":["DS 의심 증상","WBC 급증+호흡곤란","흉통/실신"]},
    "ATO": {"common":["피로/구역","전해질 이상"],"monitor":["QT 연장, K/Mg 교정","ECG 추적"],"red":["실신/심계항진","탈수 동반 구토 지속"]},
    "Anthracycline":{"common":["탈모","오심","구강염"],"monitor":["누적 용량·심초음파"],"red":["호흡곤란/부종(심부전)","흉통/부정맥"]},
    "Cytarabine":{"common":["골수억제","발열","결막염"],"monitor":["고용량 시 소뇌 실조","TLS 대비"],"red":["실조/의식변화 새로 발생","고열+오한"]},
    "L-Asparaginase":{"common":["고혈당","고지혈증"],"monitor":["췌장염·혈전/출혈"],"red":["심한 복통(췌장염)","편측 부종·통증(혈전)"]},
    "Steroid":{"common":["불면/식욕↑","혈당↑","위장불편"],"monitor":["혈당/혈압/감염","위장보호"],"red":["흑변/토혈","정신증상/심한 기분변화"]},
    "Vincristine":{"common":["말초신경병증","변비"],"monitor":["장폐색 징후"],"red":["배변/배뇨 정지·복부팽만","심한 저림·근력저하"]},
    "IT-MTX":{"common":["두통","구역"],"monitor":["신경학적 변화"],"red":["심한 두통/경련/의식저하"]},
    "FLT3i":{"common":["피로","발진"],"monitor":["QT·간기능"],"red":["심계항진/실신","황달/진한 소변"]},
    "Hydroxyurea":{"common":["피부건조/색소","골수억제"],"monitor":["CBC 추적"],"red":["출혈성 반점/코피 지속"]},
    "Aspirin":{"common":["위장불편"],"monitor":["출혈·멍"],"red":["흑변/토혈","코피 지속"]},
    "JAKi":{"common":["빈혈/혈소판감소","감염 위험"],"monitor":["CBC/감염"],"red":["고열/오한 지속","출혈"]},
    "BTKi":{"common":["설사","피멍","고혈압"],"monitor":["A-fib/출혈 위험·상호작용"],"red":["심계항진/호흡곤란","흑변/코피지속"]},
    "Venetoclax":{"common":["호중구감소","오심"],"monitor":["TLS(시작·증량)","CBC/Cr/K/P/UA"],"red":["소변감소·근경련","고열 지속"]},
    "Anti-CD20":{"common":["주입반응","감염"],"monitor":["HBV 재활성","전처치"],"red":["호흡곤란/저혈압","황달(재활성)"]},
    "Bortezomib":{"common":["말초신경병증","설사/변비"],"monitor":["헤르페스 예방","신경독성"],"red":["심한 저림/근력저하","수포성 발진+고열"]},
    "IMiD":{"common":["발진","졸림","변비"],"monitor":["혈전 예방","임신 금기"],"red":["다리 부종/통증(혈전)","호흡곤란/흉통"]},
    "Platinum":{"common":["구역/구토","신독성","말초신경병증"],"monitor":["수액·Cr/전해질","청력"],"red":["소변감소/부종","심한 저림/청력저하"]},
    "Taxane":{"common":["탈모","관절통","말초신경병증"],"monitor":["과민반응 전처치","신경증상"],"red":["호흡곤란/저혈압","타는듯 통증/저림"]},
    "Bevacizumab":{"common":["고혈압","단백뇨"],"monitor":["혈압/소변단백","상처치유 지연"],"red":["심한 두통/시야장애","복통·혈변(천공/출혈)"]},
    "EGFR-TKI":{"common":["여드름양 발진","설사"],"monitor":["피부관리/설사 조절"],"red":["호흡곤란/기침 악화(ILD)"]},
    "ALK-TKI":{"common":["피로","간수치 상승"],"monitor":["간기능/심전도"],"red":["호흡곤란(ILD)","심계항진"]},
    "IO(PD-1/PD-L1)":{"common":["피로/관절통","경미 발진/설사"],"monitor":["면역이상반응(irAE)"],"red":["숨가쁨/기침(폐렴)","지속 설사/혈변","심한 피로·황달","두근거림/저혈압"]},
    "Anti-EGFR":{"common":["피부발진","저Mg"],"monitor":["피부관리·Mg추적"],"red":["감염성 피부병변","근경련/부정맥"]},
    "Anti-VEGF":{"common":["고혈압","단백뇨"],"monitor":["혈압/소변","출혈·혈전"],"red":["심한 두통/시야장애","흑변/혈변"]},
    "Irinotecan":{"common":["설사(급성/지연)","골수억제"],"monitor":["급성: 아트로핀","지연: 로페라미드"],"red":["탈수 동반 설사 지속","고열"]},
    "Oxaliplatin":{"common":["한랭유발 신경병증","말초저림"],"monitor":["추위 회피"],"red":["구강/손 주위 경련감·호흡곤란(드뭄)"]},
    "Fluoropyrimidine":{"common":["구내염","설사","손발증후군"],"monitor":["DPD 결핍 주의"],"red":["중증 설사/탈수","가슴통증/호흡곤란"]},
    "Temozolomide":{"common":["오심","골수억제"],"monitor":["CBC, PCP 예방 고려"],"red":["고열/호흡곤란"]},
    "SSA":{"common":["복통/변비","혈당 변동"],"monitor":["담석","혈당"],"red":["황달/담낭통증"]},
    "PRRT":{"common":["오심","피로"],"monitor":["골수억제/신독성"],"red":["지속 고열/출혈","소변 감소"]},
    "TKI-BCRABL":{"common":["부종/근육통","피로"],"monitor":["간기능·QT"],"red":["흉통/호흡곤란","실신/부정맥"]},
    "TKI-VEGFR":{"common":["고혈압","구내염/손발피로"],"monitor":["혈압/단백뇨"],"red":["심한 두통·시야장애","흑변/코피 지속"]},
    "CDK4/6i":{"common":["호중구감소","피로","구내염"],"monitor":["CBC/간수치"],"red":["고열·오한"]},
    "AI/SERM":{"common":["관절통/홍조","골밀도 저하(AI)"],"monitor":["골밀도·지질"],"red":["다리 통증/부종(혈전)"]},
    "ARi":{"common":["피로","고혈압"],"monitor":["혈압·간수치"],"red":["흉통/호흡곤란"]},
    "ADC(HER2)":{"common":["피로/오심","혈소판감소(T-DM1)"],"monitor":["간기능/호흡증상"],"red":["새로운 숨가쁨/기침(ILD)"]},
    "Gemcitabine":{"common":["피로","빈혈/혈소판↓"],"monitor":["CBC/간·신장"],"red":["고열/출혈"]},
    "Docetaxel":{"common":["무력감","부종","말초신경병증"],"monitor":["감염/체액저류"],"red":["고열/호흡곤란/흉통"]},
}

def render_chemo_ae(category: str, subtype: str):
    st.markdown("### ⚠️ 예상되는 부작용 & 모니터링")
    tags = ONCO_REGIMEN_TAGS.get(subtype, [])
    if not tags:
        st.caption("이 서브타입에 매핑된 약제 태그가 아직 없어요.")
        return
    for tg in tags:
        ae = CHEMO_AE.get(tg)
        with st.expander(f"• {tg}", expanded=False):
            if not ae:
                st.write("- (준비 중)")
                continue
            if ae.get("common"):
                st.markdown("**자주 볼 수 있는 증상**")
                for x in ae["common"]: st.write("- " + x)
            if ae.get("monitor"):
                st.markdown("**모니터링/예방 포인트**")
                for x in ae["monitor"]: st.write("- " + x)
            if ae.get("red"):
                st.markdown("**바로 진료/연락이 좋아요**")
                for x in ae["red"]: st.write("- :red[" + x + "]")
    st.caption(":gray[※ 실제 약제·용량·병용, 환자 상태에 따라 부작용 양상은 달라질 수 있어요. 주치의 판단이 항상 우선입니다.]")

# ============================
# 소아 보호자 가이드(간단)
# ============================
def _peds_homecare_details_soft(*, score, stool, fever, cough, eye,
                                oliguria, ear_pain, rash, hives, abd_pain, migraine, hfmd):
    st.markdown("### 보호자 상세 가이드")

    def tip_block(title, items):
        if st.session_state.get(wkey("peds_simple"), True):
            st.write("• " + title.replace(" — 집에서", ""))
        else:
            st.markdown(f"**{title}**")
            for it in items: st.write("- " + it)

    tip_block("🟡 오늘 집에서 살펴보면 좋아요", [
        "미온수나 ORS를 소량씩 자주 드세요.", "실내는 편안한 복장·적정 가습/환기.",
        "해열제 간격: APAP ≥4h, IBU ≥6h."
    ])
    if score.get("장염 의심", 0) or stool in ["3~4회", "5~6회", "7회 이상"]:
        tip_block("💧 장염/설사 의심 — 집에서", [
            "ORS/미온수 소량씩 자주, 구토 시 10–15분 쉬고 재시도.",
            "기름지거나 자극적인 음식, 유제품은 잠시 쉬기.",
            "죽·바나나·사과퓨레·토스트 등 부드러운 음식부터.",
        ])
    if score.get("결막염 의심", 0) or eye in ["노랑-농성", "양쪽"]:
        tip_block("👁️ 결막염 — 집에서", [
            "손 씻기·개인수건 사용, 생리식염수로 부드럽게 닦기.",
            "냉찜질 짧게, 안약은 의료진 상의 후.",
        ])
    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        tip_block("🌡️ 발열 38℃ 전후 — 집에서", [
            "실내 **25–26℃** 권장, 미지근한 물수건으로 닦기(찬물/알코올 X).",
            "**미온수·ORS를 조금씩 자주** 마시게 하기.",
            "손발 따뜻=열이 잡히는 중일 수 있음 / 차가움=30–60분 후 재체크.",
        ])
    if score.get("상기도/독감 계열", 0) or cough in ["조금", "보통", "심함"]:
        tip_block("🤧 상기도/독감 — 집에서", [
            "미온수·휴식, 콧물 많으면 생리식염수 세척 후 안전 흡인.",
            "욕실 스팀은 짧게만.",
        ])
    if score.get("탈수/신장 문제", 0) or oliguria:
        tip_block("🚰 탈수 — 집에서", ["입술·혀 마름·눈물 감소·소변량 확인", "6–8h 무뇨 시 진료 요함."])
    if ear_pain: tip_block("👂 중이염 의심 — 집에서", ["해열·진통제 간격 지키기", "코막힘엔 식염수."])
    if rash or hives: tip_block("🌿 피부발진/알레르기 — 집에서", ["미온 샤워·보습", "호흡곤란/입술부종은 즉시 진료."])
    if abd_pain: tip_block("🤢 복통 — 집에서", ["소화 쉬운 음식", "혈변·담즙성 구토·고열 동반 시 바로 진료."])
    if migraine: tip_block("🧠 편두통 — 집에서", ["조용·어두운 환경", "자극 줄이기."])
    if hfmd: tip_block("🖐️ 수족구 — 집에서", ["차갑고 부드러운 음식", "수분 충분히."])
    st.markdown("---")
    tip_block("🔴 바로 진료/연락이 좋아요", [
        "38.5℃ 이상 지속/39℃ 이상, 지속 구토/소변 급감, 축 늘어짐/의식 흐림, 호흡곤란, 농성 양쪽 눈 분비물, 처짐/경련 병력 동반."
    ])

def render_caregiver_notes_peds(stool, fever, persistent_vomit, oliguria, cough, nasal, eye,
                                abd_pain, ear_pain, rash, hives, migraine, hfmd):
    score = {
        "장염 의심": 40 if stool in ["3~4회", "5~6회", "7회 이상"] else 0,
        "결막염 의심": 30 if eye in ["노랑-농성", "양쪽"] else 0,
        "상기도/독감 계열": 20 if (cough in ["조금", "보통", "심함"] or fever in ["38~38.5","38.5~39","39 이상"]) else 0,
        "탈수/신장 문제": 20 if oliguria else 0,
    }
    ordered = [f"{k}: {v}" for k, v in sorted(score.items(), key=lambda x: x[1], reverse=True) if v > 0]
    if ordered: st.write("• " + " / ".join(ordered))
    _peds_homecare_details_soft(score=score, stool=stool, fever=fever, cough=cough, eye=eye,
                                oliguria=oliguria, ear_pain=ear_pain, rash=rash, hives=hives,
                                abd_pain=abd_pain, migraine=migraine, hfmd=hfmd)

# ============================
# ONCO — 피수치(요청 16항목 고정)
# ============================
def render_onco_labs(*, temp, on_dyspnea, on_chest_pain, on_confusion, on_bleeding, on_oliguria):
    st.markdown("---")
    st.subheader("🧪 피수치 입력/해석 (요청 항목만)")

    def num_row(label, key, unit="", minv=None, maxv=None, step=0.1, default=None):
        colc, colv, colu = st.columns([0.95, 1.05, 0.7])
        with colc:
            use = st.checkbox(label, key=wkey(f"lab_use_{key}"))
        val = None
        with colv:
            if use:
                init_val = default if default is not None else minv
                val = st.number_input("", key=wkey(f"lab_val_{key}"),
                                      min_value=minv, max_value=maxv,
                                      value=init_val, step=step)
        with colu:
            st.write(unit)
        return use, val

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        u_wbc, v_wbc = num_row("WBC", "wbc", "10⁹/L", 0.0, 200.0, 0.1, 6.0)
        u_hp,  v_hp  = num_row("Hb(HP)", "hp", "g/dL", 0.0, 20.0, 0.1, 12.0)
        u_plt, v_plt = num_row("PLT", "plt", "/μL", 0, 500000, 1000, 150000)
        u_anc, v_anc = num_row("ANC", "anc", "/μL", 0, 20000, 50, 1500)
    with c2:
        u_na,  v_na  = num_row("Na", "na", "mEq/L", 100.0, 170.0, 0.5, 140.0)
        u_k,   v_k   = num_row("K", "k", "mEq/L", 1.0, 9.0, 0.1, 4.0)
        u_ca,  v_ca  = num_row("Ca", "ca", "mg/dL", 5.0, 15.0, 0.1, 9.2)
        u_p,   v_p   = num_row("P(인)", "p", "mg/dL", 0.5, 10.0, 0.1, 3.5)
    with c3:
        u_alb, v_alb = num_row("Albumin", "alb", "g/dL", 1.0, 6.0, 0.1, 4.0)
        u_tp,  v_tp  = num_row("Total Protein", "tp", "g/dL", 3.0, 10.0, 0.1, 7.0)
        u_glu, v_glu = num_row("Glucose", "glu", "mg/dL", 20.0, 600.0, 1.0, 100.0)
        u_crp, v_crp = num_row("CRP", "crp", "mg/L", 0.0, 1000.0, 0.5, 0.5)
    with c4:
        u_ast, v_ast = num_row("AST", "ast", "U/L", 0.0, 1000.0, 1.0, 25.0)
        u_alt, v_alt = num_row("ALT", "alt", "U/L", 0.0, 1000.0, 1.0, 25.0)
        u_tb,  v_tb  = num_row("Total Bilirubin", "tb", "mg/dL", 0.0, 30.0, 0.1, 0.8)
        u_cr,  v_cr  = num_row("Creatinine", "cr", "mg/dL", 0.1, 10.0, 0.1, 0.9)
    c5, c6, _ = st.columns(3)
    with c5:
        u_bun, v_bun = num_row("BUN", "bun", "mg/dL", 1.0, 200.0, 0.5, 14.0)
    with c6:
        u_ua,  v_ua  = num_row("Uric Acid", "ua", "mg/dL", 0.5, 20.0, 0.1, 5.0)

    # ---- 해석 요약
    flags = []
    def used(x): return x is not None

    # 감염/조혈
    if u_anc and used(v_anc):
        if v_anc < 500:   flags.append("ANC<500 (감염 위험↑)")
        elif v_anc < 1000: flags.append("ANC 500–999")
    if u_wbc and used(v_wbc):
        if v_wbc < 3.0: flags.append("WBC 낮음")
        elif v_wbc > 11.0: flags.append("WBC 높음")
    if u_hp and used(v_hp):
        if v_hp < 7.0:   flags.append("중증 빈혈 가능")
        elif v_hp < 8.0: flags.append("빈혈 주의")
    if u_plt and used(v_plt):
        if v_plt < 20000:  flags.append("혈소판<20k (출혈 위험)")
        elif v_plt < 50000: flags.append("혈소판 20–50k")

    # 간/담도
    if u_ast and used(v_ast) and v_ast >= 100: flags.append("AST 상승")
    if u_alt and used(v_alt) and v_alt >= 100: flags.append("ALT 상승")
    if u_tb  and used(v_tb)  and v_tb  >= 2.0: flags.append("총빌리루빈 상승")

    # 염증
    if u_crp and used(v_crp) and v_crp >= 10: flags.append("CRP≥10 (염증↑)")

    # 신장/전해질
    if u_cr and used(v_cr) and v_cr >= 1.5: flags.append("Cr 상승(신장)")
    if u_bun and used(v_bun) and v_bun >= 20: flags.append("BUN 상승")
    if u_na and used(v_na) and (v_na < 130 or v_na > 150): flags.append("나트륨 이상")
    if u_k  and used(v_k)  and (v_k  < 3.0 or v_k  >= 5.5): flags.append("칼륨 이상")
    if u_ca and used(v_ca) and (v_ca < 8.0 or v_ca > 11.5): flags.append("칼슘 이상")
    if u_p  and used(v_p)  and (v_p  < 2.0 or v_p  > 5.5):  flags.append("인(P) 이상")

    # 영양/대사
    if u_alb and used(v_alb) and v_alb < 3.0: flags.append("알부민 저하")
    if u_tp  and used(v_tp)  and (v_tp  < 5.5 or v_tp > 8.5): flags.append("총단백 이상")
    if u_glu and used(v_glu) and v_glu >= 200: flags.append("고혈당")
    if u_ua  and used(v_ua)  and v_ua >= 8.0: flags.append("요산 상승")

    if flags:
        st.warning("피수치 요약(입력한 항목 기준): " + " / ".join(flags))
    else:
        st.info("입력하신 항목 기준으로 즉시 위험 신호는 보이지 않아요. (미입력 항목은 평가 제외)")

    # ---- 자동 특수검사 제안
    st.markdown("—")
    st.subheader("특수 검사 가이드(자동 제안)")
    tips = []
    fever_high = (temp == "≥38.5℃")
    if fever_high or (u_crp and used(v_crp) and v_crp >= 10):
        tips += ["혈액배양(2세트 권장)·소변배양", "흉부 X-ray(호흡기 증상 시)"]
    if on_dyspnea or on_chest_pain:
        tips += ["ECG", "흉부 X-ray ± CT(의료진 판단)", "SpO₂/혈액가스"]
    if on_confusion:
        tips += ["혈당/전해질(Ca/Na/K) 재평가"]
    if (u_na and used(v_na) and (v_na < 130 or v_na > 150)) or (u_k and used(v_k) and (v_k < 3.0 or v_k >= 5.5)):
        tips += ["전해질 교정 계획 수립 및 재측정"]
    if on_oliguria or (u_bun and used(v_bun) and v_bun >= 20) or (u_cr and used(v_cr) and v_cr >= 1.5):
        tips += ["요검사/요배양", "신장초음파 ± 수액반응 평가"]
    if (u_ast and used(v_ast) and v_ast >= 100) or (u_alt and used(v_alt) and v_alt >= 100) or (u_tb and used(v_tb) and v_tb >= 2.0):
        tips += ["간기능 평가 보강(약물 검토, 바이러스 간염 표지자 등)"]

    if tips:
        st.markdown("**권장 검토 항목(의료진 판단 하에):**")
        for t in dict.fromkeys(tips): st.write("- " + t)
    else:
        st.write("현재 입력 기준으로 꼭 필요한 특수검사 제안은 없어요. 증상 변화에 따라 달라질 수 있어요.")

# ============================
# Tabs
# ============================
tab_labels = ["HOME", "소아", "암 분류", "암환자"]
t_home, t_peds, t_type, t_onco = st.tabs(tab_labels)

# ---- HOME ----
with t_home:
    st.subheader("응급도 가중치 (편집 + 프리셋)")
    left, mid, right = st.columns([1.5, 1, 1])
    with left:
        preset_name = st.selectbox("프리셋 선택", list(PRESETS.keys()), index=0, key=wkey("preset_sel"))
    with mid:
        if st.button("프리셋 적용", key=wkey("preset_apply")):
            set_weights(PRESETS.get(preset_name, {}))
            st.success("프리셋을 적용했어요.")
    with right:
        if st.button("기본값으로 초기화", key=wkey("preset_reset")):
            set_weights({})
            st.info("기본값으로 초기화했습니다.")

    with st.expander("현재 가중치 보기(읽기 전용)", expanded=False):
        W = get_weights()
        try: st.json({k: float(W.get(k, 1.0)) for k in sorted(W.keys())})
        except Exception: st.write(W)

    st.divider()
    if st.button("👶 소아 증상 → 바로 안내", use_container_width=True):
        st.components.v1.html("""
        <script>
          const tabs = Array.from(parent.document.querySelectorAll('button[role="tab"]'));
          const target = tabs.find(b => /소아/.test(b.textContent));
          if (target){ target.click(); }
        </script>
        """, height=0)

# ---- PEDS ----
with t_peds:
    st.subheader("소아 보호자 가이드 (증상 입력 → 자동 안내)")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: nasal = st.selectbox("콧물", ["해당 없음","맑음","끈적"], index=0, key=wkey("p_nasal"))
    with c2: cough = st.selectbox("기침", ["없음","조금","보통","심함"], index=0, key=wkey("p_cough"))
    with c3: stool = st.selectbox("설사", ["해당 없음","1~2회","3~4회","5~6회","7회 이상"], index=0, key=wkey("p_stool"))
    with c4: fever = st.selectbox("발열", ["없음","37~37.5 (미열)","38~38.5","38.5~39","39 이상"], index=0, key=wkey("p_fever"))
    with c5: eye   = st.selectbox("눈꼽/결막", ["해당 없음","맑음","양쪽","노랑-농성"], index=0, key=wkey("p_eye"))

    r1, r2, r3 = st.columns(3)
    with r1:
        abd_pain = st.checkbox("복통/압통", key=wkey("p_abd_pain"))
        ear_pain = st.checkbox("귀 통증/만지면 울음", key=wkey("p_ear_pain"))
        rash = st.checkbox("피부 발진", key=wkey("p_rash"))
    with r2:
        hives = st.checkbox("두드러기", key=wkey("p_hives"))
        migraine = st.checkbox("편두통 의심", key=wkey("p_migraine"))
        hfmd = st.checkbox("수족구 의심", key=wkey("p_hfmd"))
    with r3:
        persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("p_pvomit"))
        oliguria = st.checkbox("소변량 급감", key=wkey("p_oliguria"))

    st.toggle("간단보기", value=True, key=wkey("peds_simple"))
    render_caregiver_notes_peds(stool, fever, persistent_vomit, oliguria, cough, nasal, eye,
                                abd_pain, ear_pain, rash, hives, migraine, hfmd)

# ---- CANCER TYPE (분류/식사/특수검사) ----
with t_type:
    st.subheader("암 종류별 안내 (식사 가이드 + 특수검사 제안)")
    pick = st.selectbox("암 종류 선택", CANCER_TYPES, key=wkey("ctype"))
    diet, tests, notes = get_onco_type_guides(pick)
    st.markdown(f"### 🍽️ {pick} — 식사 가이드");  [st.write("- " + d) for d in diet]
    st.markdown(f"### 🔬 {pick} — 특수검사/추적 제안"); [st.write("- " + t) for t in tests]
    st.markdown("### 📝 주의/메모"); [st.write("- " + n) for n in notes]

    st.markdown("---")
    if st.button("암환자 상태 입력/진료 기준 보러가기", use_container_width=True, key=wkey("go_onco")):
        st.components.v1.html("""
        <script>
          const tabs = Array.from(parent.document.querySelectorAll('button[role="tab"]'));
          const target = tabs.find(b => /암환자/.test(b.textContent));
          if (target){ target.click(); }
        </script>
        """, height=0)

# ---- ONCO (암환자) ----
with t_onco:
    st.subheader("암환자 빠른 안내 (분류/치료요약 + 부작용 + 피수치/특수검사)")
    st.caption("응급이 의심되면 즉시 119/응급실을 이용하세요.")

    # 1) 카테고리/서브타입 선택
    cat = st.selectbox("암 카테고리", list(ONCO_CATEGORIES.keys()), index=0, key=wkey("on_cat"))
    sub = st.selectbox("세부분류(서브타입)", ONCO_CATEGORIES[cat], index=0, key=wkey("on_sub"))

    # 2) 대표 치료(예시)
    st.markdown(f"### 💊 {sub} — 대표 치료(예시, 주치의 판단 우선)")
    regs = ONCO_REGIMENS.get(sub, [])
    st.write("- " + "\n- ".join(regs) if regs else "- (정보 준비 중)")

    # 3) 항암제 부작용/모니터링
    render_chemo_ae(category=cat, subtype=sub)

    # 4) 상태 입력(간단 점수/태그)
    st.markdown("---"); st.markdown("### 상태 입력")
    c1, c2, c3, c4 = st.columns(4)
    with c1: on_temp = st.selectbox("체온", ["<38.0℃","38.0~38.4℃","≥38.5℃"], index=0, key=wkey("on_temp"))
    with c2: on_anc = st.number_input("ANC(호중구) /μL", 0, 10000, 1500, 100, key=wkey("on_anc"))
    with c3: on_plt = st.number_input("혈소판 /μL", 0, 500000, 150000, 1000, key=wkey("on_plt"))
    with c4: on_hb  = st.number_input("Hb (g/dL)", 0.0, 20.0, 12.0, 0.1, key=wkey("on_hb"))

    s1, s2, s3 = st.columns(3)
    with s1:
        on_chemo = st.checkbox("최근 4주 이내 항암제 치료", key=wkey("on_chemo"))
        on_cough  = st.checkbox("기침/가래", key=wkey("on_cough"))
    with s2:
        on_bleeding = st.checkbox("출혈(잇몸/코피/멍 증가)", key=wkey("on_bleed"))
        on_dyspnea  = st.checkbox("호흡곤란/숨참", key=wkey("on_dysp"))
        on_chest_pain = st.checkbox("가슴 통증", key=wkey("on_cp"))
    with s3:
        on_confusion = st.checkbox("의식저하/혼돈", key=wkey("on_conf"))
        on_pvomit    = st.checkbox("지속 구토(>6시간)", key=wkey("on_vomit"))
        on_oliguria  = st.checkbox("소변량 급감", key=wkey("on_olig"))

    nf = (on_temp != "<38.0℃") and (on_anc < 500)
    high_bleed = on_plt < 20000 or on_bleeding
    severe_anemia = on_hb < 7.0
    high_urgency = any([on_dyspnea, on_chest_pain, on_confusion]) or on_temp == "≥38.5℃" or nf

    W = get_weights()
    score = 0.0
    score += float(W.get("w_temp_ge_38_5", 1.0)) if on_temp == "≥38.5℃" else (float(W.get("w_temp_38_0_38_4", 1.0)) if on_temp == "38.0~38.4℃" else 0.0)
    score += float(W.get("w_anc_lt500", 1.0)) if on_anc < 500 else (float(W.get("w_anc_500_999", 1.0)) if on_anc < 1000 else 0.0)
    score += float(W.get("w_plt_lt20k", 1.0)) if on_plt < 20000 else 0.0
    score += float(W.get("w_hb_lt7", 1.0)) if on_hb < 7.0 else 0.0
    score += float(W.get("w_dyspnea", 1.0)) if on_dyspnea else 0.0
    score += float(W.get("w_chest_pain", 1.0)) if on_chest_pain else 0.0
    score += float(W.get("w_confusion", 1.0)) if on_confusion else 0.0
    score += float(W.get("w_persistent_vomit", 1.0)) if on_pvomit else 0.0
    score += float(W.get("w_oliguria", 1.0)) if on_oliguria else 0.0

    tags = []
    if nf: tags.append("호중구감소성 발열 의심")
    if high_bleed: tags.append("출혈 위험")
    if severe_anemia: tags.append("중증 빈혈 의심")
    st.write("• 상태 요약: " + (" / ".join(tags) if tags else "특이 위험 태그 없음") + f"  | 점수: {score:.1f}")

    st.markdown("### 집에서 살펴볼 점")
    def li(t): st.write("- " + t)
    if on_temp in ["38.0~38.4℃", "≥38.5℃"]:
        li("체온 20–30분 간격 확인, 미지근한 물수건으로 닦기(찬물/알코올 X).")
        li("수분을 조금씩 자주 섭취. 혈소판 낮으면 NSAIDs 피하기.")
    if on_anc < 1000 and on_chemo:
        li("감염 취약 시기: 마스크/손 위생, 사람 많은 곳 피하기.")
    if on_plt < 50000:
        li("양치/면도는 부드럽게, 코 풀 땐 한쪽씩. 멍/붉은 점 증가 시 연락.")
    if on_hb < 8.0:
        li("격한 활동은 잠시 줄이고 충분히 휴식.")

    st.markdown("---")
    st.markdown("### 바로 진료/연락이 좋아요")
    li(":red[체온 38.5℃ 이상 또는 오한/떨림 지속]")
    li(":red[ANC<500 + 발열(호중구감소성 발열 의심)]")
    li(":red[호흡곤란, 가슴 통증, 의식저하/혼돈]")
    li(":red[혈변/검은변, 멈추지 않는 코피, 멍·붉은 점 급증]")
    li(":red[6–8시간 무뇨 또는 수분 섭취 불가한 구토/설사]")

    if high_urgency:
        st.info("지금은 담당 병원에 즉시 연락하는 것이 좋아요. 필요 시 구급을 이용해 주세요.")

    # 5) 피수치/자동 제안
    with st.expander("🧪 피수치(체크한 항목만 평가) · 자동 특수검사 제안", expanded=False):
        render_onco_labs(temp=on_temp, on_dyspnea=on_dyspnea, on_chest_pain=on_chest_pain,
                         on_confusion=on_confusion, on_bleeding=on_bleeding, on_oliguria=on_oliguria)

    # 6) 특수검사 — 파일 연동 UI
    with st.expander("🔬 특수검사(파일 연동) — 체크리스트/메모", expanded=False):
        file_tests = load_special_tests_from_file(cat, sub)
        if file_tests:
            st.markdown("**권장 특수검사(파일 연동):**")
            for t in file_tests: st.write("- " + str(t))
        else:
            st.caption("special_tests.py에서 해당 항목을 찾지 못했습니다. 자동 제안을 참고하세요.")

        st.markdown("---"); st.markdown("**체크리스트(실시 항목 체크)**")
        base_items = [
            "혈액배양 2세트", "요배양/요검사", "흉부 X-ray", "ECG",
            "혈액가스/젖산", "흉부 CT", "복부 CT", "신장초음파",
            "응고계(PT/INR, aPTT, Fib)", "종양표지자", "심초음파", "기타"
        ] + file_tests
        seen, checks = set(), []
        cols = st.columns(3)
        for i, name in enumerate(base_items):
            if name in seen: continue
            seen.add(name)
            with cols[i % 3]:
                checks.append((name, st.checkbox(name, key=wkey(f"sp_{i}_{hash(name)}"))))
        memo = st.text_area("메모(결과·판단·계획)", height=140, key=wkey("sp_memo"))
        selected = [n for n, f in checks if f]
        summary = f"[{cat}] {sub}\n특수검사 체크리스트\n" + \
                  ("- " + "\n- ".join(selected) if selected else "- (선택 없음)") + \
                  "\n\n메모\n" + (memo or "(내용 없음)")
        st.download_button("요약 .txt 저장", summary, file_name="onco_specials_summary.txt",
                           mime="text/plain", use_container_width=True)

