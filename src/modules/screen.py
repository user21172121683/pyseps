# SPDX-License-Identifier: AGPL-3.0-or-later

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

import numpy as np

from core.registry import MODULE_REGISTRY


@dataclass
class ScreenSpec:
    lpi: int = 55
    dpi: int = 1200
    ppi: int | None = None
    hardmix: bool = False


class ScreenBase(ABC):
    """Base screen."""

    def __init__(self, spec: ScreenSpec):
        self.spec = spec
        self.spacing = spec.ppi / spec.lpi

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spec={repr(self.spec)})"

    def compute_intensity_map(
        self, image_array: np.ndarray, angle: float
    ) -> list[tuple[float, float, float]]:
        """
        Compute intensity samples across the image.
        Returns a list of (x, y, intensity) tuples.
        """

        height, width = image_array.shape
        intensity_map = []

        for x, y in self._iter_grid_points(image_array, angle):
            block = self._get_clipped_block(x, y, width, height, image_array)
            if block is None or block.size == 0:
                continue

            avg = np.mean(block)
            intensity = max(0.0, min(1.0, float(avg) / 255.0))
            intensity_map.append((x, y, intensity))

        return intensity_map

    def _get_clipped_block(
        self, x: float, y: float, width: int, height: int, pixels: np.ndarray
    ) -> np.ndarray | None:
        """Return the pixel block centered at (x, y), clipped to image bounds."""
        half = self.spacing / 2
        x0, y0 = int(x - half), int(y - half)
        x1, y1 = int(x + half), int(y + half)

        x0_clip = max(0, x0)
        y0_clip = max(0, y0)
        x1_clip = min(width, x1)
        y1_clip = min(height, y1)

        if x0_clip >= x1_clip or y0_clip >= y1_clip:
            return None

        return pixels[y0_clip:y1_clip, x0_clip:x1_clip]

    @abstractmethod
    def _iter_grid_points(
        self, image_array: np.ndarray, angle=0
    ) -> Iterator[tuple[float, float]]:
        """Yield center positions for dot placement."""
        raise NotImplementedError


@MODULE_REGISTRY.register(
    "am", "amplitude", "amplitude modulation", spec_cls=ScreenSpec
)
class AMScreen(ScreenBase):
    """Uniform cell grid."""

    def _iter_grid_points(
        self, image_array: np.ndarray, angle=0
    ) -> Iterator[tuple[float, float]]:
        height, width = image_array.shape[:2]
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        cx, cy = width / 2, height / 2

        # Rotated bounds of image
        corners = [
            (-cx, -cy),
            (width - cx, -cy),
            (-cx, height - cy),
            (width - cx, height - cy),
        ]

        rotated_x = []
        rotated_y = []
        for x, y in corners:
            rx = x * cos_a + y * sin_a
            ry = -x * sin_a + y * cos_a
            rotated_x.append(rx)
            rotated_y.append(ry)

        min_rx = min(rotated_x)
        max_rx = max(rotated_x)
        min_ry = min(rotated_y)
        max_ry = max(rotated_y)

        nx = int(math.ceil((max_rx - min_rx) / self.spacing))
        ny = int(math.ceil((max_ry - min_ry) / self.spacing))

        for i in range(nx + 1):
            for j in range(ny + 1):
                rx = min_rx + i * self.spacing
                ry = min_ry + j * self.spacing

                # Inverse rotation to image space
                dx = rx * cos_a - ry * sin_a
                dy = rx * sin_a + ry * cos_a

                x = dx + cx
                y = dy + cy

                if 0 <= x < width and 0 <= y < height:
                    yield x, y


@MODULE_REGISTRY.register(
    "dither", "floyd", "floyd-steinberg", "floydsteinberg", spec_cls=ScreenSpec
)
class DitherScreen(ScreenBase):
    """Floyd-Steinberg dithered cell grid."""

    def _iter_grid_points(
        self, image_array: np.ndarray, angle=0
    ) -> Iterator[tuple[float, float]]:
        spacing = int(self.spacing)
        height, width = image_array.shape[:2]
        theta = math.radians(angle)

        # Convert to grayscale if needed
        if image_array.ndim == 3:
            arr = np.mean(image_array, axis=2).astype(np.float32) / 255.0
        else:
            arr = image_array.astype(np.float32) / 255.0

        # Downscale to dot grid size
        small_h = max(1, height // spacing)
        small_w = max(1, width // spacing)
        small = arr[::spacing, ::spacing]
        out = np.zeros_like(small)

        # Floyd-Steinberg dithering
        h_s, w_s = small.shape
        for y in range(h_s):
            for x in range(w_s):
                old_pixel = small[y, x]
                new_pixel = 1.0 if old_pixel >= 0.5 else 0.0
                out[y, x] = new_pixel
                error = old_pixel - new_pixel

                if x + 1 < w_s:
                    small[y, x + 1] += error * 7 / 16
                if x - 1 >= 0 and y + 1 < h_s:
                    small[y + 1, x - 1] += error * 3 / 16
                if y + 1 < h_s:
                    small[y + 1, x] += error * 5 / 16
                if x + 1 < w_s and y + 1 < h_s:
                    small[y + 1, x + 1] += error * 1 / 16

        # Yield positions
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        cx, cy = width / 2, height / 2
        scx, scy = small_w / 2, small_h / 2

        for j in range(h_s):
            for i in range(w_s):
                if out[j, i] >= 1.0:
                    rx = (i + 0.5) * spacing
                    ry = (j + 0.5) * spacing

                    dx = rx - scx * spacing
                    dy = ry - scy * spacing

                    ox = dx * cos_theta - dy * sin_theta + cx
                    oy = dx * sin_theta + dy * cos_theta + cy

                    yield ox, oy


@MODULE_REGISTRY.register("threshold", spec_cls=ScreenSpec)
class ThresholdScreen(ScreenBase):
    """Threshold-based screen."""

    def _iter_grid_points(
        self, image_array: np.ndarray, angle=0
    ) -> Iterator[tuple[float, float]]:

        ys, xs = np.nonzero(image_array > 127)
        # Yield as floats
        for x, y in zip(xs, ys):
            yield float(x), float(y)
