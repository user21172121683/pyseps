from dataclasses import dataclass


@dataclass
class PreSpec:
    grayscale: bool = False
    resize: tuple[int, int] = (0, 0)
