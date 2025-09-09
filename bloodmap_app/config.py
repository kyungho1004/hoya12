# -*- coding: utf-8 -*-
"""Global configuration for BloodMap."""
APP_NAME = "BloodMap 피수치 가이드"
AUTHOR = "Hoya/GPT"
DISCLAIMER = (
    "본 도구는 보호자의 이해를 돕기 위한 참고용 정보이며, "
    "모든 의학적 판단은 주치의 및 의료진의 판단을 따릅니다."
)
# Keys for session_state
SS_KEYS = {
    "nickname": None,
    "pin": None,
    "records": {},   # key: user_key -> list of lab dicts (timestamped externally by app)
    "history": [],   # latest interpretations
    "view_count": 0,
}
