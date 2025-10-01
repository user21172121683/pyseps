from dataclasses import dataclass, field


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
