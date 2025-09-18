
# patch_indent_any_with.py — robust indent fixer for expander blocks
# Usage:
#   python patch_indent_any_with.py app.py
import io, re, sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python patch_indent_any_with.py <target.py>"); return
    p = sys.argv[1]
    with io.open(p, "r", encoding="utf-8") as f:
        s = f.read()

    # Pattern: capture indentation of 'with', then ensure the *next* non-empty line
    # that starts with 'render_antipyretic_schedule_ui(' is indented one level deeper.
    lines = s.splitlines(True)
    out = []
    i = 0
    patched = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.match(r'^([ \t]*)with\s+st\.expander\([^)]*\):\s*\r?\n$', line)
        if m and i+1 < len(lines):
            indent = m.group(1)
            nxt = lines[i+1]
            # If next line is the call and not properly indented, fix it
            if re.match(r'^\s*render_antipyretic_schedule_ui\(', nxt) and not nxt.startswith(indent + '    '):
                # strip leading whitespace then add proper indent
                stripped = nxt.lstrip()
                fixed = indent + '    ' + stripped
                out[-1] = line  # ensure original line preserved
                out.append(fixed)
                i += 2
                patched += 1
                continue
        i += 1

    if patched:
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(''.join(out))
        print(f"Patched {patched} block(s).")
    else:
        print("No changes made. (Pattern not found or already indented)")

if __name__ == "__main__":
    main()
