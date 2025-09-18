
# -*- coding: utf-8 -*-
"""
report_qr.py — 보고서/앱 링크용 QR 유틸
- 외부 라이브러리(qrcode/segno) 없이 Google Chart API를 이용해 PNG QR을 표시합니다.
- Streamlit에서 st.image로 바로 출력하거나, URL만 반환 가능.
"""
from __future__ import annotations
from typing import Optional
import urllib.parse

# 사이즈는 200~1000 권장
def qr_url(data: str, size: int = 220, ec: str = "M") -> str:
    """
    data: QR에 담을 문자열(페이지 URL, 텍스트 등)
    size: 이미지 픽셀 (정사각형)
    ec:   오류복원 (L/M/Q/H)
    """
    base = "https://chart.googleapis.com/chart"
    qs = urllib.parse.urlencode({
        "cht": "qr",
        "chs": f"{int(size)}x{int(size)}",
        "chl": data,
        "chld": f"{ec}|1",
    }, doseq=False, safe=":/?&=#,+-_.!~*'()")
    return f"{base}?{qs}"

def render_qr(st, data: str, size: int = 220, caption: Optional[str] = None) -> None:
    url = qr_url(data, size=size)
    st.image(url, caption=caption or "QR", use_column_width=False)
