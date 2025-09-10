# -*- coding: utf-8 -*-
# =========================================================
# BloodMap (피수치 가이드) - Streamlit 단일 파일 앱
# 제작: Hoya/GPT | 자문: Hoya/GPT
# 안내: 세포/면역치료(CAR-T, TCR-T, NK, HSCT 등)는 표기하지 않습니다.
# =========================================================

import io, json, uuid, base64, math
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import streamlit as st
import pandas as pd

# ------------------------- 페이지/모바일 설정 -------------------------
st.set_page_config(
    page_title="피수치 가이드 (BloodMap)",
    page_icon="🩸",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MOBILE_NOTE = "모바일에서도 입력 순서가 뒤섞이지 않도록 **단일 컬럼, 고정 순서**로 구성했습니다."

# 간단 스타일(모바일 가독성)
st.markdown("""
<style>
/* 모바일 입력 꼬임 방지: 너비 고정 + 라벨 여백 */
div.stTextInput > label, div.stSelectbox > label, div.stNumberInput > label { font-weight:600; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; }
.copywrap button { border-radius: 10px; padding: 4px 10px; }
.k-pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:600; margin-left:6px;}
.k-green{ background:#e6f7ee; color:#0a8a4a;}
.k-yellow{ background:#fff7e6; color:#b36b00;}
.k-red{ background:#ffecec; color:#c40000;}
.small{ font-size:12px; opacity:.8; }
hr{ margin: 1.0rem 0; }
</style>
""", unsafe_allow_html=True)

# ------------------------- 공통 유틸: 복사 버튼 -------------------------
from streamlit.components.v1 import html

def copy_button(text: str, label: str = "📋 복사"):
    uid = "copystatus_" + uuid.uuid4().hex
    payload = json.dumps(text)  # 안전 직렬화
    html(
        """
        <div class=\"copywrap\" style=\"display:flex;align-items:center;gap:8px;\">
          <button onclick='navigator.clipboard.writeText({payload}).then(()=>{{const el=document.getElementById("{uid}"); if(el){{el.innerText="복사됨!"; setTimeout(()=>{{el.innerText="";}},1500);}}}})'>
            {label}
          </button>
          <span id=\"{uid}\" style=\"font-size:12px;color:green;\"></span>
        </div>
        """.format(payload=payload, uid=uid, label=label),
        height=40,
    )

# ------------------------- 소아 식이가이드 -------------------------
def peds_diet_guide(disease=None, vals=None) -> Tuple[List[str], List[str], List[str]]:
    """
    Returns:
        foods, avoid, tips  (각각 list[str])
    정책:
    - 1회 용량(ml)만 표기. '1일 최대'는 표기하지 않음.
    - 로타/노로/파라인플루엔자/마이코플라즈마/열감기 포함
    """
    disease = disease or {}
    vals = vals or {}
    foods: List[str] = []
    avoid: List[str] = []
    tips:  List[str] = []

    dx_raw = str(disease.get("name") or disease.get("dx") or "").strip().lower()
    temp_c = vals.get("temp_c")
    weight = vals.get("weight_kg")

    def antipyretic_ml(weight_kg: Optional[float]):
        if not weight_kg:
            return None
        # APAP 15mg/kg (160mg/5mL), IBU 10mg/kg (100mg/5mL)
        apap_ml = round((weight_kg * 15) / 160 * 5, 1)
        ibu_ml  = round((weight_kg * 10) / 100 * 5, 1)
        return apap_ml, ibu_ml

    def add_temp_tips():
        if temp_c is None: return
        dose_line = ""
        d = antipyretic_ml(weight)
        if d:
            apap_ml, ibu_ml = d
            dose_line = f"아세트아미노펜 {apap_ml} mL 또는 이부프로펜 {ibu_ml} mL (1회용량)"
        if 38.0 <= temp_c < 38.5:
            tips.append(f"체온 {temp_c:.1f}℃: 미지근한 물수건·수분 보충. 필요 시 {dose_line}")
        elif 38.5 <= temp_c < 39.0:
            tips.append(f"체온 {temp_c:.1f}℃: {dose_line} 복용 후 경과 관찰")
        elif temp_c >= 39.0:
            tips.append(f"체온 {temp_c:.1f}℃: {dose_line} 복용 및 의료진 연락 고려")

    def add_common_gastro():
        foods.extend(["미음/쌀죽", "바나나·사과퓨레", "삶은 감자/당근", "부드러운 흰살생선", "ORS 소량씩 자주"])
        avoid.extend(["우유/유제품", "기름진 음식", "생야채/샐러드", "과일주스", "매운/자극적 음식"])
        tips.extend([
            "탈수 징후: 소변 감소·입마름·눈물 감소",
            "구토 시 30분 휴식 후 한 모금씩 재시도",
            "혈변/지속 고열/심한 탈수는 즉시 진료"
        ])

    if any(k in dx_raw for k in ["rota", "로타"]):
        add_common_gastro()
        tips.append("로타바이러스: 항생제 효과 없음(바이러스성)")
        add_temp_tips()
    elif any(k in dx_raw for k in ["noro", "노로"]):
        add_common_gastro()
        tips.append("노로바이러스: 급성 구토·설사, 가족 전파 주의")
        add_temp_tips()
    elif any(k in dx_raw for k in ["parainfluenza", "파라인플루엔자", "파라"]):
        foods.extend(["따뜻한 미음/죽", "연두부", "부드러운 달걀요리", "따뜻한 물/차", "과일퓨레"])
        avoid.extend(["차가운 음료", "매운 음식", "딱딱한 과자류", "강산성 음료"])
        tips.extend([
            "가습·따뜻한 김 쐬기, 편안한 자세 유지",
            "흡기 시 쌕쌕/크룹성 기침·함몰호흡·청색증은 즉시 진료"
        ])
        add_temp_tips()
    elif any(k in dx_raw for k in ["mycoplasma", "마이코플라즈마", "마이코"]):
        foods.extend(["부드러운 죽/수프", "단백질 보충(달걀·두부)", "따뜻한 물/차", "삶은 감자", "요거트(설사 없을 때)"])
        avoid.extend(["기름지고 매운 음식", "탄산/카페인", "과도한 당류"])
        tips.extend(["항생제는 반드시 처방에 따름(자가복용 금지)"])
        add_temp_tips()
    elif any(k in dx_raw for k in ["열감기", "fever", "cold", "열"]):
        foods.extend(["미음/죽", "연두부", "바나나", "사과퓨레", "물/ORS"])
        avoid.extend(["매운/자극적", "튀김", "과당 음료"])
        tips.append("휴식·수분 보충 우선, 해열제는 필요 시 1회 용량만 복용")
        add_temp_tips()
    else:
        foods.extend(["미음/쌀죽", "연두부", "바나나", "사과퓨레", "따뜻한 물"])
        avoid.extend(["기름진 음식", "매운 음식", "탄산/카페인", "생야채"])
        tips.append("고열·탈수·호흡곤란 시 의료진 상담 우선")
        add_temp_tips()

    tips.append("철분제+비타민C는 **백혈병 환자**에게 권장하지 않습니다. 반드시 주치의와 상의하세요.")
    return foods, avoid, tips

# ------------------------- 암 진단: 약제 데이터(요약) -------------------------
# 각 약물: 한글병기, 기전, 대표 부작용
DRUGS = {
    # 혈액암 - APL (요구: MTX, 6-MP 반드시 포함)
    "혈액암 - APL": {
        "항암제": [
            {"name": "ATRA (베사노이드)", "moa": "레티노산 수용체 작용 → 분화 유도", "se": "두통, 피부건조, 고지혈증, **분화증후군(호흡곤란/발열/부종)**"},
            {"name": "Arsenic trioxide (As2O3, 트리옥사이드)", "moa": "PML-RARA 분해 유도", "se": "QT 연장, 전해질 이상, 피로"},
            {"name": "MTX (메토트렉세이트)", "moa": "항대사제, DHFR 억제", "se": "간수치 상승, 구내염, 골수억제, 광과민"},
            {"name": "6-MP (메르캅토퓨린)", "moa": "푸린 대사 저해", "se": "골수억제, 간독성, 발진"},
        ],
        "표적치료제": [],  # APL 고유 표적치료 없음
        "항생제": [
            {"name":"Piperacillin/Tazobactam (피페라실린/타조박탐)","moa":"광범위 β-락탐 + β-락탐제 억제제","se":"알레르기, 설사, 간수치상승"},
            {"name":"Cefepime (세페핌)","moa":"광범위 4세대 세팔로스포린","se":"설사, 발진, 드물게 신경독성"},
            {"name":"Levofloxacin (레보플록사신)","moa":"퀴놀론, DNA gyrase 억제","se":"건병증 위험, QT 연장"}
        ]
    },
    # 림프종 - DLBCL 예시
    "림프종 - B거대세포": {
        "항암제": [
            {"name":"Cyclophosphamide (사이클로포스파미드)","moa":"알킬화제","se":"골수억제, 출혈성 방광염"},
            {"name":"Doxorubicin (도옥소루비신)","moa":"Topo II 억제/자유라디칼","se":"심독성, 탈모, 점막염"},
            {"name":"Vincristine (빈크리스틴)","moa":"미세소관 억제","se":"말초신경병증, 변비"},
            {"name":"Prednisone (프레드니손)","moa":"글루코코르티코이드","se":"고혈당, 감염 위험 증가"}
        ],
        "표적치료제":[
            {"name":"Rituximab (리툭시맙) [CD20]","moa":"CD20 표적 mAb","se":"주입반응, HBV 재활성"}
        ],
        "항생제":[
            {"name":"Piperacillin/Tazobactam (피페/타조)","moa":"광범위","se":"알레르기, 설사"},
            {"name":"Cefepime (세페핌)","moa":"광범위","se":"설사, 발진"}
        ]
    },
    # 고형암 - 폐선암 예시
    "고형암 - 폐선암": {
        "항암제":[
            {"name":"Pemetrexed (페메트렉시드)","moa":"항대사제","se":"골수억제, 구내염"},
            {"name":"Cisplatin (시스플라틴)","moa":"DNA 가교결합","se":"신독성, 오심/구토, 이독성"}
        ],
        "표적치료제":[
            {"name":"Osimertinib (오시머티닙) [EGFR]","moa":"EGFR-TKI","se":"설사, 발진, QT 연장"},
            {"name":"Alectinib (알렉티닙) [ALK]","moa":"ALK 억제","se":"변비, 간수치상승"}
        ],
        "항생제":[
            {"name":"Levofloxacin (레보플록사신)","moa":"호흡기 퀴놀론","se":"건병증, QT 연장"}
        ]
    },
    # 육종 - 골육종 예시
    "육종 - Osteosarcoma(골육종)": {
        "항암제":[
            {"name":"High-dose Methotrexate (고용량 MTX)","moa":"DHFR 억제","se":"간독성, 점막염"},
            {"name":"Doxorubicin (도옥소루비신)","moa":"Topo II 억제","se":"심독성"}
        ],
        "표적치료제":[],
        "항생제":[{"name":"Cefepime (세페핌)","moa":"광범위","se":"발진/설사"}]
    },
    # 희귀암 - GIST 예시
    "희귀암 - GIST": {
        "항암제":[],
        "표적치료제":[
            {"name":"Imatinib (이마티닙) [KIT]","moa":"KIT/PDGFRA TKI","se":"부종, 근육통, 오심"}
        ],
        "항생제":[]
    }
}

# --- 공통 감염/지지요법 목록 (암종 무관 기본 세트) ---
COMMON_ABX = [
    {"name": "Piperacillin/Tazobactam (피페/타조)", "moa": "광범위", "se": "알레르기, 설사"},
    {"name": "Cefepime (세페핌)", "moa": "광범위", "se": "설사, 발진"},
    {"name": "Meropenem (메로페넴)", "moa": "광범위", "se": "설사, 발열, 경련"},
    {"name": "Vancomycin (반코마이신)", "moa": "MRSA 등 그람양성균", "se": "신장독성, Red-man syndrome"},
    {"name": "Amikacin (아미카신)", "moa": "그람음성균", "se": "청각독성, 신장독성"},
    {"name": "Clindamycin (클린다마이신)", "moa": "혐기성균", "se": "설사, 위장 장애"},
    {"name": "Metronidazole (메트로니다졸)", "moa": "혐기성균", "se": "금주 필요, 구토, 구내염"},
    {"name": "Cefotaxime (세포탁심)", "moa": "그람양성/음성", "se": "설사, 피부 발진"},
    {"name": "Levofloxacin (레보플록사신)", "moa": "광범위", "se": "건염, QT 연장, 불면"},
    {"name": "Trimethoprim/Sulfamethoxazole (박트림)", "moa": "Pneumocystis 예방", "se": "저혈당, 피부 발진, 골수억제"},
    {"name": "Linezolid (리네졸리드)", "moa": "MRSA, VRE", "se": "혈소판감소증, 시신경염"},
]

COMMON_ANTIFUNGALS = [
    {"name": "Fluconazole (플루코나졸)", "moa": "칸디다, 항진균", "se": "간수치 상승, 위장장애"},
    {"name": "Amphotericin B (암포테리신)", "moa": "광범위 항진균", "se": "신장독성, 오한, 발열"},
    {"name": "Caspofungin (카스포펀진)", "moa": "항진균", "se": "간기능 이상, 발진"},
]

COMMON_STEROIDS = [
    {"name": "Dexamethasone (덱사메타손)", "moa": "항염/면역억제", "se": "혈당 상승, 불면, 위장장애"},
    {"name": "Prednisolone (프레드니솔론)", "moa": "항염/면역억제", "se": "부종, 감염 위험 증가"},
    {"name": "Hydrocortisone (하이드로코티손)", "moa": "응급 스테로이드", "se": "혈당상승, 부종"},
]

# 고형암 다른 진단 예시(직접입력 허용)
SOLID_LIST = ["폐선암", "유방암", "위암", "대장암", "간세포암", "췌장암", "담도암", "직접 입력…"]
SARCOMA_LIST = ["Osteosarcoma(골육종)", "Ewing sarcoma", "Leiomyosarcoma", "직접 입력…"]
HEME_LIST = ["APL", "ALL", "AML", "CML", "CLL", "직접 입력…"]
RARE_LIST = ["GIST", "NET", "Chordoma", "직접 입력…"]
LYMPHOMA_LIST = ["B거대세포", "Hodgkin", "FL", "MCL", "직접 입력…"]

def build_key(category:str, diag:str)->str:
    return f"{category} - {diag}"

def drug_reco(category: str, diagnosis: str):
    key = build_key(category, diagnosis)
    data = DRUGS.get(key, None)
    if data: return data
    # 기본 템플릿(미등록 진단)
    return {
        "항암제": [],
        "표적치료제": [],
        "항생제": [
            {"name":"Piperacillin/Tazobactam (피페/타조)","moa":"광범위 β-락탐","se":"알레르기, 설사"},
            {"name":"Cefepime (세페핌)","moa":"광범위 세팔로스포린","se":"발진, 드물게 신경독성"}
        ]
    }

# ------------------------- 특수검사 해석 -------------------------
QUAL = ["없음", "+", "++", "+++"]

def interpret_special_tests(q:Dict, n:Dict) -> List[str]:
    lines=[]
    # 정성
    if q.get("알부민뇨") in ["++", "+++"]:
        lines.append("알부민뇨 +++ → 🚨 신장 기능 이상 가능성")
    elif q.get("알부민뇨") == "+":
        lines.append("알부민뇨 + → 🟡 경미 단백뇨, 재검 고려")

    if q.get("혈뇨") in ["++", "+++"]:
        lines.append("혈뇨 ++ 이상 → 🟡 요로계 이상 가능성")
    if q.get("요당") in ["++", "+++"]:
        lines.append("요당 ++ 이상 → 🟡 당대사 이상 가능성")
    if q.get("케톤뇨") in ["++", "+++"]:
        lines.append("케톤뇨 ++ 이상 → 🟡 탈수/기아/당대사 이상 가능성")

    # 정량
    def _flt(x):
        try: return float(x)
        except: return None

    # 보체
    if (c3:=_flt(n.get("C3"))) is not None and c3 < 75:
        lines.append("C3 낮음 → 🟡 면역계 이상 가능성(루푸스 감별)")
    if (c4:=_flt(n.get("C4"))) is not None and c4 < 15:
        lines.append("C4 낮음 → 🟡 면역계 이상 가능성")
    if (ch50:=_flt(n.get("CH50"))) is not None and ch50 < 23:
        lines.append("CH50 낮음 → 🟡 보체 활성 저하 가능성")

    # 지질
    if (tg:=_flt(n.get("TG"))) is not None and tg >= 200:
        lines.append("TG 200 이상 → 🟡 고지혈증 가능성")
    if (hdl:=_flt(n.get("HDL"))) is not None and hdl < 40:
        lines.append("HDL 낮음 → 🟡 이상지질혈증 가능성")
    if (ldl:=_flt(n.get("LDL"))) is not None and ldl >= 160:
        lines.append("LDL 160 이상 → 🟡 고지혈증 가능성")
    if (tc:=_flt(n.get("총콜레스테롤"))) is not None and tc >= 240:
        lines.append("총콜레스테롤 240 이상 → 🟡 고지혈증 가능성")
    if (apob:=_flt(n.get("ApoB"))) is not None and apob >= 130:
        lines.append("ApoB 130 이상 → 🟡 죽상경화 위험 증가 가능")
    if (lpa:=_flt(n.get("Lp(a)"))) is not None and lpa >= 50:
        lines.append("Lp(a) 50 이상 → 🟡 유전성 이상지질혈증 가능")
    # 파생: Non-HDL = TC - HDL
    if ('총콜레스테롤' in n) and ('HDL' in n):
        tc_v = _flt(n.get('총콜레스테롤'))
        hdl_v = _flt(n.get('HDL'))
        if tc_v is not None and hdl_v is not None:
            non_hdl = tc_v - hdl_v
            if non_hdl >= 160:
                lines.append(f"Non-HDL {non_hdl:.0f} 이상 → 🟡 죽상경화 위험 증가 가능")

    # 심장지표
    if (bnp:=_flt(n.get("BNP"))) is not None and bnp >= 100:
        lines.append("BNP 100 이상 → 🟡 심부전 가능성(임상과 함께 해석)")
    if (ntp:=_flt(n.get("NT-proBNP"))) is not None and ntp >= 125:
        lines.append("NT-proBNP 상승 → 🟡 심장 부담 가능성(연령/신장기능 고려)")
    if (tni:=_flt(n.get("TroponinI"))) is not None and tni >= 0.04:
        lines.append("Troponin I 상승 → 🚨 심근손상 가능성(응급 평가 필요)")
    if (ckmb:=_flt(n.get("CK-MB"))) is not None and ckmb > 5:
        lines.append("CK-MB 상승 → 🟡 심근 손상 가능성")

    return lines

# ------------------------- 기본 피수치 입력 & 해석 -------------------------
LAB_ORDER = [
    ("WBC (백혈구)", "WBC"),
    ("Hb (혈색소)", "Hb"),
    ("혈소판", "PLT"),
    ("ANC (호중구)", "ANC"),
    ("Ca (칼슘)", "Ca"),
    ("P (인)", "P"),
    ("Na (소디움)", "Na"),
    ("K (포타슘)", "K"),
    ("Albumin (알부민)", "Albumin"),
    ("Glucose (혈당)", "Glucose"),
    ("Total Protein (총단백)", "TP"),
    ("AST", "AST"),
    ("ALT", "ALT"),
    ("LDH", "LDH"),
    ("CRP", "CRP"),
    ("Creatinine (Cr)", "Cr"),
    ("Uric Acid (UA)", "UA"),
    ("Total Bilirubin (TB)", "TB"),
    ("BUN", "BUN"),
    ("BNP (선택)", "BNP"),
]

def to_float(x):
    try:
        if x is None or str(x).strip()=="":
            return None
        return float(str(x).strip())
    except:
        return None

def interpret_labs(vals: Dict[str, Optional[float]]) -> List[str]:
    L=[]
    def add(name, txt, level):
        badge = {"ok":"🟢","warn":"🟡","danger":"🚨"}[level]
        L.append(f"- {name}: {txt} {badge}")
    v = vals

    # 참고 범위는 보호자용 단순화 (개별 상한은 병원 범위 우선)
    # 위험/주의 기준은 보수적 예시
    if (wbc:=v.get("WBC")) is not None:
        if wbc < 2: add("WBC","매우 낮음 → 감염 위험", "danger")
        elif wbc < 4: add("WBC","낮음 → 감염 주의", "warn")
        elif wbc <= 10: add("WBC","정상 범위", "ok")
        else: add("WBC","높음 → 감염/염증 가능", "warn")

    if (hb:=v.get("Hb")) is not None:
        if hb < 8: add("Hb","심한 빈혈", "danger")
        elif hb < 12: add("Hb","빈혈 경향", "warn")
        else: add("Hb","대체로 양호", "ok")

    if (plt:=v.get("PLT")) is not None:
        if plt < 20: add("혈소판","매우 낮음 → 출혈 위험", "danger")
        elif plt < 50: add("혈소판","낮음 → 멍/출혈 주의", "warn")
        elif plt < 150: add("혈소판","경계", "warn")
        else: add("혈소판","대체로 양호", "ok")

    if (anc:=v.get("ANC")) is not None:
        if anc < 500: add("ANC","중증 호중구감소(격리/식이 위생 엄격)", "danger")
        elif anc < 1000: add("ANC","호중구감소(감염 주의)", "warn")
        else: add("ANC","대체로 양호", "ok")

    # 전해질/영양/간/신장
    ranges = {
        "Na":(135,145), "K":(3.5,5.1), "Ca":(8.6,10.2), "P":(2.5,4.5),
        "Albumin":(3.5,5.0), "TP":(6.0,8.0), "Glucose":(70,140), # 식후 고려해 상한 완화
        "AST":(0,40), "ALT":(0,40), "LDH":(140,280), "CRP":(0,0.5),
        "Cr":(0.6,1.3), "UA":(3.5,7.2), "TB":(0.0,1.2), "BUN":(7,20)
    }
    for label, key in LAB_ORDER:
        if key in ["WBC","Hb","PLT","ANC","BNP"]: # 이미 처리 또는 선택
            continue
        val = v.get(key)
        if val is None: continue
        if key in ranges:
            low, high = ranges[key]
            if val < low:
                add(key, f"낮음 (기준: {low}~{high})", "warn")
            elif val > high:
                # 일부는 고위험 경고 보정
                if key in ["K","Na","Ca","Cr","TB"] and (abs(val-high) > 0.5 or abs(low-val)>0.5):
                    add(key, f"높음 (기준: {low}~{high})", "danger")
                else:
                    add(key, f"높음 (기준: {low}~{high})", "warn")
            else:
                add(key, f"정상 범위 (기준: {low}~{high})", "ok")
        else:
            add(key, f"{val}", "ok")

    if (bnp:=v.get("BNP")) is not None:
        if bnp >= 100: add("BNP","상승(심기능 저하 가능성, 임상과 함께)", "warn")
        else: add("BNP","대체로 양호", "ok")
    return L

# ------------------------- 음식 예시 추천(수치 기반) -------------------------
FOOD_EXAMPLES = {
    "Albumin_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "Na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "Ca_low": ["연어 통조림", "두부", "케일", "브로콜리", "참깨(제외 시 대체: 아몬드)"],
}

def foods_from_labs(v:Dict[str, Optional[float]])->List[str]:
    rec=[]
    def add(lst): 
        for x in lst: 
            if x not in rec: rec.append(x)
    if (alb:=v.get("Albumin")) is not None and alb < 3.5:
        add(FOOD_EXAMPLES["Albumin_low"])
    if (k:=v.get("K")) is not None and k < 3.5:
        add(FOOD_EXAMPLES["K_low"])
    if (hb:=v.get("Hb")) is not None and hb < 12:
        add(FOOD_EXAMPLES["Hb_low"])
    if (na:=v.get("Na")) is not None and na < 135:
        add(FOOD_EXAMPLES["Na_low"])
    if (ca:=v.get("Ca")) is not None and ca < 8.6:
        add(FOOD_EXAMPLES["Ca_low"])
    return rec[:5] if rec else []

def anc_food_safety(anc: Optional[float])->List[str]:
    if anc is None: return []
    if anc < 1000:
        return [
            "생채소/샐러드 금지, **익힌 음식** 또는 전자레인지 30초 이상 조리",
            "멸균·살균식품 권장, 남은 음식은 2시간 이후 섭취 금지",
            "껍질 있는 과일은 주치의와 상담 후 섭취 여부 결정",
        ]
    return []

# ------------------------- 저장/그래프 -------------------------
if "registered_ids" not in st.session_state: st.session_state.registered_ids=set()
if "history" not in st.session_state: st.session_state.history = {}  # key -> list of dict rows

def save_record(key:str, labs:Dict[str, Optional[float]]):
    row = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    row.update({k:(None if labs.get(k) is None else float(labs.get(k))) for _,k in LAB_ORDER})
    st.session_state.history.setdefault(key, []).append(row)

def plot_trends(key:str):
    data = st.session_state.history.get(key, [])
    if not data or len(data)<1: 
        st.info("아직 저장된 기록이 없습니다.")
        return
    df = pd.DataFrame(data)
    df['ts'] = pd.to_datetime(df['ts'])
    df = df.set_index('ts')
    st.markdown("#### 📈 주요 수치 추이 (WBC, Hb, 혈소판, CRP, ANC)")
    for col in ["WBC","Hb","PLT","CRP","ANC"]:
        if col in df.columns:
            st.line_chart(df[col])

# ------------------------- 보고서 생성 -------------------------
DISCLAIMER = """
본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.
약 변경/복용 중단 등은 반드시 주치의와 상의하세요.
이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.
"""

NO_CELLTHERAPY = "혼돈 방지: 저희는 **세포·면역 치료**(CAR-T, TCR-T, NK, HSCT 등)는 표기하지 않습니다."

def make_report_md(header:str, labs:Dict[str, Optional[float]], lab_lines:List[str],
                   diet_lines:List[str], anc_lines:List[str],
                   drug_block:str, sp_lines:List[str]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = []
    parts.append(f"# {header}")
    parts.append(f"- 생성시각(한국시간): {now}")
    parts.append(f"- 제작: Hoya/GPT | 자문: Hoya/GPT")
    parts.append("")
    if drug_block:
        parts.append("## 암 종류 및 약제 요약")
        parts.append(drug_block)
        parts.append("")
    if labs:
        parts.append("## 입력한 피수치")
        for label, key in LAB_ORDER:
            val = labs.get(key)
            if val is not None:
                parts.append(f"- {label}: {val}")
        parts.append("")
    if lab_lines:
        parts.append("## 자동 해석")
        for ln in lab_lines: parts.append(f"{ln}")
        parts.append("")
    if sp_lines:
        parts.append("## 특수검사 해석")
        for ln in sp_lines: parts.append(f"- {ln}")
        parts.append("")
    if diet_lines or anc_lines:
        parts.append("## 식이가이드 (예시)")
        for ln in diet_lines: parts.append(f"- {ln}")
        for ln in anc_lines: parts.append(f"- {ln}")
        parts.append("")
    parts.append("## 고지/안내")
    parts.append(f"- {NO_CELLTHERAPY}")
    parts.append(f"- {DISCLAIMER}")
    parts.append("")
    parts.append("문의/버그 제보: 네이버 카페에 남겨주세요. (피수치 가이드 공식카페)")
    return "\n".join(parts)

def download_buttons(md_text:str):
    st.markdown("#### ⤵️ 보고서 다운로드")
    # md
    st.download_button("📄 MD 저장", data=md_text.encode("utf-8"), file_name="bloodmap_report.md", mime="text/markdown")
    # txt
    st.download_button("📝 TXT 저장", data=md_text.encode("utf-8"), file_name="bloodmap_report.txt", mime="text/plain")
    # pdf (가능할 때만)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        x, y = 15*mm, height-20*mm
        for line in md_text.split("\n"):
            if y < 20*mm:
                c.showPage()
                y = height-20*mm
            c.drawString(x, y, line[:110])  # 간단 렌더(폰트 한글 미지원 환경 대비)
            y -= 6*mm
        c.save()
        pdf = buf.getvalue()
        st.download_button("📕 PDF 저장", data=pdf, file_name="bloodmap_report.pdf", mime="application/pdf")
    except Exception as e:
        st.caption("PDF 생성 모듈이 없거나 폰트 설정이 없어, PDF 저장은 환경에 따라 비활성화될 수 있습니다.")

# ------------------------- 헤더/별명+PIN -------------------------
st.markdown("### 🩸 피수치 가이드 (BloodMap)")
st.caption("제작 Hoya/GPT · 자문 Hoya/GPT · " + MOBILE_NOTE)
st.info(NO_CELLTHERAPY)

colA, colB = st.columns(2)
with colA:
    nickname = st.text_input("별명", placeholder="예: 하늘이아빠")
with colB:
    pin = st.text_input("PIN (4자리)", placeholder="1234", max_chars=4)

id_ok = bool(nickname.strip()) and pin.isdigit() and len(pin)==4
user_key = f"{nickname.strip()}#{pin}" if id_ok else None

# ------------------------- 모드 선택 -------------------------
mode = st.radio("진단 모드", ["소아 일상/질환", "암 진단"], horizontal=True)

# ------------------------- 소아 모드 -------------------------
if mode == "소아 일상/질환":
    st.markdown("#### 👶 소아 질환 선택")
    dis = st.selectbox("질환", ["로타바이러스", "노로바이러스", "파라인플루엔자", "마이코플라즈마", "열감기"])
    colw, colt = st.columns(2)
    with colw:
        w = st.text_input("체중(kg)", placeholder="예: 15.2")
    with colt:
        t = st.text_input("체온(℃)", placeholder="예: 38.6")
    weight_kg = to_float(w)
    temp_c = to_float(t)

    foods, avoid, tips = peds_diet_guide({"name":dis}, {"weight_kg":weight_kg, "temp_c":temp_c})

    st.markdown("#### 🥣 식이가이드 (예시)")
    if foods: st.markdown("- **예시 음식**: " + ", ".join(foods))
    if avoid: st.markdown("- **피해야 할 예시**: " + ", ".join(avoid))
    if tips:
        st.markdown("**참고 팁**")
        for x in tips: st.markdown(f"- {x}")
    # 복사
    diet_text = "예시 음식: " + ", ".join(foods) + "\n피해야 할 예시: " + ", ".join(avoid) + "\n" + "\n".join(tips)
    copy_button(diet_text, "📋 식이가이드 복사")

    # 선택 시에만 피수치 입력 노출(토글)
    with st.expander("🧪 (선택) 피수치 입력", expanded=False):
        st.caption("선택 시에만 입력란을 보여줍니다.")
        # 간단 5개만 예시 (소아 모듈에서는 수치 입력은 참고용)
        wbc_s = st.text_input("WBC (백혈구)")
        hb_s  = st.text_input("Hb (혈색소)")
        plt_s = st.text_input("혈소판")
        crp_s = st.text_input("CRP")
        anc_s = st.text_input("ANC (호중구)")

    st.markdown("---")
    st.markdown("#### ⚠️ 고지 문구")
    st.code(DISCLAIMER, language="text")
    st.caption("문의/버그 제보: 네이버 카페에 남겨주세요. (피수치 가이드 공식카페)")

# ------------------------- 암 진단 모드 -------------------------
else:
    st.markdown("#### 🧬 암 진단 선택")
    category = st.selectbox("암 카테고리", ["혈액암", "고형암", "육종", "희귀암", "림프종"])
    diag_options = {
        "혈액암": HEME_LIST,
        "고형암": SOLID_LIST,
        "육종": SARCOMA_LIST,
        "희귀암": RARE_LIST,
        "림프종": LYMPHOMA_LIST
    }[category]
    diag_sel = st.selectbox("진단명", diag_options)
    if diag_sel == "직접 입력…":
        diag_sel = st.text_input("진단명 직접 입력 (영어+한글 가능)", placeholder="예: Colorectal adenocarcinoma(대장선암)")    # 약제 "보기용" 자동 제안(항암제/표적/항생제)
    # rec가 정의되지 않아 NameError가 발생했던 문제를 방지하기 위해 바로 위에서 정의합니다.
    rec = drug_reco(category, diag_sel)
    # 👉 전체 섹션을 토글(Expander)로 감쌉니다.
    with st.expander("💊 보기용 약제 제안 (자동)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**항암제**")
            if rec["항암제"]:
                for d in rec["항암제"]:
                    line = "- {name}  
  · 기전: {moa}  
  · 부작용: {se}".format(
                        name=d.get("name", ""), moa=d.get("moa", ""), se=d.get("se", "")
                    )
                    st.markdown(line)
            else:
                st.caption("권장 항암제 정보 없음(진단별 상이)")

        with c2:
            st.markdown("**표적치료제 (Biomarker)**")
            if rec["표적치료제"]:
                for d in rec["표적치료제"]:
                    line = "- {name}  
  · 기전: {moa}  
  · 부작용: {se}".format(
                        name=d.get("name", ""), moa=d.get("moa", ""), se=d.get("se", "")
                    )
                    st.markdown(line)
            else:
                st.caption("표적치료 정보 없음 또는 진단별 상이")

        with c3:
            st.markdown("**자주 쓰는 항생제(진단별)**")
            for d in rec["항생제"]:
                line = "- {name}  
  · 작용: {moa}  
  · 주의: {se}".format(
                    name=d.get("name", ""), moa=d.get("moa", ""), se=d.get("se", "")
                )
                st.markdown(line)

            # ---- 공통 목록(항생제/항진균/스테로이드) 표시 ----
            with st.expander("공통 목록 (항생제/항진균/스테로이드)", expanded=False):
                st.markdown("**항생제 (공통)**")
                for d in COMMON_ABX:
                    line = "- {name}  
  · 작용: {moa}  
  · 주의: {se}".format(
                        name=d.get("name", ""), moa=d.get("moa", ""), se=d.get("se", "")
                    )
                    st.markdown(line)

                st.markdown("**항진균제 (공통)**")
                for d in COMMON_ANTIFUNGALS:
                    line = "- {name}  
  · 작용: {moa}  
  · 주의: {se}".format(
                        name=d.get("name", ""), moa=d.get("moa", ""), se=d.get("se", "")
                    )
                    st.markdown(line)

                st.markdown("**스테로이드/면역억제 (공통)**")
                for d in COMMON_STEROIDS:
                    line = "- {name}  
  · 작용: {moa}  
  · 주의: {se}".format(
                        name=d.get("name", ""), moa=d.get("moa", ""), se=d.get("se", "")
                    )
                    st.markdown(line)

                # 복사 버튼
                blk = []
                for d in COMMON_ABX: blk.append(f"{d['name']} | 작용:{d['moa']} | 주의:{d['se']}")
                blk.append("--- 항진균제 ---")
                for d in COMMON_ANTIFUNGALS: blk.append(f"{d['name']} | 작용:{d['moa']} | 주의:{d['se']}")
                blk.append("--- 스테로이드/면역억제 ---")
                for d in COMMON_STEROIDS: blk.append(f"{d['name']} | 작용:{d['moa']} | 주의:{d['se']}")
                copy_button("
".join(blk), "📋 공통 목록 복사")
            # ---- 공통 목록 끝 ----


    # 안내: 자동 저장/처방 안 함
    st.caption("※ 위 목록은 '보기용 추천'입니다. 자동 저장/처방되지 않으며, 보고서에는 '내가 선택한 약제'만 포함됩니다.")

    # ✍️ 내 선택 약제 (보고서 포함용)
    st.markdown("#### ✍️ 내 선택 약제 (보고서에 포함)")
    sel1, sel2, sel3 = st.columns(3)
    with sel1:
        pick_chemo  = st.multiselect("항암제", [d['name'] for d in rec["항암제"]], default=[])
        pick_target = st.multiselect("표적치료제", [d['name'] for d in rec["표적치료제"]], default=[])
    with sel2:
        pick_abx = st.multiselect("항생제(공통 포함)",
                              [d['name'] for d in rec["항생제"]] + [d['name'] for d in COMMON_ABX],
                              default=[])
    with sel3:
        pick_af = st.multiselect("항진균제(공통)", [d['name'] for d in COMMON_ANTIFUNGALS], default=[])
        pick_st = st.multiselect("스테로이드(공통)", [d['name'] for d in COMMON_STEROIDS], default=[])

    def _find_detail(name):
        pools = [rec["항암제"], rec["표적치료제"], rec["항생제"], COMMON_ABX, COMMON_ANTIFUNGALS, COMMON_STEROIDS]
        for pool in pools:
            for d in pool:
                if d["name"] == name:
                    return d
        return {"name": name, "moa": "-", "se": "-"}

    st.divider()
    st.markdown("#### 🧫 피수치 입력 (항상 표시)")
    st.caption("입력한 항목만 결과에 표시됩니다. (스피너 없이 전부 텍스트)")
    labs = {}
    for label, key in LAB_ORDER:
        labs[key] = to_float(st.text_input(label))

    # 특수검사 (토글)
    st.markdown("### 🧪 특수검사 (토글)")
    with st.expander("펼쳐서 입력하기", expanded=False):
        st.caption("정성: + / ++ / +++  ·  정량: 숫자 입력")
        colA, colB = st.columns(2)
        with colA:
            albq = st.selectbox("알부민뇨", QUAL, index=0)
            hemq = st.selectbox("혈뇨", QUAL, index=0)
            sugq = st.selectbox("요당", QUAL, index=0)
            ketq = st.selectbox("케톤뇨", QUAL, index=0)
            bunq = st.text_input("BUN (mg/dL) - 특수 입력란")  # 메인에도 있지만 예시로 유지
            bnpq = st.text_input("BNP (pg/mL) - 특수 입력란")
            ntpq = st.text_input("NT-proBNP (pg/mL)")
            tniq = st.text_input("Troponin I (ng/mL)")
            ckmbq = st.text_input("CK-MB (ng/mL)")
        with colB:
            c3q  = st.text_input("C3 (mg/dL)")
            c4q  = st.text_input("C4 (mg/dL)")
            ch50q = st.text_input("CH50 (U/mL)")
            tgq  = st.text_input("TG (mg/dL)")
            hdlq = st.text_input("HDL (mg/dL)")
            ldlq = st.text_input("LDL (mg/dL)")
            tcq  = st.text_input("총콜레스테롤 (mg/dL)")
            apobq = st.text_input("ApoB (mg/dL)")
            lpaq  = st.text_input("Lp(a) (mg/dL)")
        sp_q = {"알부민뇨":albq, "혈뇨":hemq, "요당":sugq, "케톤뇨":ketq}
        sp_n = {
            "BUN":bunq, "BNP":bnpq, "NT-proBNP":ntpq,
            "TroponinI":tniq, "CK-MB":ckmbq,
            "C3":c3q, "C4":c4q, "CH50":ch50q,
            "TG":tgq, "HDL":hdlq, "LDL":ldlq, "총콜레스테롤":tcq,
            "ApoB":apobq, "Lp(a)":lpaq
        }

    # 해석 버튼
    if st.button("🧠 해석하기", use_container_width=True):
        lab_lines = interpret_labs(labs)
        sp_lines = interpret_special_tests(sp_q, sp_n)

        # 음식 예시(수치기반) + ANC 식품안전
        diet_list = foods_from_labs(labs)
        anc_safety = anc_food_safety(labs.get("ANC"))

        # 암+약제 요약 블록 (보고서용) — "내가 선택한 약"만 포함
        drug_block_lines = [f"- 진단: **{category} - {diag_sel}**"]

        if pick_chemo:
            drug_block_lines.append("  - 항암제(선택):")
            for name in pick_chemo:
                d = _find_detail(name)
                drug_block_lines.append(f"    - {d['name']} | 기전: {d['moa']} | 부작용: {d['se']}")

        if pick_target:
            drug_block_lines.append("  - 표적치료제(선택):")
            for name in pick_target:
                d = _find_detail(name)
                drug_block_lines.append(f"    - {d['name']} | 기전: {d['moa']} | 부작용: {d['se']}")

        if pick_abx:
            drug_block_lines.append("  - 항생제(선택):")
            for name in pick_abx:
                d = _find_detail(name)
                drug_block_lines.append(f"    - {d['name']} | 작용: {d['moa']} | 주의: {d['se']}")

        if pick_af:
            drug_block_lines.append("  - 항진균제(선택):")
            for name in pick_af:
                d = _find_detail(name)
                drug_block_lines.append(f"    - {d['name']} | 작용: {d['moa']} | 주의: {d['se']}")

        if pick_st:
            drug_block_lines.append("  - 스테로이드/면역억제(선택):")
            for name in pick_st:
                d = _find_detail(name)
                drug_block_lines.append(f"    - {d['name']} | 작용: {d['moa']} | 주의: {d['se']}")

        drug_block = "\n".join(drug_block_lines) if len(drug_block_lines) > 1 else ""

        # 화면 출력
        st.markdown("### ✅ 해석 결과")
        if lab_lines:
            st.markdown("**피수치 해석**")
            for ln in lab_lines: st.markdown(ln)

        if sp_lines:
            st.markdown("**특수검사 해석**")
            for ln in sp_lines: st.markdown(f"- {ln}")

        st.markdown("**식이가이드 (예시)**")
        if diet_list:
            st.markdown("- 좋은 예시: " + ", ".join(diet_list))
        for ln in anc_safety: st.markdown(f"- {ln}")

        # 선택 약제 요약(화면)
        if drug_block:
            st.markdown("**내가 선택한 약제 요약**")
            st.code(drug_block, language="text")

        # 복사 버튼(화면 요약)
        screen_text = []
        screen_text += ["[피수치 해석]"] + [ln for ln in lab_lines]
        if sp_lines: 
            screen_text += ["[특수검사 해석]"] + [ln for ln in sp_lines]
        if diet_list or anc_safety:
            screen_text += ["[식이가이드(예시)]"]
            if diet_list: screen_text += ["좋은 예시: " + ", ".join(diet_list)]
            screen_text += anc_safety
        if drug_block:
            screen_text += ["[선택 약제 요약]", drug_block]
        copy_button("\n".join(screen_text), "📋 화면 결과 복사")

        # 보고서 만들기 + 다운로드 (선택 약제만 포함)
        md_text = make_report_md(
            header="BloodMap 보고서",
            labs=labs,
            lab_lines=lab_lines,
            diet_lines=[("좋은 예시: " + ", ".join(diet_list))] if diet_list else [],
            anc_lines=anc_safety,
            drug_block=drug_block,
            sp_lines=sp_lines
        )
        st.text_area("보고서 미리보기 (MD)", md_text, height=220)
        copy_button(md_text, "📋 보고서 내용 복사")
        download_buttons(md_text)

        # 저장 및 그래프
        st.markdown("---")
        if id_ok:
            # 최초 사용 등록(중복 방지)
            if user_key not in st.session_state.registered_ids:
                st.session_state.registered_ids.add(user_key)
            save_record(user_key, labs)
            st.success("결과가 저장되었습니다. (별명+PIN 기준)")
            plot_trends(user_key)
        else:
            st.warning("별명+PIN이 없으면 자동해석만 제공되고, 저장/그래프는 제공되지 않습니다.")

    st.markdown("---")
    st.markdown("#### ⚠️ 고지 문구")
    st.code(DISCLAIMER, language="text")
    st.caption("문의/버그 제보: 네이버 카페에 남겨주세요. (피수치 가이드 공식카페)")

# ------------------------- 내부 테스트 (선택 실행) -------------------------

def _self_tests():
    # 1) 문자열 조인 및 개행 관련 회귀 테스트
    parts = ["a", "b"]
    joined = "\\n".join(parts)
    assert joined == "a\\nb"

    # 2) DISCLAIMER 삼중따옴표 정상 종료 확인
    assert isinstance(DISCLAIMER, str) and ("본 수치는" in DISCLAIMER)

    # 3) 보고서 생성 기본 흐름
    md = make_report_md(
        header="테스트 리포트",
        labs={"WBC": 3.5, "Hb": 11.0},
        lab_lines=["- Hb: 빈혈 경향 🟡"],
        diet_lines=["좋은 예시: 미음"],
        anc_lines=["생야채 금지"],
        drug_block="- 진단: **혈액암 - APL**\\n  - 항암제(선택):\\n    - ATRA (베사노이드) | 기전: 분화 | 부작용: 두통",
        sp_lines=["C3 낮음"]
    )
    assert "# 테스트 리포트" in md
    assert "## 자동 해석" in md

    # 4) 특수검사 해석 케이스 (보체/지질/심장지표 포함)
    lines = interpret_special_tests(
        {"알부민뇨": "+++", "혈뇨": "+", "요당": "++", "케톤뇨": "+"},
        {"C3": "50", "C4": "10", "CH50": "20", "TG": "250", "HDL": "35", "LDL": "180",
         "총콜레스테롤": "250", "ApoB": "140", "Lp(a)": "60", "BNP": "120", "NT-proBNP": "130",
         "TroponinI": "0.08", "CK-MB": "6"}
    )
    assert any("CH50" in s for s in lines)
    assert any("ApoB" in s for s in lines) or any("Lp(a)" in s for s in lines) or any("Non-HDL" in s for s in lines)
    assert any("NT-proBNP" in s for s in lines) or any("Troponin" in s for s in lines) or any("CK-MB" in s for s in lines)

    # 5) drug_reco 기본 리턴 구조 확인 (rec NameError 방지 관련)
    dr = drug_reco("혈액암", "APL")
    assert isinstance(dr, dict)
    assert all(k in dr for k in ["항암제", "표적치료제", "항생제"])  # 키 누락 없음

# 체크박스로 내부 테스트 실행 (기본 꺼짐)
if st.sidebar.checkbox("🔧 내부 테스트 실행"):
    try:
        _self_tests()
        st.sidebar.success("내부 테스트 통과 ✅")
    except AssertionError as e:
        st.sidebar.error(f"내부 테스트 실패: {e}")
    except Exception as e:
        st.sidebar.error(f"예상치 못한 오류: {e}")
