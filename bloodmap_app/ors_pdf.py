
# -*- coding: utf-8 -*-
"""
p1_ors_pdf.py — P1: ORS 원클릭 PDF 보조 모듈
- pdf_export.export_ors_onepager가 없으면 안전하게 추가합니다.
"""
from __future__ import annotations
from pathlib import Path

def ensure_ors_onepager() -> None:
    try:
        import pdf_export as _pdf
    except Exception:
        return
    if hasattr(_pdf, "export_ors_onepager"):
        return

    def _export_ors_onepager(save_path: str = "/mnt/data/ors_onepager.pdf") -> str:
        # build a simple one-pager from markdown lines
        lines = [
            "# ORS(경구수분보충) / 탈수 가이드",
            "- 5~10분마다 소량씩 자주, 토하면 10~15분 휴식 후 재개",
            "- 2시간 이상 소변 없음 / 입마름 / 눈물 감소 / 축 늘어짐 → 진료",
            "- 가능하면 스포츠음료 대신 ORS 용액 사용",
            "",
            "# ORS 집에서 만드는 법 (WHO 권장 비율, 1 L 기준)",
            "- 끓였다 식힌 물 1 L",
            "- 설탕 작은술 6스푼(평평하게) ≈ 27 g",
            "- 소금 작은술 1/2 스푼(평평하게) ≈ 2.5 g",
            "",
            "- 모두 완전히 녹을 때까지 저어주세요.",
            "- 5~10분마다 소량씩 마시고, 토하면 10~15분 쉬었다 재개하세요.",
            "- 맛은 '살짝 짠 단물(눈물맛)' 정도가 정상입니다. 너무 짜거나 달면 물을 더 넣어 희석하세요.",
            "",
            "# 주의",
            "- 과일주스·탄산·순수한 물만 대량 섭취는 피하세요(전해질 불균형 위험).",
            "- 6개월 미만 영아/만성질환/신생아는 반드시 의료진과 상의 후 사용하세요.",
            "- 설탕 대신 꿀 금지(영아 보툴리누스 위험).",
        ]
        try:
            from pdf_export import export_md_to_pdf
        except Exception:
            return ""
        pdf_bytes = export_md_to_pdf(lines)
        Path(save_path).write_bytes(pdf_bytes)
        return save_path

    # monkey-patch
    setattr(_pdf, "export_ors_onepager", _export_ors_onepager)
