from dataclasses import dataclass
from PIL import ImageDraw


@dataclass
class SepSpec:
    tones: dict[str, tuple[int, int, int]]
    threshold: int = 30
    substrate: tuple = (255, 255, 255)


@dataclass
class HalftoneSpec:
    lpi: int = 55
    dpi: int = 1200
    ppi: int | None = None
    angle: float = 0.0
    modulate: bool = True
    hardmix: bool = False
    threshold: int = 127
    gain: float = 0.0


@dataclass
class DotSpec:
    canvas: ImageDraw
    center: tuple[float, float]
    size: float
    angle: float = 0.0
    intensity: float = 1.0
    fill: int = 0
    gradient: bool = False
