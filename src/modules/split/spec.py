from dataclasses import dataclass, field


@dataclass
class SplitSpec:
    tones: tuple[tuple[int, int, int]] = field(
        default_factory=lambda: (
            (0, 255, 255),
            (255, 0, 255),
            (255, 255, 0),
            (0, 0, 0),
        )
    )
    threshold: int = 30
    substrate: tuple[int, int, int] = (255, 255, 255)
    angles: tuple[int, ...] = (15, 75, 0, 45)
