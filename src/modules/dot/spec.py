from dataclasses import dataclass


@dataclass
class DotSpec:
    fill: int = 0
    gradient: bool = False
    gain: float = 0.0
    modulate: bool = True
