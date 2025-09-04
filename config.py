# -*- coding: utf-8 -*-
# ================== App Meta ==================
VERSION = "v3.14.4 (2025-09-04, KST)"
APP_NAME = "피수치 가이드 / BloodMap"
APP_TITLE = "🩸 피수치 가이드 / BloodMap"
PAGE_TITLE = "피수치 가이드 / BloodMap"
MADE_BY = "제작: **Hoya/GPT** · 자문: **Hoya/GPT**"
CAFE_LINK_MD = "🔗 [피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)"
FOOTER_CAFE = "© 2025 BloodMap · 보호자 참고용 — 모든 의학적 판단은 의료진의 권한입니다."
DISCLAIMER = "본 도구는 보호자의 이해를 돕기 위한 참고용입니다. 진단/치료 결정은 반드시 의료진과 상의하세요."

# PDF 폰트 (필요 시 fonts 폴더에 NotoSansKR/NanumGothic 설치 후 경로 지정)
FONT_PATH_REG = "fonts/NanumGothic.ttf"

# ================== Label Constants ==================
LBL_WBC = "WBC(백혈구)"
LBL_Hb  = "Hb(혈색소)"
LBL_PLT = "PLT(혈소판)"
LBL_ANC = "ANC(호중구)"

LBL_Ca  = "Ca(칼슘)"
LBL_P   = "P(인)"
LBL_Na  = "Na(나트륨)"
LBL_K   = "K(칼륨)"

LBL_Alb = "Albumin(알부민)"
LBL_Glu = "Glucose(혈당)"
LBL_TP  = "Total Protein(총단백)"

LBL_AST = "AST"
LBL_ALT = "ALT"
LBL_LDH = "LDH"
LBL_CRP = "CRP"

LBL_Cr  = "Creatinine(Cr)"
LBL_UA  = "Uric Acid(요산)"
LBL_TB  = "Total Bilirubin(TB)"
LBL_BUN = "BUN"
LBL_BNP = "BNP"

# ================== ORDER (기본 20항목 + BNP) ==================
ORDER = [
    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC,
    LBL_Ca, LBL_P, LBL_Na, LBL_K,
    LBL_Alb, LBL_Glu, LBL_TP,
    LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP,
    LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP
]

# ================== Fever Guide (간단 요약) ==================
FEVER_GUIDE = """
- 38.0–38.5℃: 해열제 복용 고려, 수분보충, 경과관찰
- ≥38.5℃: 주치의/병원 연락 권고
- ≥39.0℃ 또는 악화 소견: 즉시 병원 방문 권고
"""

