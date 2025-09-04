# -*- coding: utf-8 -*-
import streamlit as st
from bloodmap_app.app import main

def _banner():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered", initial_sidebar_state="collapsed")
    st.write("")

if __name__ == "__main__":
    _banner()
    main()
