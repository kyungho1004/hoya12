
import streamlit as st
from hoya12.bloodmap_app.app import main

if __name__ == "__main__":
    st.set_page_config(page_title="피수치 해석기", layout="wide")
    main()
