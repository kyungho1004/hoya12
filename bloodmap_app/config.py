# -*- coding: utf-8 -*-
"""Global configuration for BloodMap."""
APP_NAME = "BloodMap 피수치 가이드"
AUTHOR = "Hoya/GPT"
DISCLAIMER = (
    "본 도구는 보호자의 이해를 돕기 위한 참고용 정보이며, "
    "모든 의학적 판단은 주치의 및 의료진의 판단을 따릅니다.""⚠️ 철분제와 비타민C를 함께 복용하면 흡수가 촉진됩니다.  
하지만 항암 치료 중이거나 백혈병 환자는 반드시 주치의와 상담 후 복용 여부를 결정해야 합니다."
)
# Keys for session_state
SS_KEYS = {
    "nickname": None,
    "pin": None,
    "records": {},   # key: user_key -> list of lab dicts (timestamped externally by app)
    "history": [],   # latest interpretations
    "view_count": 0,
}
