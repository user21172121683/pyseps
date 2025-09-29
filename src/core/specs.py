from dataclasses import dataclass


@dataclass
class SplitSpec:
    tones: dict[str, tuple[int, int, int]]
    threshold: int = 30
    substrate: tuple[int, int, int] = (255, 255, 255)
    angles: tuple[int, ...] = (15, 75, 0, 45)


@dataclass
class HalftoneSpec:
    lpi: int = 55
    dpi: int = 1200
    ppi: int | None = None
    hardmix: bool = False


@dataclass
class DotSpec:
    fill: int = 0
    gradient: bool = False
    gain: float = 0.0
    modulate: bool = True
