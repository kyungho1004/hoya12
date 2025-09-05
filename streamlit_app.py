
import os, sys, streamlit as st

# ensure current folder on sys.path for local 'bloodmap_app'
CUR = os.path.dirname(__file__)
if CUR and CUR not in sys.path:
    sys.path.insert(0, CUR)

# try local-relative import first, then package-style
try:
    from bloodmap_app.app import main
except ModuleNotFoundError:
    try:
        from hoya12.bloodmap_app.app import main
    except ModuleNotFoundError:
        st.error("모듈을 찾을 수 없습니다. 폴더 구조를 확인하세요: hoya12/bloodmap_app/app.py")

if __name__ == "__main__":
    st.set_page_config(page_title="피수치 해석기", layout="wide")
    main()
