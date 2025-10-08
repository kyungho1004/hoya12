# -*- coding: utf-8 -*-
"""
qr_patch.py — Runtime-safe helper for QR code generation in Streamlit.
- Tries to import `qrcode`; if missing, attempts a runtime install (qrcode[pil]).
- Exposes: ensure_qrcode(), generate_qr_image(), st_qr().
- Graceful fallback: shows a readable message if install fails.
"""
from __future__ import annotations

import sys, subprocess

def _has_streamlit():
    try:
        import streamlit as st  # noqa: F401
        return True
    except Exception:
        return False

def _st_info(msg: str):
    if _has_streamlit():
        import streamlit as st
        st.info(msg)
    else:
        print(msg)

def _st_warning(msg: str):
    if _has_streamlit():
        import streamlit as st
        st.warning(msg)
    else:
        print("[WARN]", msg)

def ensure_qrcode(quiet: bool = False):
    """
    Ensure the `qrcode` module (with Pillow) is importable.
    Returns the imported module or None if installation fails.
    """
    try:
        import qrcode  # type: ignore
        return qrcode
    except Exception:
        pass

    # Try runtime install
    try:
        if not quiet:
            _st_info("QR 라이브러리가 없어 자동 설치를 시도합니다… (qrcode[pil])")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])
        import qrcode  # type: ignore
        if not quiet:
            _st_info("qrcode 설치 완료 ✅")
        return qrcode
    except Exception as e:
        _st_warning("QR 라이브러리를 찾지 못했습니다. 위 텍스트를 그대로 공유하세요. (선택: requirements에 qrcode 추가)")
        _st_warning(f"(자동 설치 실패 상세: {e})")
        return None

def generate_qr_image(data: str, box_size: int = 8, border: int = 2):
    """
    Return a PIL Image for the QR code of `data`, or None if qrcode is unavailable.
    """
    if not data:
        return None
    qrcode = ensure_qrcode(quiet=True)
    if qrcode is None:
        return None
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # Ensure a PIL.Image is returned even if qrcode returns an image factory wrapper
    try:
        from PIL import Image
        if not isinstance(img, Image.Image):
            img = img.convert("RGB")
    except Exception:
        # If Pillow not fully available, return what we have
        pass
    return img

def st_qr(data: str, caption: str | None = None, box_size: int = 8, border: int = 2):
    """
    Streamlit helper: render QR code or show a graceful fallback message.
    """
    if not _has_streamlit():
        raise RuntimeError("st_qr()는 Streamlit 환경에서만 사용하세요.")
    import streamlit as st
    if not data:
        st.warning("QR로 만들 텍스트가 없습니다.")
        return
    img = generate_qr_image(data, box_size=box_size, border=border)
    if img is None:
        # Fallback text if install/import fails
        st.code(str(data))
        st.caption("QR 라이브러리를 찾지 못했습니다. 위 텍스트를 그대로 공유하세요. (선택: requirements에 qrcode 추가)")
        return
    st.image(img, caption=caption, use_column_width=False)
    st.caption("QR이 보이지 않으면 requirements.txt에 `qrcode`를 추가한 뒤 다시 배포하세요.")
