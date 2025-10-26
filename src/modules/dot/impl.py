import math

from PIL import ImageDraw

from core.registry import MODULE_REGISTRY
from .base import DotBase


@MODULE_REGISTRY.register("round", "round dot")
class RoundDot(DotBase):
    """Simple round dot."""

    def _draw_shape(
        self,
        canvas: ImageDraw,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
        fill: int = 0,
    ):
        cx, cy = center
        r = self._return_half_size(size, intensity)
        bbox = [cx - r, cy - r, cx + r, cy + r]
        canvas.ellipse(bbox, fill=fill)


@MODULE_REGISTRY.register("square", "square dot")
class SquareDot(DotBase):
    """Simple square dot."""

    def _draw_shape(
        self,
        canvas: ImageDraw,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
        fill: int = 0,
    ):
        cx, cy = center
        half = self._return_half_size(size, intensity)

        # Define corners of an unrotated square
        corners = [
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        ]

        # Rotate if needed
        if angle != 0:
            corners = self._rotate_shape(corners, center, angle)

        canvas.polygon(corners, fill=fill)


@MODULE_REGISTRY.register("elliptical", "ellipse", "elliptical dot")
class EllipticalDot(DotBase):
    """Asymmetrically modulated elliptical dot."""

    def _draw_shape(
        self,
        canvas: ImageDraw,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
        fill: int = 0,
    ):
        cx, cy = center

        # Compute ellipse radii
        rx = self._return_half_size(size, intensity)

        # Aspect ratio modulates with intensity (more circular as intensity ↑)
        min_aspect_ratio = 1.0
        max_aspect_ratio = 4.0
        aspect_ratio = min_aspect_ratio + (1.0 - intensity) * (
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
        if angle != 0:
            points = self._rotate_shape(points, center, angle)

        canvas.polygon(points, fill=fill)
