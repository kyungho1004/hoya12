# streamlit_app.py — Entry point wrapper
# Community Cloud가 기본으로 찾는 파일명입니다.
# 실제 UI/로직은 app.py에 있고, 여기서는 그걸 import만 해 실행됩니다.

import importlib

# import 시 app.py의 최상위 Streamlit 코드가 실행됩니다.
_app = importlib.import_module("app")

# (선택) 로컬 툴링 호환용 no-op
def main():
    return None

if __name__ == "__main__":
    main()
