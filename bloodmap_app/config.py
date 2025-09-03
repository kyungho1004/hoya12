# -*- coding: utf-8 -*-
import os

APP_TITLE = "🩸 피수치 가이드(보호자님들의울타리) / BloodMap v3.14 (New Site)"
PAGE_TITLE = "피수치 가이드(보호자님들의울타리) / BloodMap"
MADE_BY = "제작·자문: **Hoya/GPT**  ·  © 2025"
CAFE_LINK_MD = "공식 카페: [피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)"
FOOTER_CAFE = "문의·피드백은 공식 카페 이용 바랍니다."
DISCLAIMER = "본 도구는 보호자의 이해를 돕기 위한 참고용 정보이며, 의학적 판단은 반드시 의료진의 책임 하에 이루어져야 합니다."

# 표시 라벨
LBL_WBC="WBC(백혈구)"; LBL_Hb="Hb(혈색소)"; LBL_PLT="혈소판(PLT)"; LBL_ANC="ANC(호중구)"
LBL_Ca="Ca(칼슘)"; LBL_P="P(인)"; LBL_Na="Na(소디움)"; LBL_K="K(포타슘)"
LBL_Alb="Albumin(알부민)"; LBL_Glu="Glucose(혈당)"; LBL_TP="Total Protein(총단백)"
LBL_AST="AST"; LBL_ALT="ALT"; LBL_LDH="LDH"; LBL_CRP="CRP"
LBL_Cr="Creatinine(Cr)"; LBL_UA="Uric Acid(UA)"; LBL_TB="Total Bilirubin(TB)"
LBL_BUN="BUN"; LBL_BNP="BNP"

# 입력/출력 순서
ORDER = [
    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC,
    LBL_Ca, LBL_P, LBL_Na, LBL_K,
    LBL_Alb, LBL_Glu, LBL_TP,
    LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP,
    LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP
]

FEVER_GUIDE = (
"**발열 대응 가이드(보호자용 간단 버전)**  \n"
"- 38.0~38.5℃: 해열제 복용 가능, 수분 보충 후 경과 관찰  \n"
"- 38.5℃ 이상: 병원/주치의에 연락 권고  \n"
"- 39.0℃ 이상: 즉시 병원 방문 권고 (특히 ANC 저하 시)"
)

# 폰트(Reportlab PDF 변환 시 한글 폰트 경로). 런타임에 없는 경우 경고만 출력.
FONT_PATH_REG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "NanumGothic.ttf")
