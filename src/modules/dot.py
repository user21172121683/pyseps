# SPDX-License-Identifier: AGPL-3.0-or-later

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

import cairo

from core.registry import MODULE_REGISTRY


@dataclass
class DotSpec:
    gradient: bool = False
    gain: float = 0.0
    modulate: bool = True


class DotBase(ABC):
    def __init__(self, spec: DotSpec):
        self.spec = spec

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spec={repr(self.spec)})"

    def draw(
        self,
        ctx: cairo.Context,
        *,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
    ):
        if self.spec.gradient:
            self._draw_concentric(ctx, center, size, angle, intensity)
        else:
            self._draw_shape(ctx, center, size, angle, intensity)

    def _draw_concentric(
        self,
        ctx: cairo.Context,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
    ):
        radius = size / 2
        for r in range(int(radius), 0, -1):
            t = (r / radius) ** 3
            self._draw_shape(ctx, center, r * 2, angle, intensity, fill=int(255 * t))

    def _return_half_size(self, size: float, intensity: float) -> float:
        if not self.spec.modulate:
            intensity = 1.0
        adjusted_radius = ((size * intensity) / 2) * (1 - self.spec.gain)
        return max(adjusted_radius, 0.0)

    @abstractmethod
    def _draw_shape(
        self,
        ctx: cairo.Context,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
        fill: int = 0,
    ):
        pass


@MODULE_REGISTRY.register("round", "round dot", spec_cls=DotSpec)
class RoundDot(DotBase):
    """Simple round dot."""

    def _draw_shape(
        self,
        ctx: cairo.Context,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
        fill: int = 0,
    ):
        cx, cy = center
        r = self._return_half_size(size, intensity)
        # Normalize fill to [0,1] for Cairo
        fill_normalized = fill / 255
        ctx.set_source_rgb(fill_normalized, fill_normalized, fill_normalized)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.fill()


@MODULE_REGISTRY.register("square", "square dot", spec_cls=DotSpec)
class SquareDot(DotBase):
    """Simple square dot."""

    def _draw_shape(
        self,
        ctx: cairo.Context,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
        fill: int = 0,
    ):
        cx, cy = center
        half = self._return_half_size(size, intensity)
        fill_normalized = fill / 255
        ctx.set_source_rgb(fill_normalized, fill_normalized, fill_normalized)

        # Save context for rotation
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(math.radians(angle))
        ctx.rectangle(-half, -half, half * 2, half * 2)
        ctx.fill()
        ctx.restore()
