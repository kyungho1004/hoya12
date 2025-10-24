"""
Small wire-up helpers to keep app.py slim.
"""
from features.explainers import (
    ensure_keyword_explainer_style,
    render_keyword_explainers,
    render_chemo_summary_example,
)
from utils.db_access import concat_ae_text

def apply_keyword_chips(st, drug_db: dict, picked_keys):
    """
    Idempotent wiring:
    - ensure CSS once (safe to call multiple times)
    - concat AE text from selected drugs
    - render chips only when keywords are present
    - render example block (demo)
    """
    try:
        ensure_keyword_explainer_style(st)
        ae_source_text = concat_ae_text(drug_db, picked_keys)
        render_keyword_explainers(st, ae_source_text)
        render_chemo_summary_example(st)
    except Exception:
        # keep UI resilient even if something fails
        pass
