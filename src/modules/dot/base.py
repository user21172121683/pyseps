# SPDX-License-Identifier: AGPL-3.0-or-later

from abc import ABC, abstractmethod
import math

from PIL import ImageDraw

from .spec import DotSpec


class DotBase(ABC):
    def __init__(self, spec: DotSpec):
        self.spec = spec

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spec={repr(self.spec)})"

    def draw(
        self,
        canvas: ImageDraw,
        *,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
    ):
        if self.spec.gradient:
            self._draw_concentric(
                canvas=canvas,
                center=center,
                size=size,
                angle=angle,
                intensity=intensity,
            )
        else:
            self._draw_shape(
                canvas=canvas,
                center=center,
                size=size,
                angle=angle,
                intensity=intensity,
            )

    def _draw_concentric(
        self,
        canvas: ImageDraw,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
    ) -> None:
        radius = size / 2
        for r in range(int(radius), 0, -1):
            t = (r / radius) ** 3
            self._draw_shape(
                canvas=canvas,
                center=center,
                size=r * 2,
                angle=angle,
                intensity=intensity,
                fill=int(255 * t),
            )

    def _rotate_shape(
        self,
        points: list[tuple[float, float]],
        center: tuple[float, float],
        angle: float,
    ) -> list[tuple[float, float]]:
        cx, cy = center
        angle_rad = math.radians(angle)
        cos_theta = math.cos(angle_rad)
        sin_theta = math.sin(angle_rad)
        rotated_points = []
        for x, y in points:
            dx = x - cx
            dy = y - cy
            qx = cx + cos_theta * dx - sin_theta * dy
            qy = cy + sin_theta * dx + cos_theta * dy
            rotated_points.append((qx, qy))
        return rotated_points

    def _return_half_size(self, size: float, intensity: float) -> float:
        if not self.spec.modulate:
            intensity = 1.0

        adjusted_radius = ((size * intensity) / 2) * (1 - self.spec.gain)

        return max(adjusted_radius, 0.0)

    @abstractmethod
    def _draw_shape(
        self,
        canvas: ImageDraw,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
        fill: int = 0,
    ):
        pass
