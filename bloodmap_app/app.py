# --- Hotfix: safe imports (works as package OR script) ---
try:
    # Package-relative (recommended when launched via: streamlit run streamlit_app.py)
    from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE, DISCLAIMER,
                         ORDER, FEVER_GUIDE)
    from .utils import user_key, init_state
    from .storage import get_user_key as std_key, load_session, append_history
    from .helpers import (compute_acr, compute_upcr, interpret_acr, interpret_upcr,
                          interpret_ast, interpret_alt, interpret_na, interpret_k, interpret_ca,
                          pediatric_guides, build_report_md, build_report_txt, build_report_pdf_bytes)
    from .counter import bump, count
    from . import drug_data
except Exception:
    # Script-relative (when launched via: streamlit run bloodmap_app/app.py)
    from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE, DISCLAIMER,
                        ORDER, FEVER_GUIDE)
    from utils import user_key, init_state
    from storage import get_user_key as std_key, load_session, append_history
    from helpers import (compute_acr, compute_upcr, interpret_acr, interpret_upcr,
                         interpret_ast, interpret_alt, interpret_na, interpret_k, interpret_ca,
                         pediatric_guides, build_report_md, build_report_txt, build_report_pdf_bytes)
    from counter import bump, count
    import drug_data
# --- End Hotfix ---
