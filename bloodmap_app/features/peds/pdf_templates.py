"""
PDF templates builder — returns element arrays that pdf_export.save_pdf or exporters can consume.
Footer includes: "Made with 💜 for Eunseo — Hoya/GPT (자문: Hoya/GPT)"
"""
from __future__ import annotations

FOOTER = "Made with 💜 for Eunseo — Hoya/GPT (자문: Hoya/GPT)"

def _kv_table(d: dict) -> list[tuple]:
    els = []
    for k, v in d.items():
        els.append(("p", f"{k}: {v}"))
    return els

def build(template: str, ctx: dict | None = None) -> list[tuple]:
    ctx = ctx or {}
    t = template.lower().strip()
    els = []
    if t == "er_onepage":
        title = ctx.get("title") or "ER 원페이지 요약"
        els.append(("h1", title))
        # vitals / key fields
        info = {
            "이름(별명)": ctx.get("nickname","-"),
            "나이(개월)": ctx.get("age_m","-"),
            "체중(kg)": ctx.get("wt_kg","-"),
            "발열(°C)": ctx.get("fever","-"),
            "증상": ", ".join(ctx.get("symptoms", [])) or "-",
        }
        els += _kv_table(info)
        # lab snapshot
        labs = ctx.get("labs") or {}
        if labs:
            els.append(("h2", "주요 검사"))
            for k, v in labs.items():
                els.append(("p", f"{k}: {v}"))
        # guardlines
        els.append(("h2", "연락/내원 기준"))
        els.append(("ul", [
            "38.5°C 이상 지속 또는 39.0°C 이상 시 즉시 연락/내원",
            "실신/심한 어지러움/호흡곤란/의식저하 발생 시 즉시 내원",
            "혈변·검은변/탈수 의심(소변 감소·눈물 감소·축 늘어짐) 시 연락",
        ]))
        # meds
        if ctx.get("drugs"):
            els.append(("h2", "현재 항암/약물"))
            els.append(("ul", list(map(str, ctx.get("drugs")))))
        els.append(("hr", ""))
        els.append(("p", FOOTER))
    else:
        # default simple
        title = ctx.get("title") or "요약"
        els = [("h1", title), ("p", ctx.get("summary","")), ("hr",""), ("p", FOOTER)]
    return els
