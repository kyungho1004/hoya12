
# Minimal config for BloodMap package app
# Put this file either at project root as `config.py` or inside the package as `bloodmap_app/config.py`.

PAGE_TITLE = "피수치 가이드 (BloodMap)"
APP_TITLE  = "피수치 가이드 (BloodMap)"
DISCLAIMER = (
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
    "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.\n"
    "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)

# Optional font path for PDF/plot (set to None if not used)
FONT_PATH_REG = None

# If the legacy app expects these optional flags/labels, keep defaults here.
# (Safe to leave as-is — the app should run without editing.)

# Show advanced pediatric block by default
PEDIATRIC_ADVANCED = True

# App behavior toggles
ENABLE_SCHEDULE = True
ENABLE_GRAPH    = True

# Fallback labels (only used if the app references them)
LBL_WBC = "WBC"
LBL_Hb  = "Hb"
LBL_PLT = "PLT"
LBL_ANC = "ANC"
LBL_Ca  = "Ca"
LBL_P   = "P"
LBL_Na  = "Na"
LBL_K   = "K"
LBL_Alb = "Alb"
LBL_Glu = "Glu"
LBL_TP  = "TP"
LBL_AST = "AST"
LBL_ALT = "ALT"
LBL_LDH = "LDH"
LBL_CRP = "CRP"
LBL_Cr  = "Cr"
LBL_UA  = "UA"
LBL_TB  = "TB"
LBL_BUN = "BUN"
LBL_BNP = "BNP"
