"""
Keyword explainer utilities.
Default: delegate to ui_results implementations (backward compatible).
Fallback: use local minimal implementation + features.explainer_rules when needed.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
import re

# --- Backward-compatible delegates ---
try:
    from ui_results import (
        ensure_keyword_explainer_style as _ensure_style_upstream,
        render_keyword_explainers as _render_upstream,
        get_chemo_summary_example_md as _example_md_upstream,
        render_chemo_summary_example as _example_upstream,
    )
except Exception:
    _ensure_style_upstream = None
    _render_upstream = None
    _example_md_upstream = None
    _example_upstream = None

# --- Local minimal implementations (fallback only) ---
def ensure_keyword_explainer_style(st):
    css = """
    <style>
      .keyword-explainers { margin: .5rem 0; display:flex; flex-wrap:wrap; gap:.5rem; }
      .explain-chip { padding:.35rem .6rem; border-radius:10px; background:#f6f7fb; border:1px solid #e6e8f0; font-size:.9rem; }
    </style>
    """
    try:
        if _ensure_style_upstream:
            _ensure_style_upstream(st)
        else:
            st.markdown(css, unsafe_allow_html=True)
    except Exception:
        pass

def _local_rules() -> List[Dict[str, Any]]:
    try:
        from features.explainer_rules import RULES
        return RULES
    except Exception:
        return []

def render_keyword_explainers(st, text: Optional[str]):
    # If upstream renderer exists, use it (non-breaking default)
    if _render_upstream:
        try:
            return _render_upstream(st, text)
        except Exception:
            # fall through to local rendering
            pass
    raw = (text or "").strip()
    if not raw:
        return
    s = re.sub(r"`{3}.*?`{3}", " ", raw, flags=re.DOTALL)
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"https?://\S+|www\.\S+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    rules = _local_rules()
    if not rules:
        return  # no local rules configured

    matched_html: List[str] = []
    for rule in rules:
        for ptn in rule.get("patterns", []):
            flags = re.IGNORECASE if isinstance(ptn, str) and ptn.startswith("(?i)") else 0
            if re.search(ptn, s, flags=flags):
                matched_html.append(rule.get("html", ""))
                break
        if len(matched_html) >= 4:
            break
    if not matched_html:
        return
    try:
        st.markdown("<div class='keyword-explainers'>"+"".join(matched_html)+"</div>", unsafe_allow_html=True)
    except Exception:
        pass

def get_chemo_summary_example_md() -> str:
    if _example_md_upstream:
        try:
            return _example_md_upstream()
        except Exception:
            pass
    return (
        "## 항암제 요약 (영/한 + 부작용)\n\n"
        "### Sunitinib (수니티닙)\n"
        "- **일반**: ...\n"
        "- **중증**: ...\n"
        "- **연락 필요**: ...\n\n"
        "### 용어 풀이(요약)\n"
        "- **QT 연장**: ...\n"
        "- **손발증후군**: ...\n"
    )

def render_chemo_summary_example(st):
    if _example_upstream:
        try:
            return _example_upstream(st)
        except Exception:
            pass
    st.markdown(get_chemo_summary_example_md())
