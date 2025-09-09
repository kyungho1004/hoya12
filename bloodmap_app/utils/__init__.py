# -*- coding: utf-8 -*-
"""Utilities facade so that `from utils import user_key, init_state` works."""
from .inputs import collect_basic_inputs  # re-export if needed
from .interpret import interpret_labs, status_color
from .reports import build_markdown_report
from .counter import get_count, bump_count

import streamlit as st
from typing import Dict, Any

def user_key(nickname: str, pin) -> str:
    """Return canonical user key as 'NICK#1234'. Enforce 4-digit pin."""
    if nickname is None:
        nickname = ""
    nickname = str(nickname).strip()
    pin_str = str(pin).zfill(4)[-4:]
    return f"{nickname}#{pin_str}"

def init_state(defaults: Dict[str, Any] | None = None):
    """Initialize streamlit session_state keys once."""
    base = {
        "nickname": "",
        "pin": "",
        "records": {},
        "history": [],
        "view_count": 0,
    }
    if defaults:
        base.update(defaults)
    for k, v in base.items():
        if k not in st.session_state:
            st.session_state[k] = v
