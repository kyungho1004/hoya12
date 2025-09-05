# -*- coding: utf-8 -*-
import streamlit as st

def inject_css():
    try:
        with open(st.secrets.get('css_path', 'bloodmap_app/style.css'), 'r', encoding='utf-8') as f:
            st.markdown(f"""<style>{f.read()}</style>""", unsafe_allow_html=True)
    except Exception:
        pass

def section(title:str):
    st.markdown(f"## {title}")

def subtitle(text:str):
    st.markdown(f"<div class='small'>{text}</div>", unsafe_allow_html=True)

def num_input(label:str, key:str, min_value=None, max_value=None, step=None, format=None, placeholder=None):
    return st.number_input(label, key=key, min_value=min_value, max_value=max_value, step=step, format=format if format else None, help=placeholder)

def pin_valid(pin_text:str)->bool:
    return pin_text.isdigit() and len(pin_text) == 4

def warn_banner(text:str):
    st.markdown(f"<span class='badge'>⚠️ {text}</span>", unsafe_allow_html=True)
