# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, timezone, timedelta

def kst_now():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

def render_er_md(summary: dict, care_txt: str) -> str:
    # summary keys expected: risk, triage, key_findings(list), vitals(str), labs_md(str)
    lines = []
    lines.append(f"# ER One-Page — {kst_now()}")
    lines.append("")
    lines.append(f"## 🆘 응급도: **{summary.get('risk','N/A')}** / 분류: **{summary.get('triage','N/A')}**")
    if summary.get("key_findings"):
        lines.append("### 주요 소견")
        for s in summary["key_findings"]:
            lines.append(f"- {s}")
    if summary.get("vitals"):
        lines.append("### 활력징후")
        lines.append(summary["vitals"])
    if summary.get("labs_md"):
        lines.append("### 최근 검사 요약")
        lines.append(summary["labs_md"])
    lines.append("### 최근 24h 케어로그")
    lines.append(care_txt or "(기록 없음)")
    return "\n".join(lines)
