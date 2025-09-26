# pathsafe.py — safe data dir + atomic JSON write (drop-in)
from __future__ import annotations
import os, json, tempfile
from pathlib import Path
from typing import Tuple, Any

def _pick_base_dir() -> str:
    # Priority: env → /mnt/data → /mount/data → ~/.local/share/bloodmap → ./data → temp
    env = os.environ.get("BLOODMAP_DATA_DIR")
    candidates = [env] if env else []
    candidates += ["/mnt/data", "/mount/data",
                   str(Path.home()/".local/share/bloodmap"),
                   str(Path.cwd()/ "data"),
                   str(Path(tempfile.gettempdir())/ "bloodmap")]
    for base in candidates:
        try:
            p = Path(base); p.mkdir(parents=True, exist_ok=True)
            tf = p/".write_test"
            with open(tf, "w") as f: f.write("ok")
            tf.unlink(missing_ok=True)
            return str(p)
        except Exception:
            continue
    return str(Path.cwd())

def resolve_data_dirs() -> tuple[str,str,str,str]:
    base = _pick_base_dir()
    SAVE_DIR = str(Path(base)/"bloodmap_graph")
    CARE_DIR = str(Path(base)/"care_log")
    PROF_DIR = str(Path(base)/"profile")
    MET_DIR  = str(Path(base)/"metrics")
    for d in (SAVE_DIR, CARE_DIR, PROF_DIR, MET_DIR):
        Path(d).mkdir(parents=True, exist_ok=True)
    return SAVE_DIR, CARE_DIR, PROF_DIR, MET_DIR

def safe_json_write(path: str, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, p)

def safe_json_read(path: str, default):
    p = Path(path)
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default