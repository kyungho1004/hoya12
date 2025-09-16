
# Hotfix — Antipyretic Schedule Clear
- `bundle_addons_hotfix.py` contains a replacement for `ui_antipyretic_card`.
- Replace the function in your `bundle_addons.py` or import this hotfix and swap the call:
  ```python
  from bundle_addons_hotfix import ui_antipyretic_card  # overrides
  ```
This makes the schedule stored in `st.session_state['antipy_sched']` and rendered from it.
Pressing **초기화** now removes it from state, so the table disappears immediately.
