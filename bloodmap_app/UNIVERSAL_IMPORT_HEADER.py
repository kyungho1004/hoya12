# --- Universal Import Header (auto-inserted by fix script) ---
# Works both when run as a package (from streamlit_app.py) and when running app.py directly.
import os, sys
PKG_DIR = os.path.dirname(__file__)
if PKG_DIR and PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

try:
    # Package-relative (preferred)
    from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE, DISCLAIMER, ORDER, FEVER_GUIDE)
    from .app_utils import user_key, init_state
    from .storage import get_user_key as std_key, load_session, append_history
    from .helpers import (compute_acr, compute_upcr, interpret_acr, interpret_upcr,
                          interpret_ast, interpret_alt, interpret_na, interpret_k, interpret_ca,
                          pediatric_guides, build_report_md, build_report_txt, build_report_pdf_bytes)
    from .counter import bump, count
    from . import drug_data
except Exception:
    # Script-relative (fallback)
    from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE, DISCLAIMER, ORDER, FEVER_GUIDE)
    from app_utils import user_key, init_state
    from storage import get_user_key as std_key, load_session, append_history
    from helpers import (compute_acr, compute_upcr, interpret_acr, interpret_upcr,
                         interpret_ast, interpret_alt, interpret_na, interpret_k, interpret_ca,
                         pediatric_guides, build_report_md, build_report_txt, build_report_pdf_bytes)
    from counter import bump, count
    import drug_data
# --- End Universal Import Header ---
