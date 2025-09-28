from PIL import Image


def norm_intensity(value: int) -> float:
    return max(0.0, min(1.0, value / 255.0))


def thumbnail(image: Image, dim: int = 200) -> Image:
    thumb = image.copy()
    thumb.thumbnail((dim, dim), Image.Resampling.LANCZOS)
    return thumb
