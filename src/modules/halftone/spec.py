from dataclasses import dataclass


@dataclass
class HalftoneSpec:
    lpi: int = 55
    dpi: int = 1200
    ppi: int | None = None
    hardmix: bool = False
