# -*- coding: utf-8 -*-
"""Pediatric module: fever & antipyretic dosing skeleton."""

TEMP_GUIDE = [
    ("38.0~38.5", "해열제 가능, 경과관찰"),
    ("38.5~39.0", "해열제 투여 + 보호자 연락/병원 문의 고려"),
    ("39.0 이상", "즉시 병원 연락"),
]

def calc_antipyretic_dose(weight_kg: float, drug: str = "acetaminophen"):
    """Return (single_dose_mg, max_times_per_day, note)."""
    drug = drug.lower()
    if drug in ("acetaminophen", "paracetamol", "apap", "타이레놀", "아세트아미노펜"):
        # 10–15 mg/kg/dose, q4–6h, max 5 times
        return (round(weight_kg * 12.5), 5, "아세트아미노펜 10–15 mg/kg/회, 4–6시간 간격")
    if drug in ("ibuprofen", "이부프로펜"):
        # 5–10 mg/kg/dose, q6–8h, max 4 times
        return (round(weight_kg * 7.5), 4, "이부프로펜 5–10 mg/kg/회, 6–8시간 간격")
    return (0, 0, "지원하지 않는 해열제")
