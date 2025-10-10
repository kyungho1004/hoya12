# -*- coding: utf-8 -*-
import streamlit as st

# ============================
# Basic Setup
# ============================
st.set_page_config(page_title="피수치 · 보호자 가이드", layout="wide")
st.info("이 앱의 안내는 참고용입니다. 응급이 의심되면 지체하지 말고 119 또는 가까운 응급실을 이용해 주세요.")

# Floating feedback button (우측 하단)
st.markdown("""
<style>
.fb-float {position: fixed; right: 16px; bottom: 16px; z-index: 99999;}
.fb-btn {background:#2563eb;color:#fff;padding:12px 14px;border-radius:999px;
         box-shadow:0 8px 24px rgba(37,99,235,.35);font-weight:600;display:inline-flex;
         align-items:center;gap:8px;text-decoration:none}
.fb-btn:hover{background:#1e40af}
</style>
<div class="fb-float">
  <a class="fb-btn" href="mailto:lee729812@gmail.com?subject=%5B%ED%94%BC%EC%88%98%EC%B9%98%20%EC%95%B1%5D%20%EC%9D%98%EA%B2%AC%20%EB%B0%8F%20%EC%98%A4%EB%A5%98%20%EC%A0%9C%EB%B3%B4"
     target="_blank">✉️ 의견 보내기</a>
</div>
""", unsafe_allow_html=True)

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

# 프리셋(필요에 맞게 확장 가능)
PRESETS = {
    "기본(Default)": {},
    "보수적(안전 우선)": {
        "w_temp_ge_38_5": 1.2, "w_dyspnea": 1.2, "w_confusion": 1.2, "w_oliguria": 1.2, "w_persistent_vomit": 1.2
    },
}

# ============================
# 암 종류(상단 분류 탭에서 사용)
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
# Hem-Onc 카테고리/서브타입(ONCO 탭에서 사용)
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
        "OS (골육종)",
        "EWS (유잉 육종)",
        "RMS (횡문근육종)",
        "LMS (평활근육종)",
        "UPS (미분화 다형성 육종)",
        "GIST (위장관 기질종양)",
    ],
    "고형암": [
        "NSCLC (비소세포 폐암)",
        "SCLC (소세포 폐암)",
        "유방암(HR+/HER2-)",
        "유방암(HER2+)",
        "유방암(삼중음성)",
        "대장암",
        "위암",
        "췌장암",
        "간세포암(HCC)",
        "담도암",
        "전립선암",
        "방광암",
        "신장암(RCC)",
        "두경부암(HNSCC)",
        "뇌종양(교모세포종 등)",
    ],
    "희귀암": [
        "NET (신경내분비종양)",
        "흉선종/흉선암",
        "생식세포종양(GCT)",
        "소아고형암(신경모세포종 등)",
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
    "MM (다발골수종)": ["PI + IMiD + 스테로이드(예: 보르테조밉+레날리도마이드+덱사)", "자체·동종 조혈모세포이식 고려"],

    # 림프종
    "DLBCL (미만성 거대 B세포 림프종)": ["R-CHOP", "고위험시 R-DA-EPOCH 등"],
    "cHL (고전적 호지킨 림프종)": ["ABVD", "브렌툭시맙 베도틴 병용/구제요법 상황별"],
    "FL (여포성 림프종)": ["R-벤다무스틴", "R-CHOP/R-CVP 상황별"],
    "MCL (외투세포 림프종)": ["R-CHOP 변형 + 시타라빈 기반", "BTK 억제제(재발)"],
    "MZL (변연부 림프종)": ["R-치료(방사선/화학) 상황별", "헬리코박터 제균(위형)"],
    "PTCL (말초 T세포 림프종)": ["CHOP 변형", "브렌툭시맙(표적 CD30) 대상군"],

    # 육종
    "OS (골육종)": ["MAP(메토트렉세이트 고용량+독소루비신+시스플라틴)", "수술 ± 방사선"],
    "EWS (유잉 육종)": ["VDC/IE 교대", "수술/방사선 병용"],
    "RMS (횡문근육종)": ["VAC/VAI 등", "국소치료 병합"],
    "LMS (평활근육종)": ["독소루비신 ± 이포스파마이드/다카바진", "파조파닙 등 표적"],
    "UPS (미분화 다형성 육종)": ["독소루비신 기반", "트라베크테딘/에리불린(상황별)"],
    "GIST (위장관 기질종양)": ["이마티닙(키트/PDGFRA 변이)", "수술 ± TKI 유지"],

    # 고형암
    "NSCLC (비소세포 폐암)": ["PD-L1/변이 따라 면역치료/표적치료", "EGFR: 오시머티닙 / ALK: 알렉티닙 등"],
    "SCLC (소세포 폐암)": ["백금+에토포사이드 ± 면역치료(아테졸리주맙 등)"],
    "유방암(HR+/HER2-)": ["AI/탐옥시펜 ± CDK4/6 억제제", "주치의 판단 하 용량/병용 조절"],
    "유방암(HER2+)": ["트라스투주맙 ± 퍼투주맙 + 택산", "T-DM1/T-DXd(상황별)"],
    "유방암(삼중음성)": ["면역치료 ± 택산/플라틴", "BRCA 변이: PARP 억제제"],
    "대장암": ["FOLFOX/FOLFIRI ± 항EGFR/항VEGF", "MSI-H: 면역치료"],
    "위암": ["플라틴+플루오로피리미딘 ± 트라스투주맙(HER2+)", "면역치료 병용(상황별)"],
    "췌장암": ["FOLFIRINOX 또는 젬시타빈+나브-파클리탁셀"],
    "간세포암(HCC)": ["아테졸리주맙+베바시주맙", "렌바티닙/소라페닙 등"],
    "담도암": ["젬시타빈+시스플라틴 ± 면역", "FGFR2/IDH1 표적(변이시)"],
    "전립선암": ["ADT ± AR 억제제(아팔루타마이드/엔잘루타마이드/아비라테론)", "도세탁셀(상황별)"],
    "방광암": ["백금 기반 ± 면역치료", "ADC(엔포투맙 등) 상황별"],
    "신장암(RCC)": ["IO/IO 또는 IO+TKI 병용"],
    "두경부암(HNSCC)": ["백금+5-FU ± 항EGFR/면역", "국소는 수술/방사선"],
    "뇌종양(교모세포종 등)": ["테모졸로마이드+방사선(스투프)", "재발: 베바시주맙 등"],

    # 희귀암
    "NET (신경내분비종양)": ["소마토스타틴 유사체(옥트레오타이드/라루트리오타이드)", "PRRT(루테튬-177)"],
    "흉선종/흉선암": ["백금 기반", "표적/면역(상황별)"],
    "생식세포종양(GCT)": ["BEP(블레오+에토포+시스플라틴)"],
    "소아고형암(신경모세포종 등)": ["리스크 기반 다약제+수술/방사선", "항GD2 면역치료(상황별)"],
}

def get_regimens_for(subtype: str):
    return ONCO_REGIMENS.get(subtype, [])

# ============================
# special_tests.py 연동 (있으면 파일 우선 사용)
# ============================
def load_special_tests_from_file(category: str, subtype: str):
    """
    special_tests.py 가 제공되면 다음 우선순위로 탐색:
    1) get_special_tests(category, subtype)
    2) get_tests_for(category, subtype)
    3) SPECIAL_TESTS[(category, subtype)] or SPECIAL_TESTS[subtype] or SPECIAL_TESTS[category]
    없으면 빈 리스트 리턴.
    """
    try:
        import special_tests as stx  # 같은 폴더에 존재
    except Exception:
        return []

    # 함수 형태
    for fname in ("get_special_tests", "get_tests_for"):
        fn = getattr(stx, fname, None)
        if callable(fn):
            try:
                res = fn(category, subtype)
                if isinstance(res, (list, tuple)):
                    return list(res)
            except Exception:
                pass

    # dict 형태
    for key in ((category, subtype), subtype, category):
        try:
            data = getattr(stx, "SPECIAL_TESTS", {})
            if isinstance(data, dict) and key in data:
                val = data[key]
                if isinstance(val, (list, tuple)):
                    return list(val)
        except Exception:
            pass
    return []

# ============================
# Pediatric caregiver guide
# ============================
def _peds_homecare_details_soft(
    *, score, stool, fever, cough, eye,
    oliguria, ear_pain, rash, hives, abd_pain, migraine, hfmd
):
    st.markdown("### 보호자 상세 가이드")

    def _box(title, items):
        if st.session_state.get(wkey("peds_simple"), True):
            st.write("• " + title.replace(" — 집에서", ""))
        else:
            st.markdown(f"**{title}**")
            for it in items:
                st.write("- " + it)

    _box("🟡 오늘 집에서 살펴보면 좋아요", [
        "미온수나 ORS를 소량씩 자주 드셔보세요.",
        "실내는 가볍고 편안한 복장, 환기와 가습을 적당히 해 주세요.",
        "해열제는 간격을 지키면 도움이 됩니다: APAP 4시간 이상, IBU 6시간 이상.",
    ])

    if score.get("장염 의심", 0) > 0 or stool in ["3~4회", "5~6회", "7회 이상"]:
        _box("💧 장염/설사 의심 — 집에서", [
            "ORS 또는 미온수/맑은 국물을 조금씩 자주 드셔보세요. 구토가 있으면 10–15분 쉬고 다시 시도해요.",
            "기름지거나 자극적인 음식, 유제품은 잠시 쉬어가요.",
            "죽·바나나·사과퓨레·토스트처럼 부드러운 음식부터 천천히 시작해요.",
            "배변·소변·체온 변화를 간단히 기록해 두시면 도움이 됩니다.",
        ])

    if score.get("결막염 의심", 0) > 0 or eye in ["노랑-농성", "양쪽"]:
        _box("👁️ 결막염 의심 — 집에서", [
            "손 씻기를 자주 해 주세요. 수건·베개는 함께 사용하지 않아요.",
            "생리식염수로 부드럽게 씻어내고, 분비물은 안쪽→바깥쪽 방향으로 닦아줘요.",
            "불편감이 있으면 짧게 냉찜질(얼음은 직접 대지 않기).",
            "안약·항생제는 **의료진과 상의 후** 사용해 주세요.",
        ])

    if score.get("상기도/독감 계열", 0) > 0 or cough in ["조금", "보통", "심함"] or fever not in ["없음", "37~37.5 (미열)"]:
        _box("🤧 상기도/독감 계열 — 집에서", [
            "미온수 자주 마시기, 충분한 휴식.",
            "콧물이 많으면 생리식염수 세척 후 안전하게 흡인.",
            "기침이 심하면 따뜻한 음료, 욕실 스팀은 짧게만.",
            "해열제는 안내된 간격과 용량을 지켜 주세요.",
        ])

    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        _box("🌡️ 발열 38℃ 전후 — 집에서", [
            "실내 온도 **25–26℃** 권장(너무 춥거나 덥지 않게).",
            "미지근한 물수건으로 몸을 부드럽게 닦아주세요(찬물/알코올 금지).",
            "**미온수·ORS를 조금씩 자주** 마시게 해 주세요(한 번에 많이 X).",
            "손발이 **따뜻**하면 열이 잡히는 중일 수 있어요.",
            "손발이 **차가우면** 해열 효과 전일 수 있어 **30–60분 뒤 체온 재확인**해 주세요.",
            "해열제 간격: **아세트아미노펜 ≥4시간**, **이부프로펜 ≥6시간** (중복복용 금지).",
        ])

    if score.get("탈수/신장 문제", 0) > 0 or oliguria:
        _box("🚰 탈수/신장 문제 — 집에서", [
            "입술·혀 마름, 눈물 감소, 소변량 변화를 살펴봐 주세요.",
            "소변이 6–8시간 이상 없으면 진료가 필요할 수 있어요.",
            "구토 시 10–15분 쉬었다가 ORS를 다시 소량씩 시도.",
        ])

    if score.get("중이염/귀질환", 0) > 0 or ear_pain:
        _box("👂 중이염/귀질환 — 집에서", [
            "해열·진통제 간격 지키기.",
            "코막힘 심하면 생리식염수 세척.",
            "귀 안에 면봉 깊게 사용/물 넣기 피하기.",
        ])

    if score.get("피부발진/경미한 알레르기", 0) > 0 or rash or hives:
        _box("🌿 피부발진/가벼운 알레르기 — 집에서", [
            "미지근한 물로 짧게 샤워, 보습제 바르기.",
            "면 소재 옷, 손톱 정리.",
            "새 세제/음식 노출이 있었다면 잠시 중단. 호흡곤란·입술부종은 즉시 진료.",
        ])

    if score.get("복통 평가", 0) > 0 or abd_pain:
        _box("🤢 복통 — 집에서", [
            "국소 압통/구부정한 자세 지속 시 악화 신호 가능.",
            "자극 적고 소화 쉬운 음식부터.",
            "혈변·담즙성 구토·고열 동반 시 바로 진료.",
        ])

    if score.get("알레르기 주의", 0) > 0:
        _box("⚠️ 알레르기 — 집에서", [
            "새로운 음식·약 복용 여부 메모.",
            "입술·혀·목 부종/숨 가쁨/쉰목소리는 즉시 응급실.",
        ])

    if score.get("편두통 의심", 0) > 0 or migraine:
        _box("🧠 편두통 — 집에서", [
            "조용하고 어두운 환경, 수분 보충.",
            "빛·소리 자극 줄이기.",
            "갑작스럽고 극심한 두통/신경학적 증상은 바로 진료.",
        ])

    if score.get("수족구 의심", 0) > 0 or hfmd:
        _box("🖐️ 수족구 — 집에서", [
            "차갑고 부드러운 음식 권장.",
            "자극적 음식 제한, 수분 충분히.",
            "탈수 신호 보이면 진료 권장.",
        ])

    aden_eye = (eye in ["노랑-농성", "양쪽"]) or (score.get("결막염 의심", 0) >= 30)
    aden_fever = fever in ["38~38.5", "38.5~39", "39 이상"]
    aden_uri = (score.get("상기도/독감 계열", 0) >= 20) or (cough in ["보통", "심함"])
    if aden_eye and aden_fever and aden_uri:
        _box("🧬 아데노바이러스 가능성 — 참고", [
            "결막 분비물(양쪽/농성) + 발열 + 상기도 증상이 함께 보이면 가능성을 의심해 볼 수 있어요.",
            "가정에서는 확진이 어렵습니다. 증상이 이어지면 진료에서 확인받는 것을 권해요.",
            "손 위생과 개인 물품 분리는 전파를 줄이는 데 도움이 됩니다.",
        ])

    st.markdown("---")
    _box("🔴 바로 진료/연락이 좋아요", [
        "체온 **38.5℃ 이상 지속** 또는 **39℃ 이상**",
        "지속 구토(>6h), **소변량 급감**, 축 늘어짐/의식 흐림",
        "호흡 곤란/청색증/입술·혀 붓기",
        "혈변/검은 변, **농성 + 양쪽** 눈 분비물",
        "**처짐**/**경련 병력** 보이면 즉시 병원",
    ])
    st.caption(":red[응급이 의심되면 지체하지 말고 119 또는 가까운 응급실을 이용해 주세요.]")

def render_caregiver_notes_peds(
    stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd
):
    score = {
        "장염 의심": 40 if stool in ["3~4회", "5~6회", "7회 이상"] else 0,
        "결막염 의심": 30 if eye in ["노랑-농성", "양쪽"] else 0,
        "상기도/독감 계열": 20 if (cough in ["조금", "보통", "심함"] or fever in ["38~38.5","38.5~39","39 이상"]) else 0,
        "탈수/신장 문제": 20 if oliguria else 0,
        "출혈성 경향": 0,
        "중이염/귀질환": 10 if ear_pain else 0,
        "피부발진/경미한 알레르기": 10 if (rash or hives) else 0,
        "복통 평가": 10 if abd_pain else 0,
        "알레르기 주의": 5 if hives else 0,
        "편두통 의심": 10 if migraine else 0,
        "수족구 의심": 10 if hfmd else 0,
    }
    ordered = sorted(score.items(), key=lambda x: x[1], reverse=True)
    if any(v > 0 for _, v in ordered):
        st.write("• " + " / ".join([f"{k}: {v}" for k, v in ordered if v > 0]))

    _peds_homecare_details_soft(
        score=score, stool=stool, fever=fever, cough=cough, eye=eye,
        oliguria=oliguria, ear_pain=ear_pain, rash=rash, hives=hives,
        abd_pain=abd_pain, migraine=migraine, hfmd=hfmd
    )

# ============================
# ONCO labs (암환자 탭 전용)
# ============================
def render_onco_labs(*, temp, on_dyspnea, on_chest_pain, on_confusion, on_bleeding, on_oliguria):
    st.markdown("---")
    st.subheader("피수치 입력/해석")

    def num_row(label, key, unit="", minv=None, maxv=None, step=0.1, default=None):
        colc, colv, colu = st.columns([0.9, 1.1, 0.6])
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

    lc1, lc2, lc3, lc4 = st.columns(4)
    with lc1:
        u_wbc,  v_wbc  = num_row("WBC", "wbc", "10⁹/L", 0.0, 200.0, 0.1, 6.0)
        u_anc,  v_anc  = num_row("절대호중구(ANC)", "anc", "/μL", 0, 20000, 50, 1500)
        u_hb,   v_hb   = num_row("Hb", "hb", "g/dL", 0.0, 20.0, 0.1, 12.0)
        u_plt,  v_plt  = num_row("혈소판", "plt", "/μL", 0, 500000, 1000, 150000)
    with lc2:
        u_crp,  v_crp  = num_row("CRP", "crp", "mg/L", 0.0, 1000.0, 0.5, 0.5)
        u_pct,  v_pct  = num_row("PCT", "pct", "ng/mL", 0.0, 100.0, 0.1, 0.05)
        u_esr,  v_esr  = num_row("ESR", "esr", "mm/hr", 0.0, 200.0, 1.0, 10.0)
        u_lac,  v_lac  = num_row("Lactate", "lact", "mmol/L", 0.0, 20.0, 0.1, 1.0)
    with lc3:
        u_na,   v_na   = num_row("Na", "na", "mEq/L", 100.0, 170.0, 0.5, 140.0)
        u_k,    v_k    = num_row("K", "k", "mEq/L", 1.0, 9.0, 0.1, 4.0)
        u_bun,  v_bun  = num_row("BUN", "bun", "mg/dL", 1.0, 200.0, 0.5, 14.0)
        u_cr,   v_cr   = num_row("Creatinine", "cr", "mg/dL", 0.1, 10.0, 0.1, 0.9)
    with lc4:
        u_ast,  v_ast  = num_row("AST", "ast", "U/L", 0.0, 1000.0, 1.0, 25.0)
        u_alt,  v_alt  = num_row("ALT", "alt", "U/L", 0.0, 1000.0, 1.0, 25.0)
        u_ldh,  v_ldh  = num_row("LDH", "ldh", "U/L", 0.0, 2000.0, 1.0, 180.0)
        u_ferr, v_ferr = num_row("Ferritin", "ferr", "ng/mL", 0.0, 5000.0, 1.0, 150.0)

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        u_pt,   v_pt   = num_row("PT (sec)", "pt", "sec", 5.0, 50.0, 0.1, 12.5)
    with sc2:
        u_inr,  v_inr  = num_row("INR", "inr", "", 0.5, 10.0, 0.01, 1.0)
    with sc3:
        u_aptt, v_aptt = num_row("aPTT", "aptt", "sec", 10.0, 200.0, 0.5, 32.0)
    with sc4:
        u_fib,  v_fib  = num_row("Fibrinogen", "fibr", "mg/dL", 50.0, 800.0, 1.0, 300.0)

    hc1, hc2, hc3, hc4 = st.columns(4)
    with hc1:
        u_trop, v_trop = num_row("Troponin", "trop", "ng/L", 0.0, 10000.0, 1.0, 5.0)
    with hc2:
        u_bnp,  v_bnp  = num_row("BNP/NT-proBNP", "bnp", "pg/mL", 0.0, 100000.0, 5.0, 80.0)
    with hc3:
        u_dd,   v_dd   = num_row("D-dimer", "dd", "μg/mL FEU", 0.0, 20.0, 0.1, 0.3)
    with hc4:
        pass

    flags = []
    def used(x): return x is not None

    if u_anc and used(v_anc):
        if v_anc < 500:   flags.append("ANC<500 (감염 위험↑)")
        elif v_anc < 1000: flags.append("ANC 500–999")
    if u_plt and used(v_plt):
        if v_plt < 20000:  flags.append("혈소판<20k (출혈 위험)")
        elif v_plt < 50000: flags.append("혈소판 20–50k")
    if u_hb and used(v_hb):
        if v_hb < 7.0:   flags.append("중증 빈혈 가능")
        elif v_hb < 8.0: flags.append("빈혈 주의")

    if u_crp and used(v_crp) and v_crp >= 10: flags.append("CRP≥10 (염증↑)")
    if u_pct and used(v_pct) and v_pct >= 0.5: flags.append("PCT≥0.5 (세균성 감염 가능)")
    if u_lac and used(v_lac) and v_lac >= 2.0: flags.append("Lactate≥2 (저관류/패혈증 의심)")

    if u_na and used(v_na) and v_na < 130: flags.append("저나트륨")
    if u_k and used(v_k) and v_k >= 5.5:  flags.append("고칼륨")
    if u_cr and used(v_cr) and v_cr >= 1.5: flags.append("Cr 상승(신장)")

    if u_ast and used(v_ast) and v_ast >= 100: flags.append("AST 상승")
    if u_alt and used(v_alt) and v_alt >= 100: flags.append("ALT 상승")
    if u_ldh and used(v_ldh) and v_ldh >= 250: flags.append("LDH 상승")
    if u_ferr and used(v_ferr) and v_ferr >= 500: flags.append("Ferritin 상승")

    if u_pt and used(v_pt) and v_pt >= 15: flags.append("PT 연장")
    if u_inr and used(v_inr) and v_inr >= 1.5: flags.append("INR 상승")
    if u_aptt and used(v_aptt) and v_aptt >= 40: flags.append("aPTT 연장")
    if u_fib and used(v_fib) and v_fib < 150: flags.append("저 Fibrinogen")

    if u_trop and used(v_trop) and v_trop >= 14: flags.append("Troponin 상승")
    if u_bnp and used(v_bnp) and v_bnp >= 300: flags.append("BNP/NT-proBNP 상승")
    if u_dd and used(v_dd) and v_dd >= 1.0: flags.append("D-dimer 상승")

    if on_dyspnea or on_chest_pain: flags.append("호흡/흉통 주의")
    if on_confusion: flags.append("의식 저하 주의")
    if on_oliguria: flags.append("소변 감소 주의")
    if on_bleeding: flags.append("출혈 양상 주의")

    if flags:
        st.warning("피수치 요약(입력한 항목 기준): " + " / ".join(flags))
    else:
        st.info("입력하신 항목 기준으로 즉시 위험 신호는 보이지 않아요. (미입력 항목은 평가 제외)")

    st.markdown("—")
    st.subheader("특수 검사 가이드(자동 제안)")
    tips = []
    fever_high = (temp == "≥38.5℃")
    if fever_high or (u_crp and used(v_crp) and v_crp >= 10) or (u_pct and used(v_pct) and v_pct >= 0.5):
        tips += ["혈액배양(2세트 권장)·소변배양", "흉부 X-ray(호흡기 증상 시 우선)"]
    if on_dyspnea or on_chest_pain or (u_trop and used(v_trop) and v_trop >= 14) or (u_bnp and used(v_bnp) and v_bnp >= 300):
        tips += ["ECG", "흉부 X-ray ± CT(의료진 판단)", "Troponin/BNP 재평가", "SpO₂/혈액가스"]
    if on_confusion or (u_lac and used(v_lac) and v_lac >= 2.0):
        tips += ["혈당/전해질/락테이트 추적", "필요 시 뇌영상(CT/MRI)"]
    if (u_dd and used(v_dd) and v_dd >= 1.0) or on_bleeding or (u_inr and used(v_inr) and v_inr >= 1.5):
        tips += ["응고계(PT/INR, aPTT, Fibrinogen) 재평가", "필요 시 혈액제제 고려(의료진 판단)"]
    if on_oliguria or (u_bun and used(v_bun) and v_bun >= 20) or (u_cr and used(v_cr) and v_cr >= 1.5):
        tips += ["요검사/요배양", "신장초음파 ± 수액반응 평가"]

    if tips:
        st.markdown("**권장 검토 항목(의료진 판단 하에):**")
        for t in dict.fromkeys(tips):
            st.write("- " + t)
    else:
        st.write("현재 입력 기준으로 꼭 필요한 특수검사 제안은 없어요. 증상 변화에 따라 달라질 수 있어요.")

# 특수검사 체크리스트 + 메모 + TXT 저장 (파일 연동 포함)
def render_onco_specials_checklist(category: str, subtype: str):
    st.subheader("🔬 특수검사(파일 연동) · 체크리스트 & 결과 메모")

    # 파일에서 가져오기(있으면 파일 우선)
    from_file = load_special_tests_from_file(category, subtype)
    if from_file:
        st.markdown("**권장 특수검사(파일 연동):**")
        for it in from_file:
            st.write("- " + str(it))
    else:
        st.caption("특수검사 파일에서 해당 항목을 찾지 못했습니다. 필요 시 자동 제안을 참고하세요.")

    st.markdown("---")
    st.markdown("**체크리스트(실시 항목 체크)**")
    cols = st.columns(3)
    items = [
        "혈액배양 2세트", "요배양/요검사", "흉부 X-ray", "ECG",
        "혈액가스/젖산", "흉부 CT", "복부 CT", "신장초음파",
        "응고계(PT/INR, aPTT, Fib)", "종양표지자", "심초음파", "기타"
    ]
    checks = []
    for i, name in enumerate(items):
        with cols[i % 3]:
            checks.append((name, st.checkbox(name, key=wkey(f"sp_{i}_{name}"))))

    st.markdown("**메모(결과·판단·계획)**")
    memo = st.text_area("", height=140, key=wkey("sp_memo"))

    selected = [n for n, f in checks if f]
    summary = f"[{category}] {subtype}\n특수검사 체크리스트\n" + \
              ("- " + "\n- ".join(selected) if selected else "- (선택 없음)") + \
              "\n\n메모\n" + (memo or "(내용 없음)")
    st.download_button("요약 .txt 저장", summary, file_name="onco_specials_summary.txt",
                       mime="text/plain", use_container_width=True)

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
            base = PRESETS.get(preset_name, {})
            set_weights(base)
            st.success("프리셋을 적용했어요.")
    with right:
        if st.button("기본값으로 초기화", key=wkey("preset_reset")):
            set_weights({})
            st.info("기본값으로 초기화했습니다.")

    W = get_weights()
    with st.expander("현재 가중치 보기(읽기 전용)", expanded=False):
        try:
            st.json({k: float(W.get(k, 1.0)) for k in sorted(W.keys())})
        except Exception:
            st.write(W)

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
    with c1:
        nasal = st.selectbox("콧물", ["해당 없음", "맑음", "끈적"], index=0, key=wkey("p_nasal"))
    with c2:
        cough = st.selectbox("기침", ["없음", "조금", "보통", "심함"], index=0, key=wkey("p_cough"))
    with c3:
        stool = st.selectbox("설사", ["해당 없음", "1~2회", "3~4회", "5~6회", "7회 이상"], index=0, key=wkey("p_stool"))
    with c4:
        fever = st.selectbox("발열", ["없음", "37~37.5 (미열)", "38~38.5", "38.5~39", "39 이상"], index=0, key=wkey("p_fever"))
    with c5:
        eye = st.selectbox("눈꼽/결막", ["해당 없음", "맑음", "양쪽", "노랑-농성"], index=0, key=wkey("p_eye"))

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
    render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd
    )

# ---- CANCER TYPE (분류/식사/특수검사) ----
with t_type:
    st.subheader("암 종류별 안내 (식사 가이드 + 특수검사 제안)")
    pick = st.selectbox("암 종류 선택", CANCER_TYPES, key=wkey("ctype"))
    diet, tests, notes = get_onco_type_guides(pick)

    st.markdown(f"### 🍽️ {pick} — 식사 가이드")
    for d in diet:
        st.write("- " + d)

    st.markdown(f"### 🔬 {pick} — 특수검사/추적 제안(의료진 판단)")
    for t in tests:
        st.write("- " + t)

    st.markdown("### 📝 주의/메모")
    for n in notes:
        st.write("- " + n)

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
    st.subheader("암환자 빠른 안내 (분류/치료요약 + 가정 대처 + 피수치/특수검사)")
    st.caption("참고용 안내입니다. 응급이 의심되면 119/응급실을 이용해 주세요.")

    # 1) 카테고리/서브타입 선택
    cat = st.selectbox("암 카테고리", list(ONCO_CATEGORIES.keys()), index=0, key=wkey("on_cat"))
    sub = st.selectbox("세부분류(서브타입)", ONCO_CATEGORIES[cat], index=0, key=wkey("on_sub"))

    # 2) 서브타입별 대표 요법(예시)
    st.markdown(f"### 💊 {sub} — 대표 치료(예시, 주치의 판단 우선)")
    regs = get_regimens_for(sub)
    if regs:
        for r in regs:
            st.write("- " + r)
    else:
        st.write("- (정보 준비 중)")
    st.caption(":gray[※ 실제 치료는 환자 상태·병기·분자유전학·부작용 위험 등을 반영해 주치의가 결정합니다.]")

    st.markdown("---")
    st.markdown("### 상태 입력")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        on_temp = st.selectbox("체온", ["<38.0℃", "38.0~38.4℃", "≥38.5℃"], index=0, key=wkey("on_temp"))
    with c2:
        on_anc = st.number_input("ANC(호중구) /μL", min_value=0, max_value=10000, value=1500, step=100, key=wkey("on_anc"))
    with c3:
        on_plt = st.number_input("혈소판 /μL", min_value=0, max_value=500000, value=150000, step=1000, key=wkey("on_plt"))
    with c4:
        on_hb = st.number_input("Hb (g/dL)", min_value=0.0, max_value=20.0, value=12.0, step=0.1, key=wkey("on_hb"))

    s1, s2, s3 = st.columns(3)
    with s1:
        on_chemo = st.checkbox("최근 4주 이내 항암제 치료", key=wkey("on_chemo"))
        on_chills = st.checkbox("오한/떨림", key=wkey("on_chills"))
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
        li("체온을 20–30분 간격으로 확인해 주세요. 미지근한 물수건으로 몸을 닦아주면 조금 편안해질 수 있어요.")
        li("수분을 조금씩 자주 섭취해 주세요. 혈소판이 낮은 경우 NSAIDs는 피하는 게 안전해요.")
    if on_anc < 1000 and on_chemo:
        li("감염에 취약한 시기예요. 외출 시 마스크, 손 위생, 사람 많은 곳은 당분간 피해주세요.")
    if on_plt < 50000:
        li("양치/면도는 부드럽게, 코 풀 때는 한쪽씩 천천히. 멍/붉은 점이 늘면 연락이 필요할 수 있어요.")
    if on_hb < 8.0:
        li("계단·격한 활동은 잠시 줄이고 충분히 쉬어주세요. 어지럼/가슴두근거림이 심해지면 진료가 좋아요.")

    st.markdown("---")
    st.markdown("### 바로 진료/연락이 좋아요")
    li(":red[체온 38.5℃ 이상 또는 오한/떨림이 지속될 때]")
    li(":red[ANC<500 이면서 발열이 있을 때(호중구감소성 발열 의심)]")
    li(":red[호흡곤란, 가슴 통증, 의식저하/혼돈이 있을 때]")
    li(":red[혈변/검은변, 멈추지 않는 코피, 멍·붉은 점이 빠르게 늘 때]")
    li(":red[소변이 6–8시간 이상 없거나 심한 구토/설사로 수분 섭취가 어려울 때]")

    if high_urgency:
        st.info("지금 상태에서는 가까운 병원 또는 담당 병원에 즉시 연락하는 것이 좋아요. 필요 시 구급을 이용해 주세요.")

    # 3) 피수치/자동 제안(ONCO 탭 전용)
    with st.expander("🧪 피수치(체크한 항목만 평가) · 자동 특수검사 제안", expanded=False):
        render_onco_labs(
            temp=on_temp,
            on_dyspnea=on_dyspnea,
            on_chest_pain=on_chest_pain,
            on_confusion=on_confusion,
            on_bleeding=on_bleeding,
            on_oliguria=on_oliguria,
        )

    # 4) 특수검사 — 파일 연동 UI (있으면 파일 내용 우선)
    with st.expander("🔬 특수검사(파일 연동) — 체크리스트/메모", expanded=False):
        render_onco_specials_checklist(category=cat, subtype=sub)

