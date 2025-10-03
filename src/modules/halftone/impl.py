import math
from typing import Iterator

from PIL import Image
import numpy as np

from core.registry import MODULE_REGISTRY
from .base import HalftoneBase


@MODULE_REGISTRY.register("am", "amplitude", "amplitude modulation")
class AMHalftone(HalftoneBase):
    """Uniform cell grid."""

    def _iter_grid_points(self, resized_image, angle=0):
        width, height = resized_image.size
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


@MODULE_REGISTRY.register("dither", "floyd", "floyd-steinberg", "floydsteinberg")
class DitherHalftone(HalftoneBase):
    """Floyd-Steinberg dithered cell grid."""

    def _iter_grid_points(
        self, resized_image, angle=0
    ) -> Iterator[tuple[float, float]]:
        spacing = int(self.spacing)
        w, h = resized_image.size
        theta = math.radians(angle)

        # Rotate image for halftone screen angle
        rotated = resized_image.rotate(
            angle, resample=Image.Resampling.BICUBIC, expand=True
        )
        rw, rh = rotated.size

        # Downscale to dot grid size
        small = rotated.resize(
            (rw // spacing, rh // spacing),
            resample=Image.Resampling.LANCZOS,
        ).convert("L")

        arr = np.array(small, dtype=np.float32) / 255.0
        height, width = arr.shape
        out = np.zeros_like(arr)

        # Apply Floyd-Steinberg Dithering
        for y in range(height):
            for x in range(width):
                old_pixel = arr[y, x]
                new_pixel = 1.0 if old_pixel >= 0.5 else 0.0
                out[y, x] = new_pixel
                error = old_pixel - new_pixel

                if x + 1 < width:
                    arr[y, x + 1] += error * 7 / 16
                if x - 1 >= 0 and y + 1 < height:
                    arr[y + 1, x - 1] += error * 3 / 16
                if y + 1 < height:
                    arr[y + 1, x] += error * 5 / 16
                if x + 1 < width and y + 1 < height:
                    arr[y + 1, x + 1] += error * 1 / 16

        # Yield positions for dots, rotating back to original image space
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)

        # Center of the rotated image
        rcx = rw / 2
        rcy = rh / 2

        # Center of original image (for inverse mapping)
        ocx = w / 2
        ocy = h / 2

        for j in range(height):
            for i in range(width):
                if out[j, i] >= 1.0:
                    # Position in rotated space
                    rx = (i + 0.5) * spacing
                    ry = (j + 0.5) * spacing

                    # Rotate back to original image space
                    dx = rx - rcx
                    dy = ry - rcy
                    ox = dx * cos_theta - dy * sin_theta + ocx
                    oy = dx * sin_theta + dy * cos_theta + ocy

                    yield (ox, oy)


@MODULE_REGISTRY.register("threshold")
class ThresholdHalftone(HalftoneBase):
    """Threshold-based halftone."""

    def _iter_grid_points(
        self, resized_image, angle=0
    ) -> Iterator[tuple[float, float]]:
        grayscale = resized_image.convert("L")
        pixels = np.array(grayscale)

        height, width = pixels.shape

        for y in range(height):
            for x in range(width):
                if pixels[y, x] > 127:
                    yield float(x), float(y)
