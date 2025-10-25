"""
Feedback panel: minimal, non-intrusive UI.
- Keeps existing flows intact (expander + local import)
- Writes CSV to /mnt/data/feedback/feedback.csv (append-only, safe)
"""
from __future__ import annotations
from typing import Optional
import os, csv
from datetime import datetime

FB_DIR = "/mnt/data/feedback"
FB_CSV = f"{FB_DIR}/feedback.csv"

def _ensure_dir():
    try:
        os.makedirs(FB_DIR, exist_ok=True)
    except Exception:
        pass

def _append_csv(ts: str, rating: Optional[int], text: str):
    try:
        _ensure_dir()
        header = ["timestamp", "rating", "text"]
        exists = os.path.exists(FB_CSV)
        with open(FB_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(header)
            w.writerow([ts, rating if rating is not None else "", text or ""])
    except Exception:
        pass

def render_feedback_panel(st):
    """Non-breaking feedback UI. Safe to call multiple times."""
    try:
        with st.expander("피드백 (도움이 되었나요?)", expanded=False):
            cols = st.columns([1,1,1,4])
            rating = None
            with cols[0]:
                if st.button("👍 5점", key="fb_5"):
                    rating = 5
            with cols[1]:
                if st.button("🙂 4점", key="fb_4"):
                    rating = 4
            with cols[2]:
                if st.button("😐 3점", key="fb_3"):
                    rating = 3

            txt = st.text_input("코멘트(선택)", key="fb_text")
            if st.button("제출", key="fb_submit"):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                _append_csv(ts, rating, txt)
                st.success("피드백이 저장되었습니다. 고맙습니다!")
                if os.path.exists(FB_CSV):
                    st.caption(f"저장 위치: {FB_CSV}")
    except Exception:
        pass
