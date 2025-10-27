
# graph_io.py - 그래프/수치 외부저장 래퍼 (패치 방식)
from __future__ import annotations
import os, json, csv

BASE_DIR = "/mnt/data/bloodmap_graph"

def _ensure_dir(path=BASE_DIR):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path

def _safe_uid(uid):
    return "".join(ch for ch in str(uid) if ch.isalnum() or ch in ("-", "_"))

def save(uid, fig=None, df=None, base_dir=BASE_DIR):
    """기존 저장 로직을 건드리지 않고 '추가 저장'만 수행.
    - fig: plotly/matplotlib 등 무엇이든 허용(없어도 됨)
    - df: pandas-like (to_csv 지원) 또는 list[dict]
    반환: (json_path or None, csv_path or None)
    """
    _ensure_dir(base_dir)
    uid_s = _safe_uid(uid or "anonymous")
    json_path = os.path.join(base_dir, f"{uid_s}.json")
    csv_path  = os.path.join(base_dir, f"{uid_s}.labs.csv")

    # fig 저장: plotly figure면 to_dict 사용, 아니면 skip
    try:
        if fig is not None:
            try:
                import plotly.graph_objects as go  # noqa: F401
                data = fig.to_dict()
            except Exception:
                data = None
            if data is not None:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

    # df 저장
    try:
        if df is not None:
            if hasattr(df, "to_csv"):
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            elif isinstance(df, list) and df and isinstance(df[0], dict):
                # best-effort CSV
                keys = sorted({k for r in df for k in r.keys()})
                with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.DictWriter(f, fieldnames=keys)
                    w.writeheader()
                    for r in df:
                        w.writerow(r)
    except Exception:
        pass

    return (json_path if os.path.exists(json_path) else None,
            csv_path if os.path.exists(csv_path) else None)

def load(uid, base_dir=BASE_DIR):
    """외부 저장 파일을 best-effort로 불러오기 (없으면 (None, None))."""
    _ensure_dir(base_dir)
    uid_s = _safe_uid(uid or "anonymous")
    json_path = os.path.join(base_dir, f"{uid_s}.json")
    csv_path  = os.path.join(base_dir, f"{uid_s}.labs.csv")
    data = None
    try:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
    except Exception:
        data = None
    csv_ok = csv_path if os.path.exists(csv_path) else None
    return data, csv_ok
