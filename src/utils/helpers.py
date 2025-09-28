def norm_intensity(value: int) -> float:
    return max(0.0, min(1.0, value / 255.0))
