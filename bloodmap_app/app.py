
import os, re, sys, datetime

APP_DIR = "/mount/src/hoya12/bloodmap_app"
APP_FILE = os.path.join(APP_DIR, "app.py")

def backup(path):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path + f".bak.{ts}"
    with open(path, "rb") as f_in, open(b, "wb") as f_out:
        f_out.write(f_in.read())
    return b

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save(path, s):
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)

def ensure_sidebar_banner(s):
    # Add a simple banner once near the top after `import streamlit as st`
    banner = '\nst.sidebar.success("✅ 해열제 기록 패널 주입 시도 — PROD PATCH")\n'
    if "import streamlit as st" in s and "해열제 기록 패널 주입 시도" not in s:
        s = s.replace("import streamlit as st", "import streamlit as st" + banner, 1)
    return s

def ensure_import_block(s):
    block = (
        "\n# --- Antipyretic log (fail-safe import) [PROD PATCH] ---\n"
        "try:\n"
        "    from onco_antipyretic_log import render_onco_antipyretic_log\n"
        "except Exception:\n"
        "    def render_onco_antipyretic_log(*args, **kwargs):\n"
        "        import streamlit as st\n"
        "        st.info(\"onco_antipyretic_log 모듈을 찾을 수 없습니다.\")\n"
    )
    if "render_onco_antipyretic_log" in s:
        return s
    # Insert after pdf_export import if present, else after "import streamlit as st"
    if "from pdf_export import export_md_to_pdf" in s:
        s = s.replace("from pdf_export import export_md_to_pdf", "from pdf_export import export_md_to_pdf" + block, 1)
    elif "import streamlit as st" in s:
        s = s.replace("import streamlit as st", "import streamlit as st" + block, 1)
    else:
        s = block + s
    return s

def inject_after_schedule_block(s):
    if "render_onco_antipyretic_log(" in s:
        return s, False
    # Find first "schedule_block()" and its indentation
    m = re.search(r'^(?P<indent>\s*)schedule_block\(\)\s*$', s, flags=re.M)
    if not m:
        return s, False
    indent = m.group("indent")
    inject = (
        "\n{indent}# 🌡️ 해열제 복용 기록(ml 통일) — 한국시간 [PROD PATCH]\n"
        "{indent}render_onco_antipyretic_log(storage_key=\"onco_antipyretic_log\")\n"
    ).format(indent=indent)
    s = s.replace(m.group(0), m.group(0) + inject, 1)
    return s, True

def main():
    if not os.path.isfile(APP_FILE):
        print("ERR: app.py not found at", APP_FILE)
        sys.exit(2)
    s = load(APP_FILE)
    bak = backup(APP_FILE)
    s = ensure_sidebar_banner(s)
    s = ensure_import_block(s)
    s, injected = inject_after_schedule_block(s)
    save(APP_FILE, s)
    print("OK: patched app.py")
    print("Backup:", bak)
    print("Injected under schedule_block():", injected)

if __name__ == "__main__":
    main()
