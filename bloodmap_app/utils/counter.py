# -*- coding: utf-8 -*-
import streamlit as st

def bump():
    S = st.session_state; S.__dict__.setdefault("_bm_views", 0); S._bm_views += 1

def count():
    return getattr(st.session_state, "_bm_views", 0)
