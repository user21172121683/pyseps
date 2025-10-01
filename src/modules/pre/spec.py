from dataclasses import dataclass


@dataclass
class PreSpec:
    grayscale: bool = True
    resize: tuple[int, int] = (0, 0)
