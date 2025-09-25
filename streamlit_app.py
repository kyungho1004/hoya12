import importlib

# import 시 app.py의 최상위 Streamlit 코드가 실행됩니다.
_app = importlib.import_module("app")

# (선택) 로컬 툴링 호환용 no-op
def main():
    return None

if __name__ == "__main__":
    main()
