# SPDX-License-Identifier: AGPL-3.0-or-later

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import cairo

from core.registry import MODULE_REGISTRY

from .screen import ScreenSpec


@dataclass
class DotSpec:
    gain: float = 0.0
    size: str = "radius"
    angle: str = "grid"


class DotBase(ABC):
    def __init__(self, spec: DotSpec, screen_spec: ScreenSpec):
        self.spec = spec
        self.screen_spec = screen_spec
        self.spacing = screen_spec.ppi / screen_spec.lpi
        self.scale = screen_spec.dpi / screen_spec.ppi

    def render(
        self,
        intensity_flow_array: np.ndarray,
        base_image: np.ndarray,
    ) -> np.ndarray:
        """
        Render a halftone pattern from the screening array that includes intensity and flow angles.
        """

        base_image = self._resize(base_image)
        height, width = base_image.shape

        # Create Cairo image surface
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
        ctx = cairo.Context(surface)

        # Fill background white
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()

        # Unpack vectorially
        x_coords = intensity_flow_array[:, 0] * self.scale
        y_coords = intensity_flow_array[:, 1] * self.scale
        intensities = intensity_flow_array[:, 2]
        angles_deg = intensity_flow_array[:, 3]

        # Draw dots
        for x, y, intensity, angle in zip(x_coords, y_coords, intensities, angles_deg):
            self._draw(
                ctx=ctx,
                center=(x, y),
                size=self.spacing * self.scale,
                angle=angle,
                intensity=intensity,
            )

        # Convert Cairo RGB surface to NumPy grayscale
        buf = surface.get_data()
        screen_image = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 4))
        screen_gray = screen_image[:, :, 0]

        if self.spec.size == "hardmix":
            screen_gray = self._hardmix(base_image, screen_gray)

        return screen_gray

    def _hardmix(self, base_image: np.ndarray, screen_gray: np.ndarray) -> np.ndarray:
        """
        Apply hardmix blending of the halftone over the base grayscale image.
        """

        # Invert the base image
        inverted_base = 255 - base_image.astype(int)

        # Combine with the halftone
        combined = inverted_base + screen_gray.astype(int)

        # Apply hardmix threshold
        result = np.where(combined < 255, 0, 255).astype(np.uint8)

        return result

    def _resize(self, image: np.ndarray) -> np.ndarray:
        """Resize the NumPy image array to match the screen DPI (nearest-neighbor)."""

        if self.screen_spec.ppi != self.screen_spec.dpi:
            new_height = max(1, int(image.shape[0] * self.scale))
            new_width = max(1, int(image.shape[1] * self.scale))
            # Nearest-neighbor resizing
            y_indices = (np.arange(new_height) / self.scale).astype(int)
            x_indices = (np.arange(new_width) / self.scale).astype(int)
            resized = image[y_indices[:, None], x_indices]
            return resized
        return image

    def _draw(
        self,
        ctx: cairo.Context,
        *,
        center: tuple[float, float],
        size: float,
        angle: float,
        intensity: float,
    ):
        if self.spec.size == "hardmix":
            self._draw_concentric(ctx, center, size, angle, intensity)
        if self.spec.size == "radius":
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
        if not self.spec.size == "radius":
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
