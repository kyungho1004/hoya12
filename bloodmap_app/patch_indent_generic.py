
# patch_indent_generic.py — fix IndentationError after 'with' statements
# Usage:
#   python patch_indent_generic.py app.py
import io, re, sys

def needs_fix(prev_line, next_line, indent_with='    '):
    # next line must be non-empty, not a comment, and not already indented deeper
    if not next_line.strip():
        return False
    if next_line.lstrip().startswith('#'):
        return False
    prev_indent = len(prev_line) - len(prev_line.lstrip(' \t'))
    next_indent = len(next_line) - len(next_line.lstrip(' \t'))
    return next_indent <= prev_indent

def main():
    if len(sys.argv) < 2:
        print("Usage: python patch_indent_generic.py <target.py>")
        return
    p = sys.argv[1]
    with io.open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out = []
    patched = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if re.match(r'^[ \t]*with\s+.+:\s*\r?\n$', line) and i+1 < len(lines):
            nxt = lines[i+1]
            if needs_fix(line, nxt):
                stripped = nxt.lstrip()
                indent = (len(line) - len(line.lstrip(' \t'))) * ' '
                fixed = indent + '    ' + stripped
                out.append(fixed)
                i += 2
                patched += 1
                continue
        i += 1

    with io.open(p, "w", encoding="utf-8") as f:
        f.writelines(out)

    print(f"Patched blocks: {patched}")

if __name__ == "__main__":
    main()
