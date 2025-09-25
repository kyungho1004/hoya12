import streamlit as st
st.set_page_config(page_title="Bloodmap — Safe Boot", layout="wide")
st.title("Bloodmap — Safe Boot")

# Import smoke tests
ok = []
def try_import(name):
    try:
        __import__(name)
        ok.append((name, True))
    except Exception as e:
        ok.append((name, False))
        st.error(f"임포트 실패: {name} → {e}")

for m in ["branding","special_tests","lab_diet","onco_map","drug_db","ui_results","pdf_export"]:
    try_import(m)

st.subheader("임포트 결과")
for name, passed in ok:
    st.write(f"- {name}: {'OK' if passed else 'FAIL'}")

st.success("앱 부팅 스텝 OK — 무한로딩이면, 이 화면도 안 떠요.")
