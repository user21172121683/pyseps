from dataclasses import dataclass, field


class Spec:
    def __init__(self):
        self._on_change = None

    def __setattr__(self, name, value):
        # Allow internal set without triggering change
        if name == "_on_change":
            object.__setattr__(self, name, value)
            return

        old_value = getattr(self, name, None)
        super().__setattr__(name, value)

        # Only call _on_change if it exists and is not None
        if hasattr(self, "_on_change") and self._on_change and value != old_value:
            self._on_change()

    def set_on_change(self, callback):
        self._on_change = callback


@dataclass
class PreSpec(Spec):
    grayscale: bool = True
    resize: tuple[int, int] = (0, 0)


@dataclass
class SplitSpec(Spec):
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

    def __post_init__(self):
        super().__init__()


@dataclass
class HalftoneSpec(Spec):
    lpi: int = 55
    dpi: int = 1200
    ppi: int | None = None
    hardmix: bool = False

    def __post_init__(self):
        super().__init__()


@dataclass
class DotSpec(Spec):
    fill: int = 0
    gradient: bool = False
    gain: float = 0.0
    modulate: bool = True

    def __post_init__(self):
        super().__init__()
