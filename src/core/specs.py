from dataclasses import dataclass, field

@dataclass
class PreSpec:
    grayscale: bool = True
    resize: tuple[int, int] = (0, 0)


@dataclass
class SplitSpec:
    tones: dict[str, tuple[int, int, int]] = field(
        default_factory=lambda: {
            "red": (255, 0, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "black": (0, 0, 0),
        }
    )
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
