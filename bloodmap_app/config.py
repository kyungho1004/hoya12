
# -*- coding: utf-8 -*-
APP_TITLE  = "피수치 가이드 (BloodMap)"
APP_URL = "https://bloodmap.streamlit.app/"
PAGE_TITLE = "BloodMap"
MADE_BY    = "제작: Hoya/GPT  |  자문: Hoya/GPT"
CAFE_LINK_MD = "[🔗 피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)"
FOOTER_CAFE  = "ⓒ BloodMap | caregiver-first UX"
DISCLAIMER = (
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.  "
    "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.  "
    "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
FEVER_GUIDE = (
    "• 38.0–38.5℃: 해열제 복용/경과 관찰  \n"
    "• 38.5–39.0℃: 병원 연락 권고  \n"
    "• ≥39.0℃: 즉시 병원 방문 고려  \n"
    "※ ANC 낮음(호중구 감소) 시 생채소 금지, 익힌 음식 권장."
)

# Labels
LBL_WBC = "WBC(백혈구)"
LBL_Hb  = "Hb(혈색소)"
LBL_PLT = "혈소판"
LBL_ANC = "ANC(호중구)"
LBL_Ca  = "칼슘(Ca)"
LBL_P   = "인(P)"
LBL_Na  = "나트륨(Na)"
LBL_K   = "칼륨(K)"
LBL_Alb = "알부민(Alb)"
LBL_Glu = "혈당(Glucose)"
LBL_TP  = "총단백(TP)"
LBL_AST = "AST"
LBL_ALT = "ALT"
LBL_LDH = "LDH"
LBL_CRP = "CRP"
LBL_Cr  = "크레아티닌(Cr)"
LBL_UA  = "요산(UA)"
LBL_TB  = "총빌리루빈(TB)"
LBL_BUN = "BUN"
LBL_BNP = "BNP(선택)"

# Order (UI/Report/Graphs 공통 적용)
ORDER = [
    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC,
    LBL_Ca, LBL_P, LBL_Na, LBL_K,
    LBL_Alb, LBL_Glu, LBL_TP,
    LBL_AST, LBL_ALT, LBL_LDH,
    LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP
]

# Optional: system font path for PDF (if available)
FONT_PATH_REG = None
