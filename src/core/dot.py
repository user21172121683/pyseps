from abc import ABC, abstractmethod
import math
from PIL import ImageDraw


class Dot(ABC):
    def __init__(
        self,
        *,
        gradient: bool = False,
    ):
        self.gradient = gradient

    def draw(
        self,
        canvas: ImageDraw,
        *,
        angle: float = 0.0,
        center: tuple,
        size: float,
        intensity: float = 1.0,
        fill: int = 0,
    ):
        if self.gradient:
            self._draw_concentric(
                canvas=canvas,
                center=center,
                angle=angle,
                size=size,
                intensity=intensity,
            )
        else:
            self._draw_shape(
                canvas=canvas,
                center=center,
                angle=angle,
                size=size,
                intensity=intensity,
                fill=fill,
            )

    def _draw_concentric(
        self,
        canvas: ImageDraw,
        *,
        center: tuple[float, float],
        angle: float = 0.0,
        size: float,
        intensity: float,
    ) -> None:
        """
        Draw concentric shapes fading from center (0) to edge (255).
        """
        radius = size / 2
        for r in range(int(radius), 0, -1):
            t = r / radius
            current_fill = int(255 * t)
            self._draw_shape(
                canvas=canvas,
                center=center,
                angle=angle,
                size=r * 2,
                intensity=intensity,
                fill=current_fill,
            )

    def _rotate_shape(
        self,
        points: list[tuple[float, float]],
        center: tuple[float, float],
        angle: float,
    ) -> list[tuple[float, float]]:
        """Rotate list of points around center."""
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
    def _draw_shape(
        self,
        canvas: ImageDraw,
        *,
        center: tuple,
        angle: float = 0.0,
        size: float,
        intensity: float = 1.0,
        fill: int = 0,
    ):
        pass


class RoundDot(Dot):
    """Simple round dot."""

    def _draw_shape(
        self,
        canvas: ImageDraw,
        *,
        center: tuple,
        angle: float = 0.0,
        size: float,
        intensity: float = 1.0,
        fill: int = 0,
    ):
        cx, cy = center
        r = (size * intensity) / 2
        bbox = [cx - r, cy - r, cx + r, cy + r]
        canvas.ellipse(bbox, fill=fill)


class SquareDot(Dot):
    """Simple square dot."""

    def _draw_shape(
        self,
        canvas: ImageDraw,
        *,
        center: tuple,
        angle: float = 0.0,
        size: float,
        intensity: float = 1.0,
        fill: int = 0,
    ):
        cx, cy = center
        half = (size * intensity) / 2

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


class EllipticalDot(Dot):
    """Asymmetrically modulated elliptical dot."""

    def _draw_shape(
        self,
        canvas: ImageDraw,
        *,
        center: tuple,
        angle: float = 0.0,
        size: float,
        intensity: float,
        fill: int = None,
    ):
        cx, cy = center

        # Compute ellipse radii
        rx = (size * intensity) / 2.0

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
