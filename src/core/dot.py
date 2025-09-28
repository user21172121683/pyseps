from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
from PIL import ImageDraw


@dataclass
class DotSpec:
    canvas: ImageDraw
    center: tuple[float, float]
    size: float
    angle: float = 0.0
    intensity: float = 1.0
    fill: int = 0
    gradient: bool = False


class Dot(ABC):
    def draw(self, spec: DotSpec):
        if spec.gradient:
            self._draw_concentric(spec)
        else:
            self._draw_shape(spec)

    def _draw_concentric(self, spec: DotSpec) -> None:
        radius = spec.size / 2
        for r in range(int(radius), 0, -1):
            t = (r / radius) ** 3
            current_fill = int(255 * t)
            updated_spec = DotSpec(
                canvas=spec.canvas,
                center=spec.center,
                size=r * 2,
                angle=spec.angle,
                intensity=spec.intensity,
                fill=current_fill,
                gradient=False,
            )
            self._draw_shape(updated_spec)

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

    @abstractmethod
    def _draw_shape(self, spec: DotSpec):
        pass


class RoundDot(Dot):
    """Simple round dot."""

    def _draw_shape(self, spec: DotSpec):
        cx, cy = spec.center
        r = (spec.size * spec.intensity) / 2
        bbox = [cx - r, cy - r, cx + r, cy + r]
        spec.canvas.ellipse(bbox, fill=spec.fill)


class SquareDot(Dot):
    """Simple square dot."""

    def _draw_shape(self, spec: DotSpec):
        cx, cy = spec.center
        half = (spec.size * spec.intensity) / 2

        # Define corners of an unrotated square
        corners = [
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        ]

        # Rotate if needed
        if spec.angle != 0:
            corners = self._rotate_shape(corners, spec.center, spec.angle)

        spec.canvas.polygon(corners, fill=spec.fill)


class EllipticalDot(Dot):
    """Asymmetrically modulated elliptical dot."""

    def _draw_shape(self, spec: DotSpec):
        cx, cy = spec.center

        # Compute ellipse radii
        rx = (spec.size * spec.intensity) / 2.0

        # Aspect ratio modulates with intensity (more circular as intensity ↑)
        min_aspect_ratio = 1.0
        max_aspect_ratio = 4.0
        aspect_ratio = min_aspect_ratio + (1.0 - spec.intensity) * (
            max_aspect_ratio - min_aspect_ratio
        )

        ry = rx / aspect_ratio

        # Generate ellipse perimeter points
        num_points = 100
        theta_step = 2 * math.pi / num_points
        points = [
            (
                cx + rx * math.cos(theta),
                cy + ry * math.sin(theta),
            )
            for theta in (i * theta_step for i in range(num_points))
        ]

        # Rotate ellipse if needed
        if spec.angle != 0:
            points = self._rotate_shape(points, spec.center, spec.angle)

        spec.canvas.polygon(points, fill=spec.fill)
