
# -*- coding: utf-8 -*-
"""
report_sections.py
- 보고서 공통 섹션 조립기
"""
from typing import Dict, List

def sec_header(ctx: Dict) -> str:
    who = ctx.get("who") or ctx.get("mode") or ""
    nick = ctx.get("nickname") or ""
    lines = [f"# BloodMap 보고서"]
    if nick: lines.append(f"- 별명: {nick}")
    lines.append(f"- 모드: {who}")
    lines.append("")
    return "\n".join(lines)

def sec_diet(diet_lines: List[str] | None) -> str:
    diet = diet_lines or []
    body = "\n## 🍽️ 식이가이드\n"
    if diet:
        body += "\n".join(f"- {L}" for L in diet)
    else:
        body += "- (입력값 기준 맞춤 식이가이드는 없습니다)"
    return body

def sec_peds_short(short_line: str | None) -> str:
    if not short_line: short_line = ""
    return "\n## ℹ️ 짧은 해석\n- " + short_line

def sec_safety(alerts: List[str] | None) -> str:
    alerts = alerts or []
    if not alerts:
        return "\n## 🚦 안전 플래그\n- (특이 경고 없음)"
    return "\n## 🚦 안전 플래그\n" + "\n".join(f"- {a}" for a in alerts)
