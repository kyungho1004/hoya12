# Short Caption Integration Guide

## What you got
- `short_caption.py`: defines `short_caption(name)` with safe defaults.
- `app_patched.py`: your `app.py` with the function **prepended** to avoid `NameError`. Status: patched_created.

## Quick use (Option A: paste function)
1) Open your `app.py`.
2) Paste the whole function block at the top (after imports is fine).
3) Deploy.

## Clean use (Option B: separate module)
1) Put `short_caption.py` next to `app.py` in your app repository.
2) Add this line near the top of `app.py`:
   ```python
   from short_caption import short_caption
   ```
3) Ensure your calls like `short_caption(disease)` keep working.

## Notes
- The function has **no external dependencies** and returns a safe generic line if it sees an unknown label.
- Korean spacing and punctuation were checked for consistency.
- If you already call `st.caption(short_caption(...))` or use it in reports, this fixes the `NameError` immediately.
