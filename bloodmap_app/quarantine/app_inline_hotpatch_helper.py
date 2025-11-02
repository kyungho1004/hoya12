# -*- coding: utf-8 -*-
"""
Inline helper if you prefer to patch inside app.py manually.
"""
def apply_inline_hotpatch(st_module):
    if not hasattr(st_module, "_bm_text_input_orig"):
        st_module._bm_text_input_orig = st_module.text_input
    st_module.text_input = st_module._bm_text_input_orig
    def _BM_TI(*a, **kw):
        return st_module._bm_text_input_orig(*a, **kw)
    return _BM_TI
