"""
Simple plotting helpers with external save path under /mnt/data.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def default_png_path(prefix: str = "fig") -> Path:
    return Path("/mnt/data") / f"{prefix}_{_timestamp()}.png"

def save_fig(fig, path: Optional[str|Path] = None, dpi: int = 180) -> str:
    """
    Save a matplotlib figure to /mnt/data as PNG and return the absolute path.
    - fig: matplotlib.figure.Figure
    - path: optional custom path; if None, an auto timestamped name is used.
    - dpi: image resolution
    """
    p = Path(path) if path else default_png_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(p.as_posix(), dpi=dpi, bbox_inches="tight")
    except Exception:
        # If fig has no savefig (Altair or others), just write nothing.
        # Callers may handle this case.
        return ""
    return p.as_posix()
