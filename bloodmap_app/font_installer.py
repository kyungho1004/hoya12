# -*- coding: utf-8 -*-
import os, requests
FONT_URLS = {
    "NotoSansKR-Regular.ttf": "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansKR-Regular.otf",
    "NanumGothic.ttf": "https://github.com/googlefonts/nanum-gothic/raw/main/fonts/ttf/NanumGothic-Regular.ttf",
}
def ensure_fonts(font_dir: str) -> dict:
    os.makedirs(font_dir, exist_ok=True)
    result = {}
    for fname, url in FONT_URLS.items():
        path = os.path.join(font_dir, fname)
        if os.path.exists(path) and os.path.getsize(path) > 50000:
            result[fname] = "skipped"; continue
        try:
            resp = requests.get(url, stream=True, timeout=30); resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    if chunk: f.write(chunk)
            result[fname] = "ok" if os.path.getsize(path) > 50000 else "error:too_small"
        except Exception as e:
            result[fname] = f"error:{e}"
    return result
