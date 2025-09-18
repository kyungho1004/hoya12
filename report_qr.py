
# -*- coding: utf-8 -*-
"""
report_qr.py — 보고서/앱 링크용 QR 유틸
1) 기본: Google Chart API URL 사용
2) 폴백: 로컬 생성 (qrcode + pillow가 있으면) → 외부망 차단 환경에서도 표시
3) 최후: 이미지 렌더 실패 시 클릭 가능한 링크를 대체 표시
"""
from __future__ import annotations
from typing import Optional
import urllib.parse

def qr_url(data: str, size: int = 220, ec: str = "M") -> str:
    base = "https://chart.googleapis.com/chart"
    qs = urllib.parse.urlencode({
        "cht": "qr",
        "chs": f"{int(size)}x{int(size)}",
        "chl": data,
        "chld": f"{ec}|1",
    }, doseq=False, safe=":/?&=#,+-_.!~*'()")
    return f"{base}?{qs}"

def _local_qr_image_bytes(data: str, size: int = 220):
    # Optional local generator (requires qrcode + pillow)
    try:
        import qrcode
        from io import BytesIO
        qr = qrcode.QRCode(
            version=None,  # auto
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        # resize to approx size
        try:
            from PIL import Image
            w, h = img.size
            scale = max(1, int(size / max(w, h)))
            img = img.resize((w*scale, h*scale), Image.NEAREST)
        except Exception:
            pass
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None

def render_qr(st, data: str, size: int = 220, caption: Optional[str] = None) -> None:
    # 1) Try local first (works offline if qrcode installed)
    png = _local_qr_image_bytes(data, size=size)
    if png:
        st.image(png, caption=caption or "QR", use_container_width=False)
        return
    # 2) Try remote URL (may fail if 외부망 차단)
    url = qr_url(data, size=size)
    try:
        st.image(url, caption=caption or "QR", use_container_width=False)
    except Exception:
        # 3) Final fallback: show link instead of a broken image
        st.markdown(f"[{caption or '열기'}]({data})")
