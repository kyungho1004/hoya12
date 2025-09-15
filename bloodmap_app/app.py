# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date

from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml
from pdf_export import export_md_to_pdf

# ---------------- 초기화 ----------------
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="BloodMap — 피수치가이드", page_icon="🩸", layout="centered")
st.title("BloodMap — 피수치가이드")

# 고지 + 즐겨찾기 + 체온계 + 카페
st.info(
    "이 앱은 의료행위가 아니며, **참고용**입니다. 진단·치료를 **대체하지 않습니다**.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
    "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.\n\n"
    "⭐ **즐겨찾기**: 특수검사 제목 옆의 ★ 버튼을 누르면 상단 '즐겨찾기' 칩으로 고정됩니다.\n"
    "🏠 가능하면 **가정용 체온계**로 측정한 값을 입력하세요."
)
st.markdown("문의/버그 제보는 **[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)** 를 이용해주세요.")

nick, pin, key = nickname_pin()
st.divider()
has_key = bool(nick and pin and len(pin) == 4)

# ---------------- 유틸 ----------------
def _fever_bucket_from_temp(temp: float) -> str:
    if temp is None or temp < 37.0: return "없음"
    if temp < 37.5: return "37~37.5"
    if temp < 38.0: return "37.5~38"
    if temp < 38.5: return "37.5~38"
    if temp < 39.0: return "38.5~39"
    return "39+"

def _peds_diet_fallback(sym: dict, disease: str|None=None) -> list[str]:
    tips = []
    temp = (sym or {}).get("체온", 0) or 0
    symptom_days = int((sym or {}).get("증상일수", 0) or 0)
    diarrhea = (sym or {}).get("설사", "")
    if symptom_days >= 2:
        tips.append("증상 2일 이상 지속 → 수분·전해질 보충(ORS) 및 탈수 관찰")
    if diarrhea in ["4~6회","7회 이상"]:
        tips.append("기름지고 자극적인 음식 제한, 바나나·쌀죽·사과퓨레·토스트(BRAT) 참고")
    if temp >= 38.5:
        tips.append("체온 관리: 얇게 입히고 미온수 보온, 해열제는 1회분만 사용")
    tips.append("식사는 소량씩 자주, 구토 시 30분 쉬었다가 맑은 수분부터 재개")
    if disease:
        if disease in ["로타","장염","노로"]:
            tips.append("설사 멎을 때까지 유제품·과일주스는 줄이기")
        if disease in ["편도염","아데노"]:
            tips.append("따뜻한 수분·연식(죽/수프)으로 목 통증 완화")
    return tips

def _safe_label(k):
    try:
        return display_label(k)
    except Exception:
        return str(k)

def _filter_known(keys):
    return [k for k in (keys or []) if k in DRUG_DB]


def _one_line_selection(ctx: dict) -> str:
    def names(keys):
        return ", ".join(_safe_label(k) for k in _filter_known(keys))
    parts = []
    a = names(ctx.get("user_chemo"))
    if a: parts.append(f"항암제: {a}")
    b = names(ctx.get("user_targeted"))
    if b: parts.append(f"표적/면역: {b}")
    c = names(ctx.get("user_abx"))
    if c: parts.append(f"항생제: {c}")
    return " · ".join(parts) if parts else "선택된 약물이 없습니다."

_PEDS_NOTES = {
    "RSV": "모세기관지염: 아기 하기도에 가래가 끼고 배출이 어려워 쌕쌕/호흡곤란이 생길 수 있어요.",
    "로타": "로타바이러스 장염: 구토·물설사로 탈수 위험, ORS로 수분 보충이 중요해요.",
    "노로": "노로바이러스 장염: 집단 유행, 구토가 두드러지며 철저한 손위생이 중요해요.",
    "독감": "인플루엔자: 갑작스런 고열·근육통, 48시간 내 항바이러스제 고려가 돼요.",
    "아데노": "아데노바이러스: 결막염/인두염/장염 등 다양한 증상, 고열이 오래갈 수 있어요.",
    "마이코": "마이코플라즈마: 마른기침이 오래가며 비정형폐렴 가능, 항생제 필요 여부는 진료로 확인하세요.",
    "수족구": "수족구병: 손·발·입 수포/궤양 + 열, 탈수 주의. 대개 대증치료로 호전돼요.",
    "편도염": "편도염/인후염: 목통증·고열, 세균성 의심 시 항생제를 쓰기도 해요.",
    "코로나": "코로나19: 발열·기침·인후통, 고위험군은 모니터링과 격리 수칙이 중요해요.",
    "중이염": "급성 중이염: 귀통증·열, 진찰 결과에 따라 진통제/항생제 여부를 결정해요.",
}
def disease_short_note(name: str) -> str:
    return _PEDS_NOTES.get(name, "")

def _export_buttons(md: str, txt: str):
    st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
    st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")
    try:
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("⬇️ PDF (.pdf)", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf")
    except Exception as e:
        st.caption(f"PDF 변환 중 오류: {e}")



def _export_report(ctx: dict, lines_blocks=None):
    footer = (
        "\n\n---\n"
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.\n"
        "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.\n"
        "버그/문의는 [피수치 가이드 공식카페](https://cafe.naver.com/bloodmap) 를 통해 해주세요.\n"
    )
    title = f"# BloodMap 결과 ({ctx.get('mode','')})\n\n"
    body = []

    # 공통 요약
    if ctx.get("mode") == "암":
        body.append(f"- 카테고리: {ctx.get('group')}")
        body.append(f"- 진단: {ctx.get('dx_label') or ctx.get('dx')}")
    if ctx.get("mode") in ["소아","일상"]:
        body.append(f"- 대상: {ctx.get('who','소아')}")
        if ctx.get("symptoms"):
            symp_text = "; ".join(f"{k}:{v}" for k, v in ctx["symptoms"].items() if v not in [None, ""])
            if symp_text:
                body.append(f"- 증상: {symp_text}")
        if ctx.get("preds"):
            preds_text = "; ".join(f"{p['label']}({p['score']})" for p in ctx["preds"])
            body.append(f"- 자동 추정: {preds_text}")
    if ctx.get("triage"):
        body.append(f"- 트리아지: {ctx['triage']}")
    if ctx.get("labs"):
        labs_t = "; ".join(f"{k}:{v}" for k,v in ctx["labs"].items() if v is not None)
        if labs_t:
            body.append(f"- 주요 수치: {labs_t}")

    # 특수검사/부작용 등 라인 블록
    if lines_blocks:
        for title2, lines in lines_blocks:
            if lines:
                body.append("\n## " + str(title2) + "\n" + "\n".join(f"- {L}" for L in lines))

    # 식이가이드 & 짧은 해석
    if ctx.get("diet_lines"):
        diet = [str(x) for x in ctx["diet_lines"] if x]
        if diet:
            body.append("\n## 🍽️ 식이가이드\n" + "\n".join(f"- {L}" for L in diet))
    if ctx.get("short_note"):
        body.append("\n## ℹ️ 짧은 해석\n- " + str(ctx["short_note"]))

    # 암 모드: 선택 요약(한 줄)
    if ctx.get("mode") == "암":
        if '_one_line_selection' in globals():
            summary = _one_line_selection(ctx)
        else:
            summary = None
        if summary:
            body.append("\n## 🗂️ 선택 요약\n- " + summary)

    md = title + "\n".join(body) + footer
    txt = md
    return md, txt
