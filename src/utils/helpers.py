import sys
from pathlib import Path
from PIL import Image


def norm_intensity(value: int) -> float:
    return max(0.0, min(1.0, value / 255.0))


def thumbnail(image: Image, dim: int = 200) -> Image:
    thumb = image.copy()
    thumb.thumbnail((dim, dim), Image.Resampling.LANCZOS)
    return thumb


def clear_pycache():
    # Don't clear pycache if running as a frozen binary
    if getattr(sys, "frozen", False):
        return

    for pycache_dir in Path(".").rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                for item in pycache_dir.iterdir():
                    item.unlink()
                pycache_dir.rmdir()
            except Exception as e:
                print(f"Failed to remove {pycache_dir}: {e}")
