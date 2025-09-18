
# patch_indent_fix.py — fix IndentationError after "with st.expander(...)"
# Usage:
#   python patch_indent_fix.py app.py
import sys, re, io

def main():
    if len(sys.argv) < 2:
        print("Usage: python patch_indent_fix.py <target.py>"); return
    p = sys.argv[1]
    with io.open(p, "r", encoding="utf-8") as f:
        s = f.read()

    # Find "with st.expander(...):\n<NON-INDENTED>render_antipyretic_schedule_ui(...)"
    def repl(m):
        indent = m.group("indent")
        call = m.group("call")
        # ensure one level indent (4 spaces) relative to 'with'
        return f'{indent}with st.expander("⏱️ 해열제 스케줄표", expanded=False):\n{indent}    {call}'

    pat = re.compile(r'(?P<indent>^[ \t]*)with st\.expander\(\s*["\']⏱️ 해열제 스케줄표["\']\s*,\s*expanded=False\s*\):\s*\n(?P<call>render_antipyretic_schedule_ui\(.*?\))', re.M)
    s2, n = pat.subn(repl, s)

    if n == 0:
        print("No target pattern found. No changes made.")
    else:
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(s2)
        print(f"Patched {n} location(s).")

if __name__ == "__main__":
    main()
